"""M6 local web API entrypoint with one /run endpoint."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

from orchestration import ResumeOrchestratorUseCase

ActionType = Literal[
    "project.init",
    "project.ingest_jd",
    "project.confirm_allocation",
    "card.add_jd",
    "card.run",
    "dialog.append",
]


class RunRequest(BaseModel):
    """Generic /run request envelope for all supported actions."""

    action: ActionType
    project_id: str = ""
    name: str = ""
    cycle: str = ""
    plan_id: str = ""
    task_card_id: str = ""
    jd_texts: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)
    jd_text: str = ""
    source_file: str = ""
    resume_text: str = ""
    risk_ack: bool = False
    role: str = "user"
    content: str = ""
    facts: list[str] = Field(default_factory=list)
    artifact_version_id: str = ""

    @model_validator(mode="after")
    def validate_required_fields(self) -> "RunRequest":
        """Validate action-level required fields to keep payload strict."""
        if self.action == "project.init" and not self.name:
            raise ValueError("name is required for project.init")

        if self.action == "project.ingest_jd":
            if not self.project_id:
                raise ValueError("project_id is required for project.ingest_jd")
            if not self.jd_texts:
                raise ValueError("jd_texts cannot be empty for project.ingest_jd")

        if self.action == "project.confirm_allocation":
            if not self.project_id:
                raise ValueError("project_id is required for project.confirm_allocation")
            if not self.plan_id:
                raise ValueError("plan_id is required for project.confirm_allocation")

        if self.action == "card.add_jd":
            if not self.project_id:
                raise ValueError("project_id is required for card.add_jd")
            if not self.task_card_id:
                raise ValueError("task_card_id is required for card.add_jd")
            if not self.jd_text:
                raise ValueError("jd_text is required for card.add_jd")

        if self.action == "card.run":
            if not self.project_id:
                raise ValueError("project_id is required for card.run")
            if not self.task_card_id:
                raise ValueError("task_card_id is required for card.run")

        if self.action == "dialog.append":
            if not self.project_id:
                raise ValueError("project_id is required for dialog.append")
            if not self.content.strip():
                raise ValueError("content is required for dialog.append")

        return self


class RunResponse(BaseModel):
    """Unified /run response shape for dialogue-first API output."""

    action: ActionType
    recommendation: str
    data: dict[str, Any]
    task_cards: list[dict[str, Any]] = Field(default_factory=list)


app = FastAPI(
    title="Resume Agent Local API",
    version="0.1.0",
    description="M6 local web API. Reuses the same orchestration core as CLI.",
)


def _status_code_from_error(message: str) -> int:
    """Map common domain errors to HTTP status."""
    lowered = message.lower()
    if "not found" in lowered:
        return 404
    return 400


@app.get("/health")
def health() -> dict[str, str]:
    """Basic liveness check for local runs."""
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run(payload: RunRequest) -> RunResponse:
    """Dispatch one action to shared orchestration use cases."""
    use_case = ResumeOrchestratorUseCase()
    task_cards: list[dict[str, Any]] = []

    try:
        if payload.action == "project.init":
            result = use_case.init_project(
                name=payload.name,
                cycle=payload.cycle,
                base_resume_text=payload.resume_text,
            )
            recommendation = "项目已创建，建议上传 JD 并预览方向分配。"
            return RunResponse(
                action=payload.action,
                recommendation=recommendation,
                data=result,
                task_cards=[],
            )

        if payload.action == "project.ingest_jd":
            result = use_case.ingest_jds(
                project_id=payload.project_id,
                jd_texts=payload.jd_texts,
                source_files=payload.source_files or None,
            )
            task_cards = use_case.list_task_cards(payload.project_id)
            recommendation = "已生成分配预览，请先确认 allocation plan。"
            return RunResponse(
                action=payload.action,
                recommendation=recommendation,
                data=result,
                task_cards=task_cards,
            )

        if payload.action == "project.confirm_allocation":
            result = use_case.confirm_allocation(
                project_id=payload.project_id,
                plan_id=payload.plan_id,
            )
            task_cards = use_case.list_task_cards(payload.project_id)
            recommendation = "分配已确认，建议先评分再运行卡片。"
            return RunResponse(
                action=payload.action,
                recommendation=recommendation,
                data=result,
                task_cards=task_cards,
            )

        if payload.action == "card.add_jd":
            result = use_case.ingest_jds(
                project_id=payload.project_id,
                jd_texts=[payload.jd_text],
                source_files=[payload.source_file or "card_add_jd.txt"],
            )
            merged = {"source_task_card_id": payload.task_card_id, **result}
            task_cards = use_case.list_task_cards(payload.project_id)
            recommendation = "已接收新增 JD，请确认新的 allocation plan。"
            return RunResponse(
                action=payload.action,
                recommendation=recommendation,
                data=merged,
                task_cards=task_cards,
            )

        if payload.action == "dialog.append":
            result = use_case.append_dialog_turn(
                project_id=payload.project_id,
                role=payload.role,
                content=payload.content,
                facts=payload.facts,
                artifact_version_id=payload.artifact_version_id,
            )
            recommendation = (
                "对话已记录并完成压缩，后续可继续稳定对话。"
                if result.get("compressed")
                else "对话已记录。"
            )
            return RunResponse(
                action=payload.action,
                recommendation=recommendation,
                data=result,
                task_cards=use_case.list_task_cards(payload.project_id),
            )

        result = use_case.run_card(
            project_id=payload.project_id,
            task_card_id=payload.task_card_id,
            resume_text=payload.resume_text,
            risk_ack=payload.risk_ack,
        )
        task_cards = use_case.list_task_cards(payload.project_id)
        recommendation = (
            str(result.get("message", "当前匹配较低，请确认风险后继续。"))
            if result.get("await_risk_ack", False)
            else "卡片已生成，建议查看输出并准备投递。"
        )
        return RunResponse(
            action=payload.action,
            recommendation=recommendation,
            data=result,
            task_cards=task_cards,
        )

    except ValueError as exc:
        raise HTTPException(status_code=_status_code_from_error(str(exc)), detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=False)
