"""Shared dataclasses for tool stubs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AllocationDecision:
    """One allocation decision for one JD entry."""

    jd_entry_id: str
    action: str
    reason: str
    target_task_card_id: Optional[str] = None
    target_direction_name: str = "通用方向"


@dataclass
class AllocationPlan:
    """Allocation plan output for allocator stub."""

    decisions: list[AllocationDecision] = field(default_factory=list)
