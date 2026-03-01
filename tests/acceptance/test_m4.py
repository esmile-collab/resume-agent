"""M4 acceptance tests for orchestration use cases."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# Add src/ as import root so top-level packages are importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from db.database import DB_PATH, init_db
from models import ScoreCard
from orchestration import ResumeOrchestratorUseCase

ARTIFACTS_ROOT = Path(".data") / "artifacts"


class LowScorer:
    """Custom scorer for testing low-match compensation branch."""

    def score(self, jd: str, resume: str) -> ScoreCard:
        _ = jd
        _ = resume
        return ScoreCard(score=30, match_level="low", suggestion="风险确认")


def _fixture_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _build_ten_jds() -> list[str]:
    strategy_seed = _fixture_text("tests/fixtures/jd/sample_jd_001.txt")
    feature_seed = _fixture_text("tests/fixtures/jd/sample_jd_002.txt")

    strategy_jds = [f"{strategy_seed}\n\n批次编号: strategy-{i}\n方向: 策略" for i in range(1, 6)]
    feature_jds = [f"{feature_seed}\n\n批次编号: feature-{i}\n方向: 功能" for i in range(1, 6)]
    return strategy_jds + feature_jds


def setup_function() -> None:
    """Reset DB and artifacts before each test."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if ARTIFACTS_ROOT.exists():
        shutil.rmtree(ARTIFACTS_ROOT)
    init_db().close()


def test_m4_e2e_ten_jd_two_direction_two_outputs() -> None:
    """Should pass end-to-end flow: 10 JDs -> 2 cards -> 2 outputs."""
    use_case = ResumeOrchestratorUseCase()
    resume_text = _fixture_text("tests/fixtures/resume/sample_resume_001.txt")

    project = use_case.init_project(
        name="m4-e2e-project",
        cycle="2026秋招",
        base_resume_text=resume_text,
    )
    project_id = project["project_id"]

    preview = use_case.ingest_jds(project_id=project_id, jd_texts=_build_ten_jds())
    assert preview["need_user_confirm"] is True
    assert preview["preview"]["jd_count"] == 10
    assert preview["preview"]["direction_count"] == 2
    assert preview["preview"]["resume_output_count"] == 2

    allocation = use_case.confirm_allocation(project_id=project_id, plan_id=preview["plan_id"])
    assert allocation["direction_count"] == 2
    assert len(allocation["task_cards"]) == 2

    scored = use_case.score_task_cards(project_id=project_id, resume_text=resume_text)
    assert len(scored["task_cards"]) == 2
    assert all(card["status"] == "scored" for card in scored["task_cards"])

    output_results: list[dict[str, str | int | bool]] = []
    for card in allocation["task_cards"]:
        result = use_case.run_card(
            project_id=project_id,
            task_card_id=card["task_card_id"],
            resume_text=resume_text,
        )
        output_results.append(result)

    assert len(output_results) == 2
    assert all(item["await_risk_ack"] is False for item in output_results)
    assert all(item["mode"] == "normal" for item in output_results)

    for item in output_results:
        output_path = Path(str(item["output_path"]))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "Evidence JD IDs" in content
        assert "Version: v1" in content


def test_m4_low_match_compensation_flow() -> None:
    """Low-match card should require risk-ack and generate compensation output."""
    use_case = ResumeOrchestratorUseCase(scorer=LowScorer())
    resume_text = _fixture_text("tests/fixtures/resume/sample_resume_001.txt")
    jd_text = _fixture_text("tests/fixtures/jd/sample_jd_001.txt")

    project = use_case.init_project(
        name="m4-low-risk-project",
        cycle="2026秋招",
        base_resume_text=resume_text,
    )
    project_id = project["project_id"]

    preview = use_case.ingest_jds(project_id=project_id, jd_texts=[jd_text])
    allocation = use_case.confirm_allocation(project_id=project_id, plan_id=preview["plan_id"])
    use_case.score_task_cards(project_id=project_id, resume_text=resume_text)

    task_card_id = allocation["task_cards"][0]["task_card_id"]
    first_try = use_case.run_card(
        project_id=project_id,
        task_card_id=task_card_id,
        resume_text=resume_text,
        risk_ack=False,
    )
    assert first_try["await_risk_ack"] is True

    second_try = use_case.run_card(
        project_id=project_id,
        task_card_id=task_card_id,
        resume_text=resume_text,
        risk_ack=True,
    )
    assert second_try["await_risk_ack"] is False
    assert second_try["mode"] == "compensation"

    output_path = Path(str(second_try["output_path"]))
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Mode: compensation" in content
