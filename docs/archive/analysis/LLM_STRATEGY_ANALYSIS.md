<!--
Input: 历史设计、专项分析或参考资料。
Output: 保留《大模型策略分析报告》作为参考或归档材料。
Pos: 历史或参考文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 大模型策略分析报告

## 当前项目使用的大模型策略

### 1. 混合评分架构（Hybrid Scoring）

```
┌─────────────────────────────────────────────────────────────┐
│                    简历评分系统架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入: JD + 简历                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │ 第一次 LLM   │  参数提取 + 软性指标评分                  │
│  │  调用        │  - 提取硬性指标参数（实习、项目、技术）   │
│  └──────────────┘  - 评分软性指标（学习能力、执行能力等）   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │ 规则引擎     │  硬性指标评分（60% 权重）                 │
│  │              │  - 实习经历 27%                          │
│  │              │  - 项目经历 22%                          │
│  │              │  - 技术实践 16%                          │
│  │              │  - 教育/专业/GPA/英语/稳定性             │
│  └──────────────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │ 第二次 LLM   │  生成改进建议                             │
│  │  调用        │  - 快速改进建议                           │
│  │              │  - 长期改进建议                           │
│  └──────────────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  输出: 评分报告                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. 当前实现的技术细节

#### 2.1 LLM 调用方式

**位置**: `src/scoring/campus_scorer.py`

```python
# 第一次 LLM 调用：参数提取 + 软性指标评分
def _extract_and_soft_score(self, jd: str, resume: str) -> ExtractionResult:
    prompt = self._build_extraction_prompt(jd, resume)
    response = self._call_llm(prompt)
    data = json.loads(response)  # 解析 JSON
    return ExtractionResult(...)

# 第二次 LLM 调用：生成改进建议
def _generate_report(...) -> ScoreReport:
    prompt = self._build_report_prompt(...)
    response = self._call_llm(prompt)
    data = json.loads(response)
    return ScoreReport(...)
```

#### 2.2 提示词工程策略

**策略**: **长 Prompt + JSON Schema**

```python
# 提示词模板（约 500-800 tokens）
prompt = f"""你是一个校招简历评估专家。请分析以下 JD 和简历，提取关键信息并进行软性指标评分。

## JD
{jd}

## 简历
{resume}

请按以下 JSON 格式输出：
{{
  "jd_summary": "JD 的简要总结（50字以内）",
  "resume_summary": "简历的简要总结（50字以内）",
  "internship_require": {{ ... }},
  "soft_metrics": {{
    "learning_ability": {{
      "dimension": "学习能力",
      "score": 0-100分数,
      "reasoning": "评分理由",
      "evidence": "证据（必须引用简历中的具体描述或数据）",
      "evidence_level": "100分标准/80分标准/60分标准/40分标准"
    }},
    ...
  }}
}}

## 软性指标评分标准（详细说明）
...

只返回 JSON，不要返回其他内容。
"""
```

#### 2.3 多模型支持

```python
def _get_llm_client():
    # 优先级：Anthropic > OpenAI
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    except:
        pass

    try:
        from openai import OpenAI
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except:
        pass

    return None  # 使用 Mock 响应
```

**支持的模型**:
- Anthropic: `claude-3-5-sonnet-20241022` / `claude-3-opus-20240229`
- OpenAI: `gpt-4o` / `gpt-3.5-turbo`

#### 2.4 降级策略

```python
def _call_llm(self, prompt: str) -> str:
    if self._client is None:
        # 返回 Mock 响应
        return '{"jd_summary": "Mock JD", "soft_metrics": {...}}'
    # ... 真实 API 调用
