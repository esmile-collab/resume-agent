<!--
Input: 当前技术架构、模块边界与工程约束。
Output: 输出技术文档《真实工具替换清单》的说明内容。
Pos: 技术设计文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 真实工具替换清单

这份清单只覆盖当前 session/message 架构下仍然偏轻实现的工具链，目标是逐步把 Demo 级实现替换成可长期维护的真实能力。

## 当前状态总览

| 能力 | 当前实现 | 问题 | 替换方向 | 优先级 |
|------|----------|------|----------|--------|
| 搜索 / Research | 尚未注册为正式 tool | 无法自动拉取外部 JD、公司信息、岗位背景 | 接入官方搜索工具或独立 research provider，统一 schema | P0 |
| JD 解析 | `MemoryManager.extract_keywords` + 轻量归档 | 只做关键词抽取，不区分职责/要求/加分项 | 做结构化 JD parser，输出 requirements / keywords / priorities | P0 |
| 简历导出 | `services/exporter.py` 只输出 markdown 风格文本 | 结构简单，投递格式不稳定 | 引入模板化 DOCX / PDF exporter，保留 markdown 中间层 | P0 |
| 简历润色 | `PolishPatcher` 基于 block 和 gaps 做轻量 patch | Patch 粒度粗，语言风格控制弱 | 接入约束化 rewrite engine，按 section / bullet / metric 重写 | P1 |
| 简历解析 | `ResumeParser` 按标题和行拆 block | 对复杂简历格式适应差 | 支持 markdown / docx / pdf 的统一 resume AST | P1 |
| 评分器 | `CampusScorerV21` 已接入真实实现 | 依赖 LLM 环境，缺少 provider 抽象和降级策略 | 增加 provider config、缓存、离线 fallback | P1 |
| 产物写入 | tool 内直接写文件 | 逻辑分散，难扩展到云存储/模板引擎 | 收敛到 artifact writer service | P1 |
| PDF 上传解析 | 文本 PDF 可用，扫描件不支持 | 图片型简历/JD 无法提取 | 增加 OCR 流程 | P2 |

## 推荐替换顺序

1. 搜索 / Research tool
2. 结构化 JD parser
3. 模板化 DOCX / PDF exporter
4. 统一 artifact writer service
5. 约束化润色引擎
6. Resume AST parser
7. 评分 provider 抽象和 fallback
8. OCR

## 每项替换的验收标准

### 1. 搜索 / Research tool

- Agent tool registry 中出现正式的 `search_research` tool。
- 输入 schema 至少支持 `query / domains / recency / intent`。
- 输出 schema 至少包含 `summary / sources / snippets / extracted_jd_text`。
- 对 React 工作台暴露可追踪的 `tool_call / observation`。

### 2. 结构化 JD parser

- 从 JD 原文中稳定拆出：
  - `responsibilities`
  - `requirements`
  - `preferred_qualifications`
  - `keywords`
  - `seniority`
- 支持对一个 track 下多个 JD 做共性聚合。

### 3. 模板化 DOCX / PDF exporter

- 生成简历后可直接导出投递版 DOCX。
- PDF 导出不依赖简单逐行写字，应支持分页和中文。
- 导出的文件能在 artifact 面板中回溯。

### 4. Artifact writer service

- `resume_score / resume_generate / resume_polish / export` 都通过统一 service 落盘。
- 文件命名、版本号、summary、metadata 规则一致。
- 后续接对象存储时不用改各个 tool。

### 5. 润色引擎

- 支持 section 级与 bullet 级 rewrite。
- 能控制“保守润色 / 强化结果 / 强化关键词对齐”模式。
- 生成 diff 时能保持可读。

### 6. Resume AST parser

- 对 markdown / docx / pdf 输入输出统一 block/section 结构。
- 能识别 summary / experience / education / skills / projects。
- 与 exporter 双向兼容。

### 7. 评分 provider 抽象

- 至少支持 OpenAI / Anthropic 两种 provider 配置。
- 无 key 时有明确 fallback，不让 runtime 直接失败。
- 对同一输入支持缓存，降低重复评分成本。

### 8. OCR

- 扫描版 PDF/JPG/PNG JD 可以提取文本。
- 失败时返回明确错误类型，不默默写入乱码。

## 当前建议负责人视角

- P0 适合先做成“可投递闭环”：搜索、JD 结构化、导出。
- P1 适合做“质量提升闭环”：润色、解析、评分稳定性。
- P2 是“输入覆盖补全”：OCR。
