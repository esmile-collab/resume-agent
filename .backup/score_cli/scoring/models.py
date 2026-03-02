"""Data models for campus scoring system v2.1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HardMetricsScore:
    """Hard metrics score based on objective rules."""

    # Dimension scores with defaults
    internship_score: float = 0.0  # 25% weight
    project_score: float = 0.0  # 20% weight
    technical_practice_score: float = 0.0  # 15% weight
    education_score: float = 0.0  # 10% weight
    major_score: float = 0.0  # 10% weight
    gpa_score: float = 0.0  # 5% weight
    competition_score: float = 0.0  # 5% weight
    english_score: float = 0.0  # 5% weight
    github_score: float = 0.0  # 3% weight
    stability_score: float = 0.0  # 2% weight

    # Total normalized score (0-100)
    total_score: float = 0.0

    # Evidence for each dimension
    evidence: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "internship": {"score": self.internship_score, "evidence": self.evidence.get("internship", "")},
            "project": {"score": self.project_score, "evidence": self.evidence.get("project", "")},
            "technical_practice": {"score": self.technical_practice_score, "evidence": self.evidence.get("technical_practice", "")},
            "education": {"score": self.education_score, "evidence": self.evidence.get("education", "")},
            "major": {"score": self.major_score, "evidence": self.evidence.get("major", "")},
            "gpa": {"score": self.gpa_score, "evidence": self.evidence.get("gpa", "")},
            "competition": {"score": self.competition_score, "evidence": self.evidence.get("competition", "")},
            "english": {"score": self.english_score, "evidence": self.evidence.get("english", "")},
            "github": {"score": self.github_score, "evidence": self.evidence.get("github", "")},
            "stability": {"score": self.stability_score, "evidence": self.evidence.get("stability", "")},
            "total": self.total_score,
        }


@dataclass
class SoftMetricDimension:
    """One soft metric dimension score."""

    dimension: str
    score: float
    reasoning: str
    evidence: str
    evidence_level: str


@dataclass
class SoftMetricsScore:
    """Soft metrics score from LLM evaluation."""

    # Dimension scores (6 unified dimensions) with defaults
    learning_ability: float = 0.0  # 25% weight
    execution: float = 0.0  # 25% weight
    communication: float = 0.0  # 15% weight
    data_awareness: float = 0.0  # 15% weight
    stability: float = 0.0  # 10% weight
    adaptability: float = 0.0  # 10% weight

    # Total score (0-100)
    total_score: float = 0.0

    # Dimension details
    dimensions: list[SoftMetricDimension] = field(default_factory=list)

    # Strengths and weaknesses
    strengths: list[dict[str, str]] = field(default_factory=list)
    weaknesses: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dimensions": [
                {
                    "dimension": d.dimension,
                    "score": d.score,
                    "reasoning": d.reasoning,
                    "evidence": d.evidence,
                    "evidence_level": d.evidence_level,
                }
                for d in self.dimensions
            ],
            "total": self.total_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


@dataclass
class ScoreReport:
    """Complete score report for campus recruitment."""

    # Input info
    jd_summary: str = ""
    resume_summary: str = ""

    # Hard metrics (rule-based, 35-50% weight)
    hard_metrics: HardMetricsScore | None = None

    # Soft metrics (LLM-based, 50-65% weight)
    soft_metrics: SoftMetricsScore | None = None

    # Final score
    final_score: float = 0.0
    match_level: str = ""  # high/medium/low
    suggestion: str = ""

    # Immediate improvements (score >= 70)
    quick_improvements: list[str] = field(default_factory=list)

    # Long-term improvements (score < 70)
    long_term_improvements: list[str] = field(default_factory=list)

    # Risk warning (if low match)
    risk_warning: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "jd_summary": self.jd_summary,
            "resume_summary": self.resume_summary,
            "hard_metrics": self.hard_metrics.to_dict() if self.hard_metrics else None,
            "soft_metrics": self.soft_metrics.to_dict() if self.soft_metrics else None,
            "final_score": self.final_score,
            "match_level": self.match_level,
            "suggestion": self.suggestion,
            "quick_improvements": self.quick_improvements,
            "long_term_improvements": self.long_term_improvements,
            "risk_warning": self.risk_warning,
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# 简历评分报告（校招版 v2.1）",
            "",
            "## 核心指标",
            f"**总分**: {self.final_score:.1f}/100",
            f"**评级**: {self._get_rating_label()}",
            f"**建议**: {self.suggestion}",
            "",
        ]

        if self.risk_warning:
            lines.extend([
                f"⚠️ **风险提示**: {self.risk_warning}",
                "",
            ])

        # Hard metrics
        if self.hard_metrics:
            lines.extend([
                "## 硬性指标评分",
                "",
                f"**总分**: {self.hard_metrics.total_score:.1f}/100",
                "",
                "| 维度 | 得分 | 说明 |",
                "|------|------|------|",
            ])

            h = self.hard_metrics
            dimension_names = {
                "internship": "💼 实习经历",
                "project": "🌛 项目经历",
                "technical_practice": "🔧 技术实践",
                "education": "📚 学历层次",
                "major": "🎓 专业对口",
                "gpa": "📊 在校成绩",
                "competition": "🏆 竞赛获奖",
                "english": "🌐 英语水平",
                "github": "🐙 开源贡献",
                "stability": "⏰ 稳定性",
            }

            for key, name in dimension_names.items():
                score = getattr(h, f"{key}_score")
                evidence = h.evidence.get(key, "")
                lines.append(f"| {name} | {score:.0f}/100 | {evidence} |")

            lines.append("")

        # Soft metrics
        if self.soft_metrics:
            lines.extend([
                "## 软性能力评分（统一指标）",
                "",
                f"**总分**: {self.soft_metrics.total_score:.1f}/100",
                "",
                "| 维度 | 得分 | 评价 |",
                "|------|------|------|",
            ])

            s = self.soft_metrics
            dimension_labels = {
                "learning_ability": "📚 学习能力",
                "execution": "⚡ 执行能力",
                "communication": "💬 沟通表达",
                "data_awareness": "📊 数据意识",
                "stability": "🎯 稳定性",
                "adaptability": "🔗 适配度",
            }

            for d in s.dimensions:
                label = dimension_labels.get(d.dimension, d.dimension)
                lines.append(f"| {label} | {d.score:.0f}/100 | {d.reasoning} |")

            lines.append("")

            # Strengths
            if s.strengths:
                lines.extend([
                    "## 优势",
                    "",
                ])
                for item in s.strengths:
                    dim = item.get("dimension", "")
                    reason = item.get("reason", "")
                    lines.append(f"✅ **{dim}**: {reason}")
                lines.append("")

            # Weaknesses
            if s.weaknesses:
                lines.extend([
                    "## 劣势",
                    "",
                ])
                for item in s.weaknesses:
                    dim = item.get("dimension", "")
                    reason = item.get("reason", "")
                    lines.append(f"❌ **{dim}**: {reason}")
                lines.append("")

        # Improvements
        if self.quick_improvements:
            lines.extend([
                "## 立即改进建议",
                "",
            ])
            for i, item in enumerate(self.quick_improvements, 1):
                lines.append(f"{i}. {item}")
            lines.append("")

        if self.long_term_improvements:
            lines.extend([
                "## 长期提升建议",
                "",
            ])
            for i, item in enumerate(self.long_term_improvements, 1):
                lines.append(f"{i}. {item}")
            lines.append("")

        return "\n".join(lines)

    def _get_rating_label(self) -> str:
        """Get Chinese rating label."""
        if self.final_score >= 75:
            return "高匹配"
        elif self.final_score >= 50:
            return "中等匹配"
        else:
            return "低匹配"
