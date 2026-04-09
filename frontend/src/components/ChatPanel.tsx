// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 Chat 面板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import { useEffect, useRef, useState } from "react";

import type { AgentAttachment, ChatMessage } from "../types";

type ChatPanelProps = {
  messages: ChatMessage[];
  activeTrackName: string;
  scoreValue: number | null;
  quickAdvice: string[];
  pending: boolean;
  uploading: boolean;
  attachment: AgentAttachment;
  draft: string;
  onDraftChange: (value: string) => void;
  onAttachmentChange: (attachment: AgentAttachment) => void;
  onAttachmentFileUpload: (file: File) => Promise<void>;
  onSend: () => void;
};

export function ChatPanel(props: ChatPanelProps) {
  const {
    messages,
    activeTrackName,
    scoreValue,
    quickAdvice,
    pending,
    uploading,
    attachment,
    draft,
    onDraftChange,
    onAttachmentChange,
    onAttachmentFileUpload,
    onSend,
  } = props;
  const messageEndRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  async function handleFileList(fileList: FileList | null) {
    const file = fileList?.[0];
    if (!file) {
      return;
    }
    await onAttachmentFileUpload(file);
  }

  return (
    <section className="panel chat-panel workspace-chat">
      <div className="chat-topbar">
        <div className="chat-heading">
          <div>
            <p className="chat-title">Resume Desk</p>
            <span className="chat-subtitle">{activeTrackName || "No target role selected"}</span>
          </div>
        </div>
        <span className="status-pill">ONLINE</span>
      </div>

      <div className="message-list workspace-thread">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>从一条自然语言消息开始。</p>
            <p>例如：“这是目标 JD，请先评分，再生成一版定制简历。”</p>
          </div>
        ) : null}
        {messages.map((message) => (
          <article
            key={message.id}
            className={`message-row ${message.role === "assistant" ? "assistant-row" : "user-row"}`}
          >
            <div className={`message-avatar ${message.role === "assistant" ? "assistant-avatar" : "user-avatar"}`}>
              {message.role === "assistant" ? (
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M12 6.25a4.25 4.25 0 0 0-4.25 4.25v1c0 .43-.15.84-.42 1.17l-.79.95a.8.8 0 0 0 .62 1.33h9.68a.8.8 0 0 0 .62-1.33l-.79-.95a1.82 1.82 0 0 1-.42-1.17v-1A4.25 4.25 0 0 0 12 6.25Zm-1.5 11h3"
                    fill="none"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.8"
                  />
                </svg>
              ) : (
                <span>Y</span>
              )}
            </div>
            <div className={`message-card role-${message.role}`}>
              <span className="message-role">{message.role === "assistant" ? "Desk" : "You"}</span>
              <p>{message.content}</p>
            </div>
          </article>
        ))}

        {pending ? (
          <article className="message-row assistant-row">
            <div className="message-avatar assistant-avatar">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="M12 6.25a4.25 4.25 0 0 0-4.25 4.25v1c0 .43-.15.84-.42 1.17l-.79.95a.8.8 0 0 0 .62 1.33h9.68a.8.8 0 0 0 .62-1.33l-.79-.95a1.82 1.82 0 0 1-.42-1.17v-1A4.25 4.25 0 0 0 12 6.25Zm-1.5 11h3"
                  fill="none"
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="1.8"
                />
              </svg>
            </div>
            <div className="message-card role-assistant is-loading">
              <span className="message-role">Desk</span>
              <p>Updating the workspace...</p>
            </div>
          </article>
        ) : null}

        {scoreValue !== null ? (
          <article className="match-score-card">
            <div className="match-score-ring">
              <strong>{Math.round(scoreValue)}</strong>
              <span>%</span>
            </div>
            <div className="match-score-copy">
              <div className="match-score-head">
                <strong>Latest Match Snapshot</strong>
                <span>{scoreValue >= 80 ? "Strong match" : scoreValue >= 60 ? "Needs polish" : "Needs review"}</span>
              </div>
              <div className="match-score-bars">
                <div>
                  <label>Keywords Match</label>
                  <progress max="100" value={Math.max(0, Math.min(100, Math.round(scoreValue)))} />
                </div>
                <div>
                  <label>Quantifiable Impact</label>
                  <progress max="100" value={Math.max(0, Math.min(100, Math.round(scoreValue * 0.62)))} />
                </div>
              </div>
              <div className="match-score-advice">
                {(quickAdvice.length > 0 ? quickAdvice.slice(0, 3) : ["Run a score and the most important revision points will show up here."]).map(
                  (item) => (
                    <p key={item}>{item}</p>
                  ),
                )}
              </div>
            </div>
          </article>
        ) : null}
        <div ref={messageEndRef} />
      </div>

      <div className="composer workspace-composer">
        {attachment.type !== "other" ? (
          <div className="attachment-pill">
            <div>
              <strong>{attachment.name || "未命名文件"}</strong>
              <span>
                {attachment.type.toUpperCase()}
                {attachment.detected_type && attachment.detected_type !== attachment.type
                  ? ` · 识别为 ${attachment.detected_type.toUpperCase()}`
                  : ""}
              </span>
            </div>
            <button
              className="icon-button subtle"
              type="button"
              onClick={() => onAttachmentChange({ type: "other", content: "", name: "" })}
            >
              ×
            </button>
          </div>
        ) : null}
        <textarea
          rows={1}
          value={draft}
          onChange={(event) => onDraftChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              if (!pending) {
                onSend();
              }
            }
          }}
          placeholder="Ask for a revision, paste a JD, or continue the current draft..."
        />
        <div className="composer-actions">
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.json,.pdf,.docx"
            className="sr-only"
            onChange={async (event) => {
              await handleFileList(event.target.files);
              event.currentTarget.value = "";
            }}
          />
          <button
            className={`icon-button ${dragActive ? "active" : ""}`}
            type="button"
            onClick={() => fileInputRef.current?.click()}
            onDragEnter={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              setDragActive(false);
            }}
            onDrop={async (event) => {
              event.preventDefault();
              setDragActive(false);
              await handleFileList(event.dataTransfer.files);
            }}
            disabled={uploading}
            title={uploading ? "上传中..." : "上传 JD / 简历"}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M12 16V7m0 0-3 3m3-3 3 3M7 17.5a4.5 4.5 0 0 1-.5-8.97A5.5 5.5 0 0 1 17 7.5a4 4 0 1 1 .5 8H12"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
              />
            </svg>
          </button>
          <span className="composer-hint">{uploading ? "Parsing file..." : "JD / PDF / DOCX"}</span>
          <button className="primary-button send-button" onClick={onSend} disabled={pending}>
            {pending ? "..." : "Send"}
          </button>
        </div>
      </div>
    </section>
  );
}
