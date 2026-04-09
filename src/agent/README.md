<!--
Input: src/agent 目录结构、子目录边界和文件职责清单。
Output: 输出当前目录的极简架构说明与成员地图。
Pos: src/agent 的目录说明文件。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# src/agent

- 定位：会话式 Agent 核心编排层。
- 边界：负责 plan、tool、memory、runtime 四块主链，驱动 think-call-observe。
- 维护：这是系统主心骨，接口或链路调整必须先在此目录落字。

## 文件清单

| 文件 | 地位 | 功能 |
| --- | --- | --- |
| `README.md` | 目录地图 | 解释当前目录下有哪些成员以及它们各自做什么。 |
| `__init__.py` | 包导出 | 把核心运行时暴露给 API 和 CLI。 |
| `memory.py` | 记忆中枢 | 维护 profile、experiences、tracks、JD 和 artifacts。 |
| `models.py` | 类型中心 | 统一 runtime、planner 和 tools 之间的数据协议。 |
| `planner.py` | 规划器 | 决定本轮是补信息、入库、评分、生成还是润色。 |
| `runtime.py` | 运行时核心 | 驱动消息主链并把结果回给前端或 CLI。 |
| `tools.py` | 工具注册表 | 把领域能力封装成 runtime 可调用的稳定工具。 |

## 子目录

| 子目录 | 地位 | 功能 |
| --- | --- | --- |
| `（空）` | 叶子目录 | 当前目录没有下一级目录。 |
