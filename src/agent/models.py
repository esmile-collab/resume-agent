# Input: planner、runtime、tool registry 共享的数据结构。
# Output: 输出会话级决策、附件、计划步骤和工具执行模型。
# Pos: Agent 内部协议类型中心。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Dataclasses for the new think-call-observe runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentAttachment:
    """One attachment from the chat UI."""

    type: str
    content: str
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntentDecision:
    """Intent result for one message."""

    intent: str
    reason: str
    need_clarification: bool = False
    clarify_question: str = ""
    target_track_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlanStep:
    """One executable step in the runtime plan."""

    thought: str
    kind: str
    tool_name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentPlan:
    """Plan for one user message."""

    decision: IntentDecision
    steps: list[PlanStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass
class ToolExecution:
    """One tool call and observation pair."""

    thought: str
    tool_name: str
    input_payload: dict[str, Any]
    observation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
