"""M5 acceptance tests for full CLI command set."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from click.testing import CliRunner

from src.cli.main import cli
from src.db.database import DB_PATH, init_db

ARTIFACTS_ROOT = Path(".data") / "artifacts"


def setup_function() -> None:
    """Reset DB and artifacts before each test."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if ARTIFACTS_ROOT.exists():
        shutil.rmtree(ARTIFACTS_ROOT)
    init_db().close()


def _extract_project_id(output: str) -> str:
    match = re.search(r"([a-z0-9]{8})", output)
    assert match is not None
    return match.group(1)


def test_m5_cli_end_to_end(tmp_path: Path) -> None:
    """Should pass full CLI flow from project init to card report output."""
    runner = CliRunner()
    resume_path = Path("tests/fixtures/resume/sample_resume_001.txt")
    jd_1 = Path("tests/fixtures/jd/sample_jd_001.txt")
    jd_2 = Path("tests/fixtures/jd/sample_jd_002.txt")

    init_result = runner.invoke(
        cli,
        [
            "project",
            "init",
            "--name",
            "m5-project",
            "--cycle",
            "2026秋招",
            "--resume",
            str(resume_path),
        ],
    )
    assert init_result.exit_code == 0
    project_id = _extract_project_id(init_result.output)

    ingest_result = runner.invoke(
        cli,
        [
            "project",
            "ingest-jd",
            "--project",
            project_id,
            "--jd",
            str(jd_1),
            "--jd",
            str(jd_2),
            "--format",
            "json",
        ],
    )
    assert ingest_result.exit_code == 0
    ingest_payload = json.loads(ingest_result.output)
    assert ingest_payload["need_user_confirm"] is True
    assert ingest_payload["preview"]["jd_count"] == 2
    plan_id = ingest_payload["plan_id"]

    confirm_result = runner.invoke(
        cli,
        [
            "project",
            "confirm-allocation",
            "--project",
            project_id,
            "--plan",
            plan_id,
            "--format",
            "json",
        ],
    )
    assert confirm_result.exit_code == 0
    confirm_payload = json.loads(confirm_result.output)
    assert confirm_payload["direction_count"] == 2
    assert len(confirm_payload["task_cards"]) == 2
    task_card_id = confirm_payload["task_cards"][0]["task_card_id"]

    add_jd_result = runner.invoke(
        cli,
        [
            "card",
            "add-jd",
            "--project",
            project_id,
            "--card",
            task_card_id,
            "--jd",
            str(jd_1),
            "--format",
            "json",
        ],
    )
    assert add_jd_result.exit_code == 0
    add_jd_payload = json.loads(add_jd_result.output)
    assert add_jd_payload["source_task_card_id"] == task_card_id
    assert add_jd_payload["need_user_confirm"] is True
    assert add_jd_payload["plan_id"]

    # Confirm card-level add-jd routed preview.
    confirm_add_result = runner.invoke(
        cli,
        [
            "project",
            "confirm-allocation",
            "--project",
            project_id,
            "--plan",
            add_jd_payload["plan_id"],
            "--format",
            "json",
        ],
    )
    assert confirm_add_result.exit_code == 0

    report_path = tmp_path / "card_report.md"
    run_result = runner.invoke(
        cli,
        [
            "card",
            "run",
            "--project",
            project_id,
            "--card",
            task_card_id,
            "--out",
            str(report_path),
            "--format",
            "json",
        ],
    )
    assert run_result.exit_code == 0
    run_payload = json.loads(run_result.output)
    assert run_payload["project_id"] == project_id
    assert run_payload["task_card_id"] == task_card_id
    assert run_payload["mode"] in {"normal", "compensation"}
    assert Path(run_payload["artifact_path"]).exists()
    assert Path(run_payload["report_path"]).exists()

    report_text = report_path.read_text(encoding="utf-8")
    assert "# Resume Agent Card Report" in report_text
    assert "## Scorecard" in report_text
    assert "## Revised Resume Artifact" in report_text
