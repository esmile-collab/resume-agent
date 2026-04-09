// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 Artifact 面板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import { useEffect, useMemo, useState } from "react";

import type { ArtifactDetail, ArtifactDiff, ArtifactSummary, TrackSummary } from "../types";

type ArtifactPanelProps = {
  artifacts: ArtifactSummary[];
  tracks: TrackSummary[];
  selectedArtifactId: string;
  detail: ArtifactDetail | null;
  diff: ArtifactDiff | null;
  loadingDetail: boolean;
  loadingDiff: boolean;
  exportNotice: string;
  onSelectArtifact: (artifactId: string) => void;
  onCompareArtifacts: (baseArtifactId: string) => Promise<void>;
  onExportArtifact: (format: "docx" | "pdf") => Promise<void>;
};

export function ArtifactPanel({
  artifacts,
  tracks,
  selectedArtifactId,
  detail,
  diff,
  loadingDetail,
  loadingDiff,
  exportNotice,
  onSelectArtifact,
  onCompareArtifacts,
  onExportArtifact,
}: ArtifactPanelProps) {
  const [trackFilter, setTrackFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [baseArtifactId, setBaseArtifactId] = useState("");

  const filteredArtifacts = useMemo(() => {
    return artifacts.filter((artifact) => {
      if (trackFilter !== "all" && artifact.track_id !== trackFilter) {
        return false;
      }
      if (typeFilter !== "all" && artifact.artifact_type !== typeFilter) {
        return false;
      }
      return true;
    });
  }, [artifacts, trackFilter, typeFilter]);

  const selectedArtifact = useMemo(
    () => filteredArtifacts.find((artifact) => artifact.id === selectedArtifactId) ?? null,
    [filteredArtifacts, selectedArtifactId],
  );

  const artifactTypes = useMemo(
    () => Array.from(new Set(artifacts.map((artifact) => artifact.artifact_type))),
    [artifacts],
  );

  const compareCandidates = useMemo(() => {
    if (!selectedArtifact) {
      return [];
    }
    return artifacts.filter(
      (artifact) =>
        artifact.id !== selectedArtifact.id &&
        artifact.artifact_type === selectedArtifact.artifact_type &&
        artifact.track_id === selectedArtifact.track_id,
    );
  }, [artifacts, selectedArtifact]);

  useEffect(() => {
    if (filteredArtifacts.length === 0) {
      return;
    }
    if (!filteredArtifacts.some((artifact) => artifact.id === selectedArtifactId)) {
      onSelectArtifact(filteredArtifacts[0].id);
    }
  }, [filteredArtifacts, onSelectArtifact, selectedArtifactId]);

  useEffect(() => {
    setBaseArtifactId(compareCandidates[0]?.id ?? "");
  }, [selectedArtifactId, compareCandidates]);

  return (
    <section className="panel artifact-panel">
      <div className="panel-head">
        <div>
          <p className="panel-kicker">Artifact Panel</p>
          <h2>产物预览与版本对比</h2>
        </div>
      </div>
      <div className="artifact-filters">
        <label className="inline-field">
          Track
          <select value={trackFilter} onChange={(event) => setTrackFilter(event.target.value)}>
            <option value="all">all</option>
            {tracks.map((track) => (
              <option key={track.id} value={track.id}>
                {track.name}
              </option>
            ))}
          </select>
        </label>
        <label className="inline-field">
          Artifact Type
          <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
            <option value="all">all</option>
            {artifactTypes.map((artifactType) => (
              <option key={artifactType} value={artifactType}>
                {artifactType}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="artifact-layout">
        <div className="artifact-sidebar">
          {filteredArtifacts.length === 0 ? (
            <div className="empty-state compact">
              <p>当前过滤条件下没有产物。</p>
            </div>
          ) : (
            <div className="artifact-selector-list">
              {filteredArtifacts.map((artifact) => (
                <button
                  key={artifact.id}
                  type="button"
                  className={`artifact-selector ${artifact.id === selectedArtifactId ? "active" : ""}`}
                  onClick={() => onSelectArtifact(artifact.id)}
                >
                  <strong>{artifact.artifact_type}</strong>
                  <span>v{artifact.version}</span>
                  <small>{artifact.path.split("/").pop()}</small>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="artifact-preview">
          {!selectedArtifact ? (
            <div className="empty-state compact">
              <p>选择一个 artifact 查看内容。</p>
            </div>
          ) : (
            <>
              <div className="section-toolbar">
                <h3>
                  {selectedArtifact.artifact_type} · v{selectedArtifact.version}
                </h3>
                <div className="card-actions">
                  <button
                    className="ghost-button compact-button"
                    type="button"
                    onClick={() => void onExportArtifact("docx")}
                  >
                    导出 DOCX
                  </button>
                  <button
                    className="ghost-button compact-button"
                    type="button"
                    onClick={() => void onExportArtifact("pdf")}
                  >
                    导出 PDF
                  </button>
                </div>
              </div>

              {exportNotice ? <div className="subtle-banner">{exportNotice}</div> : null}

              <div className="artifact-detail-card">
                {loadingDetail ? (
                  <p className="subtle-text">正在加载内容...</p>
                ) : (
                  <pre className="artifact-content">{detail?.content || "当前 artifact 没有可读内容。"}</pre>
                )}
              </div>

              <div className="section-toolbar">
                <h3>版本 Diff</h3>
                <div className="card-actions">
                  <label className="inline-field">
                    对比基线
                    <select value={baseArtifactId} onChange={(event) => setBaseArtifactId(event.target.value)}>
                      <option value="">选择版本</option>
                      {compareCandidates.map((artifact) => (
                        <option key={artifact.id} value={artifact.id}>
                          v{artifact.version} · {artifact.path.split("/").pop()}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    className="primary-button compact-button"
                    type="button"
                    disabled={!baseArtifactId}
                    onClick={() => void onCompareArtifacts(baseArtifactId)}
                  >
                    {loadingDiff ? "对比中..." : "查看 Diff"}
                  </button>
                </div>
              </div>

              {diff ? (
                <div className="artifact-diff-card">
                  <div className="tag-row">
                    <span className="tag">+{diff.stats.additions}</span>
                    <span className="tag">-{diff.stats.deletions}</span>
                  </div>
                  <pre className="artifact-content diff-content">{diff.diff || "没有内容差异。"}</pre>
                </div>
              ) : (
                <div className="empty-state compact">
                  <p>选择一个同类型旧版本后，可查看 diff。</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
