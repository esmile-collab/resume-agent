"""M4-M7 orchestration use-case layer (flow + observability + dialog compression)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Protocol, cast

from db.crud import ProjectCRUD, ProjectJDEntryCRUD, generate_short_id
from models import ScoreCard
from observability import DialogCompressionManager, ObservabilityLogger
from orchestration.models import AllocationPreviewResult, TaskCardRecord
from routes.intent import Intent, TaskState
from routes.router import TaskRouter
from tools.stub import ParserStub, ScorerStub


class ScorerProtocol(Protocol):
    """Minimal scorer protocol for dependency injection in tests."""

    def score(self, jd: str, resume: str) -> ScoreCard:
        """Return one score card for one card-level run."""


class ResumeOrchestratorUseCase:
    """End-to-end orchestration service for M4-M7."""

    def __init__(
        self,
        *,
        parser: ParserStub | None = None,
        scorer: ScorerProtocol | None = None,
        router: TaskRouter | None = None,
        telemetry: ObservabilityLogger | None = None,
        dialog_manager: DialogCompressionManager | None = None,
    ) -> None:
        self.project_crud = ProjectCRUD()
        self.jd_crud = ProjectJDEntryCRUD()
        self.parser = parser or ParserStub()
        self.scorer = scorer or ScorerStub()
        self.router = router or TaskRouter()
        self.telemetry = telemetry or ObservabilityLogger()
        self.dialog_manager = dialog_manager or DialogCompressionManager()

    def init_project(
        self, name: str, cycle: str = "", base_resume_text: str = ""
    ) -> dict[str, Any]:
        """Create one project and initialize artifact workspace."""
        project = self.project_crud.create(name=name, cycle=cycle)
        self._ensure_artifact_dirs(project.id)

        base_resume_path = self._project_root(project.id) / "resume" / "base_resume_v1.txt"
        base_resume_path.write_text(base_resume_text, encoding="utf-8")

        result = {
            "project_id": project.id,
            "name": project.name,
            "cycle": project.cycle or "",
            "base_resume_path": str(base_resume_path),
        }
        self._log_telemetry(
            project_id=project.id,
            intent=Intent.INGEST_JD.value,
            state=TaskState.PENDING.value,
            match_level="",
            risk_ack=False,
            metadata={"event": "project_initialized"},
        )
        return result

    def ingest_jds(
        self,
        project_id: str,
        jd_texts: list[str],
        source_files: list[str] | None = None,
    ) -> dict[str, Any]:
        """Ingest batch JDs, persist entries, and return preview plan for confirmation."""
        if self.project_crud.get(project_id) is None:
            raise ValueError(f"Project not found: {project_id}")
        if not jd_texts:
            raise ValueError("jd_texts cannot be empty")

        self._ensure_artifact_dirs(project_id)
        normalized_sources = source_files or []
        grouped: dict[str, dict[str, Any]] = {}
        proposed_changes: list[dict[str, str]] = []

        for index, jd_text in enumerate(jd_texts):
            source_file = (
                normalized_sources[index]
                if index < len(normalized_sources) and normalized_sources[index]
                else f"jd_{index + 1}.txt"
            )
            created = self.jd_crud.create(
                project_id=project_id, content=jd_text, source_file=source_file
            )

            jd_file = self._project_root(project_id) / "jd" / f"{created.id}.txt"
            jd_file.write_text(jd_text, encoding="utf-8")

            direction_name = self._infer_direction_name(jd_text=jd_text, index=index)
            direction_id = self._direction_id(direction_name)
            direction = grouped.setdefault(
                direction_id,
                {
                    "direction_id": direction_id,
                    "direction_name": direction_name,
                    "source_jd_ids": [],
                },
            )
            direction["source_jd_ids"].append(created.id)

            proposed_changes.append(
                {
                    "action": "create_new_card",
                    "project_jd_id": created.id,
                    "target_task_card_id": "",
                    "target_direction_name": direction_name,
                    "reason": "M4 preview: 按方向聚类后建议一方向一卡片",
                }
            )

            # Call parser stub to keep orchestration interface-complete.
            _ = self.parser.parse_jd(jd_text)

        preview = AllocationPreviewResult(
            plan_id=generate_short_id(10),
            jd_count=len(jd_texts),
            direction_count=len(grouped),
            resume_output_count=len(grouped),
            proposed_task_card_changes=proposed_changes,
        )

        plan_payload = {
            "plan_id": preview.plan_id,
            "project_id": project_id,
            "jd_count": preview.jd_count,
            "direction_count": preview.direction_count,
            "resume_output_count": preview.resume_output_count,
            "directions": list(grouped.values()),
            "proposed_task_card_changes": preview.proposed_task_card_changes,
        }
        self._plan_file(project_id, preview.plan_id).write_text(
            json.dumps(plan_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        self._log_telemetry(
            project_id=project_id,
            intent=Intent.INGEST_JD.value,
            state=TaskState.PENDING.value,
            match_level="",
            risk_ack=False,
            metadata={
                "jd_count": preview.jd_count,
                "direction_count": preview.direction_count,
                "plan_id": preview.plan_id,
            },
        )
        return {
            "plan_id": preview.plan_id,
            "need_user_confirm": True,
            "preview": asdict(preview),
        }

    def confirm_allocation(self, project_id: str, plan_id: str) -> dict[str, Any]:
        """Confirm plan and materialize/merge task cards."""
        plan_data = self._load_plan(project_id=project_id, plan_id=plan_id)
        cards = self._load_task_cards(project_id)

        by_direction = {card.direction_id: card for card in cards}
        for direction in plan_data["directions"]:
            direction_id = direction["direction_id"]
            direction_name = direction["direction_name"]
            jd_ids = direction["source_jd_ids"]

            if direction_id in by_direction:
                card = by_direction[direction_id]
                card.jd_entry_ids = self._unique(card.jd_entry_ids + jd_ids)
                continue

            new_card = TaskCardRecord(
                task_card_id=f"card_{generate_short_id(6)}",
                direction_id=direction_id,
                direction_name=direction_name,
                jd_entry_ids=list(jd_ids),
            )
            cards.append(new_card)
            by_direction[direction_id] = new_card

        self._save_task_cards(project_id, cards)
        self._log_telemetry(
            project_id=project_id,
            intent=Intent.INGEST_JD.value,
            state=TaskState.PENDING.value,
            match_level="",
            risk_ack=False,
            metadata={
                "event": "allocation_confirmed",
                "plan_id": plan_id,
                "direction_count": len(cards),
            },
        )
        return {
            "project_id": project_id,
            "plan_id": plan_id,
            "direction_count": len(cards),
            "resume_output_count": len(cards),
            "task_cards": [asdict(card) for card in cards],
        }

    def score_task_cards(self, project_id: str, resume_text: str = "") -> dict[str, Any]:
        """Run scorer for all task cards and persist score state."""
        cards = self._load_task_cards(project_id)
        if not cards:
            raise ValueError("No task cards found. Please confirm allocation first.")

        final_resume = resume_text or self._load_base_resume(project_id)
        _ = self.parser.parse_resume(final_resume)

        jd_map = {entry.id: entry.raw_content for entry in self.jd_crud.list_by_project(project_id)}
        for card in cards:
            jd_corpus = "\n".join(jd_map.get(jd_id, "") for jd_id in card.jd_entry_ids)
            score_card = self.scorer.score(jd=jd_corpus, resume=final_resume)
            card.score = score_card.score
            card.match_level = score_card.match_level
            card.status = TaskState.SCORED.value
            self._log_telemetry(
                project_id=project_id,
                task_card_id=card.task_card_id,
                intent=Intent.GENERATE.value,
                state=card.status,
                match_level=card.match_level or "",
                risk_ack=False,
                metadata={"event": "score_updated", "score": card.score},
            )

        self._save_task_cards(project_id, cards)
        return {
            "project_id": project_id,
            "task_cards": [asdict(card) for card in cards],
        }

    def run_card(
        self,
        project_id: str,
        task_card_id: str,
        *,
        resume_text: str = "",
        risk_ack: bool = False,
    ) -> dict[str, Any]:
        """Run card-level generation flow with normal/compensation routing."""
        cards = self._load_task_cards(project_id)
        card = self._find_card(cards, task_card_id)

        if card.score is None or card.match_level is None or card.status != TaskState.SCORED.value:
            self.score_task_cards(project_id=project_id, resume_text=resume_text)
            cards = self._load_task_cards(project_id)
            card = self._find_card(cards, task_card_id)

        score_card = ScoreCard(
            score=card.score or 0,
            match_level=card.match_level or "low",
            suggestion="M4 orchestration run",
        )
        decision = self.router.route(
            intent=Intent.GENERATE,
            task_state=TaskState.SCORED,
            score_card=score_card,
        )
        self._log_telemetry(
            project_id=project_id,
            task_card_id=task_card_id,
            intent=Intent.GENERATE.value,
            state=decision.state.value,
            match_level=score_card.match_level,
            risk_ack=risk_ack,
            metadata={"event": "route_decision", "await_risk_ack": decision.await_risk_ack},
        )

        if decision.await_risk_ack and not risk_ack:
            self._save_task_cards(project_id, cards)
            return {
                "project_id": project_id,
                "task_card_id": task_card_id,
                "await_risk_ack": True,
                "message": decision.message,
                "mode": None,
            }

        if decision.await_risk_ack and risk_ack:
            decision = self.router.handle_risk_ack(confirmed=True, score_card=score_card)
            self._log_telemetry(
                project_id=project_id,
                task_card_id=task_card_id,
                intent=Intent.GENERATE.value,
                state=decision.state.value,
                match_level=score_card.match_level,
                risk_ack=True,
                metadata={"event": "risk_ack_confirmed"},
            )

        if decision.state != TaskState.GENERATING:
            self._save_task_cards(project_id, cards)
            return {
                "project_id": project_id,
                "task_card_id": task_card_id,
                "await_risk_ack": False,
                "message": decision.message,
                "mode": decision.mode,
            }

        next_version = card.latest_output_version + 1
        mode = decision.mode or "normal"
        output_path = (
            self._project_root(project_id) / "outputs" / f"{task_card_id}_v{next_version}.md"
        )
        output_text = self._render_output(card=card, mode=mode, version=next_version)
        output_path.write_text(output_text, encoding="utf-8")

        card.latest_output_version = next_version
        card.status = TaskState.COMPLETED.value
        self._save_task_cards(project_id, cards)
        self._append_run_log(
            project_id=project_id,
            payload={
                "task_card_id": task_card_id,
                "version": next_version,
                "mode": mode,
                "score": card.score,
                "match_level": card.match_level,
                "evidence_jd_ids": card.jd_entry_ids,
                "output_path": str(output_path),
            },
        )
        self._log_telemetry(
            project_id=project_id,
            task_card_id=task_card_id,
            intent=Intent.GENERATE.value,
            state=card.status,
            match_level=card.match_level or "",
            risk_ack=risk_ack,
            metadata={"event": "card_generated", "mode": mode, "version": next_version},
        )

        return {
            "project_id": project_id,
            "task_card_id": task_card_id,
            "await_risk_ack": False,
            "mode": mode,
            "version": next_version,
            "output_path": str(output_path),
        }

    def list_task_cards(self, project_id: str) -> list[dict[str, Any]]:
        """List persisted task cards for one project."""
        return [asdict(card) for card in self._load_task_cards(project_id)]

    def append_dialog_turn(
        self,
        *,
        project_id: str,
        role: str,
        content: str,
        facts: list[str] | None = None,
        artifact_version_id: str = "",
    ) -> dict[str, Any]:
        """Append one dialog turn and trigger compression when threshold is exceeded."""
        if self.project_crud.get(project_id) is None:
            raise ValueError(f"Project not found: {project_id}")
        if not content.strip():
            raise ValueError("Dialog content cannot be empty.")

        self._ensure_artifact_dirs(project_id)
        result = self.dialog_manager.append_turn(
            project_root=self._project_root(project_id),
            role=role,
            content=content,
            facts=facts,
            artifact_version_id=artifact_version_id,
        )
        self._log_telemetry(
            project_id=project_id,
            intent=Intent.ADD_INFO.value,
            state=TaskState.PENDING.value,
            match_level="",
            risk_ack=False,
            metadata={
                "event": "dialog_turn_appended",
                "compressed": result.get("compressed", False),
                "summary_version": result.get("summary_version", 0),
            },
        )
        return result

    def read_telemetry_events(self, project_id: str) -> list[dict[str, Any]]:
        """Read persisted M7 telemetry events for one project."""
        return self.telemetry.read_events(project_root=self._project_root(project_id))

    def read_dialog_messages(self, project_id: str) -> list[dict[str, Any]]:
        """Read recent dialog turns after compression."""
        return self.dialog_manager.read_messages(project_root=self._project_root(project_id))

    def read_dialog_summary(self, project_id: str) -> dict[str, Any]:
        """Read dialog summary versions."""
        return self.dialog_manager.read_summary(project_root=self._project_root(project_id))

    def _render_output(self, *, card: TaskCardRecord, mode: str, version: int) -> str:
        """Render one markdown output artifact with evidence bindings."""
        return "\n".join(
            [
                f"# {card.direction_name} 简历输出",
                "",
                f"- Task Card: {card.task_card_id}",
                f"- Version: v{version}",
                f"- Mode: {mode}",
                f"- Score: {card.score}",
                f"- Match Level: {card.match_level}",
                "",
                "## Evidence",
                f"- Evidence JD IDs: {', '.join(card.jd_entry_ids)}",
                "- Evidence Binding: 产物绑定到本卡片关联的 JD ID 集合",
            ]
        )

    def _ensure_artifact_dirs(self, project_id: str) -> None:
        root = self._project_root(project_id)
        for rel in ("jd", "resume", "outputs", "plans", "state", "runs"):
            (root / rel).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _project_root(project_id: str) -> Path:
        return Path(".data") / "artifacts" / project_id

    def _plan_file(self, project_id: str, plan_id: str) -> Path:
        return self._project_root(project_id) / "plans" / f"{plan_id}.json"

    def _state_file(self, project_id: str) -> Path:
        return self._project_root(project_id) / "state" / "task_cards.json"

    def _load_plan(self, *, project_id: str, plan_id: str) -> dict[str, Any]:
        plan_file = self._plan_file(project_id, plan_id)
        if not plan_file.exists():
            raise ValueError(f"Plan not found: {plan_id}")
        return cast(dict[str, Any], json.loads(plan_file.read_text(encoding="utf-8")))

    def _load_task_cards(self, project_id: str) -> list[TaskCardRecord]:
        state_file = self._state_file(project_id)
        if not state_file.exists():
            return []
        raw = json.loads(state_file.read_text(encoding="utf-8"))
        return [TaskCardRecord(**item) for item in raw.get("task_cards", [])]

    def _save_task_cards(self, project_id: str, cards: Iterable[TaskCardRecord]) -> None:
        self._ensure_artifact_dirs(project_id)
        payload = {"task_cards": [asdict(card) for card in cards]}
        self._state_file(project_id).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _append_run_log(self, *, project_id: str, payload: dict[str, Any]) -> None:
        self._ensure_artifact_dirs(project_id)
        log_file = self._project_root(project_id) / "runs" / "runs.jsonl"
        with log_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _log_telemetry(
        self,
        *,
        project_id: str,
        intent: str,
        state: str,
        match_level: str,
        risk_ack: bool,
        task_card_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._ensure_artifact_dirs(project_id)
        self.telemetry.log_event(
            project_root=self._project_root(project_id),
            project_id=project_id,
            task_card_id=task_card_id,
            intent=intent,
            state=state,
            match_level=match_level,
            risk_ack=risk_ack,
            metadata=metadata,
        )

    def _load_base_resume(self, project_id: str) -> str:
        resume_file = self._project_root(project_id) / "resume" / "base_resume_v1.txt"
        if resume_file.exists():
            return resume_file.read_text(encoding="utf-8")
        return ""

    @staticmethod
    def _direction_id(direction_name: str) -> str:
        if direction_name == "策略产品":
            return "direction_strategy"
        if direction_name == "功能产品":
            return "direction_feature"
        return "direction_general"

    @staticmethod
    def _infer_direction_name(jd_text: str, index: int) -> str:
        text = jd_text.lower()
        if any(keyword in jd_text for keyword in ("策略", "战略", "增长")) or "strategy" in text:
            return "策略产品"
        if any(keyword in jd_text for keyword in ("功能", "需求", "prd")) or "feature" in text:
            return "功能产品"
        # Fallback keeps preview deterministic in tests without explicit keywords.
        return "策略产品" if index % 2 == 0 else "功能产品"

    @staticmethod
    def _find_card(cards: list[TaskCardRecord], task_card_id: str) -> TaskCardRecord:
        for card in cards:
            if card.task_card_id == task_card_id:
                return card
        raise ValueError(f"Task card not found: {task_card_id}")

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result
