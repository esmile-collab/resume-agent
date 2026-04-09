// Input: 浏览器事件、API 客户端和各子面板组件。
// Output: 输出统一的工作台状态编排与页面布局。
// Pos: React 前端总控组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import { useEffect, useMemo, useState } from "react";

import {
  createExperience,
  createTrack,
  createTrackJd,
  deleteExperience,
  deleteJd,
  deleteTrack,
  diffArtifact,
  exportArtifact,
  getArtifactDetail,
  getSession,
  listArtifacts,
  listSessions,
  listTrackJds,
  saveArtifactRevision,
  sendMessage,
  setPrimaryJd,
  startSession,
  updateExperience,
  updateJd,
  updateProfile,
  updateTrack,
  uploadAttachment,
} from "./api/client";
import { ChatPanel } from "./components/ChatPanel";
import { MatchesBoard } from "./components/MatchesBoard";
import { ResumeEditorPanel } from "./components/ResumeEditorPanel";
import { SessionHistoryPanel } from "./components/SessionHistoryPanel";
import { StartPanel } from "./components/StartPanel";
import type {
  AgentAttachment,
  ArtifactDetail,
  ArtifactDiff,
  ArtifactSummary,
  ChatMessage,
  ExperienceItem,
  JDSummary,
  MessageResponse,
  SessionHistoryItem,
  SessionState,
  TrackSummary,
} from "./types";

type WorkspaceTab = "resume" | "matches";

function makeLocalMessage(id: string, role: string, content: string): ChatMessage {
  return { id, role, content };
}

function hydrateMessages(state: SessionState): ChatMessage[] {
  const recent = state.snapshot.recent_messages ?? [];
  if (recent.length === 0) {
    return [
      makeLocalMessage(
        "assistant-welcome",
        "assistant",
        "工作台已就绪。先补充背景、目标岗位，或直接上传一条 JD。",
      ),
    ];
  }
  return [...recent].reverse().map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    metadata: message.metadata,
  }));
}

function isEditableArtifact(artifactType: string) {
  return ["generated_resume", "polished_resume", "edited_resume"].includes(artifactType);
}

function pickPreferredArtifactId(
  artifacts: ArtifactSummary[],
  currentSelectedId: string,
  preferredArtifactId = "",
) {
  if (
    preferredArtifactId &&
    artifacts.some(
      (artifact) => artifact.id === preferredArtifactId && isEditableArtifact(artifact.artifact_type),
    )
  ) {
    return preferredArtifactId;
  }
  const currentArtifact = artifacts.find((artifact) => artifact.id === currentSelectedId);
  if (currentArtifact && isEditableArtifact(currentArtifact.artifact_type)) {
    return currentSelectedId;
  }
  return artifacts.find((artifact) => isEditableArtifact(artifact.artifact_type))?.id ?? "";
}

function extractGeneratedArtifactId(response: MessageResponse) {
  const toolSteps = response.tool_steps ?? [];
  for (let index = toolSteps.length - 1; index >= 0; index -= 1) {
    const observation = toolSteps[index].observation;
    const artifact = observation.artifact as { id?: string; artifact_type?: string } | undefined;
    if (artifact?.id && artifact.artifact_type && isEditableArtifact(artifact.artifact_type)) {
      return artifact.id;
    }
  }
  return "";
}

function pickLatestScoreArtifact(artifacts: ArtifactSummary[], activeTrackId = "") {
  const scoreArtifacts = artifacts.filter((artifact) => artifact.artifact_type === "score_report");
  const candidates = activeTrackId
    ? scoreArtifacts.filter((artifact) => artifact.track_id === activeTrackId)
    : scoreArtifacts;

  return [...candidates].sort((left, right) => {
    if (right.version !== left.version) {
      return right.version - left.version;
    }
    return right.created_at.localeCompare(left.created_at);
  })[0];
}

const emptyAttachment: AgentAttachment = { type: "other", content: "", name: "" };
const sessionStorageKey = "resume-agent-session-id";
const activeTrackStorageKey = "resume-agent-active-track-id";

