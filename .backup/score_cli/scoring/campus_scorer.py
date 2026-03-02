"""Campus recruitment scorer v2.1 - mixed scoring approach.

This module implements the campus recruitment scoring system with:
- Rule-based hard metrics (35-50% weight)
- LLM-based soft metrics (50-65% weight)
- Two LLM calls: (1) Parameter extraction + soft scoring, (2) Report generation
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from .models import (
    HardMetricsScore,
    ScoreReport,
    SoftMetricDimension,
    SoftMetricsScore,
)


def _get_default_model() -> str:
    """Get default LLM model from env or default."""
    return os.getenv("LLM_MODEL", "claude-3.5-sonnet")


def _get_llm_client():
    """Get LLM client based on available libraries."""
    # Try anthropic first
    try:
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            return Anthropic(api_key=api_key)
    except ImportError:
        pass

    # Try openai
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return OpenAI(api_key=api_key)
    except ImportError:
        pass

    return None


@dataclass
class ExtractionResult:
    """Result from first LLM call - parameter extraction and soft scoring."""

    # Hard metrics parameters
    internship_params: dict[str, Any] = field(default_factory=dict)
    project_params: dict[str, Any] = field(default_factory=dict)
    technical_practice_params: dict[str, Any] = field(default_factory=dict)
    education_params: dict[str, Any] = field(default_factory=dict)
    major_params: dict[str, Any] = field(default_factory=dict)
    gpa_params: dict[str, Any] = field(default_factory=dict)
    competition_params: dict[str, Any] = field(default_factory=dict)
    english_params: dict[str, Any] = field(default_factory=dict)
    github_params: dict[str, Any] = field(default_factory=dict)
    stability_params: dict[str, Any] = field(default_factory=dict)

    # Soft metrics scores
    soft_metrics: dict[str, Any] = field(default_factory=dict)

    # JD and resume summary
    jd_summary: str = ""
    resume_summary: str = ""


class CampusScorerV21:
    """Campus recruitment scorer v2.1 with unified soft metrics."""

    # Hard metrics weights
    HARD_WEIGHTS = {
        "internship": 0.25,
        "project": 0.20,
        "technical_practice": 0.15,
        "education": 0.10,
        "major": 0.10,
        "gpa": 0.05,
        "competition": 0.05,
        "english": 0.05,
        "github": 0.03,
        "stability": 0.02,
    }

    # Soft metrics weights
    SOFT_WEIGHTS = {
        "learning_ability": 0.25,
        "execution": 0.25,
        "communication": 0.15,
        "data_awareness": 0.15,
        "stability": 0.10,
        "adaptability": 0.10,
    }

    def __init__(self, *, model: str | None = None):
        """Initialize scorer with optional model override."""
        self.model = model or _get_default_model()
        self._client = _get_llm_client()

    def score(self, jd: str, resume: str, *, rule_weight: float = 0.4) -> ScoreReport:
        """Score a resume against a JD.

        Args:
            jd: Job description text
            resume: Resume text
            rule_weight: Weight for rule-based scoring (0.35-0.5 recommended)

        Returns:
            Complete score report
        """
        # Step 1: Extract parameters and score soft metrics
        extraction = self._extract_and_soft_score(jd, resume)

        # Step 2: Calculate hard metrics score
        hard_score = self._calculate_hard_metrics(extraction)

        # Step 3: Build soft metrics score from extraction
        soft_score = self._build_soft_metrics(extraction)

        # Step 4: Combine scores
        soft_weight = 1.0 - rule_weight
        final_score = hard_score.total_score * rule_weight + soft_score.total_score * soft_weight

        # Step 5: Generate comprehensive report
        report = self._generate_report(
            jd=jd,
            resume=resume,
            extraction=extraction,
            hard_score=hard_score,
            soft_score=soft_score,
            final_score=final_score,
        )

        return report

    def _extract_and_soft_score(self, jd: str, resume: str) -> ExtractionResult:
        """First LLM call: Extract parameters and score soft metrics."""
        prompt = self._build_extraction_prompt(jd, resume)

        response = self._call_llm(prompt)
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Fallback to minimal extraction on error
            return ExtractionResult(jd_summary=jd[:100], resume_summary=resume[:100])

        result = ExtractionResult(
            jd_summary=data.get("jd_summary", jd[:100]),
            resume_summary=data.get("resume_summary", resume[:100]),
        )

        # Parse hard metrics parameters
        result.internship_params = data.get("internship_requirement", {})
        result.project_params = data.get("project_requirement", {})
        result.technical_practice_params = data.get("technical_practice", {})
        result.education_params = data.get("education_level", {})
        result.major_params = data.get("major_requirement", {})
        result.gpa_params = data.get("gpa_requirement", {})
        result.competition_params = data.get("competition_preference", {})
        result.english_params = data.get("english_requirement", {})
        result.github_params = data.get("github_preference", {})
        result.stability_params = data.get("availability", {})

        # Parse soft metrics
        result.soft_metrics = data.get("soft_metrics", {})

        return result

    def _calculate_hard_metrics(self, extraction: ExtractionResult) -> HardMetricsScore:
        """Calculate hard metrics score using rule-based logic."""
        score = HardMetricsScore()

        # Internship (25%)
        score.internship_score = self._score_internship(extraction.internship_params)
        score.evidence["internship"] = self._get_internship_evidence(extraction.internship_params)

        # Project (20%)
        score.project_score = self._score_project(extraction.project_params)
        score.evidence["project"] = self._get_project_evidence(extraction.project_params)

        # Technical practice (15%)
        score.technical_practice_score = self._score_technical_practice(extraction.technical_practice_params)
        score.evidence["technical_practice"] = self._get_technical_practice_evidence(extraction.technical_practice_params)

        # Education (10%)
        score.education_score = self._score_education(extraction.education_params)
        score.evidence["education"] = self._get_education_evidence(extraction.education_params)

        # Major (10%)
        score.major_score = self._score_major(extraction.major_params)
        score.evidence["major"] = self._get_major_evidence(extraction.major_params)

        # GPA (5%)
        score.gpa_score = self._score_gpa(extraction.gpa_params)
        score.evidence["gpa"] = self._get_gpa_evidence(extraction.gpa_params)

        # Competition (5%)
        score.competition_score = self._score_competition(extraction.competition_params)
        score.evidence["competition"] = self._get_competition_evidence(extraction.competition_params)

        # English (5%)
        score.english_score = self._score_english(extraction.english_params)
        score.evidence["english"] = self._get_english_evidence(extraction.english_params)

        # GitHub (3%)
        score.github_score = self._score_github(extraction.github_params)
        score.evidence["github"] = self._get_github_evidence(extraction.github_params)

        # Stability (2%)
        score.stability_score = self._score_stability(extraction.stability_params)
        score.evidence["stability"] = self._get_stability_evidence(extraction.stability_params)

        # Calculate total (weighted sum, then normalized to 0-100)
        score.total_score = (
            score.internship_score * 0.25
            + score.project_score * 0.20
            + score.technical_practice_score * 0.15
            + score.education_score * 0.10
            + score.major_score * 0.10
            + score.gpa_score * 0.05
            + score.competition_score * 0.05
            + score.english_score * 0.05
            + score.github_score * 0.03
            + score.stability_score * 0.02
        )

        return score

    def _build_soft_metrics(self, extraction: ExtractionResult) -> SoftMetricsScore:
        """Build soft metrics score from extraction result."""
        soft_data = extraction.soft_metrics
        if not soft_data:
            return SoftMetricsScore()

        score = SoftMetricsScore()

        # Parse dimension scores
        dimensions_map = {
            "learning_ability": "learning_ability",
            "execution": "execution",
            "communication": "communication",
            "data_awareness": "data_awareness",
            "stability": "stability",
            "adaptability": "adaptability",
        }

        for eng_name, soft_key in dimensions_map.items():
            dim_data = soft_data.get(soft_key, {})
            value = dim_data.get("score", 60)
            setattr(score, eng_name, value)

            # Add dimension details
            score.dimensions.append(
                SoftMetricDimension(
                    dimension=dim_data.get("dimension", eng_name),
                    score=value,
                    reasoning=dim_data.get("reasoning", ""),
                    evidence=dim_data.get("evidence", ""),
                    evidence_level=dim_data.get("evidence_level", ""),
                )
            )

        # Calculate total
        score.total_score = (
            score.learning_ability * 0.25
            + score.execution * 0.25
            + score.communication * 0.15
            + score.data_awareness * 0.15
            + score.stability * 0.10
            + score.adaptability * 0.10
        )

        # Parse strengths and weaknesses
        score.strengths = soft_data.get("strengths", [])
        score.weaknesses = soft_data.get("weaknesses", [])

        return score

    def _generate_report(
        self,
        jd: str,
        resume: str,
        extraction: ExtractionResult,
        hard_score: HardMetricsScore,
        soft_score: SoftMetricsScore,
        final_score: float,
    ) -> ScoreReport:
        """Generate comprehensive report with LLM."""
        prompt = self._build_report_prompt(
            jd=jd,
            resume=resume,
            extraction=extraction,
            hard_score=hard_score,
            soft_score=soft_score,
            final_score=final_score,
        )

        response = self._call_llm(prompt)
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Fallback to simple report
            data = {}

        report = ScoreReport(
            jd_summary=extraction.jd_summary,
            resume_summary=extraction.resume_summary,
            hard_metrics=hard_score,
            soft_metrics=soft_score,
            final_score=final_score,
        )

        # Parse match level and suggestion
        if final_score >= 75:
            report.match_level = "high"
            report.suggestion = "可直接投递"
        elif final_score >= 50:
            report.match_level = "medium"
            report.suggestion = "建议补充后投递"
        else:
            report.match_level = "low"
            report.suggestion = "需风险确认后投递"
            report.risk_warning = "低匹配度，建议谨慎投递。可先提升经历后再投递，或确认风险后继续。"

        # Parse improvements
        if final_score >= 70:
            report.quick_improvements = data.get("quick_improvements", self._default_quick_improvements(soft_score))
        else:
            report.quick_improvements = data.get("quick_improvements", self._default_quick_improvements(soft_score))
            report.long_term_improvements = data.get("long_term_improvements", self._default_long_term_improvements())

        return report

    def _build_extraction_prompt(self, jd: str, resume: str) -> str:
        """Build prompt for parameter extraction and soft scoring."""
        return f"""你是一个校招简历评估专家。请分析以下 JD 和简历，提取关键信息并进行软性指标评分。

