"""M7 acceptance tests for observability and long-dialog resilience."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from orchestration import ResumeOrchestratorUseCase
from src.db.database import DB_PATH, init_db

ARTIFACTS_ROOT = Path(".data") / "artifacts"


def setup_function() -> None:
    """Reset DB and artifacts before each test."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if ARTIFACTS_ROOT.exists():
        shutil.rmtree(ARTIFACTS_ROOT)
    init_db().close()


def _fixture_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_m7_telemetry_fields_recorded() -> None:
    """Should log required monitoring fields: intent/state/match_level/risk_ack."""
    use_case = ResumeOrchestratorUseCase()
    resume_text = _fixture_text("tests/fixtures/resume/sample_resume_001.txt")
    jd_text = _fixture_text("tests/fixtures/jd/sample_jd_001.txt")

    project = use_case.init_project(name="m7-observability", cycle="2026秋招", base_resume_text=resume_text)
    project_id = project["project_id"]

    preview = use_case.ingest_jds(project_id=project_id, jd_texts=[jd_text])
    allocation = use_case.confirm_allocation(project_id=project_id, plan_id=preview["plan_id"])
    task_card_id = allocation["task_cards"][0]["task_card_id"]
    _ = use_case.run_card(project_id=project_id, task_card_id=task_card_id, resume_text=resume_text)

    events = use_case.read_telemetry_events(project_id)
    assert len(events) >= 4
    assert all("intent" in event for event in events)
    assert all("state" in event for event in events)
    assert all("match_level" in event for event in events)
    assert all("risk_ack" in event for event in events)
    assert any(event["intent"] == "generate" for event in events)


def test_m7_dialog_compression_over_30_turns() -> None:
    """After 30+ turns system should compress and keep key facts in summary."""
    use_case = ResumeOrchestratorUseCase()
    project = use_case.init_project(name="m7-dialog", cycle="2026秋招", base_resume_text="")
    project_id = project["project_id"]

    latest = {}
    for index in range(31):
        facts = [f"关键事实-{index}"] if index in (0, 7, 15) else []
        latest = use_case.append_dialog_turn(
            project_id=project_id,
            role="user",
            content=f"第{index + 1}轮对话",
            facts=facts,
        )

    assert latest["compressed"] is True
    summary = use_case.read_dialog_summary(project_id)
    assert summary["latest_summary_version"] >= 1
    latest_summary = summary["summaries"][-1]
    assert "关键事实-0" in latest_summary["confirmed_facts"]

    messages = use_case.read_dialog_messages(project_id)
    assert len(messages) <= 10
    assert any(message["content"] == "第31轮对话" for message in messages)


def test_m7_fault_drill_recovers_from_corrupted_dialog_file() -> None:
    """Corrupted dialog storage should not break next turn append."""
    use_case = ResumeOrchestratorUseCase()
    project = use_case.init_project(name="m7-fault-drill", cycle="2026秋招", base_resume_text="")
    project_id = project["project_id"]

    dialog_file = Path(".data") / "artifacts" / project_id / "state" / "dialog_messages.json"
    dialog_file.parent.mkdir(parents=True, exist_ok=True)
    dialog_file.write_text("{ this is not valid json", encoding="utf-8")

    result = use_case.append_dialog_turn(
        project_id=project_id,
        role="user",
        content="恢复后第一条消息",
        facts=["恢复事实"],
    )

    assert result["recovered_from_corruption"] is True
    messages = use_case.read_dialog_messages(project_id)
    assert len(messages) == 1
    assert messages[0]["content"] == "恢复后第一条消息"

    # Sanity check: file is valid JSON again.
    payload = json.loads(dialog_file.read_text(encoding="utf-8"))
    assert "messages" in payload
