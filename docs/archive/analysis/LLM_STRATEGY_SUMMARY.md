<!--
Input: 历史设计、专项分析或参考资料。
Output: 保留《大模型策略总结》作为参考或归档材料。
Pos: 历史或参考文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 大模型策略总结

## 📊 当前项目使用的大模型策略

### 核心架构：混合评分 + 规则引擎

```
┌─────────────────────────────────────────────┐
│  输入: JD + 简历                            │
│         │                                   │
│         ▼                                   │
│  ┌─────────────────────────────────────┐   │
│  │  LLM 调用 #1: 参数提取 + 软性评分    │   │
│  │  - 提取实习、项目、技术等参数        │   │
│  │  - 评分学习能力、执行能力等软性指标  │   │
│  └─────────────────────────────────────┘   │
│         │                                   │
│         ▼                                   │
│  ┌─────────────────────────────────────┐   │
│  │  规则引擎: 硬性指标评分 (60%)        │   │
│  │  - 实习 27% | 项目 22% | 技术 16%    │   │
│  │  - 教育 11% | 专业 11% | GPA 6%      │   │
│  │  - 英语 5% | 稳定性 2%               │   │
│  └─────────────────────────────────────┘   │
│         │                                   │
│         ▼                                   │
│  ┌─────────────────────────────────────┐   │
│  │  LLM 调用 #2: 生成改进建议           │   │
│  │  - 快速改进建议                      │   │
│  │  - 长期改进建议                      │   │
│  └─────────────────────────────────────┘   │
│         │                                   │
│         ▼                                   │
│  输出: 评分报告 (总分 + 改进建议)           │
└─────────────────────────────────────────────┘
```

### 技术实现

| 组件 | 技术 | 说明 |
|------|------|------|
| **LLM 提示词** | 长 Prompt + JSON Schema | 约 500-800 tokens，包含详细评分标准 |
| **输出解析** | `json.loads()` | ⚠️ 脆弱，需要 try-catch |
| **模型支持** | Anthropic Claude / OpenAI GPT | Claude Sonnet/Opus, GPT-4o |
| **降级策略** | Mock 响应 | 无 API Key 时返回固定数据 |
| **重试机制** | ❌ 无 | API 失败直接降级 |

### resume-polish 实现

| 组件 | 技术 | 说明 |
|------|------|------|
| **润色方式** | ❌ 不使用 LLM | 纯规则匹配和替换 |
| **关键词强化** | 正则表达式 | "深度学习" → "深度学习/大语言模型" |
| **事实检查** | 关键词对比 | 检查是否添加了新技术/项目 |

---

## 🤔 为什么这么做？

### ✅ 优点

| 设计 | 理由 |
|------|------|
| **混合评分** | 硬性指标（可精确计算）用规则引擎，软性指标（需语义理解）用 LLM |
| **两次 LLM 调用** | 职责分离：第一次提取数据，二次生成建议，易于调试 |
| **多模型支持** | 降低单一厂商依赖，提高可用性 |
| **Mock 降级** | 保证系统在没有 API Key 时也能运行测试 |

### ⚠️ 缺点

| 问题 | 影响 |
|------|------|
| **JSON 解析脆弱** | LLM 可能返回格式错误，需要容错处理 |
| **2 次 LLM 调用** | 成本高、延迟大、JD/简历重复发送 |
| **无重试机制** | API 调用失败直接降级，体验差 |
| **无缓存** | 同一个 JD 多次评分时重复解析 |
| **resume-polish 不用 LLM** | 润色能力受限，只能做简单替换 |

---

## 🚀 更好的解法

### 1️⃣ 使用 Structured Output（强烈推荐）

**问题**: JSON 解析脆弱
**解决**: 使用 Anthropic Tool Use 或 OpenAI Structured Outputs

```python
# 当前方式（脆弱）
response = client.messages.create(...)
data = json.loads(response.content[0].text)  # 可能失败

# 改进方式（100% 可靠）
response = client.messages.create(
    tools=[{
        "name": "extract_and_score",
        "input_schema": {
            "type": "object",
            "properties": {
                "soft_metrics": {
                    "type": "object",
                    "properties": {
                        "learning_ability": {
                            "score": {"type": "number"},
                            "reasoning": {"type": "string"}
                        }
                    }
                }
            }
        }
    }]
)
# 直接获得结构化数据
data = response.content[-1].input
```

