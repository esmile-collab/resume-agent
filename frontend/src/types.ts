// Input: 后端响应结构和前端状态模型。
// Output: 输出 React 侧复用的 TypeScript 类型。
// Pos: 前端共享类型文件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
export type AgentAttachment = {
  type: "jd" | "resume" | "other";
  content: string;
  name?: string;
  detected_type?: "jd" | "resume" | "other";
  content_type?: string;
  size?: number;
  path?: string;
};

export type ChatMessage = {
  id: string;
  role: string;
  content: string;
  metadata?: Record<string, unknown>;
};

export type TrackSummary = {
  id: string;
  name: string;
  positioning: string;
  core_keywords: string[];
  resume_strategy: string;
  default_resume_outline: string;
  primary_jd_entry_id: string;
  jd_count: number;
  jd_ids: string[];
};

export type JDSummary = {
  id: string;
  track_id: string;
  name: string;
  content: string;
  preview: string;
  created_at: string;
  is_primary: boolean;
};

export type ExperienceItem = {
  id: string;
  title: string;
  organization: string;
  time_range: string;
  summary: string;
  tags: string[];
  metrics: string[];
  evidence: string[];
  confidence: number;
  source: string;
};

export type ArtifactSummary = {
  id: string;
  track_id: string;
  jd_entry_id: string;
  artifact_type: string;
  version: number;
  path: string;
  summary: Record<string, unknown>;
  created_at: string;
};

export type ArtifactDetail = {
  artifact: ArtifactSummary;
  content: string;
  parsed_payload?: Record<string, unknown> | null;
};

export type ArtifactDiff = {
  artifact_id: string;
  base_artifact_id: string;
  diff: string;
  stats: {
    additions: number;
    deletions: number;
  };
};

export type ToolStep = {
  thought: string;
  tool_name: string;
  input_payload: Record<string, unknown>;
  observation: Record<string, unknown>;
};

export type Snapshot = {
  profile: {
    summary: string;
    basics: Record<string, string>;
    preferences: Record<string, unknown>;
    constraints: Record<string, unknown>;
  };
  experiences: ExperienceItem[];
  tracks: TrackSummary[];
  artifacts: ArtifactSummary[];
  recent_messages: ChatMessage[];
  dialog_summary: Record<string, unknown>;
};

export type TraceItem = {
  id: string;
  message_id: string;
  step_index: number;
  kind: string;
  payload: Record<string, unknown>;
};

export type SessionState = {
  project_id: string;
  session_id: string;
  title: string;
  snapshot: Snapshot;
  traces: TraceItem[];
  tool_catalog?: Array<{ name: string; description: string; when_to_use: string }>;
};

export type SessionHistoryItem = {
  id: string;
  project_id: string;
  project_name: string;
  title: string;
  status: string;
  preview: string;
  created_at: string;
  updated_at: string;
};

export type MessageResponse = {
  project_id: string;
  session_id: string;
  message_id: string;
  assistant_message_id: string;
  reply: string;
  snapshot: Snapshot;
  tool_steps?: ToolStep[];
  intent?: Record<string, unknown>;
};
