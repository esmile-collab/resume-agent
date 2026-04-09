<!--
Input: 历史设计、专项分析或参考资料。
Output: 保留《简历 Agent 意图识别策略分析与优化方案》作为参考或归档材料。
Pos: 历史或参考文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 简历 Agent 意图识别策略分析与优化方案

## 📊 当前实现分析

### 架构概览

```
用户输入 (content + attachments)
        ↓
AgentPlanner.plan()
        ↓
┌─────────────────────────────────────────┐
│         意图识别（规则匹配）             │
│  ┌──────────────────────────────────┐  │
│  │ 1. _looks_like_jd()              │  │
│  │ 2. _asks_for_track_overview()    │  │
│  │ 3. _asks_for_score()             │  │
│  │ 4. _asks_for_generate()          │  │
│  │ 5. _asks_for_polish()            │  │
│  │ 6. add_info (默认)               │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
        ↓
AgentPlan (decision + steps)
        ↓
AgentRuntime (执行计划)
```

### 当前意图类型

| 意图 | 触发条件 | 优先级 |
|------|----------|--------|
| `ingest_jd` | JD 附件或关键词（岗位职责、任职要求） | 🔥 最高 |
| `track_overview` | "方向" + ("查看"/"看看"/"总览") | ⭐ 高 |
| `score_resume` | "评分"/"打分"/"匹配度" | 📊 中 |
| `generate_resume` | "生成简历"/"写简历"/"定制简历" | 📊 中 |
| `polish_resume` | "润色"/"优化简历"/"改写" | 📊 中 |
| `add_info` | 默认（无匹配） | 💤 低 |

### 识别方法

```python
# 当前实现：基于关键词的规则匹配

def _looks_like_jd(content: str, attachments: list) -> bool:
    # 1. 检查附件类型
    if any(item.type == "jd" for item in attachments):
        return True
    # 2. 关键词匹配
    markers = ("岗位职责", "任职要求", "职位描述", "岗位要求", "JD")
    return any(marker in content for marker in markers)

def _asks_for_score(lowered: str) -> bool:
    keywords = ("评分", "打分", "匹配度", "score")
    return any(token in lowered for token in keywords)

def _asks_for_generate(lowered: str) -> bool:
    keywords = ("生成简历", "写简历", "定制简历", "输出简历", "generate")
    return any(token in lowered for token in keywords)

def _asks_for_polish(lowered: str) -> bool:
    keywords = ("润色", "优化简历", "改写", "polish")
    return any(token in lowered for token in keywords)

def _asks_for_track_overview(lowered: str) -> bool:
    return "方向" in lowered and any(
        token in lowered for token in ("查看", "看看", "有哪些", "列表", "总览")
    )
```

### 上下文感知

```python
def _resolve_track(snapshot, active_track_id, active_track_name, content):
    """解析目标求职方向"""
    tracks = snapshot.get("tracks", [])

    # 优先级：
    # 1. active_track_id（当前激活的方向 ID）
    # 2. active_track_name（当前激活的方向名称）
    # 3. 从文本中提取方向名称
    # 4. 如果只有一个方向，使用它
    # 5. 否则返回 None（需要用户澄清）
```

### 决策流程

```python
def plan(self, content, attachments, snapshot, active_track_id, active_track_name):
    # 1. JD 识别（最高优先级）
    if self._looks_like_jd(content, attachments):
        return AgentPlan(
            decision=IntentDecision(intent="ingest_jd", ...),
            steps=[ingest_jd, track_overview]
        )

    # 2. 方向总览
    if self._asks_for_track_overview(lowered):
        return AgentPlan(
            decision=IntentDecision(intent="track_overview", ...),
            steps=[track_overview]
        )

    # 3. 评分
    if self._asks_for_score(lowered):
        if target_track is None:
            return AgentPlan(decision=IntentDecision(need_clarification=True))
        return AgentPlan(steps=[resume_score])

    # 4. 生成简历
    if self._asks_for_generate(lowered):
        if target_track is None:
            return AgentPlan(decision=IntentDecision(need_clarification=True))
        return AgentPlan(steps=[resume_score, resume_generate])

    # 5. 润色简历
    if self._asks_for_polish(lowered):
        if target_track is None:
            return AgentPlan(decision=IntentDecision(need_clarification=True))
        return AgentPlan(steps=[resume_score, resume_polish])

    # 6. 默认：补充信息
    return AgentPlan(decision=IntentDecision(intent="add_info"))
```

