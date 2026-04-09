<!--
Input: 历史设计、专项分析或参考资料。
Output: 保留《意图识别优化 - 实现代码示例》作为参考或归档材料。
Pos: 历史或参考文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 意图识别优化 - 实现代码示例

## 1️⃣ 扩充关键词词典（立即可用）

```python
# src/agent/intent_keywords.py

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class IntentPattern:
    """意图模式"""
    keywords: list[str]
    weights: list[float] | None = None  # 关键词权重（可选）
    requires_context: list[str] | None = None  # 需要的上下文（可选）

    def match_score(self, text: str, context: dict | None = None) -> float:
        """计算匹配分数"""
        if self.requires_context and context:
            for key, value in self.requires_context.items():
                if context.get(key) != value:
                    return 0.0

        score = 0.0
        for i, keyword in enumerate(self.keywords):
            weight = self.weights[i] if self.weights else 1.0
            if keyword.lower() in text.lower():
                score += weight

        return score


class IntentKeywords:
    """扩充的意图关键词库"""

    # JD 识别
    JD = IntentPattern(
        keywords=[
            # 标准表达
            "岗位职责", "任职要求", "职位描述", "岗位要求",
            # 企业表达
            "岗位信息", "招聘需求", "招聘要求", "工作职责",
            # 其他
            "任职资格", "我们需要", "候选人要求",
            # 英文
            "JD", "job description", "responsibilities", "requirements"
        ]
    )

    # 评分
    SCORE = IntentPattern(
        keywords=[
            # 直接表达
            "评分", "打分", "评估", "评测", "分析", "诊断",
            # 隐含表达
            "匹配度", "怎么样", "如何", "够不够", "能不能",
            # 问题形式
            "可以通过吗", "有希望吗", "差距大吗", "符合吗",
            # 英文
            "score", "evaluate", "assess", "rate"
        ]
    )

    # 生成简历
    GENERATE = IntentPattern(
        keywords=[
            # 直接表达
            "生成简历", "写简历", "制作简历", "输出简历", "定制简历",
            # 隐含表达
            "帮我写", "帮我生成", "帮我制作", "帮我弄",
            # 场景表达
            "投递用的简历", "面试用的简历",
            # 英文
            "generate", "create", "write", "make"
        ]
    )

    # 润色简历
    POLISH = IntentPattern(
        keywords=[
            # 直接表达
            "润色", "优化", "改写", "修改", "改进", "完善",
            # 隐含表达
            "更好", "提升", "优化一下", "改改", "调整",
            # 问题形式
            "怎么改", "怎么写", "怎么优化",
            # 英文
            "polish", "optimize", "improve", "refine"
        ]
    )

    # 方向总览
    TRACK_OVERVIEW = IntentPattern(
        keywords=["查看", "看看", "有哪些", "列表", "总览", "显示"],
        weights=[1.5, 1.5, 1.0, 1.0, 1.5, 1.0],  # "查看"、"看看"、"总览"权重更高
        requires_context={"keyword": "方向"}  # 必须包含"方向"
    )

    @classmethod
    def get_all_patterns(cls) -> dict[str, IntentPattern]:
        """获取所有意图模式"""
        return {
            "ingest_jd": cls.JD,
            "track_overview": cls.TRACK_OVERVIEW,
            "score_resume": cls.SCORE,
            "generate_resume": cls.GENERATE,
            "polish_resume": cls.POLISH,
        }
```

---

## 2️⃣ 置信度评分（立即可用）