## JD
{jd}

## 简历
{resume}

请按以下 JSON 格式输出：

{{
  "jd_summary": "JD 的简要总结（50字以内）",
  "resume_summary": "简历的简要总结（50字以内）",
  "internship_requirement": {{
    "required": true/false,
    "minimum_count": 数量,
    "preferred_companies": ["大厂", "独角兽"],
    "present": true/false,
    "count": 实习段数,
    "companies": ["公司1", "公司2"]
  }},
  "project_requirement": {{
    "required": true/false,
    "minimum_count": 数量,
    "present": true/false,
    "count": 项目数量,
    "project_types": ["完整项目", "课程设计", "个人项目"],
    "descriptions": ["项目1描述", "项目2描述"]
  }},
  "technical_practice": {{
    "required_techs": ["技术1", "技术2"],
    "found_techs": ["找到的技术"],
    "tech_stack_match": "完全匹配/部分匹配/不匹配"
  }},
  "education_level": {{
    "value": "985/211/双非/海外",
    "school_name": "学校名称"
  }},
  "major_requirement": {{
    "target_majors": ["目标专业"],
    "actual_major": "实际专业",
    "match": "完全对口/相关/跨专业"
  }},
  "gpa_requirement": {{
    "gpa": GPA分数,
    "ranking": "前10%/前30%/前50%/其他"
  }},
  "competition_preference": {{
    "has_competition": true/false,
    "level": "国际级/国家级/省级/校级",
    "awards": ["奖项1", "奖项2"]
  }},
  "english_requirement": {{
    "certificate": "雅思/托福/六级/无",
    "score": 分数
  }},
  "github_preference": {{
    "has_github": true/false,
    "active": true/false,
    "repos": ["仓库1", "仓库2"]
  }},
  "availability": {{
    "available_days": 可实习天数,
    "months": 可实习月数
  }},
  "soft_metrics": {{
    "learning_ability": {{
      "dimension": "学习能力",
      "score": 0-100分数,
      "reasoning": "评分理由",
      "evidence": "证据",
      "evidence_level": "100分标准/80分标准/60分标准/40分标准"
    }},
    "execution": {{
      "dimension": "执行能力",
      "score": 0-100分数,
      "reasoning": "评分理由",
      "evidence": "证据",
      "evidence_level": "100分标准/80分标准/60分标准/40分标准"
    }},
    "communication": {{
      "dimension": "沟通表达",
      "score": 0-100分数,
      "reasoning": "评分理由",
      "evidence": "证据",
      "evidence_level": "100分标准/70分标准/50分标准/40分标准"
    }},
    "data_awareness": {{
      "dimension": "数据意识",
      "score": 0-100分数,
      "reasoning": "评分理由",
      "evidence": "证据",
      "evidence_level": "100分标准/80分标准/60分标准/40分标准"
    }},
    "stability": {{
      "dimension": "稳定性",
      "score": 0-100分数,
      "reasoning": "评分理由",
      "evidence": "证据",
      "evidence_level": "100分标准/70分标准/40分标准"
    }},
    "adaptability": {{
      "dimension": "适配度",
      "score": 0-100分数,
      "reasoning": "评分理由",
      "evidence": "证据",
      "evidence_level": "100分标准/70分标准/40分标准"
    }},
    "strengths": [{{"dimension": "维度名", "reason": "原因"}}],
    "weaknesses": [{{"dimension": "维度名", "reason": "原因"}}]
  }}
}}

