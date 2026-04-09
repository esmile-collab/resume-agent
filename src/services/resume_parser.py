# Input: 原始简历文本和 block patch 请求。
# Output: 输出可编辑 block JSON 并支持回写 patch。
# Pos: 简历结构化解析服务。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Resume parsing utilities for block-level editing."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import re
from typing import Any


@dataclass
class ResumeBlock:
    """One editable resume block."""

    block_id: str
    block_type: str
    content: str
    metadata: dict[str, Any]


class ResumeParser:
    """Convert resume text to editable blocks and apply block patches."""

    _section_patterns: list[tuple[str, str]] = [
        ("summary", r"(summary|简介|个人总结)"),
        ("experience", r"(experience|经历|工作经历|项目经历)"),
        ("education", r"(education|教育|教育背景)"),
        ("skills", r"(skills|技能|能力)"),
    ]

    def parse(self, resume_text: str) -> dict[str, Any]:
        """Parse raw resume text into stable block-level JSON structure."""
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        blocks: list[ResumeBlock] = []
        current_section = "general"
        block_index = 1

        for line in lines:
            detected_section = self._detect_section(line)
            if detected_section != current_section and detected_section != "general":
                current_section = detected_section
                continue

            block_id = f"blk_{block_index:03d}"
            blocks.append(
                ResumeBlock(
                    block_id=block_id,
                    block_type=current_section,
                    content=line,
                    metadata={"line_index": block_index - 1},
                )
            )
            block_index += 1

        if not blocks:
            blocks.append(
                ResumeBlock(
                    block_id="blk_001",
                    block_type="general",
                    content=resume_text.strip(),
                    metadata={"line_index": 0},
                )
            )

        return {
            "blocks": [asdict(block) for block in blocks],
            "raw_text": resume_text,
        }

    def apply_patch(self, content_json: dict[str, Any], block_id: str, new_text: str) -> dict[str, Any]:
        """Apply a patch to one block and return new content JSON."""
        updated = deepcopy(content_json)
        blocks = updated.get("blocks", [])
        for block in blocks:
            if block.get("block_id") == block_id:
                block["content"] = new_text
                block["modified"] = True
                break
        return updated

    def _detect_section(self, line: str) -> str:
        lowered = line.lower()
        for section, pattern in self._section_patterns:
            if re.search(pattern, lowered):
                return section
        return "general"

