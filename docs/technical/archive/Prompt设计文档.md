<!--
Input: 当前技术架构、模块边界与工程约束。
Output: 输出技术文档《Prompt 设计文档》的说明内容。
Pos: 技术设计文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# Prompt 设计文档

版本：v1.1
日期：2026-02-27
维护状态：与用户共建中

---

## 文档说明

本文档收集简历优化Agent项目中所有需要LLM调用的Prompt，每个Prompt包含：
- **用途**：解决什么问题
- **输入参数**：需要传入哪些变量
- **槽位抽取**：需要从输出中提取哪些结构化信息
- **Prompt模板**：实际的Prompt内容
- **输出格式**：期望的输出格式
- **示例**：输入输出示例

**共建方式**：
- 用户可以修改任何Prompt
- 可以添加新的Prompt
- 标注每个Prompt的优化版本

---

## Prompt 索引

| ID | Prompt名称 | 模块 | 优先级 | 状态 | 优化版本 |
|---|---|---|---|---|---|
| P001 | JD解析 | JD解析 | 高 | v1.0 | - |
| P002 | 简历解析 | 简历解析 | 高 | v1.1 | ✨ 优化点2：完整证据链 |
| P003 | 方向聚类 | 方向聚类 | 中 | v1.0 | - |
| P004 | 七维评分 | 评分系统 | 高 | v1.1 | ✨ 优化点3/5/6：潜力+增量+补偿路径 |
| P005 | 映射匹配 | 简历生成 | 高 | v1.1 | ✨ 优化点4：可迁移能力 |
| P006 | 简历改写 | 简历生成 | 高 | v1.1 | ✨ 优化点2：完整证据链 |
| P007 | 复核评分 | 复核评分 | 中 | v1.0 | - |
| P008 | 面试题库生成 | 面试准备 | 中 | v1.1 | ✨ 优化点7：反问能力 |
| P009 | 个人陈述生成 | 认知补偿 | 中 | v1.0 | - |
| P010 | 求职信生成 | 认知补偿 | 中 | v1.0 | - |
| P011 | 提升建议生成 | 提升建议 | 中 | v1.1 | ✨ 优化点6：差距→补偿路径 |
| P012 | 意图分类 | 多轮对话 | 低 | v1.0 | - |
| P013 | JD分配决策 | 路由编排 | 高 | v1.0 | ✨ Project级分配器 |

---

## P001: JD解析

### 用途
从JD文本中提取结构化信息，包括岗位名称、关键词、能力要求等

### 输入参数
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `jd_text` | string | JD原始文本 | "岗位职责：负责产品策略..." |
| `jd_id` | string | JD标识ID | "jd_001" |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `job_title` | string | 岗位名称 |
| `company_level` | string | 公司级别（大厂/独角兽/中型/小厂） |
| `business_complexity` | string | 业务复杂度（多业务线/单业务线） |
| `industry` | string | 行业标签 |
| `keywords` | array<string> | 关键词列表 |
| `hard_skills` | array<string> | 硬技能列表 |
| `soft_skills` | array<string> | 软技能列表 |
| `experience_years` | object | 经验要求（数字+是否必须） |
| `education` | object | 学历要求 |

### Prompt模板

```markdown
你是一个专业的JD解析专家。请从以下岗位描述中提取结构化信息。

JD文本：
{jd_text}

请按以下JSON格式输出：

{{
    "job_title": "岗位名称",
    "company_inference": {{
        "level": "大厂/独角兽/中型/小厂/未知",
        "business_complexity": "多业务线/单业务线/未知",
        "reasoning": "判断理由"
    }},
    "industry": "行业标签（电商/内容/金融/SaaS/...）",
    "keywords": ["关键词1", "关键词2", ...],
    "hard_skills": ["硬技能1", "硬技能2", ...],
    "soft_skills": ["软技能1", "软技能2", ...],
    "requirements": {{
        "experience_years": {{"value": 数字, "must_have": true/false, "text": "原始描述"}},
        "education": {{"level": "本科/硕士/博士/不限", "must_have": true/false, "text": "原始描述"}},
        "must_have_skills": ["必须技能1", ...]
    }},
    "responsibilities": ["职责1", "职责2", ...]
}}

提取规则：
1. keywords：从岗位职责和要求中提取核心关键词，包括业务方向、产品类型、核心能力等
2. hard_skills：具体的工具、语言、框架等技能
3. soft_skills：沟通、协作、分析等通用能力
4. must_have_skills：JD中明确标注"必须"、"要求"、"具备"的技能
5. company_inference：根据JD中的公司信息推断，如果没公司信息则填"未知"
```

### 输出格式
```json
{
    "job_title": "AI产品经理",
    "company_inference": {
        "level": "大厂",
        "business_complexity": "多业务线",
        "reasoning": "JD提到多个业务线协作"
    },
    "industry": "AI",
    "keywords": ["AI产品", "大模型", "策略产品", "评测体系", "数据驱动"],
    "hard_skills": ["Python", "SQL", "A/B测试", "数据分析"],
    "soft_skills": ["沟通协作", "逻辑思维", "用户视角"],
    "requirements": {
        "experience_years": {"value": 3, "must_have": true, "text": "3年以上经验"},
        "education": {"level": "本科", "must_have": false, "text": "本科及以上"},
        "must_have_skills": ["Python", "数据分析"]
    },
    "responsibilities": ["负责AI产品策略设计", "建立评测体系", "推动算法落地"]
}
```

### 示例

**输入**：
```
岗位职责：
1. 负责AI产品策略设计，推动产品落地
2. 建立评测体系，持续优化产品体验
3. 与算法、工程团队协作，推动算法落地

任职要求：
1. 3年以上AI产品经验
2. 具备Python和SQL能力
3. 有大模型相关经验者优先
```

**输出**：
```json
{
    "job_title": "AI产品经理",
    "company_inference": {
        "level": "未知",
        "business_complexity": "多业务线",
        "reasoning": "需要与算法、工程多个团队协作"
    },
    "industry": "AI",
    "keywords": ["AI产品", "策略设计", "评测体系", "算法落地", "大模型"],
    "hard_skills": ["Python", "SQL", "大模型"],
    "soft_skills": ["协作", "策略思维"],
    "requirements": {
        "experience_years": {"value": 3, "must_have": true, "text": "3年以上经验"},
        "education": {"level": "不限", "must_have": false, "text": "未提及"},
        "must_have_skills": ["Python"]
    },
    "responsibilities": ["负责AI产品策略设计", "建立评测体系", "推动算法落地"]
}
```

---

## P002: 简历解析 (v1.1 - 优化版)

### 用途
从简历文本中提取结构化信息，包括工作经历、项目经验、技能、证据链等

### 输入参数
| 参数名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `resume_text` | string | 简历原始文本 | "教育经历：... 工作经历：..." |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `basic_info` | object | 基本信息（姓名、联系方式等） |
| `education` | array<object> | 教育经历 |
| `work_experience` | array<object> | 工作经历（含证据链） |
| `projects` | array<object> | 项目经验（含证据链） |
| `skills` | object | 技能（硬技能/软技能） |
| `self_introduction` | string | 自我介绍 |
| `evidence_chains` | array<object> | 证据链列表（新增） |

### Prompt模板