```

---

## 为什么这么做？（设计理由）

### ✅ 优点

| 策略 | 优点 |
|------|------|
| **混合评分** | 硬性指标用规则引擎（准确、快速、一致），软性指标用 LLM（理解语义、评估能力） |
| **两次 LLM 调用** | 第一次提取结构化数据，第二次生成建议，职责分离，易于调试 |
| **长 Prompt + JSON** | 提供详细的评分标准，减少 LLM 理解偏差 |
| **多模型支持** | 降低单一厂商依赖，提高可用性 |
| **Mock 降级** | 保证系统在没有 API Key 时也能运行测试 |

### ⚠️ 缺点

| 问题 | 影响 |
|------|------|
| **JSON 解析脆弱** | LLM 可能返回非标准 JSON，需要 try-catch 处理 |
| **Prompt 漂移** | 长 Prompt 可能导致 LLM 遗忘前面的指令 |
| **成本较高** | 每次评分需要 2 次 LLM 调用 |
| **无重试机制** | API 调用失败直接降级到 Mock |
| **Token 浪费** | JD 和简历被发送两次到 LLM |

---

## 更好的解法建议

### 🎯 优先级排序

#### 1️⃣ 高优先级：使用 Structured Output

**当前问题**: JSON 解析脆弱，LLM 可能返回格式错误

**解决方案**: 使用各厂商的 Structured Output 功能

```python
# 方案 A: Anthropic (推荐)
from anthropic import Anthropic
from anthropic.types import ToolUse

client = Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    tools=[{
        "name": "extract_and_score",
        "description": "提取参数并评分软性指标",
        "input_schema": {
            "type": "object",
            "properties": {
                "jd_summary": {"type": "string"},
                "soft_metrics": {
                    "type": "object",
                    "properties": {
                        "learning_ability": {
                            "type": "object",
                            "properties": {
                                "score": {"type": "number"},
                                "reasoning": {"type": "string"},
                                "evidence": {"type": "string"}
                            },
                            "required": ["score", "reasoning", "evidence"]
                        }
                    }
                }
            },
            "required": ["jd_summary", "soft_metrics"]
        }
    }],
    messages=[{"role": "user", "content": prompt}]
)

# 直接获得结构化数据，无需 json.loads()
tool_use = response.content[-1]  # 最后一个是 tool_use
extraction = tool_use.input
```

**收益**:
- ✅ 100% 保证返回结构化数据
- ✅ 无需 JSON 解析错误处理
- ✅ 减少 token 使用（不需要 JSON 格式说明）

---

#### 2️⃣ 高优先级：减少 LLM 调用次数

**当前问题**: 每次评分需要 2 次 LLM 调用

**解决方案**: 合并为 1 次调用，使用 Structured Output

```python
def score(self, jd: str, resume: str) -> ScoreReport:
    """单次 LLM 调用完成所有工作"""
    response = self._call_llm_with_tools(
        jd=jd,
        resume=resume,
        tools=[{
            "name": "complete_score",
            "input_schema": {
                "properties": {
                    # 参数提取
                    "extraction": {...},
                    # 软性指标评分
                    "soft_metrics": {...},
                    # 改进建议
                    "quick_improvements": {"type": "array", "items": {"type": "string"}},
                    "long_term_improvements": {"type": "array", "items": {"type": "string"}}
                }
            }
        }]
    )

    # 从单次调用中获取所有数据
    return ScoreReport(...)
```

**收益**:
- ✅ 减少 50% 的 API 调用成本
- ✅ 降低延迟（1 次调用 vs 2 次）
- ✅ 减少重复发送 JD 和简历

---

#### 3️⃣ 中优先级：添加重试和错误处理

**当前问题**: API 调用失败直接降级到 Mock

**解决方案**: 添加重试机制

```python
import tenacity

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    retry=tenacity.retry_if_exception_type(requests.exceptions.RequestException)
)
def _call_llm_with_retry(self, prompt: str) -> str:
    """带重试的 LLM 调用"""
    response = self._client.messages.create(...)
    return response.content[0].text
```

---

#### 4️⃣ 中优先级：缓存 JD 解析结果

**当前问题**: 同一个 JD 多次评分时，每次都要重新解析

**解决方案**: 缓存 JD 的解析结果

```python
import hashlib
from functools import lru_cache

def _get_jd_hash(self, jd: str) -> str:
    return hashlib.md5(jd.encode()).hexdigest()

@lru_cache(maxsize=100)
def _parse_jd(self, jd_hash: str, jd_text: str) -> dict:
    """解析 JD（带缓存）"""
    response = self._call_llm(f"""
    分析以下 JD，提取关键信息：
    {jd_text}

    返回 JSON: {{"required_skills": [...], "preferred_skills": [...]}}
    """)
    return json.loads(response)
