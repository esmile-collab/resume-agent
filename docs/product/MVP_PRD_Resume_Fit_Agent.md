<!--
Input: 当前产品范围、交互约束与实现边界。
Output: 输出产品文档《MVP PRD - Resume Agent》的说明内容。
Pos: 产品设计文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# MVP PRD - Resume Agent

版本：v1.0  
状态：现行  
目标：收敛到一个真实可用、可部署、可演示的简历工作台 demo。

## 1. 产品定义

Resume Agent 不是“万能求职助手”，而是一个围绕单次投递周期工作的简历工作台。它帮助用户把基础简历、求职方向、JD 和产物版本组织在同一个会话系统里，让“补充背景 -> 入库 JD -> 评分 -> 生成 -> 润色 -> 导出”成为可追踪、可复用的闭环。

## 2. 目标用户

1. 有一份基础简历，但需要针对多个方向做投递定制的学生/求职者。
2. 需要在一次会话里持续沉淀画像、经历和 JD，而不是每次重新开聊的用户。
3. 希望拿到可执行评分结果和可导出简历版本，而不是只看一段建议文本的用户。

## 3. MVP 目标

1. 支持创建 session，并把会话绑定到一个 project。
2. 支持把背景信息沉淀为 `profile / experiences / tracks`。
3. 支持 JD 入库并绑定到 track。
4. 支持对某个 track 做评分、生成、润色、导出。
5. 支持查看会话快照、run trace、artifact 列表与 diff。
6. 支持本地一键启动，支持 Render + Vercel 部署。

## 4. 非目标

1. 不做自动搜岗或自动抓取 JD。
2. 不做多 Agent 协作或复杂工作流编排。
3. 不做账号体系、多人协作、云端同步。
4. 不做“整份简历无限重写”，当前只支持规则化生成与 patch 润色。

## 5. 核心对象模型

### 5.1 Project

一次投递周期的容器，持有：

1. 基础简历文本。
2. 多个求职方向 `track`。
3. 项目级 JD 资产池。
4. artifact 文件目录与对话摘要。

### 5.2 Session

一次具体的对话运行实例，负责：

1. 记录用户与 assistant 消息。
2. 把每轮规划、工具调用和观察结果写入 trace。
3. 返回前端可直接消费的 snapshot。

### 5.3 Track

一个长期维护的求职方向，如“策略产品”“商业分析”。每个 track 维护：

1. 方向名称、定位、关键词。
2. 关联 JD 集合和主 JD。
3. 面向该方向的简历策略。
4. 与该方向绑定的产物版本。

### 5.4 Artifact

由工具链产出的版本化文件，当前包括：

1. `score_report`
2. `generated_resume`
3. `polished_resume`
4. `edited_resume`

## 6. 用户主流程

1. 用户启动会话，可直接粘贴基础简历或上传简历文件。
2. 用户补充背景、方向偏好、经验信息，系统写入结构化 memory。
3. 用户上传 JD 或粘贴岗位描述，系统识别目标 track 并完成入库。
4. 用户请求“评分”，系统基于主 JD + 当前简历生成 score report。
5. 用户请求“生成简历”，系统先评分再生成定制稿。
6. 用户请求“继续润色”，系统在生成稿或基础简历上做 block 级 patch。
7. 用户查看 artifact、diff、export，并持续补充信息再迭代。

## 7. 功能需求

### 7.1 输入

1. 文本消息。
2. JD 附件。
3. 简历附件。
4. 手动维护的 track / JD / profile / experience 数据。

### 7.2 系统能力

1. `add_info`：把背景信息写入结构化 memory。
2. `ingest_jd`：把 JD 入库并挂到 track。
3. `resume_score`：输出匹配度、差距、建议和 score artifact。
4. `resume_generate`：输出 track 定制简历草稿。
5. `resume_polish`：输出 patch 驱动的润色版本。
6. `artifact export`：导出 `docx / pdf`。

### 7.3 前端工作台能力

1. 启动/恢复 session。
2. 发送消息并展示 assistant 回复。
3. 展示 `tracks / jds / experiences / artifacts / traces`。
4. 编辑可编辑 artifact 并保存 revision。
5. 查看 artifact diff、导出结果和历史会话。

## 8. 产品约束

1. 当前意图识别以确定性规则为主，不引入复杂模型路由。
2. 当前生成与润色必须避免编造事实。
3. 当前一个 session 只服务一个 project，但一个 project 可有多个 track。
4. 当前 demo 的持久化基于本地 SQLite 与 `.data/artifacts/` 文件系统。

## 9. MVP 验收标准

1. 本地能通过 `./start.sh` 启动前后端。
2. 用户能在前端完成“补充背景 -> 上传 JD -> 评分 -> 生成 -> 润色 -> 导出”。
3. `tests/acceptance/` 全部通过。
4. 生成的 artifact 能在文件系统落盘并可回查。
5. Render + Vercel 的部署配置与文档能对齐当前代码入口。

## 10. 后续优先级

1. P1：补齐更稳定的部署与环境变量策略。
2. P1：补齐前端错误态、空态和上传态细节。
3. P1：继续压缩非主线评测脚本和历史材料对工程面的影响。
4. P2：在主链稳定后，再讨论更复杂的意图识别和工具替换计划。
