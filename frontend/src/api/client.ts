// Input: 前端组件调用的请求参数与浏览器 fetch。
// Output: 输出统一的后端 API 调用函数。
// Pos: 前端 API 适配层。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import type {
  AgentAttachment,
  ArtifactDetail,
  ArtifactDiff,
  ArtifactSummary,
  ExperienceItem,
  JDSummary,
  MessageResponse,
  SessionHistoryItem,
  SessionState,
  TrackSummary,
} from "../types";

const defaultBaseUrl = "http://127.0.0.1:8000";

function buildUrl(path: string) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || defaultBaseUrl;
  return `${baseUrl}${path}`;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function startSession(input: {
  project_name: string;
  cycle: string;
  base_resume_text: string;
}): Promise<SessionState> {
  const response = await fetch(buildUrl("/agent/sessions"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const payload = await parseJson<SessionState>(response);
  return { ...payload, traces: payload.traces || [] };
}

export async function sendMessage(
  sessionId: string,
  input: {
    content: string;
    attachments: AgentAttachment[];
    active_track_id: string;
    active_track_name: string;
  },
): Promise<MessageResponse> {
  const response = await fetch(buildUrl(`/agent/sessions/${sessionId}/messages`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      role: "user",
      content: input.content,
      attachments: input.attachments,
      active_track_id: input.active_track_id,
      active_track_name: input.active_track_name,
    }),
  });
  return parseJson<MessageResponse>(response);
}

export async function getSession(sessionId: string): Promise<SessionState> {
  const response = await fetch(buildUrl(`/agent/sessions/${sessionId}`));
  return parseJson<SessionState>(response);
}

export async function listSessions(limit = 30): Promise<SessionHistoryItem[]> {
  const response = await fetch(buildUrl(`/agent/sessions?limit=${limit}`));
  const payload = await parseJson<{ sessions: SessionHistoryItem[] }>(response);
  return payload.sessions;
}

export async function uploadAttachment(input: {
  file: File;
  attachmentType: AgentAttachment["type"];
  sessionId?: string;
}): Promise<AgentAttachment> {
  const formData = new FormData();
  formData.append("file", input.file);
  formData.append("attachment_type", input.attachmentType);
  if (input.sessionId) {
    formData.append("session_id", input.sessionId);
  }

  const response = await fetch(buildUrl("/agent/uploads"), {
    method: "POST",
    body: formData,
  });
  return parseJson<AgentAttachment>(response);
}

