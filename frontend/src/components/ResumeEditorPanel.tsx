// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 ResumeEditor 面板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import { useMemo } from "react";

import type { ArtifactDetail, ArtifactSummary, JDSummary, TrackSummary } from "../types";

type ResumeEditorPanelProps = {
  sessionTitle: string;
  activeTrack: TrackSummary | null;
  currentJd: JDSummary | null;
  artifacts: ArtifactSummary[];
  selectedArtifactId: string;
  detail: ArtifactDetail | null;
  latestScoreDetail: ArtifactDetail | null;
  loading: boolean;
  editMode: boolean;
  draftContent: string;
  draftDirty: boolean;
  savingRevision: boolean;
  exportNotice: string;
  onSelectArtifact: (artifactId: string) => void;
  onToggleEditMode: () => void;
  onDraftContentChange: (value: string) => void;
  onSaveRevision: () => Promise<void>;
  onExportArtifact: (format: "docx" | "pdf") => Promise<void>;
  onOpenMatches: () => void;
};

type ResumeSection = {
  heading: string;
  lines: string[];
};

function isKeywordSection(heading: string) {
  return /关键词|competencies|skills/i.test(heading);
}

function formatArtifactType(artifactType: string) {
  if (artifactType === "generated_resume") {
    return "Generated";
  }
  if (artifactType === "polished_resume") {
    return "Polished";
  }
  if (artifactType === "edited_resume") {
    return "Edited";
  }
  return artifactType;
}

function parseResumeContent(content: string) {
  const lines = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  let title = "";
  const sections: ResumeSection[] = [];
  let currentHeading = "Overview";
  let currentLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("# ")) {
      if (!title) {
        title = line.slice(2).trim();
        continue;
      }
      if (currentLines.length > 0) {
        sections.push({ heading: currentHeading, lines: currentLines });
      }
      currentHeading = line.slice(2).trim();
      currentLines = [];
      continue;
    }

    if (line.startsWith("## ")) {
      if (currentLines.length > 0) {
        sections.push({ heading: currentHeading, lines: currentLines });
      }
      currentHeading = line.slice(3).trim();
      currentLines = [];
      continue;
    }

    currentLines.push(line);
  }

  if (currentLines.length > 0) {
    sections.push({ heading: currentHeading, lines: currentLines });
  }

  return {
    title: title || "Resume Draft",
    sections,
  };
}

