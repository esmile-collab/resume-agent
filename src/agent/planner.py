# Input: 用户消息、附件和 memory snapshot。
# Output: 输出当前轮的 intent decision 与 plan steps。
# Pos: 会话式 Agent 的轻量规划器。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Deterministic planner for one message."""

from __future__ import annotations

from typing import Any

from agent.models import AgentAttachment, AgentPlan, IntentDecision, PlanStep


class AgentPlanner:
    """Build a compact per-message plan for the runtime."""

    def plan(
        self,
        *,
        content: str,
        attachments: list[AgentAttachment],
        snapshot: dict[str, Any],
        active_track_id: str = "",
        active_track_name: str = "",
    ) -> AgentPlan:
        lowered = content.lower().strip()

        if self._looks_like_jd(content, attachments):
            target_track_name = active_track_name or self._extract_track_name_from_text(content)
            return AgentPlan(
                decision=IntentDecision(
                    intent="ingest_jd",
                    reason="检测到 JD 文本或 JD 附件，需要先入库并归档到求职方向。",
                    target_track_name=target_track_name,
                ),
                steps=[
                    PlanStep(
                        thought="先识别 JD 所属方向并写入项目 JD 库。",
                        kind="tool",
                        tool_name="ingest_jd",
                        payload={"target_track_name": target_track_name},
                    ),
                    PlanStep(
                        thought="再读取方向总览，方便前端展示当前有哪些方向和 JD 数量。",
                        kind="tool",
                        tool_name="track_overview",
                    ),
                ],
            )

        target_track = self._resolve_track(snapshot, active_track_id, active_track_name, content)
        if self._asks_for_track_overview(lowered):
            return AgentPlan(
                decision=IntentDecision(
                    intent="track_overview",
                    reason="用户在查看当前求职方向或 JD 沉淀情况。",
                    target_track_name=target_track.get("name", "") if target_track else "",
                ),
                steps=[
                    PlanStep(
                        thought="先把方向总览拉出来，再决定是否需要进一步评分或生成。",
                        kind="tool",
                        tool_name="track_overview",
                    )
                ],
            )

        if self._asks_for_score(lowered):
            if target_track is None and len(snapshot.get("tracks", [])) != 1:
                return AgentPlan(
                    decision=IntentDecision(
                        intent="score_resume",
                        reason="用户想评分，但当前方向不明确。",
                        need_clarification=True,
                        clarify_question="请先指定要评分的求职方向，或先上传对应 JD。",
                    )
                )
            return AgentPlan(
                decision=IntentDecision(
                    intent="score_resume",
                    reason="用户希望评估当前简历与目标 JD 的匹配度。",
                    target_track_name=target_track.get("name", "") if target_track else "",
                ),
                steps=[
                    PlanStep(
                        thought="先调评分工具拿到匹配度、差距和建议。",
                        kind="tool",
                        tool_name="resume_score",
                        payload={"track_id": target_track.get("id", "") if target_track else ""},
                    )
                ],
            )

        if self._asks_for_generate(lowered):
            if target_track is None and len(snapshot.get("tracks", [])) != 1:
                return AgentPlan(
                    decision=IntentDecision(
                        intent="generate_resume",
                        reason="用户想生成简历，但当前方向不明确。",
                        need_clarification=True,
                        clarify_question="你要生成哪一个方向的简历？也可以先上传该方向的 JD。",
                    )
                )
            return AgentPlan(
                decision=IntentDecision(
                    intent="generate_resume",
                    reason="先评分再生成，更容易把生成过程收敛到当前 JD。",
                    target_track_name=target_track.get("name", "") if target_track else "",
                ),
                steps=[
                    PlanStep(
                        thought="先看当前方向的匹配度，确认缺口和风险。",
                        kind="tool",
                        tool_name="resume_score",
                        payload={"track_id": target_track.get("id", "") if target_track else ""},
                    ),
                    PlanStep(
                        thought="基于评分结果、方向总文档和相关经历生成定制简历草稿。",
                        kind="tool",
                        tool_name="resume_generate",
                        payload={"track_id": target_track.get("id", "") if target_track else ""},
                    ),
                ],
            )

        if self._asks_for_polish(lowered):
            if target_track is None and len(snapshot.get("tracks", [])) != 1:
                return AgentPlan(
                    decision=IntentDecision(
                        intent="polish_resume",
                        reason="用户想润色，但当前方向不明确。",
                        need_clarification=True,
                        clarify_question="请先指定要润色的方向，或先上传该方向的 JD。",
                    )
                )
            return AgentPlan(
                decision=IntentDecision(
                    intent="polish_resume",
                    reason="先评分再做 block 级润色，能让 patch 更贴近当前 JD。",
                    target_track_name=target_track.get("name", "") if target_track else "",
                ),
                steps=[
                    PlanStep(
                        thought="先确认当前 JD 的差距和重点改写方向。",
                        kind="tool",
                        tool_name="resume_score",
                        payload={"track_id": target_track.get("id", "") if target_track else ""},
                    ),
                    PlanStep(
                        thought="再对当前简历做 block 级 patch 润色并输出新版本。",
                        kind="tool",
                        tool_name="resume_polish",
                        payload={"track_id": target_track.get("id", "") if target_track else ""},
                    ),
                ],
            )

        return AgentPlan(
            decision=IntentDecision(
                intent="add_info",
                reason="这轮更像是补充背景、经历或偏好信息，应先写入记忆。",
            ),
            steps=[],
        )

    @staticmethod
    def _looks_like_jd(content: str, attachments: list[AgentAttachment]) -> bool:
        if any(item.type == "jd" for item in attachments):
            return True
        return any(
            marker in content
            for marker in ("岗位职责", "任职要求", "职位描述", "岗位要求", "JD", "job description")
        )

    @staticmethod
    def _asks_for_score(lowered: str) -> bool:
        return any(token in lowered for token in ("评分", "打分", "匹配度", "score"))

    @staticmethod
    def _asks_for_generate(lowered: str) -> bool:
        return any(token in lowered for token in ("生成简历", "写简历", "定制简历", "输出简历", "generate"))

    @staticmethod
    def _asks_for_polish(lowered: str) -> bool:
        return any(token in lowered for token in ("润色", "优化简历", "改写", "polish"))

    @staticmethod
    def _asks_for_track_overview(lowered: str) -> bool:
        return "方向" in lowered and any(token in lowered for token in ("查看", "看看", "有哪些", "列表", "总览"))

    @staticmethod
    def _extract_track_name_from_text(content: str) -> str:
        known = ("策略产品", "功能产品", "内容运营", "数据分析", "商业分析", "产品经理")
        for item in known:
            if item in content:
                return item
        return ""

    @staticmethod
    def _resolve_track(
        snapshot: dict[str, Any],
        active_track_id: str,
        active_track_name: str,
        content: str,
    ) -> dict[str, Any] | None:
        tracks = snapshot.get("tracks", [])
        if active_track_id:
            for track in tracks:
                if track.get("id") == active_track_id:
                    return track
        if active_track_name:
            for track in tracks:
                if track.get("name") == active_track_name:
                    return track
        extracted_name = AgentPlanner._extract_track_name_from_text(content)
        if extracted_name:
            for track in tracks:
                if track.get("name") == extracted_name:
                    return track
        if len(tracks) == 1:
            return tracks[0]
        return None
