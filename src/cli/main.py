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
from orchestration import ResumeOrchestratorUseCase, ResumePolisherUseCase
from scoring import CampusScorerV21
from scoring.models import ScoreReport


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
def resume() -> None:
    """简历级命令（M8 Resume Polisher MVP）。"""


@resume.command("init")
@click.option("--name", required=True, help="简历名称")
@click.option("--file", "resume_path", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True), help="简历文本文件")
@click.option("--user-id", default="local_user", help="用户 ID")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def resume_init(name: str, resume_path: Path, user_id: str, output_format: str) -> None:
    """Create resume root and version1 from uploaded text."""
    use_case = ResumePolisherUseCase()
    result = use_case.create_resume(user_id=user_id, name=name, resume_text=_read_text_file(resume_path))

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    click.echo(f"✓ 简历已创建: {result['resume']['id']}")
    click.echo(f"当前版本: {result['active_version']['id']}")


@resume.command("list")
@click.option("--user-id", default="local_user", help="用户 ID")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def resume_list(user_id: str, output_format: str) -> None:
    """List resumes by user."""
    use_case = ResumePolisherUseCase()
    resumes = use_case.list_resumes(user_id=user_id)

    if output_format == "json":
        click.echo(json.dumps(resumes, ensure_ascii=False, indent=2))
        return

    if not resumes:
        click.echo("未找到简历")
        return
    click.echo("ID               名称")
    click.echo("---------------- --------")
    for item in resumes:
        click.echo(f"{item['id']:<16} {item['name']}")


@resume.command("get")
@click.option("--id", "resume_id", required=True, help="简历 ID")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def resume_get(resume_id: str, output_format: str) -> None:
    """Get resume detail with version history."""
    use_case = ResumePolisherUseCase()
    try:
        result = use_case.get_resume(resume_id=resume_id)
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    click.echo(f"ID: {result['resume']['id']}")
    click.echo(f"名称: {result['resume']['name']}")
    click.echo(f"当前版本: {result['resume']['active_version_id']}")
    click.echo(f"版本数: {len(result['versions'])}")


@cli.group()
def task() -> None:
    """JD 任务卡命令（M8 Resume Polisher MVP）。"""


@task.command("create")
@click.option("--resume-id", required=True, help="简历 ID")
@click.option("--title", required=True, help="任务标题")
@click.option("--jd", "jd_path", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True), help="JD 文件")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def task_create(resume_id: str, title: str, jd_path: Path, output_format: str) -> None:
    """Create one JD task for a resume."""
    use_case = ResumePolisherUseCase()
    try:
        result = use_case.create_task(resume_id=resume_id, title=title, jd_text=_read_text_file(jd_path))
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    click.echo(f"✓ 任务已创建: {result['task']['id']}")


@task.command("list")
@click.option("--resume-id", required=True, help="简历 ID")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def task_list(resume_id: str, output_format: str) -> None:
    """List tasks under one resume."""
    use_case = ResumePolisherUseCase()
    tasks = use_case.list_tasks(resume_id=resume_id)

    if output_format == "json":
        click.echo(json.dumps(tasks, ensure_ascii=False, indent=2))
        return

    if not tasks:
        click.echo("未找到任务卡")
        return
    click.echo("ID                 标题                状态")
    click.echo("------------------ ------------------- ------------")
    for item in tasks:
        click.echo(f"{item['id']:<18} {item['title'][:19]:<19} {item['status']}")


@task.command("analyze")
@click.option("--task-id", required=True, help="任务 ID")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def task_analyze(task_id: str, output_format: str) -> None:
    """Run non-scoring analysis for a task."""
    use_case = ResumePolisherUseCase()
    try:
        result = use_case.analyze_task(task_id=task_id)
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    insight = result["insight"]
    click.echo(f"✓ 分析完成: {task_id}")
    click.echo(f"优势: {len(insight['strengths'])} 条")
    click.echo(f"不足: {len(insight['gaps'])} 条")
    click.echo(f"建议: {len(insight['actions'])} 条")


@task.command("polish")
@click.option("--task-id", required=True, help="任务 ID")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def task_polish(task_id: str, output_format: str) -> None:
    """Generate block-level polish patches."""
    use_case = ResumePolisherUseCase()
    try:
        result = use_case.polish_task(task_id=task_id)
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    click.echo(f"✓ Patch 生成完成: {task_id}")
    click.echo(f"Patch 数量: {len(result['patches'])}")


@task.command("apply-patch")
@click.option("--task-id", required=True, help="任务 ID")
@click.option("--patch-id", "patch_ids", multiple=True, required=True, help="Patch ID，可重复")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def task_apply_patch(task_id: str, patch_ids: tuple[str, ...], output_format: str) -> None:
    """Apply selected patches and create new version."""
    use_case = ResumePolisherUseCase()
    try:
        result = use_case.apply_patches(task_id=task_id, patch_ids=list(patch_ids))
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    click.echo(f"✓ 已应用 {result['applied_count']} 个 patch")
    click.echo(f"新版本: {result['new_version']['id']}")