**收益**: ✅ 无需 JSON 解析 | ✅ 减少 token 使用 | ✅ 100% 类型安全

---

### 2️⃣ 合并为 1 次 LLM 调用

**问题**: 当前需要 2 次调用（提取 + 建议）
**解决**: 使用 Structured Output 一次性返回所有数据

```python
# 当前: 2 次调用
extraction = _call_llm(prompt1)  # 提取参数
suggestions = _call_llm(prompt2)  # 生成建议

# 改进: 1 次调用
response = _call_llm_with_tools(
    tools=[{
        "input_schema": {
            "properties": {
                "extraction": {...},
                "soft_metrics": {...},
                "suggestions": {...}
            }
        }
    }]
)
```

**收益**: ✅ 成本降低 50% | ✅ 延迟减少 50% | ✅ 无重复发送 JD/简历

---

### 3️⃣ 添加重试机制

**问题**: API 调用失败直接降级
**解决**: 使用 tenacity 添加指数退避重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_llm_with_retry(self, prompt: str) -> str:
    return self.client.messages.create(...)
```

---

### 4️⃣ 使用便宜的模型分层

**问题**: 所有任务都用 Sonnet/Opus，成本高
**解决**: 简单任务用 Haiku（便宜 25 倍）

| 任务 | 当前模型 | 推荐模型 | 成本降低 |
|------|----------|----------|----------|
| 参数提取 | Sonnet | Haiku | 25x |
| 软性评分 | Sonnet | Sonnet | - |
| 报告生成 | Sonnet | Haiku | 25x |

**成本对比**（假设每次 2000 tokens）:
- 当前（Sonnet × 2）: ~$0.036/次
- 改进后（Haiku × 2）: ~$0.003/次
- **节省 92%** 🎉

---

### 5️⃣ resume-polish 引入 LLM

**问题**: 当前润色只用规则，能力有限
**解决**: 使用 LLM 进行智能润色（但仍需事实检查）

```python
def _polish_with_llm(self, section: str, jd_keywords: list[str]) -> str:
    """使用 LLM 润色（带事实检查）"""
    response = self.client.messages.create(
        model="claude-3-5-sonnet-20241022",
        tools=[{
            "name": "polish_section",
            "input_schema": {
                "properties": {
                    "polished_content": {"type": "string"},
                    "added_keywords": {"type": "array", "items": {"type": "string"}},
                    "added_technologies": {"type": "array", "items": {"type": "string"}}
                }
            }
        }],
        messages=[{
            "role": "user",
            "content": f"""
            润色以下简历段落，使其更符合 JD 要求。

            ## 原始内容
            {section}

            ## JD 关键词
            {', '.join(jd_keywords)}

            ## 要求
            1. 只优化表达，不编造事实
            2. 可以添加 JD 关键词（如果是已有内容的同义词/子集）
            3. 标记所有新增的词汇

            返回 JSON，包含润色后的内容和新增的词汇列表。
            """
        }]
    )

    result = response.content[-1].input

    # 事实检查：确保没有添加新技术
    original_techs = self._extract_technologies(section)
    added_techs = result["added_technologies"]
    if any(tech not in original_techs for tech in added_techs):
        # 回退到原始内容
        return section

    return result["polished_content"]
```

**收益**: ✅ 更自然的润色 | ✅ 保留事实检查机制 | ✅ 更好的上下文理解

---

## 📋 改进优先级建议

| 优先级 | 改进项 | 难度 | 收益 | 推荐时机 |
|--------|--------|------|------|----------|
| 🔥 **P0** | Structured Output | 低 | 高 | 立即实施 |
| 🔥 **P0** | 合并为 1 次调用 | 低 | 高 | 立即实施 |
| ⭐ **P1** | 添加重试机制 | 低 | 中 | 1 周内 |
| ⭐ **P1** | 使用 Haiku 降本 | 低 | 高 | 1 周内 |
| 📈 **P2** | JD 解析缓存 | 中 | 中 | 1 月内 |
| 📈 **P2** | resume-polish 用 LLM | 中 | 高 | 1 月内 |
| 🚀 **P3** | 批量异步处理 | 高 | 高 | 3 月内 |

---

## 完整代码示例

详见: [docs/LLM_STRATEGY_ANALYSIS.md](LLM_STRATEGY_ANALYSIS.md)
