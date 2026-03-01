"""M3-stub acceptance tests for domain tool stubs."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src/ as import root so top-level packages are importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from db.models import ProjectJDEntry
from tools.stub import AllocatorStub, ParserStub, ScorerStub


def test_scorer_stub() -> None:
    """Scorer stub should return fixed medium scorecard."""
    scorer = ScorerStub()
    card = scorer.score("jd content", "resume content")

    assert card.score == 50
    assert card.match_level == "medium"
    assert card.suggestion == "建议补充后生成"


def test_allocator_stub() -> None:
    """Allocator stub should always create new card decisions."""
    allocator = AllocatorStub()
    jd_entries = [
        ProjectJDEntry(id="jd1", project_id="p1", raw_content="jd", source_file="test.txt")
    ]

    plan = allocator.allocate(jd_entries, [])

    assert len(plan.decisions) == 1
    assert plan.decisions[0].action == "create_new_card"
    assert plan.decisions[0].jd_entry_id == "jd1"
    assert "Stub" in plan.decisions[0].reason


def test_parser_stub() -> None:
    """Parser stub should return deterministic fake parse structures."""
    parser = ParserStub()

    jd_output = parser.parse_jd("产品经理 JD 示例")
    resume_output = parser.parse_resume("张三，产品经理简历")

    assert jd_output["jd_count"] == 1
    assert jd_output["direction_count"] == 1
    assert jd_output["directions"][0]["direction_name"] == "通用方向"

    assert len(resume_output["experiences"]) == 1
    assert "skills" in resume_output