```markdown
你是一个专业的简历解析专家。请从以下简历中提取结构化信息，重点关注"完整证据链"。

简历文本：
{resume_text}

请按以下JSON格式输出：

{{
    "basic_info": {{
        "name": "姓名",
        "phone": "电话",
        "email": "邮箱"
    }},
    "education": [
        {{
            "school": "学校名称",
            "major": "专业",
            "degree": "学历",
            "start_date": "开始时间",
            "end_date": "结束时间",
            "gpa": "GPA（如有）"
        }}
    ],
    "work_experience": [
        {{
            "company": "公司名称",
            "position": "职位",
            "start_date": "开始时间",
            "end_date": "结束时间",
            "industry": "行业",
            "description": "工作描述",
            "achievements": ["成果1", "成果2"],
            "keywords": ["关键词1", "关键词2"],
            "evidence_chain": {{
                "motivation": "为什么做这件事（动机）",
                "method": "用什么方法做的（方法）",
                "result": "结果如何（数据）",
                "questionable": "能否被追问深挖",
                "risk_areas": ["可能被深问的风险点1", "风险点2"]
            }}
        }}
    ],
    "projects": [
        {{
            "name": "项目名称",
            "role": "角色",
            "start_date": "开始时间",
            "end_date": "结束时间",
            "description": "项目描述",
            "achievements": ["成果1", "成果2"],
            "technologies": ["技术1", "技术2"],
            "evidence_chain": {{
                "motivation": "为什么做这个项目",
                "method": "用什么方法/技术",
                "result": "结果如何（数据）",
                "questionable": "能否被追问深挖",
                "risk_areas": ["可能被深问的风险点"]
            }}
        }}
    ],
    "skills": {{
        "hard_skills": ["技能1", "技能2"],
        "soft_skills": ["能力1", "能力2"]
    }},
    "self_introduction": "自我介绍内容（如有）"
}}

提取规则：
1. 时间格式统一为 YYYY-MM
2. achievements 尽量量化（带数字）
3. keywords 从描述中提取核心业务关键词
4. 如果某部分缺失，返回空数组或空字符串

【新增】证据链提取规则（重要）：
1. motivation：从经历中推断"为什么做"——是主动承担还是被动分配
2. method：提取"用什么方法"——工具、框架、流程、协作方式
3. result：提取"结果如何"——必须有数据支撑，如"提升了X%"、"节省了Y小时"
4. questionable：评估"能否被追问"——如果描述模糊或数据可疑，标注为高风险
5. risk_areas：预测"面试官可能深问的问题"——比如"具体怎么做到的"、"数据来源是什么"

示例证据链：
- 好："主动发起用户调研项目，用问卷+访谈收集500+用户反馈，分析发现3个关键痛点，推动产品改版后转化率提升20%"
  - motivation: 主动发起，体现主动性
  - method: 问卷+访谈，具体可验证
  - result: 3个痛点+20%提升，有数据
  - questionable: 高风险？低，有具体数据支撑
  - risk_areas: ["具体怎么分析的","转化率提升是否与其他因素相关"]

- 差："负责产品优化工作"
  - motivation: 不明确，被动分配？
  - method: 不明确，怎么优化的？
  - result: 无数据，无法验证
  - questionable: 高风险，缺乏细节
  - risk_areas: ["具体优化了什么","用了什么方法","效果如何"]
```

### 输出格式
```json
{
    "basic_info": {
        "name": "张三",
        "phone": "138xxxx",
        "email": "xxx@xxx.com"
    },
    "work_experience": [
        {
            "company": "某公司",
            "position": "产品经理",
            "evidence_chain": {
                "motivation": "主动承担用户增长项目",
                "method": "用数据分析+用户访谈+AB测试",
                "result": "3个月内DAU提升30%",
                "questionable": "中风险",
                "risk_areas": ["具体AB测试设计了哪些变量", "如何与其他部门协作"]
            }
        }
    ]
}
```

---

## 优化日志

### P002: 简历解析

| 版本 | 日期 | 修改内容 | 修改人 |
|---|---|---|---|
| v1.0 | 2026-02-25 | 初始版本 | Claude |
| v1.1 | 2026-02-25 | ✨ 增加证据链提取（动机-方法-结果-可追问） | Claude |
| | | | |

---

## P003: 方向聚类 (v1.1 - 基于"叙事成本"聚类)

### 用途
将多个JD按照"简历准备成本"进行聚类，确定需要生成几份不同版本的简历

### 核心设计理念
**聚类目标 = 需要准备几份不同简历，而不是有几个相似JD**

关键洞察：
- 两个JD可能关键词重合度很高，但需要完全不同的简历叙事
- 两个JD可能关键词重合度较低，但可以用同一份简历投递
- 聚类应该基于"叙事框架差异度"，而非"关键词重合度"

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|---|
| `jd_list` | array<object> | JD解析结果列表（来自P001） |
| `direction_hint` | string | 方向提示（可选，仅用于提示准备成本，不做硬约束） |
| `existing_task_cards` | array<object> | 已有任务卡信息（方向名、direction_id） |
| `source_scope` | string | JD输入来源（project/task_card） |
| `source_task_card_id` | string | 当来源为task_card时，记录当前卡片ID |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `direction_count` | int | 方向数量 |
| `directions` | array<object> | 各方向详情 |
| `jd_count` | int | JD总数 |
| `preparation_cost_summary` | string | 准备成本摘要 |

### Prompt模板

