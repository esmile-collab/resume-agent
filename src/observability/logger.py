"""JSONL telemetry logger used by orchestration flows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ObservabilityLogger:
    """Append-only logger for routing and runtime monitoring fields."""

    def log_event(
        self,
        *,
        project_root: Path,
        project_id: str,
        intent: str,
        state: str,
        match_level: str = "",
        risk_ack: bool = False,
        task_card_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Write one event with M7-required telemetry fields."""
        event: dict[str, Any] = {
            "timestamp": _utc_now_iso(),
            "project_id": project_id,
            "task_card_id": task_card_id,
            "intent": intent,
            "state": state,
            "match_level": match_level,
            "risk_ack": risk_ack,
            "metadata": metadata or {},
        }
        log_file = project_root / "runs" / "telemetry.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def read_events(self, *, project_root: Path) -> list[dict[str, Any]]:
        """Load telemetry events for inspection and tests."""
        log_file = project_root / "runs" / "telemetry.jsonl"
        if not log_file.exists():
            return []

        events: list[dict[str, Any]] = []
        for line in log_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            events.append(cast(dict[str, Any], json.loads(line)))
        return events
