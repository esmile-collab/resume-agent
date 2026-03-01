"""Routing-related business models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from routes.intent import TaskState


@dataclass
class ScoreCard:
    """Scorecard used by router decisions."""

    score: int
    match_level: str
    suggestion: str


@dataclass
class RouteDecision:
    """State transition and next-action recommendation."""

    state: "TaskState"
    message: str
    actions: list[str]
    await_risk_ack: bool = False
    mode: Optional[str] = None
    warning: bool = False