---

## 🤔 当前策略的优缺点

### ✅ 优点

| 优点 | 说明 |
|------|------|
| **简单高效** | 纯规则匹配，无需 LLM 调用，响应快速 |
| **可预测性强** | 规则明确，行为可解释，易于调试 |
| **成本低** | 无 API 调用成本 |
| **上下文感知** | 考虑当前激活的方向和用户历史 |
| **澄清机制** | 方向不明确时会主动询问用户 |

### ⚠️ 缺点

| 缺点 | 影响 |
|------|------|
| **关键词覆盖有限** | 用户表达多样时可能识别失败（如"帮我看看"、"评估一下"） |
| **无法处理模糊意图** | 如"我的简历怎么样"（可能是评分、润色或咨询） |
| **无语义理解** | 无法理解上下文和隐含意图（如"怎么改"依赖于上文） |
| **优先级固定** | 无法根据用户状态动态调整优先级 |
| **无法学习** | 新意图需要硬编码，不能从用户行为中学习 |
| **多意图支持差** | 如"帮我评分然后润色"会被识别为单一意图 |

---

## 🚀 优化方向

### 方案 1️⃣：增强规则引擎（短期，1-2 周）

**目标**: 在现有基础上提高关键词覆盖率

#### 1.1 扩充关键词词典

```python
class IntentKeywords:
    """意图关键词库"""

    SCORE = [
        # 直接表达
        "评分", "打分", "评估", "评测", "分析", "诊断",
        # 隐含表达
        "匹配度", "怎么样", "如何", "够不够", "能不能",
        # 问题形式
        "可以通过吗", "有希望吗", "差距大吗",
        # 英文
        "score", "evaluate", "assess", "rate"
    ]

    GENERATE = [
        # 直接表达
        "生成简历", "写简历", "制作简历", "输出简历", "定制简历",
        # 隐含表达
        "帮我写", "帮我生成", "帮我制作",
        # 场景表达
        "投递用的简历", "面试用的简历",
        # 英文
        "generate", "create", "write", "make"
    ]

    POLISH = [
        # 直接表达
        "润色", "优化", "改写", "修改", "改进", "完善",
        # 隐含表达
        "更好", "提升", "优化一下", "改改",
        # 问题形式
        "怎么改", "怎么写", "怎么优化",
        # 英文
        "polish", "optimize", "improve", "refine"
    ]

    JD = [
        # 标准表达
        "岗位职责", "任职要求", "职位描述", "岗位要求", "JD", "job description",
        # 企业表达
        "岗位信息", "招聘需求", "招聘要求", "工作职责",
        # 其他表达
        "任职资格", "我们需要", "候选人要求"
    ]

    def __init__(self):
        # 编译正则表达式（提升性能）
        self._patterns = {
            intent: [re.compile(kw) for kw in keywords]
            for intent, keywords in self.__class__.__dict__.items()
            if not intent.startswith('_') and isinstance(keywords, list)
        }

    def match(self, text: str, intent: str) -> bool:
        """检查文本是否匹配意图"""
        patterns = self._patterns.get(intent, [])
        return any(pattern.search(text) for pattern in patterns)
```

#### 1.2 添加多模式识别

