"""Task router and state transition logic for M2."""

from __future__ import annotations

from typing import Optional

from src.models.routing import RouteDecision, ScoreCard
from src.routes.intent import Intent, TaskState


def handle_generate(task_state: TaskState, score_card: Optional[ScoreCard]) -> RouteDecision:
    """Handle generate intent based on score level."""
    if task_state != TaskState.SCORED or score_card is None:
        return RouteDecision(
            state=task_state,
            message="请先完成评分",
            actions=[],
        )

    match_level = score_card.match_level.lower().strip()
    if match_level in {"high", "medium"}:
        return RouteDecision(
            state=TaskState.GENERATING,
            mode="normal",
            message="正在生成简历...",
            actions=[],
        )

    if match_level == "low":
        return RouteDecision(
            state=TaskState.SCORED,
            await_risk_ack=True,
            message=f"匹配度较低（{score_card.score}/100），请确认是否继续",
            actions=["确认生成", "取消"],
        )

    return RouteDecision(
        state=TaskState.SCORED,
        message="评分结果异常，请先重新评分",
        actions=["重新评分"],
    )


def handle_risk_acknowledgement(confirmed: bool, score_card: ScoreCard) -> RouteDecision:
    """Handle explicit user acknowledgement for low-match generation."""
    if confirmed:
        return RouteDecision(
            state=TaskState.GENERATING,
            mode="compensation",
            warning=True,
            message=f"已确认低匹配风险（{score_card.score}/100），进入补偿模式生成",
            actions=[],
        )

    return RouteDecision(
        state=TaskState.SCORED,
        message="已取消生成，你可以先补充信息后再试",
        actions=["查看评分", "补充信息"],
    )


def route_task(
    intent: Intent,
    task_state: TaskState,
    score_card: Optional[ScoreCard] = None,
) -> RouteDecision:
    """Route one user intent against current task state."""
    if intent == Intent.GENERATE:
        return handle_generate(task_state=task_state, score_card=score_card)

    if intent in {Intent.INGEST_JD, Intent.UPDATE_RESUME, Intent.ADD_INFO}:
        return RouteDecision(
            state=TaskState.SCORED,
            message="正在重新评分...",
            actions=["查看新评分"],
        )

    if intent == Intent.COMPARE:
        return RouteDecision(
            state=task_state,
            message="已输出方向对比",
            actions=["查看对比"],
        )

    if intent == Intent.ABANDON:
        return RouteDecision(
            state=TaskState.ABANDONED,
            message="已放弃当前任务",
            actions=[],
        )

    return RouteDecision(
        state=task_state,
        message="请选择下一步操作",
        actions=[],
    )


class TaskRouter:
    """Router facade for M2 state machine behavior."""

    def route(
        self, intent: Intent, task_state: TaskState, score_card: Optional[ScoreCard] = None
    ) -> RouteDecision:
        """Route intent and return one deterministic decision."""
        return route_task(intent=intent, task_state=task_state, score_card=score_card)

    def handle_risk_ack(self, confirmed: bool, score_card: ScoreCard) -> RouteDecision:
        """Apply explicit risk confirmation decision."""
        return handle_risk_acknowledgement(confirmed=confirmed, score_card=score_card)
