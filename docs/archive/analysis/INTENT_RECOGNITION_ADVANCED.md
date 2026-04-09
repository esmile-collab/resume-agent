<!--
Input: 历史设计、专项分析或参考资料。
Output: 保留《意图识别深度优化方案对比》作为参考或归档材料。
Pos: 历史或参考文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 意图识别深度优化方案对比

## 新方案对比

### 方案 A：Query 改写 + CoT

#### 实现原理

```
用户输入
  ↓
Query 改写（LLM）
  "帮我看看" → "帮我评分一下简历"
  ↓
CoT 推理（LLM）
  "用户说'帮我看看'，结合刚上传 JD，应该是要评分"
  ↓
意图识别
```

#### 代码实现

```python
class CoTIntentRecognizer:
    """使用 CoT 的意图识别器"""

    def __init__(self, client: Anthropic):
        self.client = client

    def recognize(self, content: str, context: dict) -> IntentDecision:
        """使用 CoT 识别意图"""

        prompt = f"""
你是简历助手，需要识别用户的意图。

## 用户输入
{content}

## 上下文
- 刚才的操作: {context.get('last_action')}
- 是否有 JD: {context.get('has_jd')}
- 对话轮次: {context.get('conversation_turn')}

## 思考步骤（请逐步思考）

1. **分析用户输入**：用户具体说了什么？关键词有哪些？
2. **结合上下文**：根据对话历史，用户可能想要什么？
3. **推断意图**：综合以上信息，用户最可能的意图是什么？
4. **检查置信度**：这个推断有多大把握？

请按以下 JSON 格式返回：
{{
  "thought_process": {{
    "input_analysis": "用户输入分析",
    "context_analysis": "上下文分析",
    "intent_inference": "意图推断",
    "confidence_check": "置信度检查"
  }},
  "decision": {{
    "intent": "最终意图",
    "confidence": 0.0-1.0,
    "reasoning": "推理过程总结"
  }}
}}
"""

        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)

        return IntentDecision(
            intent=result["decision"]["intent"],
            reason=result["decision"]["reasoning"],
            confidence=result["decision"]["confidence"],
            thought_process=result["thought_process"]  # 可用于调试和用户解释
        )
```

#### 成本分析

| 项目 | 成本 | 说明 |
|------|------|------|
| **LLM 调用** | ~$0.0005/次 | 使用 Haiku，~500 tokens 输入，~500 tokens 输出 |
| **延迟增加** | +300-500ms | 需要额外的 LLM 调用 |
| **开发成本** | 2-3 天 | 实现 CoT prompt |

#### 收益分析

| 指标 | 提升 | 说明 |
|------|------|------|
| **准确率** | 85% → 92% | 特别是模糊/复杂 query |
| **可解释性** | +++ | 可以展示推理过程 |
| **用户体验** | ++ | 更自然的交互 |

#### 适用场景

✅ **适合**：
- 用户表达模糊（"可以吗"、"怎么样"、"帮我看看"）
- 上下文依赖强（"那"、"这个"、"它"）
- 需要向用户解释识别过程

❌ **不适合**：
- 明确的表达（"评分"、"润色"）- 浪费成本
- 高并发场景 - 延迟和成本都高

---

### 方案 B：专门的小模型

#### 实现原理

```
训练阶段
  收集数据 → 标注 → 微调 BERT/TinyLlama → 部署

推理阶段
  用户输入 → 小模型 → 意图分类
```

#### 代码实现

**训练数据准备**

```python
# 训练数据格式
training_data = [
    {
        "text": "帮我评分一下",
        "intent": "score_resume",
        "context": {"has_jd": True}
    },
    {
        "text": "可以吗",
        "intent": "score_resume",
        "context": {"last_action": "ingest_jd"}
    },
    {
        "text": "润色简历",
        "intent": "polish_resume",
        "context": {}
    },
    # ... 需要至少 500-1000 条标注数据
]
```

**模型训练（使用 HuggingFace）**

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer
import torch

# 使用预训练模型
model_name = "distilbert-base-uncased"  # 或 "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=6  # 6 个意图类别
)

# 准备数据集
from datasets import Dataset

train_dataset = Dataset.from_list(training_data)

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=128,
        return_tensors="pt"
)

tokenized_dataset = train_dataset.map(tokenize_function, batched=True)

# 训练
trainer = Trainer(
    model=model,
    train_dataset=tokenized_dataset,
    args=TrainingArguments(
        output_dir="./intent_classifier",
        num_train_epochs=3,
        per_device_train_batch_size=16,
        learning_rate=2e-5,
    ),
)

trainer.train()

# 保存模型
model.save_pretrained("./intent_classifier")
tokenizer.save_pretrained("./intent_classifier")
```

**推理**

```python
from transformers import pipeline

