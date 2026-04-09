// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 Start 面板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
type StartPanelProps = {
  projectName: string;
  cycle: string;
  baseResumeText: string;
  loading: boolean;
  onProjectNameChange: (value: string) => void;
  onCycleChange: (value: string) => void;
  onBaseResumeChange: (value: string) => void;
  onSubmit: () => void;
};

export function StartPanel(props: StartPanelProps) {
  const {
    projectName,
    cycle,
    baseResumeText,
    loading,
    onProjectNameChange,
    onCycleChange,
    onBaseResumeChange,
    onSubmit,
  } = props;

  return (
    <section className="start-shell">
      <div className="start-copy">
        <div className="start-nav">
          <div className="start-brand">
            <span className="brand-mark">R</span>
            <div>
              <strong>Resume Agent</strong>
              <span className="start-brand-badge">Pro</span>
            </div>
          </div>
          <div className="start-nav-links">
            <span>对话工作台</span>
            <span>JD Matches</span>
            <span>版本导出</span>
          </div>
        </div>

        <div className="start-hero">
          <span className="eyebrow">Career Workflow</span>
          <h1>Resume Agent</h1>
          <p>
            以对话为主入口，把上传 JD、匹配评分、生成简历、继续润色和版本导出收敛到一个工作台里。
          </p>
          <div className="start-hero-actions">
            <button className="primary-button" type="button" onClick={onSubmit} disabled={loading}>
              {loading ? "启动中..." : "Start Workspace"}
            </button>
            <span className="subtle-text">支持 JD / PDF / DOCX，启动后可继续上传。</span>
          </div>
        </div>

        <div className="start-feature-grid">
          <article>
            <strong>对话优先</strong>
            <p>左侧自然语言推进主流程，系统会持续给出下一步建议。</p>
          </article>
          <article>
            <strong>实时匹配</strong>
            <p>每个方向单独管理主 JD、匹配分和产出版本，不再来回切页。</p>
          </article>
          <article>
            <strong>版本沉淀</strong>
            <p>生成、润色、手改和导出都保留轨迹，便于比较和回滚。</p>
          </article>
        </div>
      </div>

      <div className="start-card">
        <div className="start-card-head">
          <div>
            <p className="panel-kicker">Launch Workspace</p>
            <h2>新建求职项目</h2>
          </div>
          <span className="status-pill">Ready</span>
        </div>

        <label>
          项目名称
          <input value={projectName} onChange={(event) => onProjectNameChange(event.target.value)} />
        </label>
        <label>
          招聘周期
          <input value={cycle} onChange={(event) => onCycleChange(event.target.value)} />
        </label>
        <label>
          基础简历
          <textarea
            rows={10}
            value={baseResumeText}
            onChange={(event) => onBaseResumeChange(event.target.value)}
            placeholder="可选。这里贴入基础简历内容，后续也可以继续上传和补充。"
          />
        </label>

        <div className="start-card-preview">
          <div className="preview-row">
            <span>步骤 1</span>
            <strong>上传简历 / JD</strong>
          </div>
          <div className="preview-row">
            <span>步骤 2</span>
            <strong>锁定方向并评分</strong>
          </div>
          <div className="preview-row">
            <span>步骤 3</span>
            <strong>生成可投递版本</strong>
          </div>
        </div>

        <button className="primary-button" onClick={onSubmit} disabled={loading}>
          {loading ? "启动中..." : "启动新会话"}
        </button>
      </div>
    </section>
  );
}
