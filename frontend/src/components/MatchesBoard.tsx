// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 Matches 看板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import { useEffect, useMemo, useState } from "react";

import type { ArtifactDetail, ArtifactSummary, JDSummary, TrackSummary } from "../types";

function splitValues(raw: string) {
  return raw
    .split(/[\n,，、/]+/)
    .map((value) => value.trim())
    .filter(Boolean);
}

function joinValues(values: string[]) {
  return values.join("，");
}

type MatchFilter = "all" | "high" | "recent" | "review";

type MatchesBoardProps = {
  tracks: TrackSummary[];
  activeTrackId: string;
  activeTrackJds: JDSummary[];
  loadingTrackJds: boolean;
  pending: boolean;
  artifacts: ArtifactSummary[];
  latestScoreDetail: ArtifactDetail | null;
  onSelectTrack: (track: TrackSummary) => void;
  onOpenResumeWorkspace: () => void;
  onCreateTrack: (input: {
    name: string;
    positioning: string;
    core_keywords: string[];
    resume_strategy: string;
    default_resume_outline: string;
  }) => Promise<TrackSummary>;
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

function scoreStatus(score: number | null) {
  if (score === null) {
    return "No score yet";
  }
  if (score >= 85) {
    return "Strong Match";
  }
  if (score >= 70) {
    return "Good Match";
  }
  return "Needs Review";
}

function scoreTone(score: number | null) {
  if (score === null) {
    return "muted";
  }
  if (score >= 85) {
    return "strong";
  }
  if (score >= 70) {
    return "warm";
  }
  return "review";
}

export function MatchesBoard({
  tracks,
  activeTrackId,
  activeTrackJds,
  loadingTrackJds,
  pending,
  artifacts,
  latestScoreDetail,
  onSelectTrack,
  onOpenResumeWorkspace,
  onCreateTrack,
  onUpdateTrack,
  onDeleteTrack,
  onCreateJd,
  onUpdateJd,
  onDeleteJd,
  onSetPrimaryJd,
}: MatchesBoardProps) {
  const activeTrack = tracks.find((track) => track.id === activeTrackId) ?? tracks[0] ?? null;
  const [filter, setFilter] = useState<MatchFilter>("all");
  const [showCreateTrack, setShowCreateTrack] = useState(false);
  const [showEditTrack, setShowEditTrack] = useState(false);
  const [showCreateJd, setShowCreateJd] = useState(false);
  const [showManageTrack, setShowManageTrack] = useState(false);
  const [newTrackForm, setNewTrackForm] = useState(emptyTrackForm);
  const [editTrackForm, setEditTrackForm] = useState(emptyTrackForm);
  const [newJdForm, setNewJdForm] = useState(emptyJdForm);
  const [editingJdId, setEditingJdId] = useState("");
  const [editingJdName, setEditingJdName] = useState("");
  const [editingJdContent, setEditingJdContent] = useState("");

  function handleToggleCreateTrack() {
    setShowCreateTrack((value) => !value);
    setShowEditTrack(false);
    setShowCreateJd(false);
    setShowManageTrack(false);
  }

  function handleToggleEditTrack() {
    setShowEditTrack((value) => !value);
    setShowCreateTrack(false);
    setShowCreateJd(false);
    setShowManageTrack(true);
  }

  function handleToggleCreateJd() {
    setShowCreateJd((value) => !value);
    setShowCreateTrack(false);
    setShowEditTrack(false);
    setShowManageTrack(true);
  }

  function handleOpenManageTrack(track: TrackSummary) {
    onSelectTrack(track);
    setShowManageTrack(true);
    setShowEditTrack(false);
    setShowCreateJd(false);
  }

  function handleCloseManageTrack() {
    setShowManageTrack(false);
    setShowEditTrack(false);
    setShowCreateJd(false);
    setEditingJdId("");
    setEditingJdName("");
    setEditingJdContent("");
  }

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

  const scoreByTrack = useMemo(() => {
    const mapping = new Map<
      string,
      {
        artifact: ArtifactSummary | null;
        score: number | null;
        matchLevel: string;
      }
    >();

    tracks.forEach((track) => {
      mapping.set(track.id, { artifact: null, score: null, matchLevel: "" });
    });

    artifacts
      .filter((artifact) => artifact.artifact_type === "score_report")
      .forEach((artifact) => {
        const current = mapping.get(artifact.track_id);
        if (!current || !current.artifact || current.artifact.version < artifact.version) {
          const scoreValue =
            typeof artifact.summary.score === "number"
              ? artifact.summary.score
              : typeof artifact.summary.final_score === "number"
                ? artifact.summary.final_score
                : null;
          const matchLevel = String(artifact.summary.match_level ?? "");
          mapping.set(artifact.track_id, { artifact, score: scoreValue, matchLevel });
        }
      });

    return mapping;
  }, [artifacts, tracks]);

  const trackCards = useMemo(() => {
    return tracks.map((track, index) => {
      const scoreMeta = scoreByTrack.get(track.id);
      return {
        track,
        index,
        score: scoreMeta?.score ?? null,
        matchLevel: scoreMeta?.matchLevel ?? "",
        version: scoreMeta?.artifact?.version ?? 0,
      };
    });
  }, [scoreByTrack, tracks]);

  const filteredTrackCards = useMemo(() => {
    const sorted = [...trackCards].sort((left, right) => right.version - left.version || left.index - right.index);
    switch (filter) {
      case "high":
        return sorted.filter((item) => item.score !== null && item.score >= 85);
      case "recent":
        return sorted.slice(0, 6);
      case "review":
        return sorted.filter((item) => item.score === null || item.score < 70);
      default:
        return sorted;
    }
  }, [filter, trackCards]);

  useEffect(() => {
    if (filteredTrackCards.length === 0) {
      return;
    }
    const activeVisible = filteredTrackCards.some((item) => item.track.id === activeTrack?.id);
    if (!activeVisible) {
      onSelectTrack(filteredTrackCards[0].track);
    }
  }, [activeTrack?.id, filteredTrackCards, onSelectTrack]);

  const activeTrackCard =
    filteredTrackCards.find((item) => item.track.id === activeTrack?.id) ??
    trackCards.find((item) => item.track.id === activeTrack?.id) ??
    null;
  const currentPrimaryJd = useMemo(
    () => activeTrackJds.find((item) => item.is_primary) ?? activeTrackJds[0] ?? null,
    [activeTrackJds],
  );
  const visibleTrackCards = filteredTrackCards.slice(0, 5);
  const hiddenTrackCount = Math.max(0, filteredTrackCards.length - visibleTrackCards.length);

  const scorePayload =
    latestScoreDetail && latestScoreDetail.artifact.track_id === activeTrack?.id
      ? latestScoreDetail.parsed_payload
      : null;
  const quickImprovements = (scorePayload?.quick_improvements as string[] | undefined) ?? [];
  const finalScore =
    typeof scorePayload?.final_score === "number"
      ? scorePayload.final_score
      : activeTrackCard?.score ?? null;

  async function handleCreateTrackClick() {
    const nextName = newTrackForm.name.trim() || "未命名方向";
    const nextJdContent = newTrackForm.positioning.trim();
    const createdTrack = await onCreateTrack({
      name: nextName,
      positioning: nextJdContent
        ? nextJdContent.slice(0, 140)
        : `${nextName} 方向，优先对齐岗位职责、核心要求与量化结果。`,
      core_keywords: splitValues(newTrackForm.core_keywords || nextName),
      resume_strategy:
        newTrackForm.resume_strategy.trim() ||
        "优先突出与目标岗位最接近的项目、量化结果和岗位关键词，不补造不存在经历。",
      default_resume_outline:
        newTrackForm.default_resume_outline.trim() || "概述 / 相关经历 / 项目经历 / 技能 / 教育",
    });

    if (nextJdContent) {
      await onCreateJd(createdTrack.id, {
        name: `${nextName}-primary-jd.txt`,
        content: nextJdContent,
        set_as_primary: true,
      });
    }

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
    setShowEditTrack(false);
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
    setShowCreateJd(false);
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

  const filterItems = [
    { key: "all" as const, label: `All Matches (${tracks.length})` },
    {
      key: "high" as const,
      label: `Strong Matches (${trackCards.filter((item) => item.score !== null && item.score >= 85).length})`,
    },
    { key: "recent" as const, label: "Recently Viewed" },
    {
      key: "review" as const,
      label: `Needs Review (${trackCards.filter((item) => item.score === null || item.score < 70).length})`,
    },
  ];

  return (
    <section className="matches-board">
      <section className="matches-hero-simple">
        <div>
          <h2>Career Dashboard</h2>
          <p className="matches-hero-copy">Optimize your profile against specific job descriptions.</p>
        </div>
        <div className="matches-hero-actions">
          <button className="primary-button compact-button" type="button" onClick={handleToggleCreateTrack}>
            + Create New Match
          </button>
        </div>
      </section>

      {showCreateTrack ? (
        <div className="matches-modal-backdrop" role="presentation" onClick={() => setShowCreateTrack(false)}>
          <section className="matches-modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <div className="matches-form-head">
              <div>
                <h3>Create New Job Match</h3>
                <p className="matches-form-copy">Add a target role and the primary job description you want to match.</p>
              </div>
              <button className="icon-button subtle" type="button" onClick={() => setShowCreateTrack(false)}>
                ×
              </button>
            </div>
            <div className="form-grid matches-create-grid">
              <label className="full-span">
                Job Title or Company Name
                <input
                  value={newTrackForm.name}
                  onChange={(event) => setNewTrackForm({ ...newTrackForm, name: event.target.value })}
                  placeholder="e.g. Senior Product Designer at TechCorp"
                />
              </label>
              <label className="full-span">
                Paste Job Description
                <textarea
                  rows={10}
                  value={newTrackForm.positioning}
                  onChange={(event) => setNewTrackForm({ ...newTrackForm, positioning: event.target.value })}
                  placeholder="Paste the full job description details here... include responsibilities, requirements, and about the company."
                />
              </label>
            </div>
            <div className="matches-modal-actions">
              <button className="ghost-button compact-button" type="button" onClick={() => setShowCreateTrack(false)}>
                Cancel
              </button>
              <button
                className="primary-button compact-button"
                type="button"
                disabled={pending || !newTrackForm.name.trim() || !newTrackForm.positioning.trim()}
                onClick={() => void handleCreateTrackClick()}
              >
                {pending ? "Saving..." : "Analyze & Match"}
              </button>
            </div>
          </section>
        </div>
      ) : null}

      {showManageTrack && activeTrack && activeTrackCard ? (
        <div className="matches-modal-backdrop" role="presentation" onClick={handleCloseManageTrack}>
          <section
            className="matches-modal matches-manage-modal"
            role="dialog"
            aria-modal="true"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="matches-form-head">
              <div>
                <p className="panel-kicker">Selected Match</p>
                <h3>{activeTrack.name}</h3>
                <p className="matches-form-copy">Review the role, update its primary JD, or jump back into the resume workspace.</p>
              </div>
              <div className="card-actions">
                <button className="ghost-button compact-button" type="button" onClick={handleToggleEditTrack}>
                  {showEditTrack ? "Close Edit" : "Edit Match"}
                </button>
                <button className="icon-button subtle" type="button" onClick={handleCloseManageTrack}>
                  ×
                </button>
              </div>
            </div>

            <div className="matches-manage-summary">
              <article>
                <span className="context-label">Role</span>
                <p>{activeTrack.positioning || "No role summary yet."}</p>
              </article>
              <article>
                <span className="context-label">Primary JD</span>
                <p>{currentPrimaryJd?.name || "No primary JD selected"}</p>
              </article>
              <article>
                <span className="context-label">Last Score</span>
                <p>{finalScore !== null ? `${finalScore.toFixed(1)}%` : "No score yet"}</p>
              </article>
            </div>

            <div className="matches-manage-actions">
              <button className="primary-button compact-button" type="button" onClick={handleToggleCreateJd}>
                {showCreateJd ? "Close JD Form" : "Add JD"}
              </button>
              <button className="ghost-button compact-button" type="button" onClick={onOpenResumeWorkspace}>
                Open Resume Workspace
              </button>
              <button
                className="danger-button compact-button"
                type="button"
                disabled={pending}
                onClick={() => void onDeleteTrack(activeTrack.id)}
              >
                Delete Match
              </button>
            </div>

            {showEditTrack ? (
              <div className="editor-card">
                <div className="form-grid">
                  <label>
                    Match Name
                    <input
                      value={editTrackForm.name}
                      onChange={(event) => setEditTrackForm({ ...editTrackForm, name: event.target.value })}
                    />
                  </label>
                  <label>
                    Keywords
                    <input
                      value={editTrackForm.core_keywords}
                      onChange={(event) =>
                        setEditTrackForm({ ...editTrackForm, core_keywords: event.target.value })
                      }
                    />
                  </label>
                  <label className="full-span">
                    Role Summary
                    <textarea
                      rows={3}
                      value={editTrackForm.positioning}
                      onChange={(event) => setEditTrackForm({ ...editTrackForm, positioning: event.target.value })}
                    />
                  </label>
                  <label className="full-span">
                    Resume Strategy
                    <textarea
                      rows={3}
                      value={editTrackForm.resume_strategy}
                      onChange={(event) =>
                        setEditTrackForm({ ...editTrackForm, resume_strategy: event.target.value })
                      }
                    />
                  </label>
                  <label className="full-span">
                    Outline
                    <textarea
                      rows={3}
                      value={editTrackForm.default_resume_outline}
                      onChange={(event) =>
                        setEditTrackForm({ ...editTrackForm, default_resume_outline: event.target.value })
                      }
                    />
                  </label>
                </div>
                <div className="card-actions">
                  <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleUpdateTrackClick()}>
                    {pending ? "Saving..." : "Save Match"}
                  </button>
                </div>
              </div>
            ) : null}

            {showCreateJd ? (
              <div className="editor-card">
                <div className="form-grid">
                  <label>
                    JD Name
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
                    Set as primary JD
                  </label>
                  <label className="full-span">
                    Job Description
                    <textarea
                      rows={6}
                      value={newJdForm.content}
                      onChange={(event) => setNewJdForm({ ...newJdForm, content: event.target.value })}
                      placeholder="Paste the job description here."
                    />
                  </label>
                </div>
                <div className="card-actions">
                  <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleCreateJdClick()}>
                    {pending ? "Saving..." : "Save JD"}
                  </button>
                </div>
              </div>
            ) : null}

            <div className="matches-jd-list compact">
              {loadingTrackJds ? (
                <div className="empty-state compact">
                  <p>Loading job descriptions...</p>
                </div>
              ) : activeTrackJds.length === 0 ? (
                <div className="empty-state compact">
                  <p>No job descriptions yet.</p>
                </div>
              ) : (
                activeTrackJds.map((jd) => {
                  const isEditing = editingJdId === jd.id;
                  return (
                    <article key={jd.id} className={`matches-jd-card ${jd.is_primary ? "primary" : ""}`}>
                      {isEditing ? (
                        <>
                          <div className="form-grid">
                            <label>
                              JD Name
                              <input value={editingJdName} onChange={(event) => setEditingJdName(event.target.value)} />
                            </label>
                            <label className="full-span">
                              Job Description
                              <textarea
                                rows={8}
                                value={editingJdContent}
                                onChange={(event) => setEditingJdContent(event.target.value)}
                              />
                            </label>
                          </div>
                          <div className="card-actions">
                            <button className="primary-button compact-button" type="button" disabled={pending} onClick={() => void handleUpdateJdClick()}>
                              {pending ? "Saving..." : "Save JD"}
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
                              Cancel
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="matches-jd-head">
                            <div>
                              <strong>{jd.name}</strong>
                              <small>{jd.is_primary ? "Primary JD" : "Secondary JD"}</small>
                            </div>
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
                                Edit
                              </button>
                              <button
                                className="ghost-button compact-button"
                                type="button"
                                disabled={pending || jd.is_primary}
                                onClick={() => void onSetPrimaryJd(activeTrack.id, jd.id)}
                              >
                                Set Primary
                              </button>
                              <button
                                className="danger-button compact-button"
                                type="button"
                                disabled={pending}
                                onClick={() => void onDeleteJd(jd.id)}
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                          <p>{jd.preview}</p>
                        </>
                      )}
                    </article>
                  );
                })
              )}
            </div>
          </section>
        </div>
      ) : null}

      <div className="matches-filter-tabs" role="tablist" aria-label="Match filters">
        {filterItems.map((item) => (
          <button
            key={item.key}
            className={filter === item.key ? "active" : ""}
            type="button"
            onClick={() => setFilter(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="matches-dashboard-grid">
        {visibleTrackCards.length === 0 ? (
            <div className="empty-state matches-empty-state">
              <p>No matches in this view.</p>
              <p>Create a new match or switch filters.</p>
            </div>
          ) : (
            visibleTrackCards.map((item) => (
              <article
                key={item.track.id}
                className={`matches-track-card ${item.track.id === activeTrack?.id ? "active" : ""}`}
              >
                <div className="matches-card-topline">
                  <span className={`matches-track-badge tone-${scoreTone(item.score)}`}>{item.track.name.slice(0, 1)}</span>
                  <button
                    className="matches-card-menu"
                    type="button"
                    aria-label={`Open ${item.track.name}`}
                    onClick={() => handleOpenManageTrack(item.track)}
                  >
                    ⋯
                  </button>
                </div>
                <div className="matches-track-copy">
                  <strong>{item.track.name}</strong>
                  <p>
                    {item.track.core_keywords.length > 0
                      ? item.track.core_keywords.slice(0, 2).join(" • ")
                      : `${item.track.jd_count} JD`}
                  </p>
                </div>
                <div className="matches-track-score-block">
                  <label>MATCH SCORE</label>
                  <div className="matches-score-inline">
                    <strong>{item.score !== null ? `${Math.round(item.score)}%` : "--"}</strong>
                    <div className={`mini-progress tone-${scoreTone(item.score)}`}>
                      <span
                        style={{ width: `${item.score !== null ? Math.max(10, Math.min(100, item.score)) : 18}%` }}
                      />
                    </div>
                  </div>
                </div>
                <div className="matches-track-footer">
                  <small>{scoreStatus(item.score)}</small>
                  <button className="matches-card-arrow" type="button" onClick={() => handleOpenManageTrack(item.track)}>
                    →
                  </button>
                </div>
              </article>
            ))
          )}

        {hiddenTrackCount > 0 ? (
          <article className="matches-track-card more-card">
            <div className="matches-card-topline">
              <span className="matches-track-badge tone-muted">+</span>
            </div>
            <div className="matches-track-copy">
              <strong>{hiddenTrackCount} more matches</strong>
              <p>Refine filters to reduce the list.</p>
            </div>
          </article>
        ) : null}

        <button type="button" className="matches-track-card add-card" onClick={handleToggleCreateTrack}>
          <span>+</span>
          <strong>Analyze New Job</strong>
          <p>Paste a JD and match your resume.</p>
        </button>
      </div>
    </section>
  );
}