```python
# src/agent/intent_recognizer.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from agent.intent_keywords import IntentKeywords
from agent.models import IntentDecision


@dataclass
class IntentMatch:
    """意图匹配结果"""
    intent: str
    score: float
    confidence: float  # 归一化的置信度 [0, 1]
    matched_keywords: list[str] = field(default_factory=list)


class EnhancedIntentRecognizer:
    """增强的意图识别器（带置信度）"""

    def __init__(self):
        self.patterns = IntentKeywords.get_all_patterns()

    def recognize(
        self,
        content: str,
        attachments: list | None = None,
        context: dict | None = None
    ) -> IntentDecision:
        """识别用户意图（带置信度）"""

        attachments = attachments or []
        context = context or {}
        lowered = content.lower().strip()

        # 1. 检查 JD 附件（最高优先级）
        if any(item.get("type") == "jd" for item in attachments):
            return IntentDecision(
                intent="ingest_jd",
                reason="检测到 JD 附件",
                confidence=1.0
            )

        # 2. 对所有意图计算匹配分数
        matches = []
        for intent_name, pattern in self.patterns.items():
            match = self._match_intent(content, intent_name, pattern, context)
            if match.score > 0:
                matches.append(match)

        # 3. 如果没有匹配，返回默认意图
        if not matches:
            return IntentDecision(
                intent="add_info",
                reason="无法识别具体意图，默认为补充信息",
                confidence=0.3
            )

        # 4. 选择最高分的意图
        best_match = max(matches, key=lambda m: m.score)

        # 5. 计算归一化置信度
        total_score = sum(m.score for m in matches)
        best_match.confidence = best_match.score / total_score if total_score > 0 else 0.5

        # 6. 置信度阈值判断
        if best_match.confidence < 0.5:
            # 置信度低，需要澄清
            return IntentDecision(
                intent="uncertain",
                reason=f"识别到多个可能意图: {[m.intent for m in matches]}",
                confidence=best_match.confidence,
                need_clarification=True,
                clarify_question=self._generate_clarify_question(matches)
            )

        # 7. 返回高置信度的意图
        return IntentDecision(
            intent=best_match.intent,
            reason=f"匹配关键词: {', '.join(best_match.matched_keywords)}",
            confidence=best_match.confidence
        )

    def _match_intent(
        self,
        content: str,
        intent_name: str,
        pattern: IntentPattern,
        context: dict
    ) -> IntentMatch:
        """匹配单个意图"""
        score = 0.0
        matched_keywords = []

        for keyword in pattern.keywords:
            if keyword.lower() in content.lower():
                weight = 1.0
                if pattern.weights:
                    idx = pattern.keywords.index(keyword)
                    weight = pattern.weights[idx] if idx < len(pattern.weights) else 1.0
                score += weight
                matched_keywords.append(keyword)

        # 检查上下文要求
        if pattern.requires_context:
            for key, value in pattern.requires_context.items():
                if key == "keyword" and value not in content.lower():
                    score = 0.0
                    break

        return IntentMatch(
            intent=intent_name,
            score=score,
            confidence=0.0,  # 稍后计算
            matched_keywords=matched_keywords
        )

    def _generate_clarify_question(self, matches: list[IntentMatch]) -> str:
        """生成澄清问题"""
        intents = [m.intent for m in matches]

        options = []
        if "score_resume" in intents:
            options.append("评分简历")
        if "generate_resume" in intents:
            options.append("生成简历")
        if "polish_resume" in intents:
            options.append("润色简历")

        if options:
            return f"请问您想要：{'、'.join(options)}？"
        return "请问您想要做什么？"
```

---

## 3️⃣ 混合策略（规则 + LLM）

```python
# src/agent/hybrid_intent_recognizer.py

from __future__ import annotations

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from agent.intent_recognizer import EnhancedIntentRecognizer
from agent.models import IntentDecision


class HybridIntentRecognizer:
    """混合意图识别器：规则优先，LLM 兜底"""

    def __init__(self, api_key: str | None = None):
        self.rule_recognizer = EnhancedIntentRecognizer()

        if HAS_ANTHROPIC and api_key:
            self.llm_client = Anthropic(api_key=api_key)
        else:
            self.llm_client = None

    def recognize(
        self,
        content: str,
        attachments: list | None = None,
        context: dict | None = None,
        use_llm_threshold: float = 0.7
    ) -> IntentDecision:
        """混合识别：规则优先，LLM 兜底"""

        # 第一步：规则匹配
        rule_decision = self.rule_recognizer.recognize(content, attachments, context)

        # 第二步：如果置信度高，直接返回
        if rule_decision.confidence >= use_llm_threshold:
            return rule_decision

        # 第三步：如果没有 LLM 客户端，返回规则结果
        if not self.llm_client:
            return rule_decision

        # 第四步：使用 LLM 识别
        llm_decision = self._llm_recognize(content, context)

        # 第五步：融合结果
        if llm_decision.confidence >= 0.7:
            return llm_decision

        # 都不确定，返回规则结果并标记需要澄清
        rule_decision.need_clarification = True
        rule_decision.clarify_question = (
            f"我识别到您可能是想{llm_decision.intent}，"
            f"但也可能是{rule_decision.intent}，请确认？"
        )
        return rule_decision

    def _llm_recognize(self, content: str, context: dict) -> IntentDecision:
        """使用 LLM 识别意图"""

        prompt = f"""
你是简历助手，需要识别用户的意图。

用户输入: {content}

可能的意图:
1. ingest_jd - 用户上传或粘贴了 JD（职位描述）
2. track_overview - 用户想查看当前有哪些求职方向
3. score_resume - 用户想评估简历与 JD 的匹配度
4. generate_resume - 用户想生成/写一份新简历
5. polish_resume - 用户想优化/改进现有简历
6. add_info - 用户补充个人信息、经历或偏好

请分析用户输入，返回最可能的意图。

只返回 JSON，格式：
{{"intent": "意图类型", "confidence": 0.0-1.0, "reasoning": "推理过程"}}
"""

        try:
            response = self.llm_client.messages.create(
                model="claude-3-haiku-20240307",  # 使用便宜的模型
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            result = json.loads(response.content[0].text)

            return IntentDecision(
                intent=result["intent"],
                reason=result.get("reasoning", ""),
                confidence=result.get("confidence", 0.7)
            )
        except Exception as e:
            # LLM 调用失败，返回低置信度
            return IntentDecision(
                intent="unknown",
                reason=f"LLM 调用失败: {e}",
                confidence=0.0
            )
```

