"""CLI entrypoint for resume_agent."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, NoReturn

import click

from src.db.crud import ProjectCRUD
from src.db.models import Project


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


@click.group()
def cli() -> None:
    """Resume Agent CLI."""


@cli.group()
def project() -> None:
    """项目管理命令。"""


@project.command("init")
@click.option("--name", required=True, help="项目名称")
@click.option("--cycle", default="", help="招聘周期")
def project_init(name: str, cycle: str) -> None:
    """Create a project."""
    created = ProjectCRUD().create(name=name, cycle=cycle)
    click.echo(f"✓ 项目已创建: {created.id}")


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
    click.echo(f"✓ 项目已删除: {project_id}")


if __name__ == "__main__":
    cli()
