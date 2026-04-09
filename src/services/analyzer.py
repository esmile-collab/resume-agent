# Input: JD 文本、简历文本和关键词提取规则。
# Output: 输出优势、缺口与行动建议分析结果。
# Pos: 非评分型 JD/简历分析服务。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Non-scoring analyzer for Resume Polisher MVP."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "your",
    "have",
    "will",
    "about",
    "职位",
    "岗位",
    "要求",
    "负责",
}


@dataclass
class AnalysisResult:
    """Structured non-scoring insight."""

    strengths: list[dict[str, str]]
    gaps: list[dict[str, str]]
    actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JDAnalyzer:
    """Analyze resume/JD overlap and generate qualitative guidance."""

    def analyze(self, resume_text: str, jd_text: str) -> AnalysisResult:
        """Return strengths/gaps/actions without numeric score."""
        resume_keywords = self._extract_keywords(resume_text)
        jd_keywords = self._extract_keywords(jd_text)
        overlap = [keyword for keyword in jd_keywords if keyword in resume_keywords]
        missing = [keyword for keyword in jd_keywords if keyword not in resume_keywords]

        strengths = self._build_strengths(overlap=overlap, resume_text=resume_text)
        gaps = self._build_gaps(missing=missing, jd_text=jd_text)
        actions = self._build_actions(gaps=gaps)

        return AnalysisResult(
            strengths=strengths[:5],
            gaps=gaps[:5],
            actions=actions[:5],
        )

    def _extract_keywords(self, text: str) -> list[str]:
        matches = re.findall(r"[A-Za-z][A-Za-z0-9+#.\-/]{2,}|[\u4e00-\u9fff]{2,8}", text)
        normalized = [match.lower() for match in matches]
        dedup: list[str] = []
        seen: set[str] = set()
        for token in normalized:
            if token in _STOPWORDS or token in seen:
                continue
            seen.add(token)
            dedup.append(token)
        return dedup[:30]

    def _build_strengths(self, *, overlap: list[str], resume_text: str) -> list[dict[str, str]]:
        strengths: list[dict[str, str]] = []
        for keyword in overlap[:5]:
            strengths.append(
                {
                    "title": f"关键词对齐：{keyword}",
                    "evidence": f"简历内容与 JD 都出现了 “{keyword}” 相关表述。",
                }
            )

        if self._contains_quantified_result(resume_text):
            strengths.append(
                {
                    "title": "已有量化表达基础",
                    "evidence": "简历中已出现数字或百分比，可进一步强化成果说服力。",
                }
            )

        defaults = [
            {
                "title": "经历结构较清晰",
                "evidence": "现有内容可按 JD 诉求做局部优化，无需整份重写。",
            },
            {
                "title": "可提炼高价值 bullet",
                "evidence": "存在可直接优化的经历段落，适合一键润色生成 patch。",
            },
            {
                "title": "可快速进入投递优化",
                "evidence": "已具备基础内容，只需补强匹配表达与业务词汇。",
            },
        ]
        strengths.extend(defaults)
        return strengths

    def _build_gaps(self, *, missing: list[str], jd_text: str) -> list[dict[str, str]]:
        gaps: list[dict[str, str]] = []
        for keyword in missing[:5]:
            gaps.append(
                {
                    "title": f"关键词覆盖不足：{keyword}",
                    "impact": f"JD 中强调 “{keyword}”，当前简历表达较弱，影响筛选通过概率。",
                }
            )

        if not self._contains_quantified_result(jd_text):
            gaps.append(
                {
                    "title": "业务结果表达不充分",
                    "impact": "缺少“动作-结果”链路描述，难突出影响力。",
                }
            )

        defaults = [
            {"title": "动作动词偏弱", "impact": "“参与/协助”过多会削弱主导性信号。"},
            {"title": "JD 术语映射可增强", "impact": "缺少与目标岗位同语义的表达，影响检索匹配。"},
            {"title": "重点经历前置不足", "impact": "高相关内容未前置，首屏说服力偏弱。"},
        ]
        gaps.extend(defaults)
        return gaps

    def _build_actions(self, *, gaps: list[dict[str, str]]) -> list[str]:
        actions: list[str] = []
        for gap in gaps[:5]:
            title = gap.get("title", "")
            if "关键词覆盖不足" in title:
                keyword = title.split("：", 1)[-1].strip()
                actions.append(f"在相关经历 bullet 中补充 “{keyword}” 的具体做法与结果。")
            elif "动作动词偏弱" in title:
                actions.append("将“参与/协助”替换为“主导/推动/负责”，并补充动作结果。")
            elif "前置" in title:
                actions.append("把与当前 JD 最相关的 1-2 条经历前置到该段落开头。")
            else:
                actions.append("为该缺口补充一条可量化结果，增强可验证性。")

        defaults = [
            "每段经历保留 1 条“问题-动作-结果”完整表述。",
            "优先改写 Top 3 高潜力段落，不做整份重写。",
            "改写后先做 diff 复核，再导出投递版本。",
        ]
        actions.extend(defaults)
        return actions

    @staticmethod
    def _contains_quantified_result(text: str) -> bool:
        return re.search(r"\d+%?|\d+\.\d+", text) is not None

