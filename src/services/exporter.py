# Input: 结构化简历 block JSON。
# Output: 输出 markdown 形式的简历文本。
# Pos: 简历导出服务。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Resume export helper."""

from __future__ import annotations

from typing import Any


class ResumeExporter:
    """Render structured resume content into plain markdown text."""

    def export(self, content_json: dict[str, Any]) -> str:
        """Export block JSON into markdown-like output."""
        blocks = content_json.get("blocks", [])
        lines: list[str] = ["# Resume Export", ""]
        for block in blocks:
            block_type = str(block.get("block_type", "general")).upper()
            content = str(block.get("content", "")).strip()
            if not content:
                continue
            lines.append(f"- [{block_type}] {content}")
        lines.append("")
        return "\n".join(lines)