```python
def _asks_for_score(self, lowered: str) -> bool:
    """多种模式组合识别"""
    # 模式 1: 关键词匹配
    if self.keywords.match(lowered, "SCORE"):
        return True

    # 模式 2: 问号 + 简历相关
    if "?" in lowered and any(word in lowered for word in ["简历", "我", "通过"]):
        return True

    # 模式 3: 上下文推断（前一轮对话是关于 JD 的）
    if self.last_intent == "ingest_jd" and any(word in lowered for word in ["可以", "怎么样", "能"]):
        return True

    return False
```

#### 1.3 添加意图置信度

```python
@dataclass
class IntentDecision:
    """意图决策（带置信度）"""
    intent: str
    reason: str
    confidence: float = 1.0  # 新增：置信度 [0, 1]
    alternatives: list[dict] = field(default_factory=list)  # 新增：其他可能意图
    need_clarification: bool = False
    clarify_question: str = ""
    target_track_name: str = ""

def _calculate_confidence(self, matched_keywords: list, total_keywords: int) -> float:
    """计算置信度"""
    if total_keywords == 0:
        return 0.5
    return len(matched_keywords) / total_keywords
```

**收益**:
- ✅ 提高关键词覆盖率 ~30%
- ✅ 支持更多表达方式
- ✅ 提供置信度，辅助决策
- ✅ 实现简单，成本低

---

### 方案 2️⃣：基于 LLM 的意图识别（中期，2-4 周）

**目标**: 使用 LLM 理解用户意图的语义

#### 2.1 单次 LLM 调用识别意图

```python
class LLMIntentRecognizer:
    """基于 LLM 的意图识别器"""

    def __init__(self, client: Anthropic):
        self.client = client
        self.intent_schema = self._build_intent_schema()

    def recognize(self, content: str, context: dict) -> IntentDecision:
        """识别用户意图"""

        # 构建提示词
        prompt = f"""
你是简历助手 Agent，需要识别用户的意图。

## 用户输入
{content}

## 当前上下文
- 激活的方向: {context.get('active_track_name')}
- 历史对话: {context.get('history')}
- 已有 JD 数量: {len(context.get('tracks', []))}

## 意图类型
1. **ingest_jd**: 用户上传或粘贴了 JD（职位描述）
2. **track_overview**: 用户想查看当前有哪些求职方向
3. **score_resume**: 用户想评估简历与 JD 的匹配度
4. **generate_resume**: 用户想生成/写一份新简历
5. **polish_resume**: 用户想优化/改进现有简历
6. **add_info**: 用户补充个人信息、经历或偏好

请分析用户输入，返回最可能的意图。

返回 JSON 格式：
{{
  "intent": "意图类型",
  "confidence": 0.0-1.0,
  "reasoning": "推理过程",
  "target_track_name": "目标方向名称（如果能提取）",
  "need_clarification": true/false,
  "clarify_question": "如果需要澄清，提问"
}}
"""

        # 调用 LLM
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",  # 便宜的模型
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        # 解析结果
        result = json.loads(response.content[0].text)

        return IntentDecision(
            intent=result["intent"],
            reason=result["reasoning"],
            confidence=result["confidence"],
            target_track_name=result.get("target_track_name", ""),
            need_clarification=result.get("need_clarification", False),
            clarify_question=result.get("clarify_question", "")
        )
```

#### 2.2 混合策略：规则 + LLM

```python
class HybridIntentRecognizer:
    """混合意图识别器：规则优先，LLM兜底"""

    def recognize(self, content: str, context: dict) -> IntentDecision:
        # 第一步：尝试规则匹配
        rule_decision = self._rule_match(content, context)

        if rule_decision.confidence >= 0.8:
            # 规则匹配置信度高，直接返回
            return rule_decision

        # 第二步：规则匹配不确定，使用 LLM
        llm_decision = self._llm_recognize(content, context)

        # 第三步：融合结果
        if llm_decision.confidence >= 0.7:
            return llm_decision

        # 都不确定，需要澄清
        return IntentDecision(
            intent="unknown",
            reason="规则和 LLM 都无法确定意图",
            confidence=0.0,
            need_clarification=True,
            clarify_question="请问您想做什么？可以：评分简历、生成简历、润色简历"
        )

    def _rule_match(self, content: str, context: dict) -> IntentDecision:
        """规则匹配"""
        # ... 现有的规则逻辑 ...
        pass
```

