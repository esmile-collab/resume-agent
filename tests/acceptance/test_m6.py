"""M6 acceptance tests for local web API."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app
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


def test_m6_api_run_e2e() -> None:
    """Should complete one full flow via POST /run with shared core logic."""
    client = TestClient(app)
    resume_text = _fixture_text("tests/fixtures/resume/sample_resume_001.txt")
    jd_1 = _fixture_text("tests/fixtures/jd/sample_jd_001.txt")
    jd_2 = _fixture_text("tests/fixtures/jd/sample_jd_002.txt")

    init_resp = client.post(
        "/run",
        json={
            "action": "project.init",
            "name": "m6-api-project",
            "cycle": "2026秋招",
            "resume_text": resume_text,
        },
    )
    assert init_resp.status_code == 200
    init_payload = init_resp.json()
    project_id = init_payload["data"]["project_id"]
    assert init_payload["recommendation"]

    ingest_resp = client.post(
        "/run",
        json={
            "action": "project.ingest_jd",
            "project_id": project_id,
            "jd_texts": [jd_1, jd_2],
            "source_files": ["sample_jd_001.txt", "sample_jd_002.txt"],
        },
    )
    assert ingest_resp.status_code == 200
    ingest_payload = ingest_resp.json()
    assert ingest_payload["data"]["need_user_confirm"] is True
    assert ingest_payload["data"]["preview"]["jd_count"] == 2
    plan_id = ingest_payload["data"]["plan_id"]

    confirm_resp = client.post(
        "/run",
        json={
            "action": "project.confirm_allocation",
            "project_id": project_id,
            "plan_id": plan_id,
        },
    )
    assert confirm_resp.status_code == 200
    confirm_payload = confirm_resp.json()
    assert confirm_payload["data"]["direction_count"] == 2
    assert len(confirm_payload["task_cards"]) == 2
    task_card_id = confirm_payload["task_cards"][0]["task_card_id"]

    run_resp = client.post(
        "/run",
        json={
            "action": "card.run",
            "project_id": project_id,
            "task_card_id": task_card_id,
        },
    )
    assert run_resp.status_code == 200
    run_payload = run_resp.json()
    run_data = run_payload["data"]
    if run_data.get("await_risk_ack"):
        rerun_resp = client.post(
            "/run",
            json={
                "action": "card.run",
                "project_id": project_id,
                "task_card_id": task_card_id,
                "risk_ack": True,
            },
        )
        assert rerun_resp.status_code == 200
        run_payload = rerun_resp.json()
        run_data = run_payload["data"]

    assert run_data["await_risk_ack"] is False
    assert run_data["mode"] in {"normal", "compensation"}
    assert Path(run_data["output_path"]).exists()


def test_m6_openapi_contains_run_endpoint() -> None:
    """OpenAPI schema should expose POST /run for frontend integration."""
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert "/run" in schema["paths"]
    assert "post" in schema["paths"]["/run"]


def test_m6_run_payload_validation() -> None:
    """Invalid action payload should return schema validation error."""
    client = TestClient(app)

    response = client.post(
        "/run",
        json={
            "action": "project.ingest_jd",
        },
    )

    assert response.status_code == 422
