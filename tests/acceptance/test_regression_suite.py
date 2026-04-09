# Input: runtime、SQLite 环境和稳定场景样本。
# Output: 验证背景捕获、JD 入库、评分生成和轨道管理回归。
# Pos: 主链回归验收测试。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Stable regression scenarios for the current agent architecture."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from src.agent.runtime import ResumeAgentRuntime
from src.db.database import DB_PATH, init_db

ARTIFACTS_ROOT = Path(".data") / "artifacts"
UPLOADS_ROOT = Path(".data") / "uploads"


def setup_function() -> None:
    """Reset persistence before each regression scenario."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if ARTIFACTS_ROOT.exists():
        shutil.rmtree(ARTIFACTS_ROOT)
    if UPLOADS_ROOT.exists():
        shutil.rmtree(UPLOADS_ROOT)
    init_db().close()


def _start_runtime_session() -> tuple[ResumeAgentRuntime, str]:
    runtime = ResumeAgentRuntime()
    started = runtime.start_session(
        project_name="regression-suite",
        cycle="2026秋招",
        base_resume_text="工作经历\n负责增长分析和经营复盘\n教育背景\n本科",
    )
    return runtime, started["session_id"]


def test_regression_background_capture() -> None:
    """Background information should consistently land in structured memory."""
    runtime, session_id = _start_runtime_session()

    result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content=(
            "我想投策略产品，base在上海，有2年产品经验，本科。"
            "我在某互联网公司做过增长项目，推动转化率提升20%。"
        ),
    )

    snapshot = result["snapshot"]
    assert result["intent"]["intent"] == "add_info"
    assert snapshot["profile"]["basics"]["education"] == "本科"
    assert snapshot["profile"]["preferences"]["preferred_city"] == "上海"
    assert "策略产品" in snapshot["profile"]["preferences"]["target_roles"]
    assert len(snapshot["experiences"]) >= 1


def test_regression_jd_ingest_sets_primary_jd() -> None:
    """JD ingest should create a track link and set a primary JD when missing."""
    runtime, session_id = _start_runtime_session()

    ingest = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="这是策略产品 JD",
        attachments=[
            {
                "type": "jd",
                "name": "strategy_jd.txt",
                "content": "岗位职责：负责增长策略和商业化分析。任职要求：2年以上产品经验。",
            }
        ],
    )

    observation = ingest["tool_steps"][0]["observation"]
    snapshot = ingest["snapshot"]
    track = next(item for item in snapshot["tracks"] if item["id"] == observation["track_id"])
    assert observation["ok"] is True
    assert track["primary_jd_entry_id"] == observation["jd_entry_id"]
    assert track["jd_count"] == 1


def test_regression_score_generate_and_polish_flow() -> None:
    """Score, generate, polish, and export should keep producing usable artifacts."""
    runtime, session_id = _start_runtime_session()

    runtime.handle_message(
        session_id=session_id,
        role="user",
        content="这是商业分析 JD",
        attachments=[
            {
                "type": "jd",
                "name": "ba_jd.txt",
                "content": "岗位职责：负责经营分析、SQL 建模和策略拆解。任职要求：2年分析经验。",
            }
        ],
    )
    track_id = runtime.get_session_snapshot(session_id)["snapshot"]["tracks"][0]["id"]

    score_result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="请帮我评分",
        active_track_id=track_id,
    )
    score_observation = score_result["tool_steps"][0]["observation"]
    assert score_observation["ok"] is True
    assert score_observation["artifact"]["artifact_type"] == "score_report"
    assert Path(score_observation["artifact"]["path"]).exists()

    generate_result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="请生成简历",
        active_track_id=track_id,
    )
    generated = generate_result["tool_steps"][-1]["observation"]
    assert generated["ok"] is True
    assert generated["artifact"]["artifact_type"] == "generated_resume"
    assert Path(generated["artifact"]["path"]).exists()

    polish_result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="请继续润色",
        active_track_id=track_id,
    )
    polished = polish_result["tool_steps"][-1]["observation"]
    assert polished["ok"] is True
    assert polished["artifact"]["artifact_type"] == "polished_resume"
    assert len(polished["patches"]) >= 1
    assert Path(polished["artifact"]["path"]).exists()
    export_docx = runtime.memory.export_artifact(
        artifact_id=polished["artifact"]["id"],
        export_format="docx",
    )
    export_pdf = runtime.memory.export_artifact(
        artifact_id=polished["artifact"]["id"],
        export_format="pdf",
    )
    assert Path(export_docx["path"]).exists()
    assert Path(export_pdf["path"]).exists()

    final_snapshot = runtime.get_session_snapshot(session_id)["snapshot"]
    artifact_types = [artifact["artifact_type"] for artifact in final_snapshot["artifacts"]]
    assert "score_report" in artifact_types
    assert "generated_resume" in artifact_types
    assert "polished_resume" in artifact_types


def test_regression_track_management_after_dialog_memory() -> None:
    """Manual track CRUD should remain compatible with tracks inferred from dialog."""
    runtime, session_id = _start_runtime_session()
    project_id = runtime.get_session_snapshot(session_id)["project_id"]

    runtime.handle_message(
        session_id=session_id,
        role="user",
        content="求职方向：内容运营。我做过社区活动策划。",
    )

    created = runtime.memory.create_track(
        project_id=project_id,
        name="用户增长",
        positioning="聚焦增长与留存。",
        core_keywords=["增长", "留存", "转化"],
        resume_strategy="突出实验和结果。",
        default_resume_outline="1. 摘要\n2. 核心经历\n3. 能力",
    )
    updated = runtime.memory.update_track(
        track_id=created["id"],
        name="用户增长",
        positioning="聚焦增长、留存与转化分析。",
        core_keywords=["增长", "留存", "转化", "分析"],
        resume_strategy="突出实验设计、复盘和指标结果。",
        default_resume_outline="1. 摘要\n2. 项目\n3. 技能",
    )

    assert updated["positioning"].endswith("转化分析。")
    snapshot = runtime.get_session_snapshot(session_id)["snapshot"]
    track_names = [track["name"] for track in snapshot["tracks"]]
    assert "内容运营" in track_names
    assert "用户增长" in track_names
