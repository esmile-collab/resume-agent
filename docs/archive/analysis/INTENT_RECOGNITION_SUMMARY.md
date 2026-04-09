<!--
Input: 历史设计、专项分析或参考资料。
Output: 保留《意图识别策略优化 - 快速总结》作为参考或归档材料。
Pos: 历史或参考文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 意图识别策略优化 - 快速总结

## 📊 当前实现

### 核心策略：基于规则的意图识别

```python
# 位置：src/agent/planner.py

class AgentPlanner:
    def plan(self, content, attachments, snapshot, active_track_id, active_track_name):
        # 按优先级匹配意图
        if self._looks_like_jd(content, attachments):      # 1️⃣ JD 识别
            return ingest_jd_plan
        if self._asks_for_track_overview(content):          # 2️⃣ 方向总览
            return track_overview_plan
        if self._asks_for_score(content):                   # 3️⃣ 评分
            return score_plan
        if self._asks_for_generate(content):                # 4️⃣ 生成简历
            return generate_plan
        if self._asks_for_polish(content):                  # 5️⃣ 润色简历
            return polish_plan
        return add_info_plan                                # 6️⃣ 默认
```

### 识别方法

| 意图 | 触发关键词 |
|------|-----------|
| `ingest_jd` | "岗位职责"、"任职要求"、"JD" |
| `track_overview` | "方向" + ("查看"/"看看"/"总览") |
| `score_resume` | "评分"、"打分"、"匹配度" |
| `generate_resume` | "生成简历"、"写简历" |
| `polish_resume` | "润色"、"优化简历" |

### 优缺点

| ✅ 优点 | ⚠️ 缺点 |
|--------|--------|
| 简单高效，响应快速 | 关键词覆盖有限 |
| 无 API 成本 | 无法处理模糊意图 |
| 行为可预测 | 无法理解上下文 |
| 易于调试 | 不支持多意图 |

---

## 🚀 优化方向

### 方案 1️⃣：扩充关键词词典（🔥 立即可做）

```python
# 扩充关键词，提升覆盖率

SCORE_KEYWORDS = [
    "评分", "打分", "评估", "匹配度", "怎么样", "可以通过吗", "差距大吗"
]

POLISH_KEYWORDS = [
    "润色", "优化", "改写", "改进", "怎么改", "更好"
]
```

**收益**: +15% 覆盖率 | **成本**: 无

---

### 方案 2️⃣：混合策略（⭐ 推荐）

```python
class HybridIntentRecognizer:
    def recognize(self, content, context):
        # 80% 请求：规则匹配（快速、免费）
        rule_decision = self._rule_match(content)
        if rule_decision.confidence >= 0.8:
            return rule_decision

        # 20% 请求：LLM 识别（准确、灵活）
        return self._llm_recognize(content, context)
```

**收益**: +25% 准确率 | **成本**: ~$0.0003/次（仅 20% 请求）

---

### 方案 3️⃣：上下文增强（⭐ 推荐）

```python
def recognize_with_context(self, content, context):
    # 利用对话历史

    # 规则 1: 刚上传 JD，用户说"可以"，很可能是评分
    if context["last_action"] == "ingest_jd" and "可以" in content:
        return IntentDecision(intent="score_resume", confidence=0.9)

    # 规则 2: 刚评分，用户说"怎么改"，很可能是润色
    if context["last_action"] == "score_resume" and "怎么改" in content:
        return IntentDecision(intent="polish_resume", confidence=0.9)
```

**收益**: +20% 准确率 | **成本**: 无

---

### 方案 4️⃣：多意图识别

```python
# 支持复合请求："帮我评分然后润色"

def recognize_multi(self, content):
    # 识别为：[score_resume, polish_resume]

    return IntentDecision(
        intents=[
            SingleIntent(intent="score_resume", confidence=0.9),
            SingleIntent(intent="polish_resume", confidence=0.9)
        ],
        steps=[
            PlanStep(tool_name="resume_score"),
            PlanStep(tool_name="resume_polish")
        ]
    )
```

**收益**: 支持复合请求 | **成本**: 中等

---

## 📋 实施路线图

| 阶段 | 任务 | 工作量 | 收益 |
|------|------|--------|------|
| **第 1 周** | 扩充关键词词典 | 2-3 天 | +15% |
| **第 1 周** | 添加置信度评分 | 1-2 天 | 更好决策 |
| **第 2 周** | 实施混合策略 | 3-5 天 | +25% |
| **第 3 周** | 上下文增强 | 3-4 天 | +20% |
| **第 4 周** | 多意图识别 | 4-5 天 | 用户体验++ |

---

## 🎯 关键决策

### 是否引入 LLM？

**推荐：混合策略**
- 80% 用规则（快速、免费）
- 20% 用 LLM（准确、兜底）
- 成本：~$0.00006/次（平均）

### 成本优化策略

```python
# 三级缓存策略
1. 规则匹配（置信度 ≥ 0.8）→ 免费
2. 历史相似案例 → 免费
3. LLM 识别 → ~$0.0003
```

---

## 📖 详细文档

详见：[INTENT_RECOGNITION_ANALYSIS.md](INTENT_RECOGNITION_ANALYSIS.md)

- 完整代码示例
- 评估指标
- A/B 测试方案
- 持续优化策略