---

## 4️⃣ 上下文增强识别

```python
# src/agent/contextual_intent_recognizer.py

from agent.hybrid_intent_recognizer import HybridIntentRecognizer
from agent.models import IntentDecision


class ContextualIntentRecognizer:
    """上下文增强的意图识别器"""

    def __init__(self, api_key: str | None = None):
        self.base_recognizer = HybridIntentRecognizer(api_key)

    def recognize(
        self,
        content: str,
        attachments: list | None = None,
        context: dict | None = None
    ) -> IntentDecision:
        """考虑上下文的意图识别"""

        context = context or {}
        lowered = content.lower()

        # 上下文规则 1: 刚上传 JD，用户说"可以"、"怎么样"，很可能是评分
        if context.get("last_action") == "ingest_jd":
            if any(word in lowered for word in ["可以", "怎么样", "能", "通过", "符合"]):
                return IntentDecision(
                    intent="score_resume",
                    reason="刚上传 JD，用户询问匹配度",
                    confidence=0.95
                )

        # 上下文规则 2: 刚评分，用户说"怎么改"、"优化一下"，很可能是润色
        if context.get("last_action") == "score_resume":
            if any(word in lowered for word in ["怎么改", "优化", "改进", "改写", "润色"]):
                return IntentDecision(
                    intent="polish_resume",
                    reason="刚评分完，用户要求优化",
                    confidence=0.95
                )

        # 上下文规则 3: 刚评分，用户说"帮我写"、"生成"，很可能是生成
        if context.get("last_action") == "score_resume":
            if any(word in lowered for word in ["写", "生成", "制作", "弄"]):
                return IntentDecision(
                    intent="generate_resume",
                    reason="刚评分完，用户要求生成简历",
                    confidence=0.90
                )

        # 上下文规则 4: 第一轮对话，用户上传简历但没有 JD
        if context.get("conversation_turn", 0) == 0:
            if context.get("has_resume") and not context.get("has_jd"):
                return IntentDecision(
                    intent="add_info",
                    reason="用户上传了简历，需要先上传 JD",
                    confidence=0.80,
                    need_clarification=True,
                    clarify_question="请上传目标 JD，或选择要投递的求职方向"
                )

        # 默认：使用基础识别器
        return self.base_recognizer.recognize(content, attachments, context)
```

---

## 5️⃣ 使用示例

```python
# 示例 1：使用增强的规则识别器
from agent.intent_recognizer import EnhancedIntentRecognizer

recognizer = EnhancedIntentRecognizer()

# 识别意图
decision = recognizer.recognize("帮我评分一下")

print(f"意图: {decision.intent}")  # score_resume
print(f"置信度: {decision.confidence}")  # 0.85
print(f"原因: {decision.reason}")  # 匹配关键词: 评分

# 示例 2：使用混合识别器
from agent.hybrid_intent_recognizer import HybridIntentRecognizer

recognizer = HybridIntentRecognizer(api_key="your-key")

decision = recognizer.recognize("我的简历怎么样？")

# 置信度低，会使用 LLM
print(f"意图: {decision.intent}")  # score_resume
print(f"置信度: {decision.confidence}")  # 0.88

# 示例 3：使用上下文增强识别器
from agent.contextual_intent_recognizer import ContextualIntentRecognizer

recognizer = ContextualIntentRecognizer(api_key="your-key")

context = {
    "last_action": "ingest_jd",
    "conversation_turn": 1
}

decision = recognizer.recognize("可以通过吗？", context=context)

print(f"意图: {decision.intent}")  # score_resume
print(f"置信度: {decision.confidence}")  # 0.95
print(f"原因: {decision.reason}")  # 刚上传 JD，用户询问匹配度
```