export async function createTrack(
  projectId: string,
  input: {
    name: string;
    positioning: string;
    core_keywords: string[];
    resume_strategy: string;
    default_resume_outline: string;
  },
): Promise<TrackSummary> {
  const response = await fetch(buildUrl(`/agent/projects/${projectId}/tracks`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const payload = await parseJson<{ track: TrackSummary }>(response);
  return payload.track;
}

export async function updateTrack(
  trackId: string,
  input: {
    name: string;
    positioning: string;
    core_keywords: string[];
    resume_strategy: string;
    default_resume_outline: string;
  },
): Promise<TrackSummary> {
  const response = await fetch(buildUrl(`/agent/tracks/${trackId}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const payload = await parseJson<{ track: TrackSummary }>(response);
  return payload.track;
}

export async function deleteTrack(trackId: string): Promise<void> {
  const response = await fetch(buildUrl(`/agent/tracks/${trackId}`), {
    method: "DELETE",
  });
  await parseJson<{ ok: boolean }>(response);
}

export async function listTrackJds(trackId: string): Promise<JDSummary[]> {
  const response = await fetch(buildUrl(`/agent/tracks/${trackId}/jds`));
  const payload = await parseJson<{ jds: JDSummary[] }>(response);
  return payload.jds;
}

export async function createTrackJd(
  trackId: string,
  input: {
    name: string;
    content: string;
    set_as_primary: boolean;
  },
): Promise<JDSummary> {
  const response = await fetch(buildUrl(`/agent/tracks/${trackId}/jds`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const payload = await parseJson<{ jd: JDSummary }>(response);
  return payload.jd;
}

export async function updateJd(
  jdId: string,
  input: {
    name: string;
    content?: string;
  },
): Promise<JDSummary> {
  const response = await fetch(buildUrl(`/agent/jds/${jdId}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const payload = await parseJson<{ jd: JDSummary }>(response);
  return payload.jd;
}

export async function deleteJd(jdId: string): Promise<void> {
  const response = await fetch(buildUrl(`/agent/jds/${jdId}`), {
    method: "DELETE",
  });
  await parseJson<{ ok: boolean }>(response);
}

export async function setPrimaryJd(trackId: string, jdEntryId: string): Promise<TrackSummary> {
  const response = await fetch(buildUrl(`/agent/tracks/${trackId}/primary-jd`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jd_entry_id: jdEntryId }),
  });
  const payload = await parseJson<{ track: TrackSummary }>(response);
  return payload.track;
}

export async function updateProfile(
  projectId: string,
  input: {
    summary: string;
    basics: Record<string, unknown>;
    preferences: Record<string, unknown>;
    constraints: Record<string, unknown>;
  },
): Promise<void> {
  const response = await fetch(buildUrl(`/agent/projects/${projectId}/profile`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  await parseJson<{ profile: unknown }>(response);
}

export async function createExperience(
  projectId: string,
  input: {
    title: string;
    organization: string;
    time_range: string;
    summary: string;
    tags: string[];
    metrics: string[];
    evidence: string[];
    confidence: number;
    source: string;
  },
): Promise<ExperienceItem> {
  const response = await fetch(buildUrl(`/agent/projects/${projectId}/experiences`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const payload = await parseJson<{ experience: ExperienceItem }>(response);
  return payload.experience;
}

export async function updateExperience(
  experienceId: string,
  input: {
    title: string;
    organization: string;
    time_range: string;
    summary: string;
    tags: string[];
    metrics: string[];
    evidence: string[];
    confidence: number;
    source: string;
  },
): Promise<ExperienceItem> {
  const response = await fetch(buildUrl(`/agent/experiences/${experienceId}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const payload = await parseJson<{ experience: ExperienceItem }>(response);
  return payload.experience;
}

export async function deleteExperience(experienceId: string): Promise<void> {
  const response = await fetch(buildUrl(`/agent/experiences/${experienceId}`), {
    method: "DELETE",
  });
  await parseJson<{ ok: boolean }>(response);
}

export async function listArtifacts(projectId: string, limit = 50): Promise<ArtifactSummary[]> {
  const response = await fetch(buildUrl(`/agent/projects/${projectId}/artifacts?limit=${limit}`));
  const payload = await parseJson<{ artifacts: ArtifactSummary[] }>(response);
  return payload.artifacts;
}

export async function getArtifactDetail(artifactId: string): Promise<ArtifactDetail> {
  const response = await fetch(buildUrl(`/agent/artifacts/${artifactId}`));
  return parseJson<ArtifactDetail>(response);
}

export async function diffArtifact(artifactId: string, baseArtifactId: string): Promise<ArtifactDiff> {
  const response = await fetch(buildUrl(`/agent/artifacts/${artifactId}/diff`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ base_artifact_id: baseArtifactId }),
  });
  return parseJson<ArtifactDiff>(response);
}

export async function exportArtifact(
  artifactId: string,
  format: "docx" | "pdf",
): Promise<{ artifact_id: string; format: string; path: string; generated_at: string }> {
  const response = await fetch(buildUrl(`/agent/artifacts/${artifactId}/export`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format }),
  });
  return parseJson<{ artifact_id: string; format: string; path: string; generated_at: string }>(response);
}

export async function saveArtifactRevision(
  artifactId: string,
  content: string,
): Promise<ArtifactSummary> {
  const response = await fetch(buildUrl(`/agent/artifacts/${artifactId}/revisions`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  const payload = await parseJson<{ artifact: ArtifactSummary }>(response);
  return payload.artifact;
}