**收益**:
- ✅ 理解语义，支持更多表达
- ✅ 处理模糊意图
- ✅ 利用上下文信息
- ✅ 置信度辅助决策

**成本**:
- 单次 LLM 调用（~$0.0003，使用 Haiku）
- 延迟增加 ~200-500ms

---

### 方案 3️⃣：多意图识别（中期，3-4 周）

**目标**: 支持用户在一个请求中表达多个意图

#### 3.1 意图拆分

```python
@dataclass
class IntentDecision:
    """意图决策（支持多意图）"""
    intents: list[SingleIntent]  # 改为列表
    need_clarification: bool = False
    clarify_question: str = ""

@dataclass
class SingleIntent:
    """单个意图"""
    intent: str
    confidence: float
    target_track_name: str = ""

def recognize_multi_intent(self, content: str) -> IntentDecision:
    """识别多意图"""

    # 示例输入："帮我评分然后润色一下"
    # 识别为：[score_resume, polish_resume]

    # 使用 LLM 识别
    prompt = f"""
分析用户输入，可能包含多个意图。

用户输入: {content}

可能的意图:
- score_resume: 评分
- polish_resume: 润色
- generate_resume: 生成

返回 JSON:
{{
  "intents": [
    {{"intent": "score_resume", "confidence": 0.9}},
    {{"intent": "polish_resume", "confidence": 0.9}}
  ]
}}
"""

    result = self._call_llm(prompt)

    # 构建多步骤计划
    steps = []
    for single_intent in result["intents"]:
        if single_intent["intent"] == "score_resume":
            steps.append(PlanStep(tool_name="resume_score"))
        elif single_intent["intent"] == "polish_resume":
            steps.append(PlanStep(tool_name="resume_polish"))

    return IntentDecision(intents=result["intents"], steps=steps)
```

**收益**:
- ✅ 支持复合请求（"评分然后润色"）
- ✅ 提升用户体验（一次交互完成多个任务）
- ✅ 减少对话轮次

---

### 方案 4️⃣：上下文增强识别（中期，2-3 周）

**目标**: 利用对话历史和用户状态提升识别准确率

#### 4.1 对话历史分析

```python
class ContextAwareIntentRecognizer:
    """上下文感知的意图识别器"""

    def recognize(self, content: str, context: dict) -> IntentDecision:
        """考虑上下文的意图识别"""

        # 提取上下文特征
        features = {
            "last_intent": context.get("last_intent"),
            "last_action": context.get("last_action"),
            "conversation_turn": context.get("turn", 0),
            "user_uploaded_jd": context.get("has_jd", False),
            "user_uploaded_resume": context.get("has_resume", False),
        }

        # 规则 1: 刚上传 JD，用户说"可以"、"怎么样"，很可能是评分
        if features["last_action"] == "ingest_jd":
            if any(word in content for word in ["可以", "怎么样", "能", "通过"]):
                return IntentDecision(
                    intent="score_resume",
                    reason=f"刚上传 JD，用户询问是否可以（匹配度）",
                    confidence=0.9
                )

        # 规则 2: 刚评分，用户说"怎么改"、"优化一下"，很可能是润色
        if features["last_action"] == "score_resume":
            if any(word in content for word in ["怎么改", "优化", "改进"]):
                return IntentDecision(
                    intent="polish_resume",
                    reason=f"刚评分完，用户要求优化",
                    confidence=0.9
                )

        # 规则 3: 第 1 轮对话，用户上传简历但没有 JD
        if features["conversation_turn"] == 0 and features["user_uploaded_resume"]:
            return IntentDecision(
                intent="add_info",
                reason="用户上传了简历，需要先上传 JD 或选择方向",
                confidence=0.7,
                need_clarification=True,
                clarify_question="请上传目标 JD，或选择要投递的方向"
            )

        # 默认：使用基础识别
        return self._base_recognize(content, context)
```