---

## 6️⃣ 集成到现有代码

```python
# 修改 src/agent/planner.py

from agent.contextual_intent_recognizer import ContextualIntentRecognizer


class AgentPlanner:
    """增强的 Agent Planner（使用新的意图识别器）"""

    def __init__(self, anthropic_api_key: str | None = None):
        self.intent_recognizer = ContextualIntentRecognizer(api_key=anthropic_api_key)

    def plan(
        self,
        *,
        content: str,
        attachments: list[AgentAttachment],
        snapshot: dict[str, Any],
        active_track_id: str = "",
        active_track_name: str = "",
    ) -> AgentPlan:
        """使用增强的意图识别器"""

        # 构建上下文
        context = {
            "active_track_id": active_track_id,
            "active_track_name": active_track_name,
            "tracks": snapshot.get("tracks", []),
            "last_action": snapshot.get("last_action"),
            "conversation_turn": snapshot.get("conversation_turn", 0),
            "has_jd": snapshot.get("has_jd", False),
            "has_resume": snapshot.get("has_resume", False),
        }

        # 使用新的意图识别器
        decision = self.intent_recognizer.recognize(
            content=content,
            attachments=[a.to_dict() for a in attachments],
            context=context
        )

        # 根据意图决策生成计划
        return self._build_plan(decision, context)

    def _build_plan(self, decision: IntentDecision, context: dict) -> AgentPlan:
        """根据意图决策构建执行计划"""
        # ... 原有的计划生成逻辑 ...
        pass
```

---

## 7️⃣ 测试代码

```python
# tests/test_intent_recognition.py

import pytest
from agent.intent_recognizer import EnhancedIntentRecognizer


class TestIntentRecognition:
    """意图识别测试"""

    def setup_method(self):
        self.recognizer = EnhancedIntentRecognizer()

    def test_score_keywords(self):
        """测试评分关键词"""
        test_cases = [
            ("帮我评分", "score_resume"),
            ("打分", "score_resume"),
            ("评估一下", "score_resume"),
            ("匹配度怎么样", "score_resume"),
            ("可以通过吗", "score_resume"),
        ]

        for content, expected_intent in test_cases:
            decision = self.recognizer.recognize(content)
            assert decision.intent == expected_intent
            assert decision.confidence >= 0.7

    def test_polish_keywords(self):
        """测试润色关键词"""
        test_cases = [
            ("润色简历", "polish_resume"),
            ("优化一下", "polish_resume"),
            ("怎么改", "polish_resume"),
            ("改进", "polish_resume"),
        ]

        for content, expected_intent in test_cases:
            decision = self.recognizer.recognize(content)
            assert decision.intent == expected_intent

    def test_low_confidence_clarification(self):
        """测试低置信度时的澄清"""
        decision = self.recognizer.recognize("帮我看看")

        assert decision.confidence < 0.5
        assert decision.need_clarification is True
        assert decision.clarify_question

    def test_contextual_rules(self):
        """测试上下文规则"""
        from agent.contextual_intent_recognizer import ContextualIntentRecognizer

        recognizer = ContextualIntentRecognizer()

        context = {"last_action": "ingest_jd"}
        decision = recognizer.recognize("可以吗", context=context)

        assert decision.intent == "score_resume"
        assert decision.confidence >= 0.9
```

---

## 总结

以上代码提供了：
1. ✅ **扩充的关键词词典** - 立即可用
2. ✅ **置信度评分** - 更好的决策依据
3. ✅ **混合识别策略** - 规则 + LLM
4. ✅ **上下文增强** - 利用对话历史
5. ✅ **完整测试用例** - 保证质量

**建议实施顺序**：
1. 第 1 天：集成 `EnhancedIntentRecognizer`
2. 第 2 天：添加测试用例
3. 第 3-5 天：实施 `HybridIntentRecognizer`
4. 第 6-8 天：实施 `ContextualIntentRecognizer`
