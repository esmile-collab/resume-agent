<!--
Input: 当前产品范围、交互约束与实现边界。
Output: 输出产品文档《UI交互设计》的说明内容。
Pos: 产品设计文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# UI交互设计

版本：v1.0  
状态：现行  
对应实现：`frontend/src/App.tsx`
视觉基准：Figma Prototype `Resume Agent Frontend Prototype`

## 1. 设计目标

1. 把复杂能力收敛成一个单工作台，而不是多页面跳转。
2. 让会话成为主操作入口，其他面板承担“查看、切换、编辑、复核”。
3. 让用户始终看得见当前方向、当前产物和当前运行轨迹。
4. 把可编辑产物和评分结果放进同一个上下文，避免来回切换。

## 2. 工作台结构

当前前端由一个总控组件加多个业务面板组成。真实挂载到 `App.tsx` 的主视图如下：

1. `StartPanel`：创建或恢复会话。
2. `ChatPanel`：主对话流和附件发送。
3. `ResumeEditorPanel`：展示右侧简历画布、版本切换、编辑和导出。
4. `MatchesBoard`：展示 JD Matches 仪表盘、方向卡片、主 JD 管理和创建弹窗。
5. `SessionHistoryPanel`：历史 session 恢复。

当前保留但未挂载为独立主面板的组件：

1. `TrackPanel`
2. `MemoryPanel`
3. `ScorePanel`
4. `ArtifactPanel`
5. `RunTracePanel`

## 3. 交互原则

1. 主操作走对话：补充背景、上传 JD、发起评分、生成、润色。
2. 管理操作走次视图：在 `JD Matches` 中切换方向、维护主 JD、创建新 match。
3. 复核操作走右侧工作区：看评分摘要、编辑产物、导出结果。
4. 恢复操作走历史：用户进入页面时优先恢复上次 session 和 active track。

## 4. 核心交互流程

### 4.1 启动会话

1. 用户输入 project 名称、招聘周期和基础简历。
2. 前端调用 `POST /agent/sessions`。
3. 返回 `session_id / project_id / snapshot / tool_catalog`。

### 4.2 补充背景

1. 用户在 `ChatPanel` 输入背景信息。
2. assistant 回复后，前端刷新 `messages + snapshot + traces`。
3. `MemoryPanel` 同步显示 profile 与 experiences 的新增结果。

### 4.3 入库 JD

1. 用户直接上传 JD，或在侧栏手动新增 JD。
2. 系统把 JD 绑定到某个 track，并在 `TrackPanel` 展示 JD 列表。
3. 若当前只有一个 track，前端默认激活该 track。

### 4.4 评分 / 生成 / 润色

1. 用户在聊天区发起“评分”“生成简历”“继续润色”。
2. 前端将 active track 一并发给后端。
3. 返回后刷新 `artifacts`、`latestScoreDetail`、`selectedArtifactDetail`。
4. 若生成了可编辑 artifact，右侧画布自动切换到该版本。
5. 若当前只有评分报告而没有可编辑简历版本，右侧继续保持简历空态画布，不把评分报告当作简历正文渲染。

### 4.5 编辑与导出

1. 用户在 `ResumeEditorPanel` 修改 artifact 内容并保存 revision。
2. 用户可基于另一个 artifact 生成 diff。
3. 用户可从 `ArtifactPanel` 发起 `docx / pdf` 导出。

## 5. 页面状态要求

1. 启动中：明确展示 session 恢复状态。
2. 发送中：聊天区要能区分“用户已发出”和“后端处理中”。
3. 上传中：附件上传有单独 loading，不阻塞整个页面。
4. 评分空态：没有 score artifact 时明确提示下一步。
5. 编辑空态：没有可编辑 artifact 时保留简历纸张空态和生成引导，而不是展示错误内容。

## 6. 当前设计边界

1. 不做多 tab 项目切换；当前以单 session 恢复为主。
2. 不做复杂按钮工作流；主链仍靠自然语言触发。
3. 当前高保真视觉对齐以 Figma prototype 为主，保留当前系统需要的会话历史、刷新和导出能力。
4. 不做“自动最佳 track 选择”，当前由 active track 或单 track 自动推断。

## 7. 验收标准

1. 页面刷新后能恢复最近一次 session。
2. 用户能在同一工作台里看到 tracks、memory、score、artifact、trace。
3. 生成或润色后，可编辑 artifact 会自动成为默认焦点。
4. 所有面板消费同一份后端 snapshot，不允许各自维护割裂状态。