## 软性指标评分标准

### 学习能力（25%）
- 100分：快速掌握多项新技能（3个月3项新技能，自学难度高的技术）
- 80分：正常掌握新技能（按计划学习，在项目中应用）
- 60分：较慢掌握新技能（学习时间比预期长，需要额外指导）
- 40分：学习困难（技能掌握不扎实，需要反复指导）

### 执行能力（25%）
- 100分：主导完成完整项目（从0到1完成项目上线，独立负责核心模块）
- 80分：参与完成项目（参与项目并负责重要部分，独立完成分配任务）
- 60分：辅助完成项目（协助团队完成支持工作，按指令完成任务）
- 40分：只有想法未落地（提出想法但未实施，参与讨论但无产出）

### 沟通表达（15%）
- 100分：表达清晰，逻辑严密（项目描述清晰，回答问题有条理）
- 70分：表达基本清晰（能说明白项目内容，逻辑基本通顺）
- 50分：表达一般（描述不够清晰，逻辑有些混乱）
- 40分：表达混乱（说不清楚做了什么，逻辑混乱）

### 数据意识（15%）
- 100分：量化成果，用数据指导决策（将留存率提升30%，A/B测试数据显示方案A更好）
- 80分：有数据意识，偶尔用数据（提到一些数据，但不够深入）
- 60分：提到数据但不够深入（说效果很好但无具体数据）
- 40分：完全没有数据意识（全部是定性描述，无量化思维）

