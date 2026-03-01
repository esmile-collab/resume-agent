"""Scorer stub for M3-stub stage."""

from __future__ import annotations

from models import ScoreCard


class ScorerStub:
    """Return deterministic fixed score for pipeline smoke tests."""

    def score(self, jd: str, resume: str) -> ScoreCard:
        """Score interface-compatible stub implementation."""
        _ = jd
        _ = resume
        return ScoreCard(
            score=50,
            match_level="medium",
            suggestion="建议补充后生成",
        )