```markdown
你是一个专业的职业方向分析专家。请将以下JD列表按照"简历准备成本"进行聚类。

**核心原则**：聚类目标是"需要准备几份不同版本的简历"，而不是"有几个相似的JD"。

JD列表：
{jd_list_json}

方向提示（可选，仅用于提示准备成本，不做硬约束）：
{direction_hint}

请按以下JSON格式输出：

{{
    "jd_count": 总JD数量,
    "direction_count": 方向数量,
    "need_preview_confirm": true/false,
    "preparation_cost_summary": "预计准备成本（如：需要准备3份不同侧重点的简历）",
    "directions": [
        {{
            "direction_name": "方向名称（如：策略产品、功能产品）",
            "jd_ids": ["该方向包含的JD ID列表"],
            "jd_count": 该方向包含的JD数量,
            "narrative_framework": "该方向的叙事框架（需要讲什么核心故事）",
            "key_experience_focus": "需要强调哪类经历（如：策略制定/产品设计/增长实验）",
            "key_skills_highlight": ["需要突出的关键技能"],
            "clustering_reason": "为什么这些JD归为同一方向（核心理由）",
            "preparation_cost": "该方向的准备成本（如：中等 - 需要1份强调策略和数据能力的简历）"
        }}
    ],
    "direction_hint_note": "方向数量提示说明（如：当前识别3个方向，建议优先处理策略与功能方向）",
    "proposed_card_actions": [
        {{
            "project_jd_id": "JD编号",
            "action": "assign_current_card/assign_existing_card/create_new_card",
            "target_task_card_id": "目标卡片ID（可空）",
            "target_direction_name": "目标方向名称",
            "reason": "分配理由"
        }}
    ]
}}

---

## 分析框架

### 第一步：叙事框架识别

对每个JD，分析其需要的"简历叙事"：

1. **核心能力叙事**：需要突出什么核心能力？
   - 策略思维 / 产品设计 / 数据分析 / 用户洞察 / 增长实验 / 内容策划

2. **经历侧重点**：需要强调哪类经历？
   - B端经验 vs C端经验
   - 从0到1 vs 优化迭代
   - 策略制定 vs 执行落地
   - 数据分析 vs 用户研究

3. **技能侧重点**：需要突出哪些技能？
   - SQL/Python / 原型设计 / A/B测试 / 内容创作 / 用户运营

4. **叙事框架**：简历整体讲故事的方式
   - "数据驱动决策" vs "用户体验优化" vs "增长实验驱动"

### 第二步：叙事成本聚类

**判断规则**：

1. 如果 **核心能力叙事相同** 且 **经历侧重点相同** → 很可能同一方向

2. 如果 **叙事框架相同**，只有 **业务场景不同**（如电商vs内容）→ 同一方向
   - 理由：可以用同一份简历投递，只需微调业务关键词

3. 如果 **经历侧重点不同**（如B端vs C端，从0到1 vs 优化迭代）→ 不同方向
   - 理由：需要完全不同的叙事方式

4. 如果 **技能侧重点不同**（如数据分析 vs 原型设计）→ 可能不同方向
   - 需要看核心能力叙事是否相同

### 第三步：方向数量提示（不做硬约束）

**提示规则**：

1. 不做自动合并或自动拆分，保持聚类结果原样输出。
2. 当方向数量较多时，只给用户提示准备成本，不强制压缩方向数。
3. 用户可手动选择是否合并方向。

### 第四步：分类理由生成

为每个方向生成清晰的"为什么归为一类"的解释：

- 说明这些JD的共同叙事框架
- 说明为什么可以用同一份简历投递
- 如果业务场景不同，说明为什么这不影响简历叙事

---

## 示例

### 示例1：策略产品 vs 功能产品

**输入JD**：
- JD1: 策略产品经理（电商方向）- 强调策略思维、数据分析
- JD2: 策略产品经理（内容方向）- 强调策略思维、数据驱动
- JD3: 功能产品经理 - 强调产品设计、用户体验

**聚类结果**：
```json
{{
    "jd_count": 3,
    "direction_count": 2,
    "directions": [
        {{
            "direction_name": "策略产品",
            "jd_ids": ["jd_1", "jd_2"],
            "jd_count": 2,
            "narrative_framework": "强调策略思维、数据驱动决策、复杂问题分析",
            "key_experience_focus": "需要突出策略制定、数据分析、跨部门协作经历",
            "key_skills_highlight": ["SQL", "数据分析", "A/B测试", "策略思维"],
            "clustering_reason": "虽然业务场景不同（电商vs内容），但都需要策略思维和数据分析能力，可以用同一份简历投递",
            "preparation_cost": "中等 - 需要准备1份强调策略和数据能力的简历"
        }},
        {{
            "direction_name": "功能产品",
            "jd_ids": ["jd_3"],
            "jd_count": 1,
            "narrative_framework": "强调产品设计、用户体验、需求分析",
            "key_experience_focus": "需要突出产品设计、用户研究、需求迭代经历",
            "key_skills_highlight": ["原型设计", "用户研究", "PRD", "项目管理"],
            "clustering_reason": "需要产品设计和用户体验能力，与策略产品的叙事框架完全不同",
            "preparation_cost": "中等 - 需要准备1份强调产品设计和用户体验的简历"
        }}
    ]
}}
```

### 示例2：不同业务场景但叙事相同

**输入JD**：
- JD1: 内容运营（电商方向）
- JD2: 内容运营（教育方向）
- JD3: 内容运营（金融方向）

**聚类结果**：
```json
{{
    "jd_count": 3,
    "direction_count": 1,
    "directions": [
        {{
            "direction_name": "内容运营",
            "jd_ids": ["jd_1", "jd_2", "jd_3"],
            "jd_count": 3,
            "narrative_framework": "强调内容策划、用户洞察、数据分析",
            "key_experience_focus": "需要突出内容创作、用户分析、效果优化经历",
            "key_skills_highlight": ["内容策划", "数据分析", "用户洞察", "A/B测试"],
            "clustering_reason": "虽然行业不同（电商/教育/金融），但核心都是内容策划和用户分析，叙事框架完全一致，可以用同一份简历投递",
            "preparation_cost": "低 - 只需准备1份强调内容策划能力的简历"
        }}
    ]
}}
```

### 示例3：看似相似但叙事不同

**输入JD**：
- JD1: 产品经理（功能设计）- 强调PRD、原型设计、用户体验
- JD2: 产品经理（用户增长）- 强调A/B测试、数据分析、增长策略

**聚类结果**：
```json
{{
    "jd_count": 2,
    "direction_count": 2,
    "directions": [
        {{
            "direction_name": "功能产品",
            "jd_ids": ["jd_1"],
            "jd_count": 1,
            "narrative_framework": "强调产品设计、用户体验、需求分析",
            "key_experience_focus": "需要突出产品设计、用户研究、需求迭代经历",
            "key_skills_highlight": ["原型设计", "用户研究", "PRD", "项目管理"],
            "clustering_reason": "需要产品设计和用户体验能力，叙事重点是'如何做好产品设计'",
            "preparation_cost": "中等 - 需要准备1份强调产品设计的简历"
        }},
        {{
            "direction_name": "用户增长",
            "jd_ids": ["jd_2"],
            "jd_count": 1,
            "narrative_framework": "强调数据驱动、增长实验、效果优化",
            "key_experience_focus": "需要突出增长项目、A/B测试、数据优化经历",
            "key_skills_highlight": ["A/B测试", "增长策略", "数据分析", "用户运营"],
            "clustering_reason": "需要增长思维和实验驱动能力，叙事重点是'如何通过数据驱动增长'，与功能产品的叙事框架完全不同",
            "preparation_cost": "中等 - 需要准备1份强调增长和实验能力的简历"
        }}
    ]
}}
```

---

## 常见错误

### 错误1：只看关键词重合度
❌ 错误做法：关键词重合>60%就归为同一方向
✅ 正确做法：分析叙事框架是否相同

示例：
- "策略产品（电商）"和"功能产品"的关键词重合可能达到70%
- 但叙事框架完全不同，应该分为不同方向

### 错误2：过度细分业务场景
❌ 错误做法：电商产品、内容产品、金融产品分为不同方向
✅ 正确做法：如果叙事框架相同，归为同一方向

示例：
- 三个都是"功能产品经理"，只是行业不同
- 应该归为同一个"功能产品"方向

### 错误3：用系统硬规则强行压缩方向
❌ 错误做法：系统自动把方向压到固定数量
✅ 正确做法：输出真实聚类结果，并提示准备成本，由用户决定是否合并

---

## 输出格式

```json
{{
    "jd_count": 15,
    "direction_count": 3,
    "need_preview_confirm": true,
    "preparation_cost_summary": "需要准备3份不同侧重点的简历：策略版、功能版、增长版",
    "directions": [
        {{
            "direction_name": "策略产品",
            "jd_ids": ["jd_01", "jd_02", "jd_03", "jd_04", "jd_05", "jd_06", "jd_07"],
            "jd_count": 7,
            "narrative_framework": "强调策略思维、数据驱动决策、复杂问题分析能力",
            "key_experience_focus": "需要突出策略制定、数据分析、跨部门协作、复杂问题解决经历",
            "key_skills_highlight": ["策略思维", "SQL", "数据分析", "A/B测试", "跨部门协作"],
            "clustering_reason": "虽然业务场景不同（电商/内容/金融），但都需要策略思维和数据分析能力，叙事框架一致，可以用同一份简历投递",
            "preparation_cost": "中等 - 需要准备1份强调策略思维和数据能力的简历"
        }}
    ],
    "direction_hint_note": "自动聚类结果为3个方向。系统不做硬约束，可按需要手动合并方向。",
    "proposed_card_actions": [
        {{
            "project_jd_id": "jd_01",
            "action": "assign_existing_card",
            "target_task_card_id": "card_strategy",
            "target_direction_name": "策略产品",
            "reason": "叙事框架与现有策略卡一致"
        }}
    ]
}}
```

### 输出格式
```json
{
    "jd_count": 15,
    "direction_count": 3,
    "need_preview_confirm": true,
    "preparation_cost_summary": "需要准备3份不同侧重点的简历：策略版、功能版、增长版",
    "directions": [
        {
            "direction_name": "策略产品",
            "jd_ids": ["jd_01", "jd_02", "...", "jd_07"],
            "jd_count": 7,
            "narrative_framework": "强调策略思维、数据驱动决策、复杂问题分析",
            "key_experience_focus": "需要突出策略制定、数据分析、跨部门协作经历",
            "key_skills_highlight": ["SQL", "数据分析", "A/B测试", "策略思维"],
            "clustering_reason": "虽然业务场景不同（电商/内容/金融），但都需要策略思维和数据分析能力，可以用同一份简历投递",
            "preparation_cost": "中等 - 需要准备1份强调策略和数据能力的简历"
        },
        {
            "direction_name": "功能产品",
            "jd_ids": ["jd_08", "...", "jd_12"],
            "jd_count": 5,
            "narrative_framework": "强调产品设计、用户体验、需求分析",
            "key_experience_focus": "需要突出产品设计、用户研究、需求迭代经历",
            "key_skills_highlight": ["原型设计", "用户研究", "PRD", "项目管理"],
            "clustering_reason": "都需要产品设计和用户体验能力，叙事框架一致",
            "preparation_cost": "中等 - 需要准备1份强调产品设计和用户体验的简历"
        },
        {
            "direction_name": "用户增长",
            "jd_ids": ["jd_13", "jd_14", "jd_15"],
            "jd_count": 3,
            "narrative_framework": "强调数据驱动、增长实验、效果优化",
            "key_experience_focus": "需要突出增长项目、A/B测试、数据优化经历",
            "key_skills_highlight": ["A/B测试", "增长策略", "数据分析", "用户运营"],
            "clustering_reason": "都需要增长思维和实验驱动能力，与其他方向叙事框架不同",
            "preparation_cost": "中等 - 需要准备1份强调增长和实验能力的简历"
        }
    ],
    "direction_hint_note": "自动聚类结果为3个方向。系统不做硬约束，可按需要手动合并方向。",
    "proposed_card_actions": [
        {
            "project_jd_id": "jd_01",
            "action": "assign_existing_card",
            "target_task_card_id": "card_strategy",
            "target_direction_name": "策略产品",
            "reason": "叙事框架与现有策略卡一致"
        }
    ]
}
```

---

## 优化日志

### P003: 方向聚类

| 版本 | 日期 | 修改内容 | 修改人 |
|---|---|---|---|
| v1.0 | 2026-02-25 | 初始版本，基于关键词重合度聚类 | Claude |
| v1.1 | 2026-02-27 | ✨ 从"关键词重合度"改为"叙事框架差异度"聚类 | Claude |
| | | ✨ 增加"简历准备成本"评估和说明 | |
| | | ✨ 改为方向数量提示逻辑（不做硬约束） | |
| | | ✨ 增加分类理由生成，让用户理解为什么这样分 | |
| | | ✨ 新增 Project 级卡片分配预览字段（需用户确认） | |

---

## P004: 七维评分 (v1.1 - 优化版)

### 用途
对简历与JD的匹配度进行评分，包括能力匹配、潜力匹配、增量价值分析

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `jd_info` | object | JD解析结果（来自P001） |
| `resume_info` | object | 简历解析结果（来自P002） |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `total_score` | int | 总分（0-100） |
| `match_level` | string | 匹配级别（high/medium/low） |
| `dimensions` | array<object> | 各维度评分详情 |
| `potential_match` | object | 潜力匹配分析（新增） |
| `incremental_value` | object | 增量价值分析（新增） |
| `compensation_strategy` | object | 补偿策略（新增） |
| `suggestion` | string | 投递建议 |

### Prompt模板

```markdown
你是一个专业的简历评估专家（HR视角+匹配思维）。请对以下简历与JD进行匹配度评分。