class SmallModelIntentRecognizer:
    """使用小模型的意图识别器"""

    def __init__(self, model_path: str = "./intent_classifier"):
        self.classifier = pipeline(
            "text-classification",
            model=model_path,
            tokenizer=model_path,
            device=0 if torch.cuda.is_available() else -1
        )

        # 意图映射
        self.id_to_intent = {
            0: "ingest_jd",
            1: "track_overview",
            2: "score_resume",
            3: "generate_resume",
            4: "polish_resume",
            5: "add_info"
        }

    def recognize(self, content: str, context: dict) -> IntentDecision:
        """识别意图"""

        # 构建输入（包含上下文）
        context_str = self._format_context(context)
        input_text = f"{context_str} {content}".strip()

        # 推理
        result = self.classifier(input_text, return_all_scores=True)

        # 获取最高分的意图
        top_result = max(result, key=lambda x: x["score"])

        return IntentDecision(
            intent=self.id_to_intent[int(top_result["label"].split("_")[-1])],
            confidence=top_result["score"],
            reason="小模型预测"
        )

    def _format_context(self, context: dict) -> str:
        """格式化上下文"""
        parts = []
        if context.get("last_action"):
            parts.append(f"上次:{context['last_action']}")
        if context.get("has_jd"):
            parts.append("有JD")
        if context.get("active_track_name"):
            parts.append(f"方向:{context['active_track_name']}")
        return " ".join(parts) if parts else ""
```

#### 成本分析

| 项目 | 成本 | 说明 |
|------|------|------|
| **数据标注** | $500-2000 | 外包标注 500-1000 条数据，$1-2/条 |
| **训练成本** | $10-50 | 使用云 GPU（如 Colab Pro）训练 2-3 小时 |
| **部署成本** | $0 | 本地部署，或使用免费的 HuggingFace Spaces |
| **推理成本** | $0/次 | 本地推理，或 HF Spaces 免费额度 |
| **维护成本** | 低 | 偶尔重新训练更新模型 |

#### 收益分析

| 指标 | 数值 | 说明 |
|------|------|------|
| **准确率** | 80-90% | 取决于训练数据质量 |
| **延迟** | <50ms | 远低于 LLM |
| **吞吐量** | >1000 QPS | 单机可支持高并发 |
| **可解释性** | 低 | 黑盒模型 |

#### 适用场景

✅ **适合**：
- 高并发场景（>1000 QPS）
- 需要低延迟（<100ms）
- 有足够的训练数据
- 长期使用（摊薄训练成本）

❌ **不适合**：
- 低并发场景（<100 QPS）- 训练成本摊不薄
- 缺乏训练数据
- 需要频繁更新意图

---

## 综合对比

### 方案对比表

| 维度 | 规则引擎 | 混合策略 | Query改写+CoT | 小模型 |
|------|----------|----------|---------------|--------|
| **准确率** | 70-80% | 85-90% | 90-95% | 80-90% |
| **延迟** | <10ms | ~200ms | ~500ms | <50ms |
| **单次成本** | $0 | $0.00006 | $0.0005 | $0 |
| **初始成本** | $0 | $0 | 2-3天开发 | $500-2000 |
| **可维护性** | 高 | 中 | 中 | 低 |
| **可解释性** | 高 | 中 | 高 | 低 |
| **并发能力** | 无限 | 受LLM限制 | 受LLM限制 | >1000 QPS |

### 成本收益曲线

```
成本/收益
  ↑
  │      小模型
  │        /
  │       /  ← 准确率 80-90%
  │      /
  │     /
  │    /  Query改写+CoT
  │   /    ↑ 准确率 90-95%
  │  /
  │ /
  │/  混合策略
  └─────────────────→ 准确率 85-90%
```

---

## 落地快且收益高的方案排序

### 🥇 第1名：混合策略（规则+LLM兜底）

**为什么第一？**

| 指标 | 评分 |
|------|------|
| 落地速度 | ⭐⭐⭐⭐⭐ 3-5天 |
| 收益 | ⭐⭐⭐⭐⭐ +25% 准确率 |
| 成本 | ⭐⭐⭐⭐⭐ $0.00006/次 |
| 可维护性 | ⭐⭐⭐⭐ 高 |

**实施步骤**：
1. Day 1-2: 扩充关键词词典
2. Day 3-4: 实现混合识别器
3. Day 5: 测试上线

**代码量**: ~200 行

---

### 🥈 第2名：Query 改写（仅在必要时）

**关键优化：选择性使用 CoT**

```python
class SmartCoTRecognizer:
    """智能 CoT 识别器：仅在必要时使用"""

    def recognize(self, content: str, context: dict) -> IntentDecision:
        # 1. 先用规则快速匹配
        rule_decision = self._rule_match(content)
        if rule_decision.confidence >= 0.8:
            return rule_decision

        # 2. 简单 LLM 识别（不用 CoT）
        simple_decision = self._llm_simple(content, context)
        if simple_decision.confidence >= 0.7:
            return simple_decision

        # 3. 复杂场景才用 CoT
        return self._llm_cot(content, context)

    def _llm_simple(self, content: str, context: dict) -> IntentDecision:
        """简单 LLM 识别（无 CoT，便宜）"""
        prompt = f"识别意图: {content}，返回 JSON: {{intent, confidence}}"
        # 成本：~$0.0001
        pass

    def _llm_cot(self, content: str, context: dict) -> IntentDecision:
        """CoT 识别（仅 10-20% 的请求）"""
        # 成本：~$0.0005，但只对复杂请求使用
        pass
