# Input: 项目目录、消息历史和 JSON 文件存储。
# Output: 输出长对话压缩、摘要恢复和消息落盘能力。
# Pos: 对话观测与压缩模块。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Long-dialog compression manager (M7, 30-turn threshold)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


class DialogCompressionManager:
    """Persist dialog turns and compress old context when threshold is exceeded."""

    def __init__(self, *, max_turns: int = 30, keep_recent_turns: int = 10) -> None:
        self.max_turns = max_turns
        self.keep_recent_turns = keep_recent_turns

    def append_turn(
        self,
        *,
        project_root: Path,
        role: str,
        content: str,
        facts: list[str] | None = None,
        artifact_version_id: str = "",
    ) -> dict[str, Any]:
        """Append one dialog message and optionally trigger compression."""
        messages, recovered_messages = self._load_messages(project_root=project_root)
        message = {
            "message_id": f"msg_{uuid4().hex[:10]}",
            "role": role,
            "content": content,
            "facts": list(facts or []),
            "artifact_version_id": artifact_version_id,
            "created_at": _utc_now_iso(),
        }
        messages.append(message)

        recovered_summary = False
        if len(messages) <= self.max_turns:
            self._write_json(self._messages_file(project_root), {"messages": messages})
            return {
                "compressed": False,
                "summary_version": 0,
                "message_id": message["message_id"],
                "recovered_from_corruption": recovered_messages,
            }

        older = messages[: -self.keep_recent_turns]
        recent = messages[-self.keep_recent_turns :]
        summary_doc, recovered_summary = self._load_summary(project_root=project_root)
        summary_version = int(summary_doc.get("latest_summary_version", 0)) + 1

        summary = {
            "summary_version": summary_version,
            "created_at": _utc_now_iso(),
            "compressed_message_count": len(older),
            "window_start_message_id": older[0]["message_id"] if older else "",
            "window_end_message_id": older[-1]["message_id"] if older else "",
            "confirmed_facts": self._extract_confirmed_facts(older),
            "unfinished_tasks": self._extract_unfinished_tasks(older),
            "pending_questions": self._extract_pending_questions(older),
            "artifact_refs": self._extract_artifact_refs(older),
        }
        summaries = cast(list[dict[str, Any]], summary_doc.get("summaries", []))
        summaries.append(summary)

        self._write_json(
            self._summary_file(project_root),
            {"latest_summary_version": summary_version, "summaries": summaries},
        )
        self._write_json(self._messages_file(project_root), {"messages": recent})

        return {
            "compressed": True,
            "summary_version": summary_version,
            "message_id": message["message_id"],
            "recovered_from_corruption": recovered_messages or recovered_summary,
        }

    def read_messages(self, *, project_root: Path) -> list[dict[str, Any]]:
        """Return persisted recent dialog turns."""
        messages, _ = self._load_messages(project_root=project_root)
        return messages

    def read_summary(self, *, project_root: Path) -> dict[str, Any]:
        """Return summary state for one project."""
        summary, _ = self._load_summary(project_root=project_root)
        return summary

    def _load_messages(self, *, project_root: Path) -> tuple[list[dict[str, Any]], bool]:
        payload, recovered = self._safe_read_json(
            self._messages_file(project_root), default={"messages": []}
        )
        return cast(list[dict[str, Any]], payload.get("messages", [])), recovered

    def _load_summary(self, *, project_root: Path) -> tuple[dict[str, Any], bool]:
        payload, recovered = self._safe_read_json(
            self._summary_file(project_root), default={"latest_summary_version": 0, "summaries": []}
        )
        return cast(dict[str, Any], payload), recovered

    @staticmethod
    def _extract_confirmed_facts(messages: list[dict[str, Any]]) -> list[str]:
        facts: list[str] = []
        for message in messages:
            facts.extend(cast(list[str], message.get("facts", [])))
            content = str(message.get("content", ""))
            for line in content.splitlines():
                normalized = line.strip()
                if normalized.startswith(("事实:", "FACT:")):
                    facts.append(normalized.split(":", 1)[1].strip())
        return _unique(facts)

    @staticmethod
    def _extract_unfinished_tasks(messages: list[dict[str, Any]]) -> list[str]:
        tasks: list[str] = []
        for message in messages:
            content = str(message.get("content", ""))
            for line in content.splitlines():
                normalized = line.strip()
                if normalized.startswith("TODO:"):
                    tasks.append(normalized.split(":", 1)[1].strip())
                elif "待办" in normalized:
                    tasks.append(normalized)
        return _unique(tasks)

    @staticmethod
    def _extract_pending_questions(messages: list[dict[str, Any]]) -> list[str]:
        questions: list[str] = []
        for message in messages:
            content = str(message.get("content", "")).strip()
            if content.endswith(("?", "？")):
                questions.append(content)
        return _unique(questions)

    @staticmethod
    def _extract_artifact_refs(messages: list[dict[str, Any]]) -> list[str]:
        refs: list[str] = []
        for message in messages:
            ref = str(message.get("artifact_version_id", "")).strip()
            if ref:
                refs.append(ref)
        return _unique(refs)

    @staticmethod
    def _messages_file(project_root: Path) -> Path:
        return project_root / "state" / "dialog_messages.json"

    @staticmethod
    def _summary_file(project_root: Path) -> Path:
        return project_root / "state" / "dialog_summary.json"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _safe_read_json(path: Path, *, default: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        if not path.exists():
            return default, False

        try:
            return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8"))), False
        except json.JSONDecodeError:
            return default, True