JD信息：
{jd_info_json}

简历信息：
{resume_info_json}

请按以下JSON格式输出：

{{
    "total_score": 总分（0-100）,
    "match_level": "high/medium/low",
    "dimensions": [
        {{
            "name": "公司级别匹配度",
            "score": 得分（0-10）,
            "max_score": 10,
            "reasoning": "评分理由",
            "gap_analysis": "差距分析（如有）"
        }},
        {{
            "name": "业务级别匹配度",
            "score": 得分（0-15）,
            "max_score": 15,
            "reasoning": "评分理由",
            "gap_analysis": "差距分析"
        }},
        {{
            "name": "行业匹配度",
            "score": 得分（0-10）,
            "max_score": 10,
            "reasoning": "评分理由",
            "gap_analysis": "差距分析"
        }},
        {{
            "name": "岗位经验匹配度",
            "score": 得分（0-20）,
            "max_score": 20,
            "reasoning": "评分理由",
            "gap_analysis": "差距分析"
        }},
        {{
            "name": "能力匹配度",
            "score": 得分（0-20）,
            "max_score": 20,
            "reasoning": "评分理由",
            "gap_analysis": "差距分析"
        }},
        {{
            "name": "真实性可信度",
            "score": 得分（0-15）,
            "max_score": 15,
            "reasoning": "评分理由",
            "gap_analysis": "差距分析"
        }},
        {{
            "name": "可复述性",
            "score": 得分（0-10）,
            "max_score": 10,
            "reasoning": "评分理由",
            "gap_analysis": "差距分析"
        }}
    ],
    "potential_match": {{
        "score": 得分（0-10）,
        "max_score": 10,
        "reasoning": "潜力匹配理由",
        "learning_ability": "学习能力证据（课程、自学、快速上手案例）",
        "growth_trajectory": "成长轨迹（职级提升、责任增加）",
        "industry_insight": "行业理解深度"
    }},
    "incremental_value": {{
        "score": 得分（0-10）,
        "max_score": 10,
        "reasoning": "增量价值理由",
        "what_i_bring": "我能在原有基础上增加什么",
        "unique_contribution": "我的独特贡献",
        "cross_domain_insight": "跨领域视角"
    }},
    "compensation_strategy": {{
        "current_gap": "当前差距",
        "available_resources": "可用资源（现有经历中可用的部分）",
        "quick_wins": ["快速可做的改进（1周内）"],
        "medium_term_actions": ["中期行动（1个月）"],
        "long_term_plan": ["长期计划（3个月）"]
    }},
    "suggestion": "投递建议"
}}

---

## 评分标准

### 基础七维度

1. **公司级别匹配度**（10分）：
   - 大厂 ↔ 大厂：10分
   - 大厂 ↔ 独角兽：7分
   - 大厂 ↔ 中型：5分
   - 大厂 ↔ 小厂：3分
   - 业务复杂度也纳入考量

2. **业务级别匹配度**（15分）：
   - 关键词重合率 × 10 + 场景相似度 × 5
   - 重合率 = (JD关键词 ∩ 简历关键词) / JD关键词数

3. **行业匹配度**（10分）：
   - 完全相同行业：10分
   - 相邻行业：5分
   - 跨行业：0分

4. **岗位经验匹配度**（20分）：
   - 职责重合度 × 15 + 产出物相似度 × 5
   - 重合度基于工作描述的语义相似度

5. **能力匹配度**（20分）：
   - 硬技能覆盖率 × 15 + AI产品相关经验 × 5

6. **真实性可信度**（15分）：
   - 经历有具体数据支撑：高评分
   - 经历描述模糊：低评分

7. **可复述性**（10分）：
   - STAR完整度 × 7 + 语言清晰度 × 3
   - 有具体成果可追溯：高评分

---

## 【新增】潜力匹配维度（10分）

评估"未来能干"而非仅仅"现在能干"：

1. **学习能力**（4分）：
   - 有主动学习行为：+2分（课程、证书、自学）
   - 有快速上手案例：+2分（短时间掌握新技能）

2. **成长轨迹**（3分）：
   - 职级明显提升：+1分
   - 责任范围扩大：+1分
   - 有跨领域发展：+1分

3. **行业理解**（3分）：
   - 对行业有深入洞察：+2分
   - 关注行业动态：+1分

评分标准：
- 8-10分：高潜力，即使经历不完全匹配也值得考虑
- 5-7分：中等潜力，需要一定培养时间
- 0-4分：低潜力，更看重现成能力

---

## 【新增】增量价值维度（10分）

评估"我能给团队带来什么增量价值"：

1. **独特贡献**（4分）：
   - 有独特的跨领域视角：+2分
   - 能补充团队现有短板：+2分

2. **创新能力**（3分）：
   - 有创新的思考方式：+2分
   - 能带来新的方法论：+1分

3. **协同效应**（3分）：
   - 能提升团队整体能力：+2分
   - 有跨团队协作经验：+1分

评分标准：
- 8-10分：高增量价值，能带来显著提升
- 5-7分：中等增量价值，有一定补充作用
- 0-4分：低增量价值，主要是执行角色

---

## 【增强】差距分析→补偿策略

gap_analysis 从"有什么差距"升级为"如何弥补差距"：

{{
    "current_gap": "当前差距（如：业务匹配度低，电商选品 vs 内容运营）",
    "available_resources": "可用资源（如：选品经验中的用户分析能力）",
    "compensation_strategy": "补偿策略（如：用认知弥补，强调用户理解可迁移）",
    "quick_wins": [
        "1周内可做：补充内容运营相关的数据观察（如：'通过数据分析发现用户偏好XXX内容'）"
    ],
    "medium_term_actions": [
        "1个月内可做：完成XX平台《内容运营基础》课程（约10小时）"
    ],
    "long_term_plan": [
        "3-6个月：运营自己的内容账号，积累实战经验；加入内容运营交流群学习"
    ]
}}

评级标准：
- total_score >= 75：high
- 50 <= total_score < 75：medium
- total_score < 50：low
```

### 输出格式
```json
{
    "total_score": 67,
    "match_level": "medium",
    "dimensions": [...],
    "potential_match": {
        "score": 7,
        "max_score": 10,
        "reasoning": "有快速学习能力（3周掌握SQL），但行业理解深度中等",
        "learning_ability": "有快速学习案例：3周掌握SQL并独立完成数据分析",
        "growth_trajectory": "职级从专员→专员，职责范围扩大",
        "industry_insight": "关注行业动态，但缺乏深度洞察"
    },
    "incremental_value": {
        "score": 6,
        "max_score": 10,
        "reasoning": "能带来数据分析视角的补充，但创新性一般",
        "what_i_bring": "我能在原有数据分析能力基础上，为内容策略提供数据支撑",
        "unique_contribution": "跨领域的数据分析视角，可以量化内容效果",
        "cross_domain_insight": "电商的数据驱动思维可以迁移到内容运营"
    },
    "compensation_strategy": {
        "current_gap": "业务匹配度低（22%）：电商选品 vs 内容运营",
        "available_resources": "用户分析能力、数据驱动思维、快速学习能力",
        "quick_wins": [
            "1周内：补充内容运营相关的数据观察（如：'通过选品工作发现用户偏好XXX内容'）",
            "1周内：分析10个竞品账号的内容策略，输出观察报告"
        ],
        "medium_term_actions": [
            "1个月内：完成XX平台《内容运营基础》课程（约10小时）",
            "1个月内：用ChatGPT协助完成1周内容AB测试，记录数据"
        ],
        "long_term_plan": [
            "3-6个月：运营自己的内容账号（公众号/小红书）",
            "3-6个月：加入内容运营交流群，学习经验"
        ]
    },
    "suggestion": "建议补充业务相关经历后投递。同时可突出快速学习能力和数据驱动思维的迁移价值。"
}
```

---

## 优化日志

### P004: 七维评分

| 版本 | 日期 | 修改内容 | 修改人 |
|---|---|---|---|
| v1.0 | 2026-02-25 | 初始版本，七维度评分 | Claude |
| v1.1 | 2026-02-25 | ✨ 增加潜力匹配维度（优化点3） | Claude |
| | | ✨ 增加增量价值分析（优化点5） | |
| | | ✨ 增强差距分析→补偿策略（优化点6） | |

---

## P005: 映射匹配 (v1.1 - 优化版)

### 用途
识别简历中可以改写的经历模块，找到与JD要求匹配的潜质，显性识别可迁移能力

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `jd_info` | object | JD解析结果 |
| `resume_info` | object | 简历解析结果 |
| `score_card` | object | 评分卡（来自P004） |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `mappable_modules` | array<object> | 可映射的经历模块 |
| `transferable_skills` | array<object> | 可迁移能力列表（新增） |
| `supplement_opportunities` | array<object> | 补充机会 |

### Prompt模板

```markdown
你是一个专业的简历优化专家。请分析以下简历，找出可以与JD要求匹配的经历模块，特别关注"可迁移能力"。

