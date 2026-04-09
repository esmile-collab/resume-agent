# Input: planner、memory、tool registry 和持久化 CRUD。
# Output: 输出会话创建、消息处理、快照与 trace 结果。
# Pos: 服务端 think-call-observe 主运行时。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Server-side think-call-observe runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.memory import MemoryManager
from agent.models import AgentAttachment, AgentPlan, ToolExecution
from agent.planner import AgentPlanner
from agent.tools import AgentToolRegistry
from db.agent_crud import AgentSessionCRUD, RunTraceCRUD, SessionMessageCRUD
from db.crud import ProjectCRUD


class ResumeAgentRuntime:
    """Session-based runtime for the React chat frontend."""

    def __init__(
        self,
        *,
        planner: AgentPlanner | None = None,
        memory_manager: MemoryManager | None = None,
        tool_registry: AgentToolRegistry | None = None,
    ) -> None:
        self.memory = memory_manager or MemoryManager()
        self.planner = planner or AgentPlanner()
        self.tools = tool_registry or AgentToolRegistry(memory_manager=self.memory)
        self.project_crud = ProjectCRUD()
        self.session_crud = AgentSessionCRUD()
        self.message_crud = SessionMessageCRUD()
        self.trace_crud = RunTraceCRUD()

    def start_session(
        self,
        *,
        project_id: str = "",
        project_name: str = "",
        cycle: str = "",
        base_resume_text: str = "",
    ) -> dict[str, Any]:
        resolved_project_id = project_id
        resolved_project_name = project_name or "简历 Agent 项目"

        if not resolved_project_id:
            created = self.project_crud.create(name=resolved_project_name, cycle=cycle)
            resolved_project_id = str(created.id)
            resolved_project_name = str(created.name)
            self.memory.ensure_project_dirs(resolved_project_id)
            if base_resume_text.strip():
                resume_path = self._base_resume_path(resolved_project_id)
                resume_path.write_text(base_resume_text, encoding="utf-8")
        else:
            if self.project_crud.get(resolved_project_id) is None:
                raise ValueError(f"Project not found: {resolved_project_id}")
            self.memory.ensure_project_dirs(resolved_project_id)
            if base_resume_text.strip():
                self.memory.write_resume_text(resolved_project_id, base_resume_text)

        session = self.session_crud.create(
            project_id=resolved_project_id,
            title=f"{resolved_project_name} 对话会话",
        )
        snapshot = self.memory.build_snapshot(project_id=resolved_project_id, session_id=session.id)
        return {
            "project_id": resolved_project_id,
            "session_id": session.id,
            "title": session.title,
            "tool_catalog": self.tools.catalog(),
            "snapshot": snapshot,
        }

    def handle_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        attachments: list[dict[str, str]] | None = None,
        active_track_id: str = "",
        active_track_name: str = "",
    ) -> dict[str, Any]:
        session = self.session_crud.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        attachment_models = [AgentAttachment(**item) for item in (attachments or [])]
        user_message = self.message_crud.create(
            session_id=session_id,
            role=role,
            content=content,
            metadata={"attachments": [item.to_dict() for item in attachment_models]},
        )
        self.session_crud.touch(session_id)
        self.memory.append_project_dialog(
            project_id=session.project_id,
            role=role,
            content=content,
        )

        memory_updates = self.memory.apply_dialog_memory(
            project_id=session.project_id,
            content=content,
            attachments=[item.to_dict() for item in attachment_models],
        )
        snapshot = self.memory.build_snapshot(project_id=session.project_id, session_id=session_id)
        plan = self.planner.plan(
            content=content,
            attachments=attachment_models,
            snapshot=snapshot,
            active_track_id=active_track_id,
            active_track_name=active_track_name,
        )

        self._log_trace(
            project_id=session.project_id,
            session_id=session_id,
            message_id=user_message.id,
            step_index=0,
            kind="intent",
            payload=plan.decision.to_dict(),
        )

        tool_steps: list[ToolExecution] = []
        step_index = 1
        for step in plan.steps:
            self._log_trace(
                project_id=session.project_id,
                session_id=session_id,
                message_id=user_message.id,
                step_index=step_index,
                kind="thought",
                payload={"thought": step.thought, "tool_name": step.tool_name},
            )
            step_index += 1

            if step.kind != "tool":
                continue

            tool_payload = {
                **step.payload,
                "project_id": session.project_id,
                "session_id": session_id,
                "content": content,
                "attachments": [item.to_dict() for item in attachment_models],
                "active_track_id": active_track_id,
                "active_track_name": active_track_name,
            }
            self._log_trace(
                project_id=session.project_id,
                session_id=session_id,
                message_id=user_message.id,
                step_index=step_index,
                kind="tool_call",
                payload={"tool_name": step.tool_name, "input": tool_payload},
            )
            step_index += 1

            observation = self.tools.invoke(step.tool_name, tool_payload)
            tool_steps.append(
                ToolExecution(
                    thought=step.thought,
                    tool_name=step.tool_name,
                    input_payload=tool_payload,
                    observation=observation,
                )
            )
            self._log_trace(
                project_id=session.project_id,
                session_id=session_id,
                message_id=user_message.id,
                step_index=step_index,
                kind="observation",
                payload={"tool_name": step.tool_name, "output": observation},
            )
            step_index += 1

        snapshot = self.memory.build_snapshot(project_id=session.project_id, session_id=session_id)
        reply = self._build_reply(plan=plan, memory_updates=memory_updates, tool_steps=tool_steps, snapshot=snapshot)
        assistant_message = self.message_crud.create(
            session_id=session_id,
            role="assistant",
            content=reply,
            metadata={
                "intent": plan.decision.intent,
                "tool_steps": [item.to_dict() for item in tool_steps],
            },
        )
        self.memory.append_project_dialog(
            project_id=session.project_id,
            role="assistant",
            content=reply,
        )

        return {
            "project_id": session.project_id,
            "session_id": session_id,
            "message_id": user_message.id,
            "assistant_message_id": assistant_message.id,
            "intent": plan.decision.to_dict(),
            "plan": plan.to_dict(),
            "memory_updates": memory_updates,
            "tool_steps": [item.to_dict() for item in tool_steps],
            "reply": reply,
            "snapshot": snapshot,
        }

    def get_session_snapshot(self, session_id: str) -> dict[str, Any]:
        session = self.session_crud.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        traces = []
        for trace in self.trace_crud.list_by_session(session_id, limit=120):
            traces.append(
                {
                    "id": trace.id,
                    "message_id": trace.message_id,
                    "step_index": trace.step_index,
                    "kind": trace.kind,
                    "payload": json.loads(trace.payload_json),
                }
            )
        return {
            "project_id": session.project_id,
            "session_id": session_id,
            "title": session.title,
            "snapshot": self.memory.build_snapshot(project_id=session.project_id, session_id=session_id),
            "tool_catalog": self.tools.catalog(),
            "traces": traces,
        }

    def list_sessions(self, *, limit: int = 30) -> dict[str, Any]:
        return {"sessions": self.memory.list_sessions(limit=limit)}

    def _build_reply(
        self,
        *,
        plan: AgentPlan,
        memory_updates: dict[str, Any],
        tool_steps: list[ToolExecution],
        snapshot: dict[str, Any],
    ) -> str:
        if plan.decision.need_clarification:
            return plan.decision.clarify_question

        if plan.decision.intent == "add_info":
            parts = []
            if memory_updates.get("track_ids"):
                names = [
                    track["name"]
                    for track in snapshot.get("tracks", [])
                    if track["id"] in set(memory_updates["track_ids"])
                ]
                if names:
                    parts.append(f"已记录求职方向：{' / '.join(names)}。")
            if memory_updates.get("new_experience_ids"):
                parts.append(f"已新增 {len(memory_updates['new_experience_ids'])} 条可复用经历。")
            if memory_updates.get("profile_updated"):
                parts.append("候选人画像已更新。")
            if not parts:
                parts.append("这轮信息已记录。")
            parts.append("接下来你可以继续上传 JD、继续评分，或直接生成某个方向的简历。")
            return " ".join(parts)

        if plan.decision.intent == "ingest_jd":
            ingest = self._find_tool(tool_steps, "ingest_jd")
            overview = self._find_tool(tool_steps, "track_overview")
            if ingest and ingest.get("ok"):
                track_name = ingest.get("track_name", "未命名方向")
                jd_entry_id = ingest.get("jd_entry_id", "")
                count = overview.get("track_count", len(snapshot.get("tracks", []))) if overview else len(snapshot.get("tracks", []))
                return (
                    f"已把新 JD 归档到「{track_name}」方向，JD ID 为 {jd_entry_id}。"
                    f" 当前共维护 {count} 个求职方向。"
                )
            return "没有成功识别 JD，请检查内容是否完整。"

        if plan.decision.intent == "track_overview":
            tracks = snapshot.get("tracks", [])
            if not tracks:
                return "当前还没有求职方向。你可以先补充目标岗位，或直接上传一条 JD。"
            summary = "；".join(f"{track['name']}（{track['jd_count']} 条 JD）" for track in tracks)
            return f"当前方向总览：{summary}。"

        if plan.decision.intent == "score_resume":
            score = self._find_tool(tool_steps, "resume_score")
            if score and score.get("ok"):
                top_gap = score.get("gaps", [{}])[0].get("title", "") if score.get("gaps") else ""
                return (
                    f"方向「{score['track_name']}」当前匹配度为 {score['score']}/100，"
                    f"评级 {score['match_level']}。"
                    f"{' 主要缺口：' + top_gap + '。' if top_gap else ''}"
                )
            return str(score.get("message", "评分失败，请先上传 JD 或基础简历。")) if score else "评分失败。"

        if plan.decision.intent == "generate_resume":
            score = self._find_tool(tool_steps, "resume_score")
            generated = self._find_tool(tool_steps, "resume_generate")
            if generated and generated.get("ok"):
                path = generated["artifact"]["path"]
                score_text = (
                    f" 生成前评分 {score['score']}/100，评级 {score['match_level']}。"
                    if score and score.get("ok")
                    else ""
                )
                return f"已生成「{generated['track_name']}」方向简历草稿：{path}。{score_text}"
            return "生成失败，请先补充该方向的 JD 或经历信息。"

        if plan.decision.intent == "polish_resume":
            polished = self._find_tool(tool_steps, "resume_polish")
            if polished and polished.get("ok"):
                return (
                    f"已输出「{polished['track_name']}」方向的润色版本：{polished['artifact']['path']}。"
                    f" 共应用 {len(polished.get('patches', []))} 条 patch。"
                )
            return str(polished.get("message", "润色失败。")) if polished else "润色失败。"

        return "当前操作已完成。"

    def _log_trace(
        self,
        *,
        project_id: str,
        session_id: str,
        message_id: str,
        step_index: int,
        kind: str,
        payload: dict[str, Any],
    ) -> None:
        self.trace_crud.create(
            project_id=project_id,
            session_id=session_id,
            message_id=message_id,
            step_index=step_index,
            kind=kind,
            payload=payload,
        )

    @staticmethod
    def _find_tool(tool_steps: list[ToolExecution], tool_name: str) -> dict[str, Any]:
        for step in tool_steps:
            if step.tool_name == tool_name:
                return step.observation
        return {}

    @staticmethod
    def _base_resume_path(project_id: str) -> Path:
        return Path(".data") / "artifacts" / project_id / "resume" / "base_resume_v1.txt"
