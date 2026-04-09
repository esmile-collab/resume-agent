<!--
Input: tests/acceptance 目录结构、子目录边界和文件职责清单。
Output: 输出当前目录的极简架构说明与成员地图。
Pos: tests/acceptance 的目录说明文件。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# tests/acceptance

- 定位：现行验收测试目录。
- 边界：覆盖 runtime、HTTP API 和稳定回归场景，是 demo 可信度基线。
- 维护：行为变化后必须先补这里，再谈文档更新完成。

## 文件清单

| 文件 | 地位 | 功能 |
| --- | --- | --- |
| `README.md` | 目录地图 | 解释当前目录下有哪些成员以及它们各自做什么。 |
| `test_agent_api.py` | 验收测试 | 覆盖会话、上传、管理端点和产物链路。 |
| `test_agent_runtime.py` | 验收测试 | 确保 ingest/score/generate/polish 主流程可用。 |
| `test_regression_suite.py` | 回归测试 | 把容易回退的关键行为钉在当前架构上。 |

## 子目录

| 子目录 | 地位 | 功能 |
| --- | --- | --- |
| `（空）` | 叶子目录 | 当前目录没有下一级目录。 |