JD信息：
{jd_info_json}

简历信息：
{resume_info_json}

评分信息：
{score_card_json}

请按以下JSON格式输出：

{{
    "mappable_modules": [
        {{
            "module_type": "工作经历/项目经历",
            "module_id": "对应ID",
            "original_content": "原始内容",
            "jd_requirements": ["匹配的JD要求1", "要求2"],
            "match_potential": "高/中/低",
            "suggested_rewrites": [
                {{
                    "original": "原始描述",
                    "suggested": "建议改写为",
                    "evidence_in_resume": "可用的证据",
                    "reasoning": "改写理由"
                }}
            ]
        }}
    ],
    "transferable_skills": [
        {{
            "source_experience": "A领域经验（来自简历）",
            "transferred_to": "B领域要求（来自JD）",
            "bridge_reasoning": "迁移理由（底层能力是什么）",
            "bridge_type": "底层能力类型（数据分析/用户理解/逻辑思维/项目管理/沟通协调）",
            "confidence": "高/中/低",
            "suggested_expression": "建议如何表述这种迁移",
            "evidence_available": "是否有可用证据",
            "examples": [
                {{
                    "original": "简历中的原始描述",
                    "transfer_to": "可以如何迁移到JD要求",
                    "verifiable": "是否可被追问验证"
                }}
            ]
        }}
    ],
    "supplement_opportunities": [
        {{
            "dimension": "可补充的维度",
            "current_gap": "当前差距",
            "suggested_addition": "建议补充内容",
            "evidence_available": "是否有可用证据"
        }}
    ]
}}

---

## 分析规则

### 基础规则
1. 优先选择与JD要求直接相关的经历
2. 识别可以"包装"的经历：本质相同但表述不同
3. 标注每条改写的证据来源
4. 不虚构经历，只优化表述
5. 标注需要补充的内容类型

---

## 【新增】可迁移能力识别规则

### 识别逻辑

**第一步：识别底层能力**
- 从简历经历中提取"底层能力"：数据分析、用户理解、逻辑思维、项目管理、沟通协调等
- 从JD要求中提取"底层能力"：这些岗位本质需要什么能力

**第二步：寻找迁移路径**
- A领域的经验中，哪些能力可以应用到B领域？
- 比如：电商选品中的"用户分析" → 内容运营中的"用户洞察"

**第三步：评估迁移可信度**
- 高置信度：底层能力完全相同，只是应用场景不同
- 中置信度：底层能力相似，需要一定适配
- 低置信度：底层能力不同，迁移理由薄弱

### 可迁移能力的类型

| 迁移类型 | 说明 | 示例 |
|---|---|---|
| **方法迁移** | A领域的方法论应用到B领域 | 数据分析方法迁移 |
| **视角迁移** | A领域的视角应用到B领域 | 电商用户视角迁移到内容运营 |
| **工具迁移** | A领域的工具应用到B领域 | SQL/Python工具迁移 |
| **思维迁移** | A领域的思维模式应用到B领域 | 数据驱动思维迁移 |

### 表述策略

**高置信度迁移**：
```
"虽然直接内容运营经验较少，但在选品工作中积累了用户偏好理解，
这同样适用于内容策略优化。我具备快速学习能力，期待深入发展。"
```

**中置信度迁移**：
```
"虽然未直接负责过内容策略，但在选品工作中经常需要分析用户行为，
对用户需求有深入理解。我可以将数据分析能力迁移到内容运营中。"
```

**低置信度迁移**（谨慎使用）：
```
"我对内容运营很感兴趣，正在积极学习相关知识。虽然直接经验有限，
但我相信在选职工作中培养的数据敏感度可以为内容策略提供支持。"
```
```

### 输出示例

{{
    "mappable_modules": [...],
    "transferable_skills": [
        {{
            "source_experience": "电商选品中的用户分析",
            "transferred_to": "内容运营中的用户洞察",
            "bridge_reasoning": "底层能力都是数据分析+用户理解",
            "bridge_type": "数据分析+用户理解",
            "confidence": "高",
            "suggested_expression": "虽然直接内容运营经验较少，但在选品工作中通过数据分析积累了用户偏好理解，这同样适用于内容策略优化",
            "evidence_available": true,
            "examples": [
                {{
                    "original": "负责选品，通过数据分析发现用户偏好XX品类，推动选品策略调整",
                    "transfer_to": "在内容运营中，可以用同样的数据分析方法发现用户偏好的内容类型",
                    "verifiable": true
                }}
            ]
        }},
        {{
            "source_experience": "选品工作中的A/B测试经验",
            "transferred_to": "内容运营中的内容效果测试",
            "bridge_reasoning": "底层能力都是实验设计和数据分析",
            "bridge_type": "实验思维+数据分析",
            "confidence": "高",
            "suggested_expression": "在选品工作中积累了A/B测试经验，可以迁移到内容运营中进行效果测试和优化",
            "evidence_available": true,
            "examples": [
                {{
                    "original": "设计了XX次A/B测试，通过数据分析优化选品策略，提升了转化率",
                    "transfer_to": "可以用同样的实验设计和分析方法优化内容效果",
                    "verifiable": true
                }}
            ]
        }}
    ]
}}
```

---

## 优化日志

### P005: 映射匹配

| 版本 | 日期 | 修改内容 | 修改人 |
|---|---|---|---|
| v1.0 | 2026-02-25 | 初始版本 | Claude |
| v1.1 | 2026-02-25 | ✨ 增加可迁移能力显性识别（优化点4） | Claude |
| | | | |

---

## P006: 简历改写 (v1.1 - 优化版)

### 用途
根据映射匹配结果，生成改写后的简历，强调"完整证据链"

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `jd_info` | object | JD解析结果 |
| `resume_info` | object | 简历解析结果 |
| `mappings` | object | 映射匹配结果（来自P005） |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `revised_resume` | object | 改写后的简历 |
| `change_summary` | array<object> | 改动摘要 |
| `evidence_chains` | array<object> | 完整证据链（新增） |
| `questionable_areas` | array<object> | 需要准备的风险点（新增） |

### Prompt模板

