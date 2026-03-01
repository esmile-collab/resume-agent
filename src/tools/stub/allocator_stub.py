"""Project JD allocator stub for M3-stub stage."""

from __future__ import annotations

from typing import Any, Iterable

from .models import AllocationDecision, AllocationPlan


class AllocatorStub:
    """Always routes input JD entries to 'create_new_card'."""

    def allocate(self, jd_entries: Iterable[Any], existing_cards: list[Any]) -> AllocationPlan:
        """Return one create-new-card decision for each JD entry."""
        _ = existing_cards
        decisions: list[AllocationDecision] = []
        for index, jd in enumerate(jd_entries):
            jd_entry_id = self._extract_entry_id(jd, index)
            decisions.append(
                AllocationDecision(
                    jd_entry_id=jd_entry_id,
                    action="create_new_card",
                    reason="Stub: 总是创建新卡片",
                )
            )
        return AllocationPlan(decisions=decisions)

    @staticmethod
    def _extract_entry_id(jd_entry: Any, index: int) -> str:
        """Read JD ID from object or mapping, fallback to deterministic stub ID."""
        if hasattr(jd_entry, "id"):
            value = getattr(jd_entry, "id")
            if isinstance(value, str) and value:
                return value
        if isinstance(jd_entry, dict):
            for key in ("id", "project_jd_id", "jd_id"):
                value = jd_entry.get(key)
                if isinstance(value, str) and value:
                    return value
        return f"stub_jd_{index + 1}"