#### 4.2 用户状态追踪

```python
@dataclass
class UserState:
    """用户状态"""
    has_uploaded_jd: bool = False
    has_uploaded_resume: bool = False
    active_track_id: str = ""
    last_intent: str = ""
    last_action: str = ""
    conversation_turn: int = 0
    preferred_intent: str = ""  # 从历史行为中学习的偏好

class IntentRecognizer:
    def __init__(self):
        self.user_states = {}  # user_id -> UserState

    def recognize(self, user_id: str, content: str) -> IntentDecision:
        """识别意图（考虑用户状态）"""
        state = self.user_states.get(user_id, UserState())

        # 使用状态增强识别
        decision = self._recognize_with_state(content, state)

        # 更新状态
        state.last_intent = decision.intent
        state.conversation_turn += 1
        self.user_states[user_id] = state

        return decision
```

**收益**:
- ✅ 提升识别准确率 ~15-20%
- ✅ 支持省略表达（"可以呢"、"改一下"）
- ✅ 更自然的对话体验

---

### 方案 5️⃣：意图识别评估与迭代（长期，持续）

**目标**: 建立评估体系，持续优化识别效果

#### 5.1 评估指标

```python
@dataclass
class IntentMetrics:
    """意图识别评估指标"""
    accuracy: float  # 准确率
    precision: dict[str, float]  # 各意图的精确率
    recall: dict[str, float]  # 各意图的召回率
    f1: dict[str, float]  # 各意图的 F1 分数
    confusion_matrix: dict  # 混淆矩阵

class IntentEvaluator:
    """意图识别评估器"""

    def evaluate(self, predictions: list, ground_truth: list) -> IntentMetrics:
        """评估识别效果"""
        # 计算准确率
        accuracy = sum(p == g for p, g in zip(predictions, ground_truth)) / len(predictions)

        # 计算各意图的 precision/recall/F1
        intents = set(predictions + ground_truth)
        precision = {}
        recall = {}
        f1 = {}

        for intent in intents:
            tp = sum(p == intent and g == intent for p, g in zip(predictions, ground_truth))
            fp = sum(p == intent and g != intent for p, g in zip(predictions, ground_truth))
            fn = sum(p != intent and g == intent for p, g in zip(predictions, ground_truth))

            precision[intent] = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall[intent] = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1[intent] = 2 * precision[intent] * recall[intent] / (precision[intent] + recall[intent]) \
                if (precision[intent] + recall[intent]) > 0 else 0

        # 混淆矩阵
        confusion = self._compute_confusion_matrix(predictions, ground_truth)

        return IntentMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1=f1,
            confusion_matrix=confusion
        )
```

#### 5.2 A/B 测试

```python
class IntentABTest:
    """意图识别 A/B 测试"""

    def __init__(self):
        self.version_a = RuleBasedIntentRecognizer()  # 基于规则
        self.version_b = LLMIntentRecognizer()  # 基于 LLM

    def test(self, user_id: str, content: str, context: dict) -> IntentDecision:
        """A/B 测试"""
        # 50% 用户使用 A 版本
        if hash(user_id) % 2 == 0:
            decision = self.version_a.recognize(content, context)
            decision.version = "A"
        else:
            decision = self.version_b.recognize(content, context)
            decision.version = "B"

        # 记录用于后续分析
        self.log_decision(user_id, content, decision)

        return decision
```

#### 5.3 用户反馈学习