export function ResumeEditorPanel({
  sessionTitle,
  activeTrack,
  currentJd,
  artifacts,
  selectedArtifactId,
  detail,
  latestScoreDetail,
  loading,
  editMode,
  draftContent,
  draftDirty,
  savingRevision,
  exportNotice,
  onSelectArtifact,
  onToggleEditMode,
  onDraftContentChange,
  onSaveRevision,
  onExportArtifact,
  onOpenMatches,
}: ResumeEditorPanelProps) {
  const editableArtifacts = useMemo(
    () =>
      artifacts.filter((artifact) =>
        ["generated_resume", "polished_resume", "edited_resume"].includes(artifact.artifact_type),
      ),
    [artifacts],
  );

  const selectedArtifact =
    editableArtifacts.find((artifact) => artifact.id === selectedArtifactId) ?? editableArtifacts[0] ?? null;
  const previewContent = draftContent || detail?.content || "";
  const parsed = useMemo(() => parseResumeContent(previewContent), [previewContent]);
  const scorePayload = latestScoreDetail?.parsed_payload ?? null;
  const scoreValue =
    typeof scorePayload?.final_score === "number"
      ? scorePayload.final_score
      : typeof scorePayload?.total_score === "number"
        ? scorePayload.total_score
        : null;
  const matchLevel =
    typeof scorePayload?.match_level === "string" ? scorePayload.match_level.toUpperCase() : "";

  return (
    <section className="panel resume-stage-panel">
      <div className="resume-stage-head">
        <div>
          <p className="panel-kicker">Resume Workspace</p>
          <h2>{activeTrack?.name || sessionTitle}</h2>
          <p className="resume-stage-subtitle">
            {currentJd?.name
              ? `当前主 JD：${currentJd.name}`
              : "还没有绑定主 JD。先在 JD Matches 里锁定主方向和主 JD。"}
          </p>
        </div>
        <div className="resume-head-actions">
          {selectedArtifact ? (
            <span className="soft-chip">{formatArtifactType(selectedArtifact.artifact_type)}</span>
          ) : null}
          <button className="ghost-button compact-button" type="button" onClick={onOpenMatches}>
            JD Matches
          </button>
        </div>
      </div>

      <div className="resume-toolbar">
        <div className="resume-status-strip">
          <span className="meta-pill">Track · {activeTrack?.name || "未锁定"}</span>
          <span className="meta-pill">JD · {currentJd?.name || "未绑定"}</span>
          {selectedArtifact ? (
            <label className="meta-pill meta-pill-select">
              <span>Version</span>
              <select
                value={selectedArtifact.id}
                onChange={(event) => onSelectArtifact(event.target.value)}
                disabled={editableArtifacts.length === 0}
              >
                {editableArtifacts.map((artifact) => (
                  <option key={artifact.id} value={artifact.id}>
                    {formatArtifactType(artifact.artifact_type)} · v{artifact.version}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <span className="meta-pill emphasis">
            Match · {scoreValue !== null ? `${scoreValue.toFixed(1)}` : "待评分"}
            {matchLevel ? ` · ${matchLevel}` : ""}
          </span>
        </div>
      </div>

      {exportNotice ? <div className="subtle-banner">{exportNotice}</div> : null}

      <div className={`resume-stage-shell ${editMode ? "is-editing" : ""}`}>
        <div className="resume-canvas">
          {loading ? (
            <div className="empty-state compact">
              <p>正在加载简历内容...</p>
            </div>
          ) : previewContent ? (
            <div className="resume-page-frame">
              <article className="resume-page">
                <header className="resume-page-header">
                  <div>
                    <h1>{parsed.title}</h1>
                    <p>{activeTrack?.positioning || "Current tailored resume draft"}</p>
                  </div>
                  <div className="resume-page-side">
                    {currentJd?.name ? <span>{currentJd.name}</span> : null}
                    {scoreValue !== null ? (
                      <span>
                        Match {scoreValue.toFixed(1)}
                        {matchLevel ? ` · ${matchLevel}` : ""}
                      </span>
                    ) : null}
                    {!currentJd && scoreValue === null ? <span>Ready for next draft</span> : null}
                  </div>
                </header>

                <div className="resume-page-body">
                  {parsed.sections.map((section) => (
                    <section key={section.heading} className="resume-section">
                      <div className="resume-section-label">{section.heading}</div>
                      <div className="resume-section-content">
                        {isKeywordSection(section.heading) ? (
                          <div className="resume-tag-list">
                            {section.lines.map((line, index) => (
                              <span key={`${section.heading}-${index}`} className="resume-tag">
                                {line.replace(/^- /, "").replace(/^\[[^\]]+\]\s*/, "")}
                              </span>
                            ))}
                          </div>
                        ) : (
                          section.lines.map((line, index) => {
                            const cleaned = line.replace(/^- /, "").trim();
                            const richTagMatch = cleaned.match(/^\[([^\]]+)\]\s*(.+)$/);
                            if (richTagMatch) {
                              return (
                                <p key={`${section.heading}-${index}`} className="resume-block">
                                  <span className="resume-inline-tag">{richTagMatch[1]}</span>
                                  {richTagMatch[2]}
                                </p>
                              );
                            }
                            return (
                              <p key={`${section.heading}-${index}`} className="resume-block">
                                {cleaned}
                              </p>
                            );
                          })
                        )}
                      </div>
                    </section>
                  ))}
                </div>
              </article>
            </div>
          ) : (
            <div className="resume-page-frame">
              <article className="resume-page ghost">
                <header className="resume-page-header">
                  <div>
                    <h1>{activeTrack?.name || "Resume Draft"}</h1>
                    <p>{currentJd?.name ? "Primary JD Locked" : "Ready for first tailored draft"}</p>
                  </div>
                  <div className="resume-page-side">
                    <span>{currentJd?.name || "No primary JD selected"}</span>
                    <span>
                      {scoreValue !== null
                        ? `Match ${scoreValue.toFixed(1)}${matchLevel ? ` · ${matchLevel}` : ""}`
                        : "Run a score to see fit"}
                    </span>
                  </div>
                </header>
                <div className="resume-page-body ghost-body">
                  <section className="resume-section">
                    <div className="resume-section-label">Professional Summary</div>
                    <div className="resume-section-content">
                      <div className="ghost-line w-92" />
                      <div className="ghost-line w-84" />
                      <div className="ghost-line w-76" />
                    </div>
                  </section>
                  <section className="resume-section">
                    <div className="resume-section-label">Core Strengths</div>
                    <div className="resume-section-content">
                      <div className="ghost-chip-row">
                        {(activeTrack?.core_keywords.slice(0, 4).length
                          ? activeTrack.core_keywords.slice(0, 4)
                          : ["Execution", "Product Sense", "Analysis", "Communication"]
                        ).map((keyword) => (
                          <span key={keyword} className="resume-tag">
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  </section>
                  <section className="resume-section">
                    <div className="resume-section-label">Experience</div>
                    <div className="resume-section-content">
                      <div className="ghost-line w-96" />
                      <div className="ghost-line w-88" />
                      <div className="ghost-line w-80" />
                      <div className="ghost-line w-90" />
                    </div>
                  </section>
                  <section className="resume-section">
                    <div className="resume-section-label">Selected Impact</div>
                    <div className="resume-section-content">
                      <div className="ghost-line w-90" />
                      <div className="ghost-line w-82" />
                      <div className="ghost-line w-74" />
                    </div>
                  </section>
                </div>
              </article>
            </div>
          )}
        </div>

        {editMode ? (
          <aside className="editor-drawer">
            <div className="editor-drawer-head">
              <strong>实时编辑</strong>
              <span>{draftDirty ? "有未保存修改" : "预览与当前版本一致"}</span>
            </div>
            <textarea
              value={draftContent}
              onChange={(event) => onDraftContentChange(event.target.value)}
              placeholder="在这里直接修改简历正文，右侧预览会实时更新。"
            />
            <div className="editor-drawer-foot">
              <span>{previewContent.length} chars</span>
              <button
                className="primary-button compact-button"
                type="button"
                disabled={!draftDirty || savingRevision}
                onClick={() => void onSaveRevision()}
              >
                {savingRevision ? "保存中..." : "保存新版本"}
              </button>
            </div>
          </aside>
        ) : null}
      </div>

      {selectedArtifact ? (
        <div className="resume-floating-dock">
          <button className="dock-button" type="button" onClick={onToggleEditMode}>
            {editMode ? "Close Edit" : "Edit Mode"}
          </button>
          {editMode ? <span className="dock-divider" aria-hidden="true" /> : null}
          {editMode ? (
            <button
              className="dock-button"
              type="button"
              disabled={!draftDirty || savingRevision}
              onClick={() => void onSaveRevision()}
            >
              {savingRevision ? "Saving..." : "Save Version"}
            </button>
          ) : null}
          <span className="dock-divider" aria-hidden="true" />
          <button className="dock-button" type="button" onClick={() => void onExportArtifact("pdf")}>
            Export PDF
          </button>
          <span className="dock-divider" aria-hidden="true" />
          <button className="dock-button" type="button" onClick={() => void onExportArtifact("docx")}>
            Export DOCX
          </button>
        </div>
      ) : null}
    </section>
  );
}