```markdown
你是一个专业的简历改写专家。请根据JD要求，对简历进行针对性改写，特别注意"完整证据链"的构建。

JD要求：
{jd_info_json}

原始简历：
{resume_info_json}

映射建议：
{mappings_json}

请按以下JSON格式输出：

{{
    "revised_resume": {{
        "basic_info": {{...}},
        "work_experience": [
            {{
                "id": "经历ID",
                "original": "原始内容",
                "revised": "改写后内容",
                "changes": [
                    {{
                        "type": "修改类型（新增/调整/重排/强化）",
                        "original": "原始片段",
                        "revised": "改写片段",
                        "reason": "改写原因",
                        "evidence_source": "证据来源（来自简历哪部分）",
                        "jd_requirement": "对应的JD要求",
                        "evidence_chain": {{
                            "motivation": "为什么做这件事（在改写中体现）",
                            "method": "用什么方法做的（在改写中体现）",
                            "result": "结果如何（在改写中体现数据）",
                            "questionable": "能否被追问深挖（高/中/低）",
                            "risk_areas": ["可能被深问的问题1", "问题2"]
                        }}
                    }}
                ],
                "highlight_changes": ["需要高亮或加粗的改动点"]
            }}
        ],
        "projects": [...],
        "skills": {...}
    }},
    "change_summary": [
        {{
            "module": "改动模块",
            "change_count": 改动数量,
            "key_improvements": ["关键改进点1", "改进点2"]
        }}
    ],
    "evidence_chains": [
        {{
            "experience_id": "经历ID",
            "before": "改写前：只描述了做了什么",
            "after": "改写后：体现了为什么+怎么做+结果如何",
            "strengthened": "强化的证据链部分"
        }}
    ],
    "questionable_areas": [
        {{
            "area": "风险领域描述",
            "question": "可能被问到的问题",
            "suggested_preparation": "如何准备这个问题的回答"
        }}
    ]
}}

---

## 改写原则

### 核心原则

1. **证据链完整**（优化点2 - 核心）
   - 每条改动必须构建完整证据链：动机-方法-结果
   - "为什么做"：体现主动性和思考
   - "怎么做"：体现方法和工具
   - "结果如何"：必须有数据支撑

2. **不虚构，只优化**
   - 不虚构经历，只优化表述
   - 不添加未掌握的技能
   - 不夸大成果

3. **JD关键词匹配**
   - 使用JD中的关键词
   - 提高匹配度

4. **可被追问**
   - 每条改动都要能被面试追问
   - 标注高风险领域

---

## 完整证据链示例

### 改写前
```
负责产品优化工作
```

### 改写后
```
主动发起用户体验优化项目，通过数据分析+用户访谈收集500+用户反馈，
分析发现3个关键痛点（页面加载慢、导航不清晰、转化路径复杂），
推动产品改版后转化率从5%提升到8%（提升60%）
```

### 证据链拆解
- **动机**："主动发起" → 体现主动性
- **方法**："数据分析+用户访谈" → 具体方法可验证
- **结果**："3个痛点+转化率60%提升" → 有数据支撑
- **可追问**：中风险 → 可以解释"怎么分析的3个痛点"、"如何推动改版"

---

## 改写策略

### 策略1：强化动机
**改写前**："参与产品优化项目"
**改写后**："主动承担用户增长项目，目标是通过数据驱动提升产品体验"

### 策略2：具体化方法
**改写前**："使用数据分析"
**改写后**："通过SQL分析用户行为数据，用Python可视化发现用户流失节点"

### 策略3：量化结果
**改写前**："优化了用户体验"
**改写后**："通过AB测试优化了用户注册流程，注册转化率从15%提升到23%"

### 策略4：标注风险
对于无法提供详细证据的改动，标注为"中风险"或"高风险"

---

## 禁止事项

1. 不虚构项目经历
2. 不夸大成果（无证据支撑）
3. 不添加未掌握的技能
4. 不编造数据

---

## 优化日志

### P006: 简历改写

| 版本 | 日期 | 修改内容 | 修改人 |
|---|---|---|---|
| v1.0 | 2026-02-25 | 初始版本 | Claude |
| v1.1 | 2026-02-25 | ✨ 强调完整证据链（优化点2） | Claude |
| | | ✨ 增加风险点标注 | |

---

## P007: 复核评分

### 用途
对改写后的简历进行复核评分，确保质量和真实性

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `jd_info` | object | JD解析结果 |
| `original_resume` | object | 原始简历 |
| `revised_resume` | object | 改写后简历 |
| `original_score` | int | 改前评分 |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `new_score` | int | 改后评分 |
| `score_delta` | int | 评分变化 |
| `quality_check` | object | 质量检查结果 |

### Prompt模板

```markdown
你是一个简历质量审核专家。请对改写后的简历进行复核。

JD要求：
{jd_info_json}

原始简历：
{original_resume_json}

改写后简历：
{revised_resume_json}

改前评分：{original_score}

请按以下JSON格式输出：

{{
    "new_score": 改后评分（0-100）,
    "score_delta": 评分变化,
    "quality_check": {{
        "evidence_binding_rate": 证据绑定率（0-1）,
        "fabrication_risk": "虚构风险等级（高/中/低）",
        "issues_found": [
            {{
                "issue_type": "问题类型",
                "severity": "严重程度（高/中/低）",
                "location": "问题位置",
                "description": "问题描述",
                "suggestion": "改进建议"
            }}
        ],
        "verifiable_statements": 可验证陈述数量,
        "total_statements": 总陈述数量
    }},
    "improvements": ["改进点1", "改进点2"]
}}

审核标准：
1. 证据绑定：每条改动是否都有原始证据
2. 虚构风险：是否存在无证据支撑的夸大
3. 逻辑一致性：时间线、因果关系是否合理
4. 可复述性：用户能否口头解释改写内容

严重问题定义：
- 高严重：虚构经历、无证据的夸大
- 中严重：过度包装、证据薄弱
- 低严重：表述不够清晰、可优化
```

---

## P008: 面试题库生成 (v1.1 - 优化版)

### 用途
基于简历改动点，生成面试问题、参考答案，以及"反问问题"

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `changes` | array<object> | 简历改动列表（来自P006） |
| `jd_info` | object | JD解析结果 |
| `score_card` | object | 评分卡（来自P004，可选） |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `interview_questions` | array<object> | 面试问题列表 |
| `questions_to_ask` | array<object> | 应该问面试官的问题（新增） |

### Prompt模板

```markdown
你是一个面试准备专家。请根据简历改动点，生成面试问题和参考答案，同时准备"反问问题"。

简历改动：
{changes_json}

JD要求：
{jd_info_json}

请按以下JSON格式输出：

{{
    "interview_questions": [
        {{
            "question": "面试问题",
            "category": "问题类别（经历类/技能类/行为类/场景类）",
            "related_change": "关联的改动点",
            "difficulty": "难度（易/中/难）",
            "suggested_answer": "参考答案",
            "key_points": ["要点1", "要点2"],
            "evidence_needed": ["需要的证据1", "证据2"],
            "follow_up_questions": ["可能的追问1", "追问2"]
        }}
    ],
    "questions_to_ask": [
        {{
            "question": "应该问面试官的问题",
            "purpose": "这个问题展示你的什么能力/理解",
            "timing": "什么时候问合适（开场/中段/结尾）",
            "alternative_versions": ["备用版本1", "备用版本2"],
            "preparation_needed": ["需要提前准备什么"]
        }}
    ]
}}

---

## 出题原则

### 被问到的问题

1. **优先针对改动点生成**
2. **难度递进**：先问基础，再深入
3. **每个问题都要有明确答案要点**
4. **标注需要准备的证据**
5. **预测面试官可能的追问**

---

## 【新增】应该问面试官的问题

### 问题的类型

1. **展示理解类**：展示你对岗位和公司的理解
2. **展示兴趣类**：展示你对岗位的热情
3. **展示思考类**：展示你的思维深度
4. **展示能力类**：展示你的专业能力

### 问题示例

#### 1. 展示理解类

**问题**："这个岗位未来3个月的核心目标是什么？"
- **目的**：展示你对目标的理解和结果导向
- **时机**：面试中后段
- **备用版本**："团队对这个岗位的期待是什么？"

#### 2. 展示兴趣类

**问题**："这个岗位最吸引你的地方是什么？"
- **目的**：展示你的动机和热情
- **时机**：面试开场或结尾
- **备用版本**："为什么选择这个方向？"

#### 3. 展示思考类

**问题**："团队目前在这个方向遇到的最大的挑战是什么？"
- **目的**：展示你的思考深度和问题解决能力
- **时机**：面试中段
- **备用版本**："这个岗位在公司战略中的定位是什么？"

#### 4. 展示能力类

**问题**："这个岗位需要和哪些团队协作？"
- **目的**：展示你的沟通协作意识
- **时机**：面试中段
- **备用版本**："这个岗位的工作流程是怎样的？"

#### 5. 展示学习类

**问题**："如果我在这个方向需要补充哪些知识，团队有推荐的学习路径吗？"
- **目的**：展示你的学习意愿和主动性
- **时机**：面试结尾
- **备用版本**："公司有内部培训或学习资源吗？"

### 问题选择原则

1. **不要问太多**：准备3-5个高质量问题即可
2. **不要问薪资**：除非HR主动提起，否则不要在技术面/业务面问
3. **不要问太基础**：不要问公司是做什么的（应该提前了解）
4. **不要问负面问题**：如"这个岗位离职率为什么高？"

### 输出示例

