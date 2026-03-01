"""Dataclasses for orchestration state and results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaskCardRecord:
    """Persisted task-card runtime record."""

    task_card_id: str
    direction_id: str
    direction_name: str
    jd_entry_ids: list[str] = field(default_factory=list)
    status: str = "pending"
    score: int | None = None
    match_level: str | None = None
    latest_output_version: int = 0


@dataclass
class AllocationPreviewResult:
    """In-memory shape for batch JD preview output."""

    plan_id: str
    jd_count: int
    direction_count: int
    resume_output_count: int
    proposed_task_card_changes: list[dict[str, str]]