### 稳定性（10%）
- 100分：职业规划清晰，长期意愿（希望在XX领域深耕，3-5年职业规划明确）
- 70分：基本稳定，短期意愿（愿意先尝试这个方向）
- 40分：不稳定，频繁跳方向（短期内多次换方向，职业目标模糊）

### 适配度（10%）
- 100分：高度匹配，价值观契合（个人兴趣与岗位高度契合，对公司文化有了解）
- 70分：基本匹配，可以适应（具备岗位要求的能力，愿意学习）
- 40分：不太匹配，需要调整（兴趣不匹配，能力明显不足）

只返回 JSON，不要返回其他内容。
"""

    def _build_report_prompt(
        self,
        jd: str,
        resume: str,
        extraction: ExtractionResult,
        hard_score: HardMetricsScore,
        soft_score: SoftMetricsScore,
        final_score: float,
    ) -> str:
        """Build prompt for comprehensive report generation."""
        return f"""基于以下评分结果，生成改进建议。

## 硬性指标评分
总分: {hard_score.total_score:.1f}/100

- 实习经历: {hard_score.internship_score:.0f}/100
- 项目经历: {hard_score.project_score:.0f}/100
- 技术实践: {hard_score.technical_practice_score:.0f}/100
- 学历层次: {hard_score.education_score:.0f}/100
- 专业对口: {hard_score.major_score:.0f}/100