{{
    "interview_questions": [
        {{
            "question": "你在简历中提到负责用户增长，能具体说说是怎么做的吗？",
            "category": "经历类",
            "related_change": "工作经历1",
            "difficulty": "中",
            "suggested_answer": "我主要通过数据分析+用户访谈来做用户增长。比如...",
            "key_points": ["数据分析", "用户访谈", "结果导向"],
            "evidence_needed": ["具体的数据分析方法", "用户反馈收集了多少"],
            "follow_up_questions": ["具体用了什么工具分析？", "用户反馈率是多少？"]
        }}
    ],
    "questions_to_ask": [
        {{
            "question": "这个岗位未来3个月的核心目标是什么？",
            "purpose": "展示你对目标的理解和结果导向思维",
            "timing": "面试中后段",
            "alternative_versions": [
                "团队对这个岗位的期待是什么？",
                "这个岗位在公司战略中的定位是什么？"
            ],
            "preparation_needed": [
                "提前了解公司业务方向",
                "思考这个岗位在业务中的价值"
            ]
        }},
        {{
            "question": "团队目前在内容运营方向遇到的最大的挑战是什么？",
            "purpose": "展示你的问题意识和对岗位的理解",
            "timing": "面试中段",
            "alternative_versions": [
                "这个岗位需要和哪些团队协作？",
                "团队目前的资源配置如何？"
            ],
            "preparation_needed": [
                "了解公司业务现状",
                "思考你如何帮助解决这个问题"
            ]
        }}
    ]
}}
```

---

## 优化日志

### P008: 面试题库生成

| 版本 | 日期 | 修改内容 | 修改人 |
|---|---|---|---|
| v1.0 | 2026-02-25 | 初始版本 | Claude |
| v1.1 | 2026-02-25 | ✨ 增加反问问题（优化点7） | Claude |
| | | | |

---

## P009: 个人陈述生成

### 用途
为低匹配场景生成个人陈述，用认知弥补经历差距

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `jd_info` | object | JD解析结果 |
| `resume_info` | object | 简历解析结果 |
| `gap_analysis` | object | 差距分析（来自P004） |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `self_statement` | string | 个人陈述内容 |
| `highlight_points` | array<string> | 强调的要点 |

### Prompt模板

```markdown
你是一个求职辅导专家。请为以下情况生成个人陈述，用认知和能力弥补经历差距。

JD要求：
{jd_info_json}

用户简历：
{resume_info_json}

差距分析：
{gap_analysis_json}

请按以下JSON格式输出：

{{
    "self_statement": "个人陈述全文（200字以内）",
    "highlight_points": [
        {{
            "point": "强调点",
            "evidence": "可用证据",
            "transferable_skill": "可迁移能力"
        }}
    ],
    "tone": "语气风格（诚恳但不失自信）"
}}

个人陈述策略：
1. 诚实承认经历差距，但强调学习能力
2. 突出可迁移能力：A经验如何应用于B场景
3. 展示对目标岗位的理解和热情
4. 提及主动学习的内容（课程、项目等）
5. 表达快速上手和长期发展的信心

避免事项：
1. 不虚构经历
2. 不过度承诺
3. 不贬低自己原有经历
```

---

## P010: 求职信生成

### 用途
为低匹配场景生成求职信，表达热情和理解

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `jd_info` | object | JD解析结果 |
| `company_name` | string | 公司名称 |
| `self_statement` | string | 个人陈述（来自P009） |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `cover_letter` | string | 求职信内容 |

### Prompt模板

```markdown
你是一个求职辅导专家。请生成一封求职信，帮助候选人在经历不完全匹配的情况下争取机会。

JD要求：
{jd_info_json}

目标公司：{company_name}

个人陈述：
{self_statement}

请按以下JSON格式输出：

{{
    "cover_letter": "求职信全文",
    "structure": {{
        "opening": "开头（表达兴趣）",
        "understanding": "对岗位的理解",
        "transferable_value": "可迁移的价值",
        "learning_initiative": "主动学习的内容",
        "closing": "结尾（表达期待）"
    }}
}}

求职信要点：
1. 开头：明确表达对岗位的兴趣
2. 理解：展示对岗位和公司的了解
3. 价值：说明现有经验如何迁移
4. 学习：列举主动学习的内容
5. 真诚：不夸大，但展现潜力

格式：
- 正式商务格式
- 300字以内
- 语气诚恳专业
```

---

## P011: 提升建议生成 (v1.1 - 优化版)

### 用途
为低匹配场景生成具体的提升建议，强调"如何弥补差距"而非仅仅"有什么差距"

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `score_card` | object | 评分卡（来自P004） |
| `jd_info` | object | JD解析结果 |
| `resume_info` | object | 简历解析结果 |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `compensation_strategy` | object | 补偿策略（核心） |
| `improvement_plan` | object | 提升计划 |
| `recommended_resources` | array<object> | 推荐资源 |

### Prompt模板

```markdown
你是一个职业规划专家。请为以下低匹配情况生成具体的提升建议，重点在于"如何弥补差距"而非仅仅"有什么差距"。

评分信息：
{score_card_json}

JD要求：
{jd_info_json}

用户简历：
{resume_info_json}

请按以下JSON格式输出：

{{
    "compensation_strategy": {{
        "philosophy": "用认知弥补经历差距，不虚构经历",
        "available_resources": "可用资源（现有经历中可迁移的能力）",
        "quick_wins": [
            {{
                "action": "1周内可做的改进",
                "specific": "具体做什么",
                "evidence_available": "是否有可用证据",
                "impact": "对匹配度的预期提升"
            }}
        ],
        "medium_term_actions": [
            {{
                "action": "1个月内可做的改进",
                "specific": "具体做什么",
                "time_required": "所需时间",
                "difficulty": "难度（易/中/难）",
                "impact": "对匹配度的预期提升"
            }}
        ],
        "long_term_plan": [
            {{
                "phase": "阶段（1个月/3个月/6个月）",
                "actions": ["行动1", "行动2"],
                "expected_outcome": "预期成果"
            }}
        ]
    }},
    "improvement_plan": {{
        "gap_summary": "差距总结",
        "priority_gaps": [
            {{
                "dimension": "差距维度",
                "gap_description": "具体差距",
                "priority": "优先级（高/中/低）",
                "compensation_method": "补偿方法（认知补偿/技能补充/项目实战）"
            }}
        ]
    }},
    "recommended_resources": [
        {{
            "type": "课程/项目/书籍/工具",
            "title": "标题",
            "provider": "提供方（如：XX平台、XX大学）",
            "url": "链接（如有）",
            "time_required": "所需时间",
            "cost": "费用（免费/付费/价格）",
            "difficulty": "难度（入门/中级/高级）",
            "why_recommended": "推荐理由"
        }}
    ],
    "mindset_advice": {{
        "focus": "心态建议",
        "preparation_strategy": "准备策略",
        "interview_tips": ["面试时怎么说", "如何展示学习意愿"]
    }}
}}

---

## 补偿策略设计原则

### 核心理念

**经历不够，认知来补；能力不够，潜力来补**

1. **诚实不虚构**
   - 承认经历差距，不夸大
   - 强调学习能力和迁移能力

2. **主动展示**
   - 主动学习的内容（课程、项目）
   - 主动思考的理解（对行业、岗位的思考）

3. **具体可验证**
   - 给出具体的学习计划
   - 提供可验证的项目成果

---

## 改进策略分阶段设计

### Quick Wins（1周内）

**目标**：快速展示对方向的理解和学习意愿

| 行动 | 具体做法 | 所需时间 | 证据 |
|---|---|---|---|
| 行业研究 | 分析10个竞品账号的内容策略 | 2小时 | 分析报告 |
| 数据观察 | 用现有工作数据发现用户洞察 | 1小时 | 数据分析记录 |
| 知识学习 | 阅读行业报告/趋势文章 | 3小时 | 阅读笔记 |

### 中期行动（1个月）

**目标**：补充基础能力，展示学习成果

| 行动 | 具体做法 | 所需时间 | 证据 |
|---|---|---|---|
| 课程学习 | 完成XX平台《内容运营基础》 | 10小时 | 证书/笔记 |
| 小项目 | 用ChatGPT协助完成1周内容AB测试 | 5小时 | 测试报告 |
| 内容创作 | 发布10篇内容验证效果 | 持续 | 数据截图 |

### 长期计划（3-6个月）

**目标**：积累实战经验，形成作品集

| 阶段 | 目标 | 行动 | 预期成果 |
|---|---|---|---|
| 1-3个月 | 掌握基础技能 | 3个内容小项目 | 作品集 |
| 3-6个月 | 形成个人方法论 | 运营自己的账号 | 数据成果 |

---

## 推荐资源（示例）

### 课程类
- 《内容运营基础》- XX平台
- 《数据分析入门》- XX大学
- 《内容策略实战》- XX训练营

### 项目类
- 自己账号的内容运营（可快速启动）
- 帮朋友公司优化内容策略
- 参与开源内容项目

### 书籍类
- 《内容运营实战》
- 《增长黑客》
- 《精益创业》

---

## 输出示例