```

**优化后的成本**：
- 80% 规则：$0
- 15% 简单 LLM：$0.0001 × 0.15 = $0.000015
- 5% CoT：$0.0005 × 0.05 = $0.000025
- **平均成本**：$0.00004/次（比纯 CoT 便宜 92%）

**收益**：准确率 90%+（仅增加 25% 成本）

---

### 🥉 第3名：小模型（适合高并发）

**什么情况下值得做？**

使用收益公式：
```
收益 = (LLM成本 - 小模型成本) × QPS × 时间 - 训练成本

假设：
- LLM 成本：$0.00006/次
- QPS：1000
- 时间：365 天
- 训练成本：$1000

收益 = $0.00006 × 1000 × 86400 × 365 - $1000
     = $1,897,920 - $1,000
     = $1,896,920
```

**结论**：
- ✅ QPS > 100：值得做
- ✅ QPS > 1000：强烈推荐
- ❌ QPS < 100：不推荐（训练成本摊不薄）

---

## 最终推荐方案

### 阶段 1：立即实施（1 周）

```python
# 混合策略 + 选择性 CoT

class OptimalIntentRecognizer:
    """最优意图识别器"""

    def recognize(self, content: str, context: dict) -> IntentDecision:
        # 1. 规则匹配（80%，免费）
        rule_decision = self._rule_match(content)
        if rule_decision.confidence >= 0.8:
            return rule_decision

        # 2. 简单 LLM（15%，$0.0001）
        simple_decision = self._llm_simple(content, context)
        if simple_decision.confidence >= 0.7:
            return simple_decision

        # 3. CoT（5%，$0.0005）
        return self._llm_cot(content, context)
```

**收益**：准确率 90%+，成本 $0.00004/次

---

### 阶段 2：3 个月后（QPS > 100）

```python
# 训练小模型

# 1. 收集数据（自动标注）
training_data = self._auto_label_from_logs()

# 2. 训练模型
model = self._train_small_model(training_data)

# 3. A/B 测试
if self._ab_test(model) > baseline:
    # 4. 逐步切换流量
    self._gradual_rollout(model, start_percentage=10)
```

**收益**：长期成本降低 80%，延迟降低 90%

---

## 成本收益总结

### 短期（1-3 个月）

| 方案 | 准确率 | 成本/次 | 开发时间 | 推荐度 |
|------|--------|---------|----------|--------|
| **混合策略+选择性CoT** | 90%+ | $0.00004 | 1 周 | ⭐⭐⭐⭐⭐ |
| 纯 CoT | 92% | $0.0005 | 3 天 | ⭐⭐⭐ |
| 小模型 | 85% | $0 | 4-6 周 | ⭐⭐ |

### 长期（6-12 个月）

| 方案 | 准确率 | 成本/次 | 维护成本 | 推荐度 |
|------|--------|---------|----------|--------|
| **小模型** | 90%+ | $0 | 低 | ⭐⭐⭐⭐⭐ |
| 混合策略+选择性CoT | 90%+ | $0.00004 | 中 | ⭐⭐⭐⭐ |
| 纯 CoT | 92% | $0.0005 | 中 | ⭐⭐ |

---

## 实施建议

### 立即做（本周）

1. **扩充关键词词典** - 2 小时
   - 添加同义词、缩写、模糊表达

2. **实现混合策略** - 3 天
   - 规则优先 + LLM 兜底

### 近期做（本月）

3. **添加选择性 CoT** - 2 天
   - 仅对复杂请求使用 CoT
   - 降低 92% 成本

4. **收集数据** - 持续
   - 记录用户 query 和识别结果
   - 为小模型训练准备

### 长期做（QPS > 100）

5. **训练小模型** - 4-6 周
   - 使用收集的数据训练
   - A/B 测试验证效果
   - 逐步切换流量

---

## 关键指标

| 指标 | 目标 | 监控方式 |
|------|------|----------|
| 准确率 | >90% | 人工抽检 10% |
| 澄清率 | <5% | 统计 need_clarification 比例 |
| 延迟 | P95 <200ms | 监控 API 延迟 |
| 成本 | <$0.0001/次 | 统计 LLM 调用次数 |
| 用户满意度 | >4.5/5 | 用户反馈评分 |
