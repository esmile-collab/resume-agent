// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 Track 面板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import { useEffect, useState } from "react";

import type { JDSummary, TrackSummary } from "../types";

function splitValues(raw: string) {
  return raw
    .split(/[\n,，、/]+/)
    .map((value) => value.trim())
    .filter(Boolean);
}

function joinValues(values: string[]) {
  return values.join("，");
}

type TrackPanelProps = {
  tracks: TrackSummary[];
  activeTrackId: string;
  activeTrackJds: JDSummary[];
  loadingTrackJds: boolean;
  pending: boolean;
  onSelect: (track: TrackSummary) => void;
  onCreateTrack: (input: {
    name: string;
    positioning: string;
    core_keywords: string[];
    resume_strategy: string;
    default_resume_outline: string;
  }) => Promise<void>;
  onUpdateTrack: (
    trackId: string,
    input: {
      name: string;
      positioning: string;
      core_keywords: string[];
      resume_strategy: string;
      default_resume_outline: string;
    },
  ) => Promise<void>;
  onDeleteTrack: (trackId: string) => Promise<void>;
  onCreateJd: (
    trackId: string,
    input: {
      name: string;
      content: string;
      set_as_primary: boolean;
    },
  ) => Promise<void>;
  onUpdateJd: (jdId: string, input: { name: string; content?: string }) => Promise<void>;
  onDeleteJd: (jdId: string) => Promise<void>;
  onSetPrimaryJd: (trackId: string, jdEntryId: string) => Promise<void>;
};

const emptyTrackForm = {
  name: "",
  positioning: "",
  core_keywords: "",
  resume_strategy: "",
  default_resume_outline: "",
};

const emptyJdForm = {
  name: "",
  content: "",
  set_as_primary: false,
};

