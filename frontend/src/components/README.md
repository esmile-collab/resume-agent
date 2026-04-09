<!--
Input: frontend/src/components 目录结构、子目录边界和文件职责清单。
Output: 输出当前目录的极简架构说明与成员地图。
Pos: frontend/src/components 的目录说明文件。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# frontend/src/components

- 定位：前端业务面板目录。
- 边界：每个组件承担一个工作台子视图，围绕同一份会话状态工作。
- 维护：组件职责变化后，更新本页，避免 UI 与系统地图脱节。

## 文件清单

| 文件 | 地位 | 功能 |
| --- | --- | --- |
| `README.md` | 目录地图 | 解释当前目录下有哪些成员以及它们各自做什么。 |
| `ArtifactPanel.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |
| `ChatPanel.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |
| `MatchesBoard.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |
| `MemoryPanel.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |
| `ResumeEditorPanel.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |
| `RunTracePanel.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |
| `ScorePanel.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |
| `SessionHistoryPanel.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |
| `StartPanel.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |
| `TrackPanel.tsx` | 业务组件 | 承担工作台中的一个具体面板或看板。 |

## 子目录

| 子目录 | 地位 | 功能 |
| --- | --- | --- |
| `（空）` | 叶子目录 | 当前目录没有下一级目录。 |
