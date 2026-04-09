# Input: runtime、SQLite 环境和文件产物目录。
# Output: 验证 think-call-observe 主链能完整跑通。
# Pos: 现行运行时验收测试。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Acceptance tests for the new session/message runtime."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from src.agent.runtime import ResumeAgentRuntime
from src.db.database import DB_PATH, init_db

ARTIFACTS_ROOT = Path(".data") / "artifacts"


def setup_function() -> None:
    """Reset DB and artifacts before each test."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if ARTIFACTS_ROOT.exists():
        shutil.rmtree(ARTIFACTS_ROOT)
    init_db().close()


def test_agent_runtime_loop_end_to_end() -> None:
    """Should finish a think-call-observe loop across ingest/score/generate/polish."""
    runtime = ResumeAgentRuntime()

    started = runtime.start_session(
        project_name="agent-runtime-e2e",
        cycle="2026秋招",
        base_resume_text="工作经历\n负责增长分析和项目推进\n教育背景\n本科",
    )
    session_id = started["session_id"]

    info_result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="我想投策略产品，我有2年产品经验，在某互联网公司负责增长项目，提升转化率20%。",
    )
    assert "策略产品" in info_result["reply"]
    assert len(info_result["memory_updates"]["new_experience_ids"]) == 1

    ingest_result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="这是一个策略产品 JD",
        attachments=[
            {
                "type": "jd",
                "content": (
                    "岗位职责：负责增长策略制定和商业化分析。"
                    "任职要求：2年以上产品经验，数据分析能力强。"
                ),
                "name": "strategy_pm.txt",
            }
        ],
    )
    assert ingest_result["intent"]["intent"] == "ingest_jd"
    assert ingest_result["tool_steps"][0]["observation"]["track_name"] == "策略产品"

    score_result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="请帮我评分",
    )
    assert score_result["intent"]["intent"] == "score_resume"
    assert score_result["tool_steps"][0]["observation"]["ok"] is True
    assert score_result["tool_steps"][0]["observation"]["match_level"] in {"high", "medium", "low"}

    generate_result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="请生成简历",
    )
    generated = generate_result["tool_steps"][-1]["observation"]
    assert generated["ok"] is True
    assert Path(generated["artifact"]["path"]).exists()

    polish_result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="请继续润色",
    )
    polished = polish_result["tool_steps"][-1]["observation"]
    assert polished["ok"] is True
    assert len(polished["patches"]) >= 1
    assert Path(polished["artifact"]["path"]).exists()

    snapshot = runtime.get_session_snapshot(session_id)
    trace_kinds = [trace["kind"] for trace in snapshot["traces"]]
    assert "thought" in trace_kinds
    assert "tool_call" in trace_kinds
    assert "observation" in trace_kinds


def test_agent_runtime_snapshot_contains_memory_layers() -> None:
    """Snapshot should expose profile, tracks, experiences, and artifacts."""
    runtime = ResumeAgentRuntime()
    started = runtime.start_session(project_name="agent-runtime-memory", cycle="2026秋招")
    session_id = started["session_id"]

    _ = runtime.handle_message(
        session_id=session_id,
        role="user",
        content="求职方向：内容运营。我有一段社区项目经历，负责活动策划，带来15%留存提升。",
    )

    snapshot = runtime.get_session_snapshot(session_id)["snapshot"]
    assert snapshot["profile"]["preferences"]["target_roles"] == ["内容运营"]
    assert len(snapshot["experiences"]) == 1
    assert snapshot["tracks"][0]["name"] == "内容运营"
