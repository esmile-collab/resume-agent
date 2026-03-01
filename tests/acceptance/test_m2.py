"""M2 acceptance tests for router and task state machine."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src/ as import root so top-level packages (routes/models) are importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from models import ScoreCard
from routes.intent import Intent, TaskState
from routes.router import TaskRouter


def test_generate_high_match() -> None:
    """High match should generate in normal mode."""
    router = TaskRouter()
    score_card = ScoreCard(score=80, match_level="high", suggestion="建议生成")

    decision = router.route(Intent.GENERATE, TaskState.SCORED, score_card)

    assert decision.state == TaskState.GENERATING
    assert decision.mode == "normal"
    assert decision.await_risk_ack is False


def test_generate_low_match() -> None:
    """Low match should stay scored and require risk acknowledgement."""
    router = TaskRouter()
    score_card = ScoreCard(score=30, match_level="low", suggestion="风险确认")

    decision = router.route(Intent.GENERATE, TaskState.SCORED, score_card)

    assert decision.state == TaskState.SCORED
    assert decision.await_risk_ack is True


def test_abandon_moves_to_abandoned() -> None:
    """Abandon intent should force task into abandoned state."""
    router = TaskRouter()
    decision = router.route(Intent.ABANDON, TaskState.SCORED)
    assert decision.state == TaskState.ABANDONED


def test_low_match_risk_ack_confirmed() -> None:
    """Risk confirmation should switch generation mode to compensation."""
    router = TaskRouter()
    score_card = ScoreCard(score=35, match_level="low", suggestion="风险确认")

    decision = router.handle_risk_ack(True, score_card)

    assert decision.state == TaskState.GENERATING
    assert decision.mode == "compensation"
    assert decision.warning is True
