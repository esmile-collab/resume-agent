// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 Memory 面板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import { useEffect, useState } from "react";

import type { ExperienceItem, Snapshot } from "../types";

function splitValues(raw: string) {
  return raw
    .split(/[\n,，、/]+/)
    .map((value) => value.trim())
    .filter(Boolean);
}

function joinValues(values: string[]) {
  return values.join("，");
}

const emptyExperience: Omit<ExperienceItem, "id"> = {
  title: "",
  organization: "",
  time_range: "",
  summary: "",
  tags: [],
  metrics: [],
  evidence: [],
  confidence: 0.7,
  source: "manual",
};

type MemoryPanelProps = {
  snapshot: Snapshot | null;
  pending: boolean;
  onSaveProfile: (input: {
    summary: string;
    education: string;
    years_of_experience: string;
    preferred_city: string;
    target_roles: string[];
    exclusions: string[];
  }) => Promise<void>;
  onCreateExperience: (input: Omit<ExperienceItem, "id">) => Promise<void>;
  onUpdateExperience: (experienceId: string, input: Omit<ExperienceItem, "id">) => Promise<void>;
  onDeleteExperience: (experienceId: string) => Promise<void>;
};

export function MemoryPanel({
  snapshot,
  pending,
  onSaveProfile,
  onCreateExperience,
  onUpdateExperience,
  onDeleteExperience,
}: MemoryPanelProps) {
  const [summary, setSummary] = useState("");
  const [education, setEducation] = useState("");
  const [yearsOfExperience, setYearsOfExperience] = useState("");
  const [preferredCity, setPreferredCity] = useState("");
  const [targetRolesText, setTargetRolesText] = useState("");
  const [exclusionsText, setExclusionsText] = useState("");
  const [showNewExperience, setShowNewExperience] = useState(false);
  const [newExperience, setNewExperience] = useState<Omit<ExperienceItem, "id">>(emptyExperience);
  const [editingExperienceId, setEditingExperienceId] = useState("");
  const [editingExperience, setEditingExperience] = useState<Omit<ExperienceItem, "id">>(emptyExperience);

  useEffect(() => {
    if (!snapshot) {
      return;
    }
    setSummary(snapshot.profile.summary ?? "");
    setEducation((snapshot.profile.basics.education as string | undefined) ?? "");
    setYearsOfExperience((snapshot.profile.basics.years_of_experience as string | undefined) ?? "");
    setPreferredCity((snapshot.profile.preferences.preferred_city as string | undefined) ?? "");
    setTargetRolesText(joinValues((snapshot.profile.preferences.target_roles as string[] | undefined) ?? []));
    setExclusionsText(joinValues((snapshot.profile.constraints.exclusions as string[] | undefined) ?? []));
  }, [snapshot]);

  if (!snapshot) {
    return null;
  }

  async function handleSaveProfile() {
    await onSaveProfile({
      summary,
      education,
      years_of_experience: yearsOfExperience,
      preferred_city: preferredCity,
      target_roles: splitValues(targetRolesText),
      exclusions: splitValues(exclusionsText),
    });
  }

  async function handleCreateExperienceClick() {
    await onCreateExperience({
      ...newExperience,
      tags: splitValues(joinValues(newExperience.tags)),
      metrics: splitValues(joinValues(newExperience.metrics)),
      evidence: splitValues(joinValues(newExperience.evidence)),
    });
    setNewExperience(emptyExperience);
    setShowNewExperience(false);
  }

  function startEditingExperience(item: ExperienceItem) {
    setEditingExperienceId(item.id);
    setEditingExperience({
      title: item.title,
      organization: item.organization,
      time_range: item.time_range,
      summary: item.summary,
      tags: item.tags,
      metrics: item.metrics,
      evidence: item.evidence,
      confidence: item.confidence,
      source: item.source,
    });
  }

  async function handleUpdateExperienceClick() {
    await onUpdateExperience(editingExperienceId, {
      ...editingExperience,
      tags: splitValues(joinValues(editingExperience.tags)),
      metrics: splitValues(joinValues(editingExperience.metrics)),
      evidence: splitValues(joinValues(editingExperience.evidence)),
    });
    setEditingExperienceId("");
    setEditingExperience(emptyExperience);
  }

  return (
    <section className="panel side-panel">
      <div className="panel-head">
        <div>
          <p className="panel-kicker">Memory Panel</p>
          <h2>候选人记忆</h2>
        </div>
        <span className="chip">可审核 / 可编辑</span>
      </div>

      <div className="profile-hero">
        <strong>{summary || "等待更多背景信息"}</strong>
        <div className="profile-meta">
          {education ? <span>{education}</span> : null}
          {yearsOfExperience ? <span>{yearsOfExperience} 年经验</span> : null}
          {preferredCity ? <span>{preferredCity}</span> : null}
        </div>
      </div>

      <div className="memory-section">
        <div className="section-toolbar">
          <h3>画像与偏好</h3>
          <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleSaveProfile()}>
            {pending ? "保存中..." : "保存画像"}
          </button>
        </div>
        <div className="form-grid">
          <label>
            候选人摘要
            <textarea rows={4} value={summary} onChange={(event) => setSummary(event.target.value)} />
          </label>
          <label>
            目标方向
            <input value={targetRolesText} onChange={(event) => setTargetRolesText(event.target.value)} placeholder="策略产品，商业分析" />
          </label>
          <label>
            学历
            <input value={education} onChange={(event) => setEducation(event.target.value)} placeholder="本科 / 硕士" />
          </label>
          <label>
            经验年限
            <input value={yearsOfExperience} onChange={(event) => setYearsOfExperience(event.target.value)} placeholder="2" />
          </label>
          <label>
            目标城市
            <input value={preferredCity} onChange={(event) => setPreferredCity(event.target.value)} placeholder="上海" />
          </label>
          <label>
            排除项
            <input value={exclusionsText} onChange={(event) => setExclusionsText(event.target.value)} placeholder="纯销售，不考虑出差过多" />
          </label>
        </div>
      </div>

      <div className="memory-section">
        <div className="section-toolbar">
          <h3>经历资产</h3>
          <button
            className="ghost-button compact-button"
            type="button"
            onClick={() => setShowNewExperience((value) => !value)}
          >
            {showNewExperience ? "收起新增" : "新增经历"}
          </button>
        </div>

        {showNewExperience ? (
          <div className="editor-card">
            <div className="form-grid">
              <label>
                标题
                <input
                  value={newExperience.title}
                  onChange={(event) => setNewExperience({ ...newExperience, title: event.target.value })}
                />
              </label>
              <label>
                公司/项目
                <input
                  value={newExperience.organization}
                  onChange={(event) => setNewExperience({ ...newExperience, organization: event.target.value })}
                />
              </label>
              <label>
                时间
                <input
                  value={newExperience.time_range}
                  onChange={(event) => setNewExperience({ ...newExperience, time_range: event.target.value })}
                  placeholder="2024.01 - 2024.12"
                />
              </label>
              <label>
                置信度
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={newExperience.confidence}
                  onChange={(event) =>
                    setNewExperience({ ...newExperience, confidence: Number(event.target.value) || 0 })
                  }
                />
              </label>
              <label className="full-span">
                描述
                <textarea
                  rows={4}
                  value={newExperience.summary}
                  onChange={(event) => setNewExperience({ ...newExperience, summary: event.target.value })}
                />
              </label>
              <label>
                标签
                <input
                  value={joinValues(newExperience.tags)}
                  onChange={(event) => setNewExperience({ ...newExperience, tags: splitValues(event.target.value) })}
                />
              </label>
              <label>
                指标
                <input
                  value={joinValues(newExperience.metrics)}
                  onChange={(event) =>
                    setNewExperience({ ...newExperience, metrics: splitValues(event.target.value) })
                  }
                />
              </label>
              <label className="full-span">
                证据
                <input
                  value={joinValues(newExperience.evidence)}
                  onChange={(event) =>
                    setNewExperience({ ...newExperience, evidence: splitValues(event.target.value) })
                  }
                />
              </label>
            </div>
            <div className="card-actions">
              <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleCreateExperienceClick()}>
                {pending ? "处理中..." : "保存经历"}
              </button>
            </div>
          </div>
        ) : null}

        {snapshot.experiences.length === 0 ? (
          <p className="subtle-text">还没有沉淀可复用经历。</p>
        ) : (
          <div className="memory-stack">
            {snapshot.experiences.map((item) => {
              const isEditing = editingExperienceId === item.id;
              return (
                <article key={item.id} className="memory-card">
                  {isEditing ? (
                    <>
                      <div className="form-grid">
                        <label>
                          标题
                          <input
                            value={editingExperience.title}
                            onChange={(event) =>
                              setEditingExperience({ ...editingExperience, title: event.target.value })
                            }
                          />
                        </label>
                        <label>
                          公司/项目
                          <input
                            value={editingExperience.organization}
                            onChange={(event) =>
                              setEditingExperience({ ...editingExperience, organization: event.target.value })
                            }
                          />
                        </label>
                        <label>
                          时间
                          <input
                            value={editingExperience.time_range}
                            onChange={(event) =>
                              setEditingExperience({ ...editingExperience, time_range: event.target.value })
                            }
                          />
                        </label>
                        <label>
                          置信度
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.1"
                            value={editingExperience.confidence}
                            onChange={(event) =>
                              setEditingExperience({
                                ...editingExperience,
                                confidence: Number(event.target.value) || 0,
                              })
                            }
                          />
                        </label>
                        <label className="full-span">
                          描述
                          <textarea
                            rows={4}
                            value={editingExperience.summary}
                            onChange={(event) =>
                              setEditingExperience({ ...editingExperience, summary: event.target.value })
                            }
                          />
                        </label>
                        <label>
                          标签
                          <input
                            value={joinValues(editingExperience.tags)}
                            onChange={(event) =>
                              setEditingExperience({
                                ...editingExperience,
                                tags: splitValues(event.target.value),
                              })
                            }
                          />
                        </label>
                        <label>
                          指标
                          <input
                            value={joinValues(editingExperience.metrics)}
                            onChange={(event) =>
                              setEditingExperience({
                                ...editingExperience,
                                metrics: splitValues(event.target.value),
                              })
                            }
                          />
                        </label>
                        <label className="full-span">
                          证据
                          <input
                            value={joinValues(editingExperience.evidence)}
                            onChange={(event) =>
                              setEditingExperience({
                                ...editingExperience,
                                evidence: splitValues(event.target.value),
                              })
                            }
                          />
                        </label>
                      </div>
                      <div className="card-actions">
                        <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleUpdateExperienceClick()}>
                          {pending ? "处理中..." : "保存修改"}
                        </button>
                        <button
                          className="ghost-button compact-button"
                          type="button"
                          onClick={() => {
                            setEditingExperienceId("");
                            setEditingExperience(emptyExperience);
                          }}
                        >
                          取消
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="memory-card-head">
                        <strong>{item.title}</strong>
                        <span>{item.time_range || "未标注时间"}</span>
                      </div>
                      <p>{item.summary}</p>
                      <div className="tag-row">
                        {item.tags.map((tag) => (
                          <span key={tag} className="tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                      <div className="card-actions">
                        <button className="ghost-button compact-button" type="button" onClick={() => startEditingExperience(item)}>
                          编辑
                        </button>
                        <button className="danger-button compact-button" type="button" disabled={pending} onClick={() => void onDeleteExperience(item.id)}>
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
    </section>
  );
}