{{
    "compensation_strategy": {
        "philosophy": "用认知弥补经历差距",
        "available_resources": "数据分析能力、用户理解能力、快速学习能力",
        "quick_wins": [
            {
                "action": "补充内容运营相关的数据观察",
                "specific": "从选品工作中提取用户偏好洞察，如'通过数据分析发现用户偏好XXX类型内容'",
                "evidence_available": true,
                "impact": "展示用户理解能力，匹配度+3分"
            },
            {
                "action": "分析竞品内容策略",
                "specific": "分析10个竞品账号的内容策略，输出观察报告",
                "evidence_available": true,
                "impact": "展示行业理解，匹配度+5分"
            }
        ],
        "medium_term_actions": [
            {
                "action": "完成内容运营课程",
                "specific": "完成XX平台《内容运营基础》课程（约10小时）",
                "time_required": "2周",
                "difficulty": "易",
                "impact": "展示学习能力，匹配度+5分"
            },
            {
                "action": "内容AB测试小项目",
                "specific": "用ChatGPT协助完成1周内容AB测试，记录数据",
                "time_required": "1周",
                "difficulty": "中",
                "impact": "展示实战经验，匹配度+10分"
            }
        ],
        "long_term_plan": [
            {
                "phase": "3个月",
                "actions": ["运营自己的内容账号，积累实战经验", "加入内容运营交流群学习"],
                "expected_outcome": "形成作品集，匹配度提升到中等以上"
            }
        ]
    },
    "recommended_resources": [
        {
            "type": "课程",
            "title": "内容运营基础课程",
            "provider": "XX平台",
            "url": "https://xxx.com",
            "time_required": "10小时",
            "cost": "免费（可付费获得证书）",
            "difficulty": "入门",
            "why_recommended": "系统化学习内容运营基础知识"
        }
    ],
    "mindset_advice": {
        "focus": "强调学习能力和迁移能力，而非直接经验",
        "preparation_strategy": "准备1份'能力迁移'的说辞：虽然直接经验有限，但数据分析能力可以快速迁移",
        "interview_tips": [
            "被问'为什么选品经验能做内容运营'：强调'底层能力都是数据+用户理解'",
            "被问'没有直接经验怎么办'：强调'3周掌握SQL的快速学习能力'"
        ]
    }
}
```

---

## 优化日志

### P011: 提升建议生成

| 版本 | 日期 | 修改内容 | 修改人 |
|---|---|---|---|
| v1.0 | 2026-02-25 | 初始版本 | Claude |
| v1.1 | 2026-02-25 | ✨ 增强"差距→补偿路径"（优化点6） | Claude |
| | | 增加 Quick Wins / 中长期 / 资源推荐 | |

---

## P012: 意图分类

### 用途
在多轮对话中识别用户意图

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `user_input` | string | 用户输入 |
| `context` | object | 对话上下文 |
| `source_scope` | string | 输入来源（project/task_card） |
| `current_task_card_id` | string | 当前卡片ID（来源为task_card时） |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `primary_intent` | string | 主意图 |
| `candidates` | array<string> | 候选意图列表 |
| `need_clarification` | bool | 是否需要澄清 |
| `clarify_question` | string | 澄清问题（可空） |
| `source_scope` | string | 路由来源（project/task_card） |
| `source_task_card_id` | string | 路由卡片ID（可空） |

### Prompt模板

```markdown
你是一个意图分类器。请将用户输入分类为以下意图之一：

意图列表：
- ingest_jd：添加JD
- update_resume：更新简历
- add_info：补充信息
- generate：生成简历
- compare：对比方向
- abandon：放弃任务

别名规则：
- add_jd（卡片内新增JD）应归一映射为 ingest_jd

用户输入：{user_input}

上下文：
- 当前状态：{context.state}
- 方向数量：{context.direction_count}
- 当前评分：{context.current_score}
- 输入来源：{source_scope}
- 当前卡片ID：{current_task_card_id}

请按以下JSON格式输出：

{{
    "primary_intent": "意图名称",
    "reasoning": "判断理由",
    "candidates": ["候选意图1", "候选意图2"],
    "need_clarification": true/false,
    "clarify_question": "如果不确定，用一句话询问用户",
    "source_scope": "project|task_card",
    "source_task_card_id": "string/空"
}}

分类规则：
1. 优先匹配关键词
2. 结合上下文判断
3. 无法唯一判断时给出候选并触发澄清问题
```

---

## P013: JD分配决策（Project级）

### 用途
在 `ingest_jd` 后，基于方向聚类结果和现有卡片，输出 JD 的归属方案与用户确认预览。

### 输入参数
| 参数名 | 类型 | 说明 |
|---|---|---|
| `source_scope` | string | 输入来源（project/task_card） |
| `source_task_card_id` | string | 当前卡片ID（可空） |
| `jd_entries` | array<object> | 已解析JD条目（含project_jd_id、direction_id） |
| `existing_task_cards` | array<object> | 现有卡片（task_card_id、direction_id、direction_name） |

### 槽位抽取
| 槽位名 | 类型 | 说明 |
|---|---|---|
| `need_user_confirm` | bool | 是否需要先让用户确认预览 |
| `allocations` | array<object> | 每条JD的分配决策 |
| `decision` | string | assign_current_card/assign_existing_card/create_new_card |
| `target_task_card_id` | string | 目标卡片ID（可空） |
| `reason` | string | 决策理由 |

### Prompt模板

```markdown
你是一个Project级JD分配器。请把JD条目分配到最合适的Task Card。

输入来源：{source_scope}
当前卡片：{source_task_card_id}
JD条目：{jd_entries_json}
现有卡片：{existing_task_cards_json}

分配原则：
1. JD原文属于Project层，Task Card只保存引用关系。
2. 若来源为task_card，优先判断是否可加入当前卡片。
3. 若不适合当前卡片，尝试匹配已有同方向卡片。
4. 若无合适卡片，给出create_new_card。
5. 批量或方向不明确时应要求用户先确认预览。

输出JSON：
{
  "need_user_confirm": true/false,
  "preview_summary": "一句话说明分配结果",
  "allocations": [
    {
      "project_jd_id": "string",
      "decision": "assign_current_card|assign_existing_card|create_new_card",
      "target_task_card_id": "string/空",
      "target_direction_name": "string",
      "reason": "string"
    }
  ]
}
```

---

## 待补充Prompt

以下Prompt待后续补充：

- [ ] 确认对话框生成
- [ ] 错误处理响应生成
- [ ] 帮助文档生成
- [ ] 补充信息表单生成

---

## 总优化日志

### 基于PDF《求职底层逻辑》的优化总览

| 优化点 | 影响的Prompt | 版本 | 核心改进 | 状态 |
|---|---|---|---|---|
| **优化点2：完整证据链** | P002/P006 | v1.1 | 增加"动机-方法-结果-可追问"的完整证据链提取 | ✅ 完成 |
| **优化点3：潜力匹配** | P004 | v1.1 | 增加"未来能干"的评估维度 | ✅ 完成 |
| **优化点4：可迁移能力** | P005 | v1.1 | 显性识别A经验如何迁移到B场景 | ✅ 完成 |
| **优化点5：增量视角** | P004 | v1.1 | 增加"我能给团队带来什么增量价值" | ✅ 完成 |
| **优化点6：差距→补偿路径** | P004/P011 | v1.1 | 从"有什么差距"升级为"如何弥补差距" | ✅ 完成 |
| **优化点7：反问能力** | P008 | v1.1 | 增加"应该问面试官什么问题" | ✅ 完成 |
| 优化点1：三维匹配 | - | - | 暂不实施（复杂度较高） | ⏸️ 跳过 |

### 优化优先级总结

| 优先级 | 优化点 | 收益 | 状态 |
|---|---|---|---|
| **高** | 完整证据链 | 直接提升简历质量和真实性 | ✅ 已完成 |
| **高** | 可迁移能力 | 提升低匹配场景的转化率 | ✅ 已完成 |
| **高** | 差距→补偿路径 | 让用户知道"怎么做" | ✅ 已完成 |
| **中** | 潜力匹配 | 增加"未来能干"的评估 | ✅ 已完成 |
| **中** | 增量视角 | 展示差异化价值 | ✅ 已完成 |
| **中** | 反问能力 | 提升面试表现 | ✅ 已完成 |

### 核心改进总结

**从"静态匹配"到"动态匹配"**：
- 之前：只看"现在能干什么"
- 现在：考虑"未来能干什么"+"能带来什么增量"+"如何弥补差距"

**从"有证据"到"完整证据链"**：
- 之前：有证据就行
- 现在：必须说明"为什么做+怎么做+结果如何+能否被追问"

**从"有什么差距"到"如何弥补"**：
- 之前：告诉你差在哪里
- 现在：告诉你1周/1月/3个月分别能做什么
