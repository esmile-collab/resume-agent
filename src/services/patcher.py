# Input: 简历 block、JD 文本和缺口提示。
# Output: 输出可应用的 block 级 patch 候选。
# Pos: 简历润色 patch 生成服务。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Patch generator for block-level resume polishing."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass
class PatchCandidate:
    """One proposed patch for a resume block."""

    target_block_id: str
    old_text: str
    new_text: str
    reason: str
    potential_score: float


class PolishPatcher:
    """Generate local rewrite patches instead of full resume rewrite."""

    def generate_patches(
        self,
        resume_blocks: list[dict[str, Any]],
        jd_text: str,
        gaps: list[dict[str, str]],
    ) -> list[PatchCandidate]:
        """Generate Top-K patch candidates from current blocks."""
        if not resume_blocks:
            return []

        scored_blocks: list[tuple[float, dict[str, Any]]] = []
        for block in resume_blocks:
            content = str(block.get("content", ""))
            if not content.strip():
                continue
            score = self._score_block(content=content, jd_text=jd_text)
            scored_blocks.append((score, block))

        scored_blocks.sort(key=lambda pair: pair[0], reverse=True)
        block_count = len(scored_blocks)
        if block_count == 0:
            return []

        max_patches = min(8, max(1, block_count - 1), max(1, int(block_count * 0.35)))
        selected = scored_blocks[:max_patches]
        hints = [gap.get("title", "") for gap in gaps if isinstance(gap, dict)]
        hint_text = "；".join(hints[:2]) if hints else "突出与 JD 相关的动作与结果"

        patches: list[PatchCandidate] = []
        for base_score, block in selected:
            old_text = str(block.get("content", ""))
            target_block_id = str(block.get("block_id", ""))
            new_text = self._rewrite_text(old_text=old_text, hint_text=hint_text)
            if new_text == old_text:
                continue
            candidate = PatchCandidate(
                target_block_id=target_block_id,
                old_text=old_text,
                new_text=new_text,
                reason=f"对齐 JD 缺口：{hint_text}",
                potential_score=self.calculate_potential_score(old_text=old_text, jd_text=jd_text, base=base_score),
            )
            patches.append(candidate)

        return patches

    def calculate_potential_score(self, *, old_text: str, jd_text: str, base: float = 0.0) -> float:
        """Calculate patch potential score with weighted heuristic."""
        jd_gap_relevance = 1.0 if self._has_keyword_overlap(old_text, jd_text) else 0.4
        quantification_gap = 0.8 if re.search(r"\d+%?|\d+\.\d+", old_text) is None else 0.3
        weak_action_verb = 0.9 if re.search(r"(参与|协助|support|assist)", old_text.lower()) else 0.4
        verbosity_penalty = 0.8 if len(old_text) > 120 else 0.3

        score = (
            0.40 * jd_gap_relevance
            + 0.25 * quantification_gap
            + 0.20 * weak_action_verb
            + 0.15 * verbosity_penalty
        )
        return round(min(1.0, (score + base) / 2), 4)

    @staticmethod
    def _rewrite_text(*, old_text: str, hint_text: str) -> str:
        text = old_text.strip()
        # Keep local rewrite deterministic and avoid fabricating facts.
        if "主导" not in text and "推动" not in text:
            text = text.replace("参与", "主导").replace("协助", "推动")
        if "，" in text:
            return f"{text}；并围绕目标 JD 强化：{hint_text}。"
        return f"{text}，并围绕目标 JD 强化：{hint_text}。"

    @staticmethod
    def _score_block(*, content: str, jd_text: str) -> float:
        overlap_bonus = 0.3 if PolishPatcher._has_keyword_overlap(content, jd_text) else 0.0
        length_bonus = min(0.4, len(content) / 300)
        weak_verb_bonus = 0.3 if re.search(r"(参与|协助|support|assist)", content.lower()) else 0.1
        return round(overlap_bonus + length_bonus + weak_verb_bonus, 4)

    @staticmethod
    def _has_keyword_overlap(content: str, jd_text: str) -> bool:
        content_tokens = set(re.findall(r"[A-Za-z]{3,}|[\u4e00-\u9fff]{2,6}", content.lower()))
        jd_tokens = set(re.findall(r"[A-Za-z]{3,}|[\u4e00-\u9fff]{2,6}", jd_text.lower()))
        return bool(content_tokens & jd_tokens)

