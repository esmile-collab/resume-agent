# Input: click、runtime 和数据库初始化能力。
# Output: 输出命令行子命令与本地调试入口。
# Pos: 仓库 CLI 主入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""CLI entrypoint for the current session/message based resume agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from agent.runtime import ResumeAgentRuntime
from db.database import init_db


def _read_text_file(path: Path) -> str:
    """Read one UTF-8 text file."""
    return path.read_text(encoding="utf-8")


def _echo_json(payload: dict[str, Any]) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@click.group()
def cli() -> None:
    """Resume Agent CLI."""


@cli.command("serve")
@click.option("--host", default="127.0.0.1", show_default=True, help="监听地址")
@click.option("--port", default=8000, show_default=True, type=int, help="监听端口")
@click.option("--reload/--no-reload", default=False, show_default=True, help="开发热更新")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the HTTP API used by the React frontend."""
    import uvicorn

    uvicorn.run("api.main:app", host=host, port=port, reload=reload)


@cli.group()
def session() -> None:
    """Session-based runtime commands."""


@cli.command("init-db")
def init_database() -> None:
    """Initialize the SQLite database and print the target path."""
    conn = init_db()
    db_path = Path(conn.execute("PRAGMA database_list").fetchone()[2])
    conn.close()
    click.echo(f"initialized: {db_path}")


@session.command("start")
@click.option("--project-id", default="", help="已有项目 ID")
@click.option("--name", "project_name", default="简历 Agent 项目", help="项目名称")
@click.option("--cycle", default="", help="招聘周期")
@click.option(
    "--resume",
    "resume_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help="基础简历文件路径",
)
def session_start(project_id: str, project_name: str, cycle: str, resume_path: Path | None) -> None:
    """Create a new agent session."""
    runtime = ResumeAgentRuntime()
    result = runtime.start_session(
        project_id=project_id,
        project_name=project_name,
        cycle=cycle,
        base_resume_text=_read_text_file(resume_path) if resume_path else "",
    )
    _echo_json(result)


@session.command("send")
@click.option("--session-id", required=True, help="会话 ID")
@click.option("--message", required=True, help="用户消息")
@click.option(
    "--jd",
    "jd_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help="附加 JD 文件",
)
@click.option(
    "--resume",
    "resume_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help="附加简历文件",
)
@click.option("--track-id", default="", help="激活方向 ID")
@click.option("--track-name", default="", help="激活方向名称")
def session_send(
    session_id: str,
    message: str,
    jd_path: Path | None,
    resume_path: Path | None,
    track_id: str,
    track_name: str,
) -> None:
    """Send a message into the agent runtime."""
    attachments: list[dict[str, str]] = []
    if jd_path:
        attachments.append({"type": "jd", "content": _read_text_file(jd_path), "name": jd_path.name})
    if resume_path:
        attachments.append(
            {"type": "resume", "content": _read_text_file(resume_path), "name": resume_path.name}
        )
    runtime = ResumeAgentRuntime()
    result = runtime.handle_message(
        session_id=session_id,
        role="user",
        content=message,
        attachments=attachments,
        active_track_id=track_id,
        active_track_name=track_name,
    )
    _echo_json(result)


@session.command("snapshot")
@click.option("--session-id", required=True, help="会话 ID")
def session_snapshot(session_id: str) -> None:
    """Print the current session snapshot."""
    runtime = ResumeAgentRuntime()
    _echo_json(runtime.get_session_snapshot(session_id))


@session.command("list")
@click.option("--limit", default=20, show_default=True, type=int, help="返回会话数量")
def session_list(limit: int) -> None:
    """List recent sessions."""
    runtime = ResumeAgentRuntime()
    _echo_json(runtime.list_sessions(limit=limit))
