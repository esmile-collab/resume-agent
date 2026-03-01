"""CLI entrypoint for resume_agent."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

import click

from db.crud import ProjectCRUD
from db.models import Project
from orchestration import ResumeOrchestratorUseCase


def _format_datetime(value: datetime | None) -> str:
    """Format datetime for human-readable CLI output."""
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _project_to_dict(project: Project) -> dict[str, Any]:
    """Serialize project object for JSON output."""
    return {
        "id": project.id,
        "name": project.name,
        "cycle": project.cycle or "",
        "base_resume_path": project.base_resume_path or "",
        "created_at": _format_datetime(project.created_at),
    }


def _echo_not_found(project_id: str) -> NoReturn:
    """Print not-found message and terminate command with non-zero code."""
    click.echo(f"✗ 项目不存在: {project_id}")
    raise click.exceptions.Exit(1)


def _print_projects_table(projects: list[Project]) -> None:
    """Render project list in a simple table format."""
    if not projects:
        click.echo("未找到项目")
        return

    id_width = max(len("ID"), *(len(project.id) for project in projects))
    name_width = max(len("名称"), *(len(project.name) for project in projects))
    cycle_width = max(len("周期"), *(len(project.cycle or "") for project in projects))

    header = f"{'ID':<{id_width}}  {'名称':<{name_width}}  {'周期':<{cycle_width}}  创建时间"
    click.echo(header)
    click.echo("-" * len(header))
    for project in projects:
        click.echo(
            f"{project.id:<{id_width}}  "
            f"{project.name:<{name_width}}  "
            f"{(project.cycle or ''):<{cycle_width}}  "
            f"{_format_datetime(project.created_at)}"
        )


def _print_project_table(project: Project) -> None:
    """Render one project detail in key-value lines."""
    click.echo(f"ID: {project.id}")
    click.echo(f"名称: {project.name}")
    click.echo(f"周期: {project.cycle or ''}")
    click.echo(f"基础简历路径: {project.base_resume_path or ''}")
    click.echo(f"创建时间: {_format_datetime(project.created_at)}")


def _read_text_file(path: Path) -> str:
    """Read UTF-8 text file for resume/JD CLI inputs."""
    return path.read_text(encoding="utf-8")


def _render_card_markdown_report(
    *,
    project_id: str,
    task_card: dict[str, Any],
    run_result: dict[str, Any],
    artifact_content: str,
) -> str:
    """Build markdown card report expected by M5."""
    return "\n".join(
        [
            "# Resume Agent Card Report",
            "",
            "## Summary",
            f"- Project ID: {project_id}",
            f"- Task Card ID: {task_card['task_card_id']}",
            f"- Direction: {task_card['direction_name']}",
            f"- Mode: {run_result.get('mode', '')}",
            f"- Version: v{run_result.get('version', '')}",
            "",
            "## Scorecard",
            f"- Score: {task_card.get('score')}",
            f"- Match Level: {task_card.get('match_level')}",
            "",
            "## Change Log",
            "- M5 stub pipeline: use-case generated one deterministic artifact.",
            "- Evidence is bound to task-card JD references.",
            "",
            "## Revised Resume Artifact",
            artifact_content,
        ]
    )


@click.group()
def cli() -> None:
    """Resume Agent CLI."""


@cli.group()
def project() -> None:
    """项目管理命令。"""


@project.command("init")
@click.option("--name", required=True, help="项目名称")
@click.option("--cycle", default="", help="招聘周期")
@click.option(
    "--resume",
    "resume_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help="基础简历路径（文本/PDF OCR文本）",
)
def project_init(name: str, cycle: str, resume_path: Path | None) -> None:
    """Create a project."""
    use_case = ResumeOrchestratorUseCase()
    resume_text = _read_text_file(resume_path) if resume_path else ""
    created = use_case.init_project(name=name, cycle=cycle, base_resume_text=resume_text)
    click.echo(f"✓ 项目已创建: {created['project_id']}")


@project.command("list")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def project_list(output_format: str) -> None:
    """List all projects."""
    projects = ProjectCRUD().list_all()

    if output_format == "json":
        click.echo(
            json.dumps(
                [_project_to_dict(project) for project in projects], ensure_ascii=False, indent=2
            )
        )
        return

    _print_projects_table(projects)


@project.command("get")
@click.option("--id", "project_id", required=True, help="项目 ID")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def project_get(project_id: str, output_format: str) -> None:
    """Get a single project by ID."""
    project_obj = ProjectCRUD().get(project_id)
    if project_obj is None:
        _echo_not_found(project_id)

    if output_format == "json":
        click.echo(json.dumps(_project_to_dict(project_obj), ensure_ascii=False, indent=2))
        return

    _print_project_table(project_obj)


@project.command("delete")
@click.option("--id", "project_id", required=True, help="项目 ID")
def project_delete(project_id: str) -> None:
    """Delete a project by ID."""
    crud = ProjectCRUD()
    if not crud.delete(project_id):
        _echo_not_found(project_id)

    artifact_root = Path(".data") / "artifacts" / project_id
    if artifact_root.exists():
        shutil.rmtree(artifact_root)
    click.echo(f"✓ 项目已删除: {project_id}")


@project.command("ingest-jd")
@click.option("--project", "project_id", required=True, help="项目 ID")
@click.option(
    "--jd",
    "jd_paths",
    multiple=True,
    required=True,
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    help="JD 文件路径，可重复传入实现批量",
)
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def project_ingest_jd(project_id: str, jd_paths: tuple[Path, ...], output_format: str) -> None:
    """Ingest JD files and create allocation preview."""
    use_case = ResumeOrchestratorUseCase()
    try:
        result = use_case.ingest_jds(
            project_id=project_id,
            jd_texts=[_read_text_file(path) for path in jd_paths],
            source_files=[path.name for path in jd_paths],
        )
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    preview = result["preview"]
    click.echo("✓ JD 已接入，等待确认分配")
    click.echo(f"Plan ID: {result['plan_id']}")
    click.echo(f"JD 数量: {preview['jd_count']}")
    click.echo(f"方向数量: {preview['direction_count']}")
    click.echo(f"预计输出简历数: {preview['resume_output_count']}")


@project.command("confirm-allocation")
@click.option("--project", "project_id", required=True, help="项目 ID")
@click.option("--plan", "plan_id", required=True, help="分配计划 ID")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def project_confirm_allocation(project_id: str, plan_id: str, output_format: str) -> None:
    """Confirm one allocation plan and materialize task cards."""
    use_case = ResumeOrchestratorUseCase()
    try:
        result = use_case.confirm_allocation(project_id=project_id, plan_id=plan_id)
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    click.echo("✓ 分配已确认")
    click.echo(f"方向数量: {result['direction_count']}")
    click.echo(f"预计输出简历数: {result['resume_output_count']}")
    click.echo("Task Cards:")
    for card in result["task_cards"]:
        click.echo(f"  - {card['task_card_id']}: {card['direction_name']}")


@cli.group()
def card() -> None:
    """卡片级命令。"""


@card.command("add-jd")
@click.option("--project", "project_id", required=True, help="项目 ID")
@click.option("--card", "task_card_id", required=True, help="任务卡片 ID")
@click.option(
    "--jd",
    "jd_path",
    required=True,
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    help="新增 JD 文件路径",
)
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def card_add_jd(project_id: str, task_card_id: str, jd_path: Path, output_format: str) -> None:
    """Add JD from card entry, still routed by project-level allocator."""
    use_case = ResumeOrchestratorUseCase()
    try:
        result = use_case.ingest_jds(
            project_id=project_id,
            jd_texts=[_read_text_file(jd_path)],
            source_files=[jd_path.name],
        )
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    payload = {
        "source_task_card_id": task_card_id,
        **result,
    }
    if output_format == "json":
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    click.echo("✓ 已接收卡片内新增 JD（已上收至 Project 分配流程）")
    click.echo(f"Source Card: {task_card_id}")
    click.echo(f"Plan ID: {result['plan_id']}")
    click.echo("请执行: resume_agent project confirm-allocation --project <id> --plan <plan_id>")


@card.command("run")
@click.option("--project", "project_id", required=True, help="项目 ID")
@click.option("--card", "task_card_id", required=True, help="任务卡片 ID")
@click.option(
    "--out",
    "out_path",
    required=True,
    type=click.Path(path_type=Path, dir_okay=False, writable=True),
    help="输出 Markdown 报告路径",
)
@click.option(
    "--resume",
    "resume_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True),
    default=None,
    help="可选：覆盖使用的简历文本路径",
)
@click.option("--risk-ack", is_flag=True, default=False, help="低匹配场景确认风险并继续补偿模式")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def card_run(
    project_id: str,
    task_card_id: str,
    out_path: Path,
    resume_path: Path | None,
    risk_ack: bool,
    output_format: str,
) -> None:
    """Run one task card and write markdown report."""
    use_case = ResumeOrchestratorUseCase()
    resume_text = _read_text_file(resume_path) if resume_path else ""

    try:
        result = use_case.run_card(
            project_id=project_id,
            task_card_id=task_card_id,
            resume_text=resume_text,
            risk_ack=risk_ack,
        )
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if result.get("await_risk_ack", False):
        click.echo(str(result.get("message", "需要风险确认")))
        click.echo("如确认继续，请追加参数: --risk-ack")
        raise click.exceptions.Exit(1)

    artifact_path = Path(str(result["output_path"]))
    artifact_content = artifact_path.read_text(encoding="utf-8")
    task_cards = use_case.list_task_cards(project_id)
    target_card = next(card for card in task_cards if card["task_card_id"] == task_card_id)

    report = _render_card_markdown_report(
        project_id=project_id,
        task_card=target_card,
        run_result=result,
        artifact_content=artifact_content,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    payload = {
        "project_id": project_id,
        "task_card_id": task_card_id,
        "mode": result.get("mode"),
        "version": result.get("version"),
        "artifact_path": str(artifact_path),
        "report_path": str(out_path),
    }
    if output_format == "json":
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    click.echo(f"✓ 卡片运行完成: {task_card_id}")
    click.echo(f"模式: {result.get('mode')}")
    click.echo(f"报告输出: {out_path}")


if __name__ == "__main__":
    cli()
