// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 Score 面板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import type { ArtifactDetail } from "../types";

function scoreBucketClass(score: number) {
  if (score >= 80) {
    return "score-good";
  }
  if (score >= 60) {
    return "score-mid";
  }
  return "score-low";
}

export function ScorePanel({ detail }: { detail: ArtifactDetail | null }) {
  const payload = detail?.parsed_payload;
  const hardMetrics = (payload?.hard_metrics as Record<string, unknown> | undefined) ?? {};
  const softMetrics = (payload?.soft_metrics as Record<string, unknown> | undefined) ?? {};
  const softDimensions = (softMetrics.dimensions as Array<Record<string, unknown>> | undefined) ?? [];
  const quickImprovements = (payload?.quick_improvements as string[] | undefined) ?? [];
  const longTermImprovements = (payload?.long_term_improvements as string[] | undefined) ?? [];
  const finalScore = Number(payload?.final_score ?? 0);

  return (
    <section className="panel score-panel">
      <div className="panel-head">
        <div>
          <p className="panel-kicker">Score Panel</p>
          <h2>评分结果解释</h2>
        </div>
      </div>
      {!payload ? (
        <div className="empty-state compact">
          <p>还没有评分报告。</p>
          <p>先让 Agent 执行一次 `resume_score`，这里会展示硬性指标、skills 维度和改进建议。</p>
        </div>
      ) : (
        <div className="score-layout">
          <div className={`score-hero ${scoreBucketClass(finalScore)}`}>
            <strong>{finalScore.toFixed(1)}</strong>
            <span>{String(payload.match_level ?? "unknown")}</span>
            <p>{String(payload.suggestion ?? "")}</p>
          </div>

          {payload.risk_warning ? <div className="global-error">{String(payload.risk_warning)}</div> : null}

          <div className="memory-section">
            <h3>硬性指标</h3>
            <div className="score-grid">
              {Object.entries(hardMetrics)
                .filter(([key]) => key !== "total")
                .map(([key, value]) => {
                  const item = value as { score?: number; evidence?: string };
                  return (
                    <article key={key} className="score-card">
                      <strong>{key}</strong>
                      <span>{Number(item.score ?? 0).toFixed(0)}</span>
                      <p>{item.evidence ?? ""}</p>
                    </article>
                  );
                })}
            </div>
          </div>

          <div className="memory-section">
            <h3>Skills / 软性维度</h3>
            <div className="score-grid">
              {softDimensions.map((dimension) => (
                <article key={String(dimension.dimension)} className="score-card">
                  <strong>{String(dimension.dimension)}</strong>
                  <span>{Number(dimension.score ?? 0).toFixed(0)}</span>
                  <p>{String(dimension.reasoning ?? "")}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="memory-section">
            <h3>快速改进</h3>
            {quickImprovements.length === 0 ? (
              <p className="subtle-text">当前没有额外的快速改进建议。</p>
            ) : (
              <div className="memory-stack">
                {quickImprovements.map((item) => (
                  <article key={item} className="memory-card">
                    <p>{item}</p>
                  </article>
                ))}
              </div>
            )}
          </div>

          <div className="memory-section">
            <h3>长期改进</h3>
            {longTermImprovements.length === 0 ? (
              <p className="subtle-text">当前没有额外的长期改进建议。</p>
            ) : (
              <div className="memory-stack">
                {longTermImprovements.map((item) => (
                  <article key={item} className="memory-card">
                    <p>{item}</p>
                  </article>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