export function TrackPanel({
  tracks,
  activeTrackId,
  activeTrackJds,
  loadingTrackJds,
  pending,
  onSelect,
  onCreateTrack,
  onUpdateTrack,
  onDeleteTrack,
  onCreateJd,
  onUpdateJd,
  onDeleteJd,
  onSetPrimaryJd,
}: TrackPanelProps) {
  const activeTrack = tracks.find((track) => track.id === activeTrackId) ?? null;
  const [showCreateTrack, setShowCreateTrack] = useState(false);
  const [newTrackForm, setNewTrackForm] = useState(emptyTrackForm);
  const [editTrackForm, setEditTrackForm] = useState(emptyTrackForm);
  const [newJdForm, setNewJdForm] = useState(emptyJdForm);
  const [editingJdId, setEditingJdId] = useState("");
  const [editingJdName, setEditingJdName] = useState("");
  const [editingJdContent, setEditingJdContent] = useState("");

  useEffect(() => {
    if (!activeTrack) {
      setEditTrackForm(emptyTrackForm);
      return;
    }
    setEditTrackForm({
      name: activeTrack.name,
      positioning: activeTrack.positioning,
      core_keywords: joinValues(activeTrack.core_keywords),
      resume_strategy: activeTrack.resume_strategy,
      default_resume_outline: activeTrack.default_resume_outline,
    });
    setNewJdForm({
      name: `${activeTrack.name}-jd.txt`,
      content: "",
      set_as_primary: activeTrack.jd_count === 0,
    });
  }, [activeTrack]);

  async function handleCreateTrackClick() {
    await onCreateTrack({
      name: newTrackForm.name.trim(),
      positioning: newTrackForm.positioning.trim(),
      core_keywords: splitValues(newTrackForm.core_keywords),
      resume_strategy: newTrackForm.resume_strategy.trim(),
      default_resume_outline: newTrackForm.default_resume_outline.trim(),
    });
    setNewTrackForm(emptyTrackForm);
    setShowCreateTrack(false);
  }

  async function handleUpdateTrackClick() {
    if (!activeTrack) {
      return;
    }
    await onUpdateTrack(activeTrack.id, {
      name: editTrackForm.name.trim(),
      positioning: editTrackForm.positioning.trim(),
      core_keywords: splitValues(editTrackForm.core_keywords),
      resume_strategy: editTrackForm.resume_strategy.trim(),
      default_resume_outline: editTrackForm.default_resume_outline.trim(),
    });
  }

  async function handleCreateJdClick() {
    if (!activeTrack) {
      return;
    }
    await onCreateJd(activeTrack.id, {
      name: newJdForm.name.trim() || `${activeTrack.name}-jd.txt`,
      content: newJdForm.content,
      set_as_primary: newJdForm.set_as_primary,
    });
    setNewJdForm({
      name: `${activeTrack.name}-jd.txt`,
      content: "",
      set_as_primary: false,
    });
  }

  async function handleUpdateJdClick() {
    await onUpdateJd(editingJdId, { name: editingJdName.trim(), content: editingJdContent });
    setEditingJdId("");
    setEditingJdName("");
    setEditingJdContent("");
  }

  return (
    <section className="panel side-panel">
      <div className="panel-head">
        <div>
          <p className="panel-kicker">Track Panel</p>
          <h2>方向与 JD Library</h2>
        </div>
        <button
          className="ghost-button compact-button"
          type="button"
          onClick={() => setShowCreateTrack((value) => !value)}
        >
          {showCreateTrack ? "收起方向" : "新建方向"}
        </button>
      </div>

      {showCreateTrack ? (
        <div className="editor-card">
          <div className="form-grid">
            <label>
              方向名称
              <input
                value={newTrackForm.name}
                onChange={(event) => setNewTrackForm({ ...newTrackForm, name: event.target.value })}
                placeholder="策略产品"
              />
            </label>
            <label>
              核心关键词
              <input
                value={newTrackForm.core_keywords}
                onChange={(event) =>
                  setNewTrackForm({ ...newTrackForm, core_keywords: event.target.value })
                }
                placeholder="增长，商业化，数据分析"
              />
            </label>
            <label className="full-span">
              方向定位
              <textarea
                rows={3}
                value={newTrackForm.positioning}
                onChange={(event) =>
                  setNewTrackForm({ ...newTrackForm, positioning: event.target.value })
                }
              />
            </label>
            <label className="full-span">
              简历策略
              <textarea
                rows={3}
                value={newTrackForm.resume_strategy}
                onChange={(event) =>
                  setNewTrackForm({ ...newTrackForm, resume_strategy: event.target.value })
                }
              />
            </label>
            <label className="full-span">
              默认简历框架
              <textarea
                rows={4}
                value={newTrackForm.default_resume_outline}
                onChange={(event) =>
                  setNewTrackForm({ ...newTrackForm, default_resume_outline: event.target.value })
                }
              />
            </label>
          </div>
          <div className="card-actions">
            <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleCreateTrackClick()}>
              {pending ? "处理中..." : "创建方向"}
            </button>
          </div>
        </div>
      ) : null}

      {tracks.length === 0 ? (
        <div className="empty-state compact">
          <p>还没有方向总文档。</p>
          <p>先创建一个方向，或通过对话上传 JD 让系统自动归档。</p>
        </div>
      ) : (
        <div className="track-list">
          {tracks.map((track) => (
            <button
              key={track.id}
              type="button"
              className={`track-card ${activeTrackId === track.id ? "active" : ""}`}
              onClick={() => onSelect(track)}
            >
              <div className="track-card-head">
                <strong>{track.name}</strong>
                <span>{track.jd_count} JD</span>
              </div>
              <p>{track.positioning}</p>
              <div className="tag-row">
                {track.core_keywords.slice(0, 5).map((keyword) => (
                  <span key={keyword} className="tag">
                    {keyword}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </div>
      )}

      {activeTrack ? (
        <>
          <div className="memory-section">
            <div className="section-toolbar">
              <h3>方向编辑</h3>
              <div className="card-actions">
                <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleUpdateTrackClick()}>
                  {pending ? "处理中..." : "保存方向"}
                </button>
                <button className="danger-button compact-button" type="button" disabled={pending} onClick={() => void onDeleteTrack(activeTrack.id)}>
                  删除方向
                </button>
              </div>
            </div>
            <div className="editor-card">
              <div className="form-grid">
                <label>
                  名称
                  <input
                    value={editTrackForm.name}
                    onChange={(event) => setEditTrackForm({ ...editTrackForm, name: event.target.value })}
                  />
                </label>
                <label>
                  核心关键词
                  <input
                    value={editTrackForm.core_keywords}
                    onChange={(event) =>
                      setEditTrackForm({ ...editTrackForm, core_keywords: event.target.value })
                    }
                  />
                </label>
                <label className="full-span">
                  方向定位
                  <textarea
                    rows={3}
                    value={editTrackForm.positioning}
                    onChange={(event) =>
                      setEditTrackForm({ ...editTrackForm, positioning: event.target.value })
                    }
                  />
                </label>
                <label className="full-span">
                  简历策略
                  <textarea
                    rows={3}
                    value={editTrackForm.resume_strategy}
                    onChange={(event) =>
                      setEditTrackForm({ ...editTrackForm, resume_strategy: event.target.value })
                    }
                  />
                </label>
                <label className="full-span">
                  默认简历框架
                  <textarea
                    rows={4}
                    value={editTrackForm.default_resume_outline}
                    onChange={(event) =>
                      setEditTrackForm({
                        ...editTrackForm,
                        default_resume_outline: event.target.value,
                      })
                    }
                  />
                </label>
              </div>
            </div>
          </div>

          <div className="memory-section">
            <div className="section-toolbar">
              <h3>JD Library</h3>
              <span className="subtle-text">
                {loadingTrackJds ? "加载中..." : `${activeTrackJds.length} 条 JD`}
              </span>
            </div>
            <div className="editor-card">
              <div className="form-grid">
                <label>
                  JD 名称
                  <input
                    value={newJdForm.name}
                    onChange={(event) => setNewJdForm({ ...newJdForm, name: event.target.value })}
                  />
                </label>
                <label className="inline-checkbox">
                  <input
                    type="checkbox"
                    checked={newJdForm.set_as_primary}
                    onChange={(event) =>
                      setNewJdForm({ ...newJdForm, set_as_primary: event.target.checked })
                    }
                  />
                  设为主 JD
                </label>
                <label className="full-span">
                  JD 内容
                  <textarea
                    rows={6}
                    value={newJdForm.content}
                    onChange={(event) => setNewJdForm({ ...newJdForm, content: event.target.value })}
                    placeholder="粘贴岗位职责、任职要求、加分项等原文。"
                  />
                </label>
              </div>
              <div className="card-actions">
                <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleCreateJdClick()}>
                  {pending ? "处理中..." : "新增 JD"}
                </button>
              </div>
            </div>

            {activeTrackJds.length === 0 ? (
              <div className="empty-state compact">
                <p>当前方向还没有 JD。</p>
              </div>
            ) : (
              <div className="memory-stack">
                {activeTrackJds.map((jd) => {
                  const isEditing = editingJdId === jd.id;
                  return (
                    <article key={jd.id} className="memory-card">
                      {isEditing ? (
                        <>
                          <div className="form-grid">
                            <label>
                              JD 名称
                              <input value={editingJdName} onChange={(event) => setEditingJdName(event.target.value)} />
                            </label>
                            <label className="full-span">
                              JD 内容
                              <textarea
                                rows={8}
                                value={editingJdContent}
                                onChange={(event) => setEditingJdContent(event.target.value)}
                              />
                            </label>
                          </div>
                          <div className="card-actions">
                            <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleUpdateJdClick()}>
                              {pending ? "处理中..." : "保存 JD"}
                            </button>
                            <button
                              className="ghost-button compact-button"
                              type="button"
                              onClick={() => {
                                setEditingJdId("");
                                setEditingJdName("");
                                setEditingJdContent("");
                              }}
                            >
                              取消
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="memory-card-head">
                            <strong>{jd.name}</strong>
                            <span>{jd.is_primary ? "主 JD" : "备选 JD"}</span>
                          </div>
                          <pre className="jd-preview">{jd.content}</pre>
                          <div className="card-actions">
                            <button
                              className="ghost-button compact-button"
                              type="button"
                              onClick={() => {
                                setEditingJdId(jd.id);
                                setEditingJdName(jd.name);
                                setEditingJdContent(jd.content);
                              }}
                            >
                              编辑
                            </button>
                            <button
                              className="ghost-button compact-button"
                              type="button"
                              disabled={pending || jd.is_primary}
                              onClick={() => void onSetPrimaryJd(activeTrack.id, jd.id)}
                            >
                              设为主 JD
                            </button>
                            <button
                              className="danger-button compact-button"
                              type="button"
                              disabled={pending}
                              onClick={() => void onDeleteJd(jd.id)}
                            >
                              删除
                            </button>
                          </div>
                        </>
                      )}
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        </>
      ) : null}
    </section>
  );
}