```

---

#### 5️⃣ 低优先级：使用更便宜的模型

**当前问题**: 使用 Claude Sonnet/Opus，成本较高

**解决方案**: 分层使用模型

```python
def _choose_model(self, task_type: str) -> str:
    """根据任务类型选择模型"""
    if task_type == "parameter_extraction":
        # 简单任务，使用便宜模型
        return "claude-3-haiku-20240307"  # 便宜 25x
    elif task_type == "soft_scoring":
        # 中等任务，使用中等模型
        return "claude-3-5-sonnet-20241022"
    elif task_type == "report_generation":
        # 复杂任务，使用最强模型
        return "claude-3-opus-20240229"
```

**成本对比**（假设每次评分 2000 tokens）:
| 模型 | 输入成本 | 输出成本 | 总成本（2 次调用） |
|------|----------|----------|-------------------|
| Opus | $3.00/M | $15.00/M | ~$0.036 |
| Sonnet | $3.00/M | $15.00/M | ~$0.036 |
| **Haiku** | **$0.25/M** | **$1.25/M** | **~$0.003** |

---

#### 6️⃣ 低优先级：批量处理优化

**当前问题**: 如果要对 100 份简历评分，需要串行调用 200 次 LLM

**解决方案**: 批量异步处理

```python
import asyncio
from anthropic import AsyncAnthropic

async def score_batch(self, jds: list[str], resumes: list[str]) -> list[ScoreReport]:
    """批量评分"""
    client = AsyncAnthropic()

    tasks = [
        self._score_async(client, jd, resume)
        for jd, resume in zip(jds, resumes)
    ]

    results = await asyncio.gather(*tasks)
    return results
```

---

## 总结：推荐的改进路线

### 短期（1-2 周）

1. ✅ **使用 Structured Output** - 解决 JSON 解析问题
2. ✅ **合并为 1 次 LLM 调用** - 降低成本和延迟
3. ✅ **添加重试机制** - 提高稳定性

### 中期（1-2 月）

4. ✅ **添加 JD 解析缓存** - 提高批量处理效率
5. ✅ **分层使用模型** - 降低成本
6. ✅ **改进 Prompt** - 使用 CoT、少样本学习

### 长期（3-6 月）

7. ✅ **批量异步处理** - 支持大规模评分
8. ✅ **Fine-tune 小模型** - 针对评分任务微调 Haiku
9. ✅ **本地模型支持** - 使用 Ollama + Llama 3

---

## 代码示例：改进后的实现

```python
# 改进后的评分器
class CampusScorerV22:
    """Campus recruitment scorer v2.2 with Structured Output"""

    def __init__(self, *, model: str = None):
        self.model = model or "claude-3-5-sonnet-20241022"
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def score(self, jd: str, resume: str) -> ScoreReport:
        """单次 LLM 调用完成所有工作"""

        # 定义输出结构
        tool_schema = {
            "name": "complete_score",
            "description": "完整的简历评分",
            "input_schema": {
                "type": "object",
                "properties": {
                    # 参数提取
                    "internship_params": {...},
                    "project_params": {...},
                    # 软性指标
                    "soft_metrics": {
                        "type": "object",
                        "properties": {
                            "learning_ability": {
                                "type": "object",
                                "properties": {
                                    "score": {"type": "number", "minimum": 0, "maximum": 100},
                                    "reasoning": {"type": "string"},
                                    "evidence": {"type": "string"}
                                },
                                "required": ["score", "reasoning", "evidence"]
                            }
                        }
                    },
                    # 改进建议
                    "improvements": {
                        "type": "object",
                        "properties": {
                            "quick": {"type": "array", "items": {"type": "string"}},
                            "long_term": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "required": ["internship_params", "soft_metrics", "improvements"]
            }
        }

        # 单次调用
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            tools=[tool_schema],
            messages=[{
                "role": "user",
                "content": self._build_prompt(jd, resume)
            }]
        )

        # 直接获取结构化数据
        tool_use = response.content[-1]
        result = tool_use.input

        # 计算硬性指标（规则引擎）
        hard_score = self._calculate_hard_metrics(result)

        # 构建软性指标（来自 LLM）
        soft_score = self._build_soft_metrics(result["soft_metrics"])

        # 计算总分
        final_score = hard_score.total_score * 0.6 + soft_score.total_score * 0.4

        return ScoreReport(
            hard_metrics=hard_score,
            soft_metrics=soft_score,
            final_score=final_score,
            quick_improvements=result["improvements"]["quick"],
            long_term_improvements=result["improvements"]["long_term"]
        )
```

---

## 参考资料

- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