```python
class FeedbackLearner:
    """从用户反馈中学习"""

    def collect_feedback(self, user_id: str, content: str, predicted_intent: str, feedback: str):
        """收集用户反馈"""
        # feedback: "对"/"不对"/"应该是评分"
        self.feedback_data.append({
            "user_id": user_id,
            "content": content,
            "predicted": predicted_intent,
            "feedback": feedback
        })

    def learn(self):
        """从反馈中学习，更新规则"""
        # 分析错误案例
        errors = [f for f in self.feedback_data if f["feedback"] != "对"]

        for error in errors:
            # 提取新的关键词模式
            self._extract_patterns(error["content"], error["feedback"])

        # 更新关键词词典
        self._update_keywords()
```

**收益**:
- ✅ 量化识别效果
- ✅ 持续优化识别策略
- ✅ 从用户反馈中学习

---

## 📋 优化路线图

| 阶段 | 优先级 | 方案 | 工作量 | 预期收益 |
|------|--------|------|--------|----------|
| **第 1 周** | 🔥 P0 | 扩充关键词词典 | 2-3 天 | +15% 覆盖率 |
| **第 1 周** | 🔥 P0 | 添加置信度评分 | 1-2 天 | 更好的决策依据 |
| **第 2 周** | ⭐ P1 | 混合策略（规则+LLM） | 3-5 天 | +25% 准确率 |
| **第 3 周** | ⭐ P1 | 上下文增强识别 | 3-4 天 | +20% 准确率 |
| **第 4 周** | 📈 P2 | 多意图识别 | 4-5 天 | 支持复合请求 |
| **长期** | 🚀 P3 | 评估与迭代 | 持续 | 持续优化 |

---

## 💡 实施建议

### 短期（立即实施）

1. **扩充关键词词典**
   - 收集用户真实表达（日志分析）
   - 添加同义词、缩写、错别字
   - 添加英文表达

2. **添加置信度**
   - 为每个意图决策打分
   - 低置信度时主动澄清

### 中期（2-4 周）

3. **实施混合策略**
   - 规则优先（快速、便宜）
   - LLM 兜底（准确、灵活）

4. **增强上下文感知**
   - 利用对话历史
   - 追踪用户状态

### 长期（持续）

5. **建立评估体系**
   - 定义评估指标
   - 收集标注数据
   - A/B 测试

6. **持续优化**
   - 分析错误案例
   - 从用户反馈学习
   - 迭代关键词和规则

---

## 🎯 关键决策点

### 是否引入 LLM？

| 方面 | 规则引擎 | 混合策略 | 纯 LLM |
|------|----------|----------|--------|
| **成本** | 最低 | 低（~10% 用 LLM） | 高 |
| **准确率** | 70-80% | 85-95% | 90-98% |
| **延迟** | <10ms | ~200ms | ~500ms |
| **可维护性** | 高（显式规则） | 中 | 低（黑盒） |
| **推荐场景** | 简单项目 | ✅ **推荐** | 复杂对话 |

**建议**: 采用**混合策略**
- 80% 请求用规则（快速、便宜）
- 20% 请求用 LLM（兜底、准确）

### 如何平衡准确率与成本？

```python
# 成本优化策略
def optimize_cost(content: str, context: dict) -> IntentDecision:
    # 1. 高置信度规则匹配（免费）
    rule_decision = rule_match(content)
    if rule_decision.confidence >= 0.8:
        return rule_decision

    # 2. 历史相似案例（免费）
    similar = find_similar_historical_case(content)
    if similar and similar.confidence >= 0.8:
        return similar.decision

    # 3. LLM 识别（~$0.0003）
    return llm_recognize(content, context)
```

---

## 📖 参考资源

- [Intent Recognition Best Practices](https://dialogue.com/intent-recognition/)
- [Hybrid Approaches for NLU](https://arxiv.org/abs/2104.06597)
- [Context-Aware Intent Detection](https://aclanthology.org/2021.acl-long.57/)