## 软性能力评分
总分: {soft_score.total_score:.1f}/100

- 学习能力: {soft_score.learning_ability:.0f}/100
- 执行能力: {soft_score.execution:.0f}/100
- 沟通表达: {soft_score.communication:.0f}/100
- 数据意识: {soft_score.data_awareness:.0f}/100
- 稳定性: {soft_score.stability:.0f}/100
- 适配度: {soft_score.adaptability:.0f}/100

## 总分
{final_score:.1f}/100

## 优势
{json.dumps(soft_score.strengths, ensure_ascii=False, indent=2)}

## 劣势
{json.dumps(soft_score.weaknesses, ensure_ascii=False, indent=2)}

请按以下 JSON 格式返回改进建议：

{{
  "quick_improvements": [
    "立即可以改进的建议1",
    "立即可以改进的建议2"
  ],
  "long_term_improvements": [
    "长期提升建议1",
    "长期提升建议2"
  ]
}}

注意：
- 如果总分 >= 70，只返回 quick_improvements（立即改进建议）
- 如果总分 < 70，同时返回 quick_improvements 和 long_term_improvements
- 改进建议要具体可操作，不要泛泛而谈

只返回 JSON，不要返回其他内容。
"""

    def _call_llm(self, prompt: str) -> str:
        """Call LLM and return response."""
        if self._client is None:
            # Return mock response for testing
            return '{"jd_summary": "Mock JD", "resume_summary": "Mock resume", "soft_metrics": {"learning_ability": {"dimension": "学习能力", "score": 70, "reasoning": "Mock", "evidence": "Mock", "evidence_level": "80分标准"}, "execution": {"dimension": "执行能力", "score": 70}, "communication": {"dimension": "沟通表达", "score": 70}, "data_awareness": {"dimension": "数据意识", "score": 70}, "stability": {"dimension": "稳定性", "score": 70}, "adaptability": {"dimension": "适配度", "score": 70}, "strengths": [], "weaknesses": []}}'

        # Try Anthropic
        try:
            from anthropic import Anthropic

            if isinstance(self._client, Anthropic):
                response = self._client.messages.create(
                    model="claude-3-5-sonnet-20241022" if "sonnet" in self.model else "claude-3-opus-20240229",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
        except Exception:
            pass

        # Try OpenAI
        try:
            from openai import OpenAI

            if isinstance(self._client, OpenAI):
                response = self._client.chat.completions.create(
                    model="gpt-4o" if "gpt-4" in self.model else "gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content
        except Exception:
            pass

        return '{"error": "LLM call failed"}'

    # Hard metrics scoring methods

    def _score_internship(self, params: dict[str, Any]) -> float:
        """Score internship: 一线大厂=100, 独角兽=85, 中型=70, 初创=50, 无=20."""
        if not params.get("present", False):
            return 20.0

        companies = params.get("companies", [])
        if not companies:
            return 20.0

        # Top tier: 字节跳动, 腾讯, 阿里, 美团, 百度, 京东, 拼多多, 抖音, 小米等
        top_tier = {"字节跳动", "腾讯", "阿里", "阿里巴巴", "美团", "百度", "京东", "拼多多", "抖音", "小米", "华为", "网易", "携程", "哔哩哔哩", "bilibili"}
        # Unicorn: 知名独角兽
        unicorn = {"滴滴", "快手", "小红书", "贝壳", "商汤", "旷视", "依图", "寒武纪", "理想", "蔚来", "小鹏"}

        max_score = 50.0
        for company in companies:
            if any(tier in company for tier in top_tier):
                max_score = max(max_score, 100.0)
            elif any(uni in company for uni in unicorn):
                max_score = max(max_score, 85.0)
            else:
                max_score = max(max_score, 70.0)

        return max_score

    def _get_internship_evidence(self, params: dict[str, Any]) -> str:
        """Get internship evidence string."""
        if not params.get("present", False):
            return "无实习经历"
        companies = params.get("companies", [])
        count = params.get("count", len(companies))
        if count == 0:
            return "无实习经历"
        return f"{count}段实习: {', '.join(companies[:3])}{'...' if len(companies) > 3 else ''}"

    def _score_project(self, params: dict[str, Any]) -> float:
        """Score project: 完整上线=100, 课程设计=60, 想法阶段=30."""
        if not params.get("present", False):
            return 0.0

        types = params.get("project_types", [])
        if not types:
            return 30.0

        if "完整项目" in types or "上线" in str(types):
            return 100.0
        elif "课程设计" in types:
            return 60.0
        else:
            return 30.0

    def _get_project_evidence(self, params: dict[str, Any]) -> str:
        """Get project evidence string."""
        count = params.get("count", 0)
        types = params.get("project_types", [])
        if count == 0:
            return "无项目经历"
        type_str = ", ".join(types) if types else "未说明类型"
        return f"{count}个项目 ({type_str})"

    def _score_technical_practice(self, params: dict[str, Any]) -> float:
        """Score technical practice based on tech stack matching."""
        required = params.get("required_techs", [])
        found = params.get("found_techs", [])
        match_type = params.get("tech_stack_match", "不匹配")

        if not required:
            return 70.0  # No specific requirement, give medium score

        if match_type == "完全匹配":
            return 100.0
        elif match_type == "部分匹配":
            return 70.0
        else:
            return 30.0

    def _get_technical_practice_evidence(self, params: dict[str, Any]) -> str:
        """Get technical practice evidence string."""
        required = params.get("required_techs", [])
        found = params.get("found_techs", [])
        match_type = params.get("tech_stack_match", "未知")

        if not required:
            return "无特殊技术要求"

        if found:
            return f"要求: {', '.join(required[:3])} | 找到: {', '.join(found[:3])} ({match_type})"
        else:
            return f"要求: {', '.join(required[:3])} | 未找到相关技术"

    def _score_education(self, params: dict[str, Any]) -> float:
        """Score education: 985/海外top=100, 211=85, 双非一本=70, 其他=50."""
        value = params.get("value", "")
        if "985" in value or "海外" in value or "top" in value.lower():
            return 100.0
        elif "211" in value:
            return 85.0
        elif "双非" in value or "一本" in value:
            return 70.0
        else:
            return 50.0

    def _get_education_evidence(self, params: dict[str, Any]) -> str:
        """Get education evidence string."""
        school = params.get("school_name", "")
        value = params.get("value", "")
        return f"{school} ({value})" if school else value

    def _score_major(self, params: dict[str, Any]) -> float:
        """Score major: 完全对口=100, 相关=70, 跨专业=40."""
        match = params.get("match", "跨专业")
        if "完全对口" in match or match == "对口":
            return 100.0
        elif "相关" in match:
            return 70.0
        else:
            return 40.0

    def _get_major_evidence(self, params: dict[str, Any]) -> str:
        """Get major evidence string."""
        actual = params.get("actual_major", "")
        match = params.get("match", "未知")
        return f"{actual} ({match})"

    def _score_gpa(self, params: dict[str, Any]) -> float:
        """Score GPA: 前10%=100, 前30%=80, 前50%=60, 其他=40."""
        ranking = params.get("ranking", "")
        if "前10%" in ranking or "top10%" in ranking.lower():
            return 100.0
        elif "前30%" in ranking or "top30%" in ranking.lower():
            return 80.0
        elif "前50%" in ranking or "top50%" in ranking.lower():
            return 60.0
        else:
            return 40.0

    def _get_gpa_evidence(self, params: dict[str, Any]) -> str:
        """Get GPA evidence string."""
        gpa = params.get("gpa", 0)
        ranking = params.get("ranking", "未知")
        return f"GPA: {gpa} ({ranking})" if gpa else ranking

    def _score_competition(self, params: dict[str, Any]) -> float:
        """Score competition: 国际级=100, 国家级=85, 省级=70, 校级=50."""
        level = params.get("level", "")
        if not params.get("has_competition", False):
            return 30.0

        if "国际" in level:
            return 100.0
        elif "国家" in level:
            return 85.0
        elif "省" in level:
            return 70.0
        else:
            return 50.0

    def _get_competition_evidence(self, params: dict[str, Any]) -> str:
        """Get competition evidence string."""
        if not params.get("has_competition", False):
            return "无竞赛获奖"
        level = params.get("level", "")
        awards = params.get("awards", [])
        if awards:
            return f"{level}: {awards[0]}{'...' if len(awards) > 1 else ''}"
        return level

    def _score_english(self, params: dict[str, Any]) -> float:
        """Score English: 雅思7+/托福100+=100, 六级500+=85, 六级425+=70."""
        cert = params.get("certificate", "")
        score = params.get("score", 0)

        if "雅思" in cert and score >= 7:
            return 100.0
        elif "托福" in cert and score >= 100:
            return 100.0
        elif "六级" in cert:
            if score >= 500:
                return 85.0
            elif score >= 425:
                return 70.0
            else:
                return 50.0
        else:
            return 40.0

    def _get_english_evidence(self, params: dict[str, Any]) -> str:
        """Get English evidence string."""
        cert = params.get("certificate", "无证书")
        score = params.get("score", 0)
        return f"{cert} {score}分" if score else cert

    def _score_github(self, params: dict[str, Any]) -> float:
        """Score GitHub: 有且活跃=100, 有一般=70, 无=30."""
        if params.get("has_github", False):
            return 100.0 if params.get("active", False) else 70.0
        return 30.0

    def _get_github_evidence(self, params: dict[str, Any]) -> str:
        """Get GitHub evidence string."""
        if not params.get("has_github", False):
            return "无 GitHub"
        active = "活跃" if params.get("active", False) else "一般"
        repos = params.get("repos", [])
        if repos:
            return f"有 GitHub ({active}): {repos[0]}{'...' if len(repos) > 1 else ''}"
        return f"有 GitHub ({active})"

    def _score_stability(self, params: dict[str, Any]) -> float:
        """Score stability: 完全满足=100, 基本满足=70, 有冲突=40."""
        days = params.get("available_days", 0)
        months = params.get("months", 0)

        if days >= 4 and months >= 3:
            return 100.0
        elif days >= 3 and months >= 2:
            return 70.0
        else:
            return 40.0

    def _get_stability_evidence(self, params: dict[str, Any]) -> str:
        """Get stability evidence string."""
        days = params.get("available_days", 0)
        months = params.get("months", 0)
        return f"可实习 {days}天/周, {months}个月"

    # Default improvement suggestions

    def _default_quick_improvements(self, soft_score: SoftMetricsScore) -> list[str]:
        """Generate default quick improvements based on soft score."""
        improvements = []

        for item in soft_score.weaknesses:
            dim = item.get("dimension", "")
            if "数据意识" in dim or "data_awareness" in dim.lower():
                improvements.append("用数据量化项目成果（例如：用户数 5000 → 日活 25%）")
            elif "沟通表达" in dim or "communication" in dim.lower():
                improvements.append("简化简历描述，用'做了什么→得到什么结果'的结构")
            elif "学习能力" in dim or "learning" in dim.lower():
                improvements.append("补充快速学习能力的证据（例如：2周学 XX 技术并完成项目）")
            elif "执行能力" in dim or "execution" in dim.lower():
                improvements.append("强化项目主导经历，突出个人贡献和落地成果")

        return improvements or ["仔细检查简历，确保描述清晰有逻辑"]

    def _default_long_term_improvements(self) -> list[str]:
        """Generate default long-term improvements."""
        return [
            "争取一份相关实习（大厂 > 独角兽 > 中型公司）",
            "完成 1-2 个完整的个人/开源项目",
            "补充 GitHub 开源贡献",
            "系统学习核心技能并产出项目",
        ]