export default function App() {
  const [projectName, setProjectName] = useState("产品经理秋招资产");
  const [cycle, setCycle] = useState("2026 秋招");
  const [baseResumeText, setBaseResumeText] = useState("");
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [attachment, setAttachment] = useState<AgentAttachment>(emptyAttachment);
  const [activeTrack, setActiveTrack] = useState<TrackSummary | null>(null);
  const [trackJds, setTrackJds] = useState<JDSummary[]>([]);
  const [sessions, setSessions] = useState<SessionHistoryItem[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([]);
  const [selectedArtifactId, setSelectedArtifactId] = useState("");
  const [selectedArtifactDetail, setSelectedArtifactDetail] = useState<ArtifactDetail | null>(null);
  const [latestScoreDetail, setLatestScoreDetail] = useState<ArtifactDetail | null>(null);
  const [artifactDiffState, setArtifactDiffState] = useState<ArtifactDiff | null>(null);
  const [loadingSession, setLoadingSession] = useState(false);
  const [pendingMessage, setPendingMessage] = useState(false);
  const [uploadingAttachment, setUploadingAttachment] = useState(false);
  const [loadingTrackJds, setLoadingTrackJds] = useState(false);
  const [savingTracks, setSavingTracks] = useState(false);
  const [savingMemory, setSavingMemory] = useState(false);
  const [loadingArtifactDetail, setLoadingArtifactDetail] = useState(false);
  const [loadingArtifactDiff, setLoadingArtifactDiff] = useState(false);
  const [restoringSession, setRestoringSession] = useState(true);
  const [exportNotice, setExportNotice] = useState("");
  const [error, setError] = useState("");
  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>("resume");
  const [showHistory, setShowHistory] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editorContent, setEditorContent] = useState("");
  const [editorArtifactId, setEditorArtifactId] = useState("");
  const [editorDirty, setEditorDirty] = useState(false);
  const [savingRevision, setSavingRevision] = useState(false);
  const workspaceAccountName = "Alex Chen";
  const workspaceAccountMeta = workspaceTab === "matches" ? "Personal" : "Workspace";

  function handleWorkspaceTabChange(tab: WorkspaceTab) {
    setWorkspaceTab(tab);
    setShowHistory(false);
  }

  useEffect(() => {
    async function bootstrap() {
      try {
        await refreshSessionsList();
        const storedSessionId = window.localStorage.getItem(sessionStorageKey);
        if (storedSessionId) {
          const state = await getSession(storedSessionId);
          setSessionState(state);
          setMessages(hydrateMessages(state));
        }
      } catch (err) {
        window.localStorage.removeItem(sessionStorageKey);
        window.localStorage.removeItem(activeTrackStorageKey);
        setError(err instanceof Error ? err.message : "恢复会话失败");
      } finally {
        setRestoringSession(false);
      }
    }

    void bootstrap();
  }, []);

  useEffect(() => {
    if (!sessionState) {
      return;
    }
    window.localStorage.setItem(sessionStorageKey, sessionState.session_id);
  }, [sessionState]);

  useEffect(() => {
    if (activeTrack) {
      window.localStorage.setItem(activeTrackStorageKey, activeTrack.id);
      return;
    }
    window.localStorage.removeItem(activeTrackStorageKey);
  }, [activeTrack]);

  useEffect(() => {
    if (!sessionState) {
      return;
    }
    const storedTrackId = window.localStorage.getItem(activeTrackStorageKey);
    if (storedTrackId) {
      const restored = sessionState.snapshot.tracks.find((track) => track.id === storedTrackId);
      if (restored) {
        setActiveTrack(restored);
        return;
      }
    }
    if (!activeTrack && sessionState.snapshot.tracks.length === 1) {
      setActiveTrack(sessionState.snapshot.tracks[0]);
    }
  }, [sessionState, activeTrack]);

  useEffect(() => {
    if (!activeTrack) {
      setTrackJds([]);
      return;
    }
    void loadTrackJds(activeTrack.id);
  }, [activeTrack]);

  useEffect(() => {
    if (!sessionState) {
      setArtifacts([]);
      setSelectedArtifactId("");
      setSelectedArtifactDetail(null);
      setLatestScoreDetail(null);
      return;
    }
    void refreshArtifacts(sessionState.project_id);
  }, [sessionState?.project_id]);

  useEffect(() => {
    async function loadLatestScoreDetail() {
      const latestScoreArtifact = pickLatestScoreArtifact(artifacts, activeTrack?.id ?? "");
      if (!latestScoreArtifact) {
        setLatestScoreDetail(null);
        return;
      }

      try {
        const detail = await getArtifactDetail(latestScoreArtifact.id);
        setLatestScoreDetail(detail);
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载评分详情失败");
      }
    }

    void loadLatestScoreDetail();
  }, [activeTrack?.id, artifacts]);

  useEffect(() => {
    if (!selectedArtifactId) {
      setSelectedArtifactDetail(null);
      return;
    }
    void loadArtifactDetail(selectedArtifactId, true);
  }, [selectedArtifactId]);

  useEffect(() => {
    if (workspaceTab !== "resume" || artifacts.length === 0) {
      return;
    }
    const preferredId = pickPreferredArtifactId(artifacts, selectedArtifactId);
    if (preferredId && preferredId !== selectedArtifactId) {
      setSelectedArtifactId(preferredId);
    }
  }, [artifacts, selectedArtifactId, workspaceTab]);

  useEffect(() => {
    if (!selectedArtifactDetail) {
      setEditorArtifactId("");
      setEditorContent("");
      setEditorDirty(false);
      return;
    }
    if (selectedArtifactDetail.artifact.id !== editorArtifactId) {
      setEditorArtifactId(selectedArtifactDetail.artifact.id);
      setEditorContent(selectedArtifactDetail.content);
      setEditorDirty(false);
    }
  }, [editorArtifactId, selectedArtifactDetail]);

  const editableArtifacts = useMemo(
    () => artifacts.filter((artifact) => isEditableArtifact(artifact.artifact_type)),
    [artifacts],
  );
  const currentPrimaryJd = useMemo(() => trackJds.find((item) => item.is_primary) ?? trackJds[0] ?? null, [trackJds]);
  const latestScoreValue = useMemo(() => {
    const payload = latestScoreDetail?.parsed_payload;
    if (typeof payload?.final_score === "number") {
      return payload.final_score;
    }
    if (typeof payload?.total_score === "number") {
      return payload.total_score;
    }
    return null;
  }, [latestScoreDetail]);
  const latestQuickAdvice = useMemo(() => {
    const payload = latestScoreDetail?.parsed_payload;
    return ((payload?.quick_improvements as string[] | undefined) ?? []).slice(0, 3);
  }, [latestScoreDetail]);

  async function refreshSessionsList() {
    const history = await listSessions();
    setSessions(history);
  }

  async function refreshArtifacts(projectId: string, preferredArtifactId = "") {
    const nextArtifacts = await listArtifacts(projectId);
    setArtifacts(nextArtifacts);
    const nextSelectedId = pickPreferredArtifactId(nextArtifacts, selectedArtifactId, preferredArtifactId);
    setSelectedArtifactId(nextSelectedId);
    if (!nextSelectedId) {
      setSelectedArtifactDetail(null);
      setArtifactDiffState(null);
    }
  }

  async function loadArtifactDetail(artifactId: string, clearDiff = false) {
    setLoadingArtifactDetail(true);
    try {
      const detail = await getArtifactDetail(artifactId);
      setSelectedArtifactDetail(detail);
      if (clearDiff) {
        setArtifactDiffState(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载产物详情失败");
    } finally {
      setLoadingArtifactDetail(false);
    }
  }

  async function handleStartSession() {
    setLoadingSession(true);
    setError("");
    try {
      const state = await startSession({
        project_name: projectName,
        cycle,
        base_resume_text: baseResumeText,
      });
      setSessionState(state);
      setMessages(hydrateMessages(state));
      setActiveTrack(null);
      setTrackJds([]);
      setWorkspaceTab("resume");
      setShowHistory(false);
      await refreshSessionsList();
    } catch (err) {
      setError(err instanceof Error ? err.message : "启动会话失败");
    } finally {
      setLoadingSession(false);
    }
  }

  async function refreshSession(
    sessionId: string,
    preferredTrackId?: string | null,
    preferredArtifactId = "",
  ) {
    const state = await getSession(sessionId);
    setSessionState(state);
    setMessages(hydrateMessages(state));

    const latestTracks = state.snapshot.tracks;
    const desiredTrackId = preferredTrackId === undefined ? activeTrack?.id ?? "" : preferredTrackId ?? "";
    let nextActive = desiredTrackId ? latestTracks.find((item) => item.id === desiredTrackId) ?? null : null;
    if (!nextActive && latestTracks.length === 1) {
      nextActive = latestTracks[0];
    }
    if (!nextActive && preferredTrackId === null) {
      nextActive = latestTracks[0] ?? null;
    }
    setActiveTrack(nextActive);
    await Promise.all([refreshSessionsList(), refreshArtifacts(state.project_id, preferredArtifactId)]);
  }

  async function handleOpenSession(sessionId: string) {
    setError("");
    setExportNotice("");
    setShowHistory(false);
    await refreshSession(sessionId, null);
  }

  async function loadTrackJds(trackId: string) {
    setLoadingTrackJds(true);
    try {
      const jds = await listTrackJds(trackId);
      setTrackJds(jds);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载 JD 列表失败");
    } finally {
      setLoadingTrackJds(false);
    }
  }

  async function handleSendMessage() {
    if (!sessionState) {
      return;
    }
    if (!draft.trim() && attachment.type === "other") {
      return;
    }

    setPendingMessage(true);
    setError("");
    setExportNotice("");

    try {
      const attachments = attachment.type === "other" ? [] : [attachment];
      const response = await sendMessage(sessionState.session_id, {
        content: draft,
        attachments,
        active_track_id: activeTrack?.id ?? "",
        active_track_name: activeTrack?.name ?? "",
      });
      const preferredArtifactId = extractGeneratedArtifactId(response);
      setDraft("");
      setAttachment(emptyAttachment);
      if (preferredArtifactId) {
        setWorkspaceTab("resume");
      }
      await refreshSession(sessionState.session_id, undefined, preferredArtifactId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送消息失败");
    } finally {
      setPendingMessage(false);
    }
  }

  async function handleAttachmentFileUpload(file: File) {
    setUploadingAttachment(true);
    setError("");
    try {
      const uploaded = await uploadAttachment({
        file,
        attachmentType: "other",
        sessionId: sessionState?.session_id,
      });
      setAttachment(uploaded);
      if (uploaded.type === "other") {
        setError("文件已上传，但未能识别为 JD 或简历。你仍然可以直接发送消息补充说明。");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "文件上传失败");
    } finally {
      setUploadingAttachment(false);
    }
  }

  async function handleCreateTrack(input: {
    name: string;
    positioning: string;
    core_keywords: string[];
    resume_strategy: string;
    default_resume_outline: string;
  }): Promise<TrackSummary> {
    if (!sessionState) {
      throw new Error("会话未启动");
    }
    setSavingTracks(true);
    setError("");
    try {
      const track = await createTrack(sessionState.project_id, input);
      await refreshSession(sessionState.session_id, track.id);
      return track;
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建方向失败");
      throw err;
    } finally {
      setSavingTracks(false);
    }
  }

  async function handleUpdateTrack(
    trackId: string,
    input: {
      name: string;
      positioning: string;
      core_keywords: string[];
      resume_strategy: string;
      default_resume_outline: string;
    },
  ) {
    if (!sessionState) {
      return;
    }
    setSavingTracks(true);
    setError("");
    try {
      await updateTrack(trackId, input);
      await refreshSession(sessionState.session_id, trackId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新方向失败");
    } finally {
      setSavingTracks(false);
    }
  }

  async function handleDeleteTrack(trackId: string) {
    if (!sessionState) {
      return;
    }
    setSavingTracks(true);
    setError("");
    try {
      await deleteTrack(trackId);
      await refreshSession(sessionState.session_id, null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除方向失败");
    } finally {
      setSavingTracks(false);
    }
  }

  async function handleCreateJd(
    trackId: string,
    input: { name: string; content: string; set_as_primary: boolean },
  ) {
    if (!sessionState) {
      return;
    }
    setSavingTracks(true);
    setError("");
    try {
      await createTrackJd(trackId, input);
      await refreshSession(sessionState.session_id, trackId);
      await loadTrackJds(trackId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "新增 JD 失败");
    } finally {
      setSavingTracks(false);
    }
  }

  async function handleUpdateJd(jdId: string, input: { name: string; content?: string }) {
    if (!sessionState || !activeTrack) {
      return;
    }
    setSavingTracks(true);
    setError("");
    try {
      await updateJd(jdId, input);
      await refreshSession(sessionState.session_id, activeTrack.id);
      await loadTrackJds(activeTrack.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新 JD 失败");
    } finally {
      setSavingTracks(false);
    }
  }

  async function handleDeleteJd(jdId: string) {
    if (!sessionState || !activeTrack) {
      return;
    }
    setSavingTracks(true);
    setError("");
    try {
      await deleteJd(jdId);
      await refreshSession(sessionState.session_id, activeTrack.id);
      await loadTrackJds(activeTrack.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除 JD 失败");
    } finally {
      setSavingTracks(false);
    }
  }

  async function handleSetPrimaryJd(trackId: string, jdEntryId: string) {
    if (!sessionState) {
      return;
    }
    setSavingTracks(true);
    setError("");
    try {
      await setPrimaryJd(trackId, jdEntryId);
      await refreshSession(sessionState.session_id, trackId);
      await loadTrackJds(trackId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "切换主 JD 失败");
    } finally {
      setSavingTracks(false);
    }
  }

  async function handleSaveProfile(input: {
    summary: string;
    education: string;
    years_of_experience: string;
    preferred_city: string;
    target_roles: string[];
    exclusions: string[];
  }) {
    if (!sessionState) {
      return;
    }
    setSavingMemory(true);
    setError("");
    try {
      const current = sessionState.snapshot.profile;
      await updateProfile(sessionState.project_id, {
        summary: input.summary,
        basics: {
          ...current.basics,
          education: input.education,
          years_of_experience: input.years_of_experience,
        },
        preferences: {
          ...current.preferences,
          preferred_city: input.preferred_city,
          target_roles: input.target_roles,
        },
        constraints: {
          ...current.constraints,
          exclusions: input.exclusions,
        },
      });
      await refreshSession(sessionState.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存画像失败");
    } finally {
      setSavingMemory(false);
    }
  }

  async function handleCreateExperience(input: Omit<ExperienceItem, "id">) {
    if (!sessionState) {
      return;
    }
    setSavingMemory(true);
    setError("");
    try {
      await createExperience(sessionState.project_id, input);
      await refreshSession(sessionState.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "新增经历失败");
    } finally {
      setSavingMemory(false);
    }
  }

  async function handleUpdateExperience(experienceId: string, input: Omit<ExperienceItem, "id">) {
    if (!sessionState) {
      return;
    }
    setSavingMemory(true);
    setError("");
    try {
      await updateExperience(experienceId, input);
      await refreshSession(sessionState.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新经历失败");
    } finally {
      setSavingMemory(false);
    }
  }

  async function handleDeleteExperience(experienceId: string) {
    if (!sessionState) {
      return;
    }
    setSavingMemory(true);
    setError("");
    try {
      await deleteExperience(experienceId);
      await refreshSession(sessionState.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除经历失败");
    } finally {
      setSavingMemory(false);
    }
  }

  async function handleCompareArtifacts(baseArtifactId: string) {
    if (!selectedArtifactId) {
      return;
    }
    setLoadingArtifactDiff(true);
    setError("");
    try {
      const diff = await diffArtifact(selectedArtifactId, baseArtifactId);
      setArtifactDiffState(diff);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载版本 diff 失败");
    } finally {
      setLoadingArtifactDiff(false);
    }
  }

  async function handleExportArtifact(format: "docx" | "pdf") {
    if (!selectedArtifactId) {
      return;
    }
    setError("");
    try {
      const exported = await exportArtifact(selectedArtifactId, format);
      setExportNotice(`已导出 ${format.toUpperCase()}：${exported.path}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "导出产物失败");
    }
  }

  async function handleSaveRevision() {
    if (!selectedArtifactDetail || !editorDirty || !sessionState) {
      return;
    }
    setSavingRevision(true);
    setError("");
    setExportNotice("");
    try {
      const artifact = await saveArtifactRevision(selectedArtifactDetail.artifact.id, editorContent);
      setEditMode(false);
      await refreshSession(sessionState.session_id, activeTrack?.id, artifact.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存新版本失败");
    } finally {
      setSavingRevision(false);
    }
  }

  function handleResetSession() {
    setSessionState(null);
    setMessages([]);
    setActiveTrack(null);
    setTrackJds([]);
    setArtifacts([]);
    setSelectedArtifactId("");
    setSelectedArtifactDetail(null);
    setLatestScoreDetail(null);
    setArtifactDiffState(null);
    setAttachment(emptyAttachment);
    setExportNotice("");
    setEditorContent("");
    setEditorArtifactId("");
    setEditorDirty(false);
    setEditMode(false);
    setWorkspaceTab("resume");
    setShowHistory(false);
    window.localStorage.removeItem(sessionStorageKey);
    window.localStorage.removeItem(activeTrackStorageKey);
  }

  if (restoringSession) {
    return (
      <main className="app-shell">
        <section className="start-shell">
          <div className="start-copy">
            <span className="eyebrow">Session Runtime</span>
            <h1>恢复最近会话</h1>
            <p>正在从本地状态恢复上一次的简历 Agent 工作台。</p>
          </div>
        </section>
      </main>
    );
  }

  if (!sessionState) {
    return (
      <main className="app-shell">
        <StartPanel
          projectName={projectName}
          cycle={cycle}
          baseResumeText={baseResumeText}
          loading={loadingSession}
          onProjectNameChange={setProjectName}
          onCycleChange={setCycle}
          onBaseResumeChange={setBaseResumeText}
          onSubmit={handleStartSession}
        />
        {sessions.length > 0 ? (
          <section className="history-shell">
            <SessionHistoryPanel sessions={sessions} currentSessionId="" onOpenSession={handleOpenSession} />
          </section>
        ) : null}
        {error ? <div className="global-error">{error}</div> : null}
      </main>
    );
  }

  return (
    <main className="app-shell active workspace-shell">
      <header className="workspace-topbar">
        <div className="workspace-brand">
          <button
            className="brand-mark interactive"
            type="button"
            onClick={() => handleWorkspaceTabChange("resume")}
            aria-label="打开简历工作台"
          >
            <svg viewBox="0 0 24 24">
              <path
                d="M7 4.75h6.25l3 3V18a1.75 1.75 0 0 1-1.75 1.75h-7A1.75 1.75 0 0 1 5.75 18V6.5A1.75 1.75 0 0 1 7.5 4.75Zm5.5 1.9V8.5h2.85"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
              />
            </svg>
          </button>
          <div>
            <div className="workspace-brand-line">
              <strong>{workspaceTab === "matches" ? "Resume Agent" : "Resume Workspace"}</strong>
              {workspaceTab === "matches" ? <span className="workspace-plan-badge">PRO</span> : null}
            </div>
            {workspaceTab === "matches" ? null : <span>{sessionState.title}</span>}
          </div>
        </div>

        <nav className="workspace-tabs" aria-label="Workspace views">
          <button
            type="button"
            className={workspaceTab === "resume" ? "active" : ""}
            onClick={() => handleWorkspaceTabChange("resume")}
          >
            Resume Workspace
          </button>
          <button
            type="button"
            className={workspaceTab === "matches" ? "active" : ""}
            onClick={() => handleWorkspaceTabChange("matches")}
          >
            JD Matches
          </button>
        </nav>

        <div className="workspace-actions">
          <button
            className={`utility-icon ${showHistory ? "active" : ""}`}
            type="button"
            aria-label="切换会话历史"
            title="切换会话历史"
            onClick={() => setShowHistory((value) => !value)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M7.5 6.75h9m-9 5.25h9m-9 5.25h6"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
              />
            </svg>
          </button>
          <button
            className="utility-icon"
            type="button"
            aria-label="通知"
            title="通知"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M12 4.75a4.75 4.75 0 0 0-4.75 4.75v2.56l-.89 2.24a.75.75 0 0 0 .7 1.03h9.88a.75.75 0 0 0 .7-1.03l-.89-2.24V9.5A4.75 4.75 0 0 0 12 4.75Zm-1.9 12.5a1.9 1.9 0 0 0 3.8 0"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
              />
            </svg>
          </button>
          <button
            className="utility-icon"
            type="button"
            aria-label="新建会话"
            title="新建会话"
            onClick={handleResetSession}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M12 5.25v13.5M5.25 12h13.5"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
              />
            </svg>
          </button>
          <div className="workspace-account" aria-label="当前账号">
            <span className="workspace-account-avatar">{workspaceAccountName.slice(0, 1)}</span>
            <span className="workspace-account-copy">
              <strong>{workspaceAccountName}</strong>
              <small>{workspaceAccountMeta}</small>
            </span>
          </div>
        </div>
      </header>

      {error ? <div className="global-error">{error}</div> : null}

      <section className={`workspace-main ${workspaceTab === "matches" ? "matches-layout" : "resume-layout"}`}>
        {workspaceTab === "resume" ? (
          <ChatPanel
            messages={messages}
            activeTrackName={activeTrack?.name ?? ""}
            scoreValue={latestScoreValue}
            quickAdvice={latestQuickAdvice}
            pending={pendingMessage}
            uploading={uploadingAttachment}
            attachment={attachment}
            draft={draft}
            onDraftChange={setDraft}
            onAttachmentChange={setAttachment}
            onAttachmentFileUpload={handleAttachmentFileUpload}
            onSend={handleSendMessage}
          />
        ) : null}
        <div className="workspace-detail">
          {workspaceTab === "resume" ? (
            <ResumeEditorPanel
              sessionTitle={sessionState.title}
              activeTrack={activeTrack}
              currentJd={currentPrimaryJd}
              artifacts={editableArtifacts}
              selectedArtifactId={selectedArtifactId}
              detail={selectedArtifactDetail}
              latestScoreDetail={latestScoreDetail}
              loading={loadingArtifactDetail}
              editMode={editMode}
              draftContent={editorContent}
              draftDirty={editorDirty}
              savingRevision={savingRevision}
              exportNotice={exportNotice}
              onSelectArtifact={setSelectedArtifactId}
              onToggleEditMode={() => setEditMode((value) => !value)}
              onDraftContentChange={(value) => {
                setEditorContent(value);
                setEditorDirty(true);
              }}
              onSaveRevision={handleSaveRevision}
              onExportArtifact={handleExportArtifact}
              onOpenMatches={() => handleWorkspaceTabChange("matches")}
            />
          ) : (
            <div className="matches-view">
              <MatchesBoard
                tracks={sessionState.snapshot.tracks}
                activeTrackId={activeTrack?.id ?? ""}
                activeTrackJds={trackJds}
                loadingTrackJds={loadingTrackJds}
                pending={savingTracks}
                artifacts={artifacts}
                latestScoreDetail={latestScoreDetail}
                onSelectTrack={setActiveTrack}
                onOpenResumeWorkspace={() => handleWorkspaceTabChange("resume")}
                onCreateTrack={handleCreateTrack}
                onUpdateTrack={handleUpdateTrack}
                onDeleteTrack={handleDeleteTrack}
                onCreateJd={handleCreateJd}
                onUpdateJd={handleUpdateJd}
                onDeleteJd={handleDeleteJd}
                onSetPrimaryJd={handleSetPrimaryJd}
              />
            </div>
          )}
        </div>
      </section>

      {showHistory ? (
        <aside className="history-drawer">
          <SessionHistoryPanel
            sessions={sessions}
            currentSessionId={sessionState.session_id}
            onOpenSession={handleOpenSession}
          />
        </aside>
      ) : null}
    </main>
  );
}
