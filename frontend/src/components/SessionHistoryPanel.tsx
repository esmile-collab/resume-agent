// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 SessionHistory 面板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import type { SessionHistoryItem } from "../types";

type SessionHistoryPanelProps = {
  sessions: SessionHistoryItem[];
  currentSessionId: string;
  onOpenSession: (sessionId: string) => Promise<void>;
};

export function SessionHistoryPanel({
  sessions,
  currentSessionId,
  onOpenSession,
}: SessionHistoryPanelProps) {
  return (
    <section className="panel side-panel">
      <div className="panel-head">
        <div>
          <p className="panel-kicker">Session History</p>
          <h2>会话历史</h2>
        </div>
      </div>
      {sessions.length === 0 ? (
        <div className="empty-state compact">
          <p>当前还没有历史会话。</p>
        </div>
      ) : (
        <div className="session-history-list">
          {sessions.map((session) => (
            <button
              key={session.id}
              type="button"
              className={`session-card ${session.id === currentSessionId ? "active" : ""}`}
              onClick={() => void onOpenSession(session.id)}
            >
              <div className="session-card-head">
                <strong>{session.project_name}</strong>
                <span>{session.id === currentSessionId ? "当前" : "打开"}</span>
              </div>
              <p>{session.title}</p>
              <small>{session.preview || "暂无最近消息"}</small>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