@task.command("rollback")
@click.option("--task-id", required=True, help="任务 ID")
@click.option("--version-id", required=True, help="目标版本 ID")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def task_rollback(task_id: str, version_id: str, output_format: str) -> None:
    """Rollback task resume pointer to one existing version."""
    use_case = ResumePolisherUseCase()
    try:
        result = use_case.rollback_task(task_id=task_id, target_version_id=version_id)
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    click.echo(f"✓ 已回滚到版本: {result['active_version_id']}")


@task.command("export")
@click.option("--task-id", required=True, help="任务 ID")
@click.option("--output", "output_path", required=True, type=click.Path(path_type=Path, dir_okay=False, writable=True), help="导出路径")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table")
def task_export(task_id: str, output_path: Path, output_format: str) -> None:
    """Export current task resume to markdown."""
    use_case = ResumePolisherUseCase()
    try:
        result = use_case.export_task(task_id=task_id, output_path=str(output_path))
    except ValueError as exc:
        click.echo(f"✗ {exc}")
        raise click.exceptions.Exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    click.echo(f"✓ 已导出: {result['output_path']}")


@cli.group()
def score() -> None:
    """校招评分命令（混合评分系统 v2.1）。"""


@score.command("evaluate")
@click.option("--jd", "jd_path", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True), help="JD 文件路径")
@click.option("--resume", "resume_path", required=True, type=click.Path(path_type=Path, exists=True, dir_okay=False, readable=True), help="简历文件路径")
@click.option("--output", "output_path", type=click.Path(path_type=Path, dir_okay=False, writable=True), help="输出报告路径（可选，默认打印到终端）")
@click.option("--format", "output_format", type=click.Choice(["json", "markdown", "table"]), default="markdown", help="输出格式")
@click.option("--rule-weight", default=0.4, type=float, help="规则评分权重（0.35-0.5，默认 0.4）")
@click.option("--model", default=None, help="LLM 模型（默认 claude-3.5-sonnet）")
def score_evaluate(jd_path: Path, resume_path: Path, output_path: Path | None, output_format: str, rule_weight: float, model: str | None) -> None:
    """评估简历与 JD 的匹配度（校招版 v2.1）。

    使用混合评分系统：
    - 硬性指标（规则评分）：实习、项目、技术实践、学历等
    - 软性指标（LLM 评分）：学习能力、执行能力、沟通表达等

    示例：
        resume_agent score evaluate --jd jd.txt --resume resume.txt
        resume_agent score evaluate --jd jd.txt --resume resume.txt --output report.md
        resume_agent score evaluate --jd jd.txt --resume resume.txt --format json
    """
    scorer = CampusScorerV21(model=model)
    jd_text = _read_text_file(jd_path)
    resume_text = _read_text_file(resume_path)

    click.echo("正在评估...")
    report = scorer.score(jd=jd_text, resume=resume_text, rule_weight=rule_weight)

    if output_format == "json":
        output = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    elif output_format == "markdown":
        output = report.to_markdown()
    else:  # table
        output = _format_score_table(report)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        click.echo(f"✓ 评估完成，报告已保存到: {output_path}")
    else:
        click.echo("\n" + output)


def _format_score_table(report: ScoreReport) -> str:
    """Format score report as simple table."""
    lines = [
        "## 简历评分报告",
        "",
        f"总分: {report.final_score:.1f}/100  |  评级: {report.match_level}  |  建议: {report.suggestion}",
        "",
    ]

    if report.risk_warning:
        lines.append(f"⚠️  {report.risk_warning}")
        lines.append("")

    if report.hard_metrics:
        lines.extend([
            "## 硬性指标",
            f"总分: {report.hard_metrics.total_score:.1f}/100",
            "",
            "实习: {:.0f}/100  |  项目: {:.0f}/100  |  技术实践: {:.0f}/100".format(
                report.hard_metrics.internship_score,
                report.hard_metrics.project_score,
                report.hard_metrics.technical_practice_score,
            ),
            "学历: {:.0f}/100  |  专业: {:.0f}/100  |  GPA: {:.0f}/100".format(
                report.hard_metrics.education_score,
                report.hard_metrics.major_score,
                report.hard_metrics.gpa_score,
            ),
            "",
        ])

    if report.soft_metrics:
        lines.extend([
            "## 软性能力",
            f"总分: {report.soft_metrics.total_score:.1f}/100",
            "",
            "学习: {:.0f}/100  |  执行: {:.0f}/100  |  沟通: {:.0f}/100".format(
                report.soft_metrics.learning_ability,
                report.soft_metrics.execution,
                report.soft_metrics.communication,
            ),
            "数据: {:.0f}/100  |  稳定: {:.0f}/100  |  适配: {:.0f}/100".format(
                report.soft_metrics.data_awareness,
                report.soft_metrics.stability,
                report.soft_metrics.adaptability,
            ),
            "",
        ])

    if report.quick_improvements:
        lines.extend(["## 立即改进", ""] + [f"{i}. {item}" for i, item in enumerate(report.quick_improvements, 1)] + [""])

    if report.long_term_improvements:
        lines.extend(["## 长期提升", ""] + [f"{i}. {item}" for i, item in enumerate(report.long_term_improvements, 1)] + [""])

    return "\n".join(lines)


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
