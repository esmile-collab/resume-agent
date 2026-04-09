# Input: memory、评分器、分析器、解析器、导出器和 patcher。
# Output: 输出可被 runtime 调用的内置工具目录与执行结果。
# Pos: 当前系统的工具注册表。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Tool registry for the new runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.memory import MemoryManager
from scoring import CampusScorerV21
from services.analyzer import JDAnalyzer
from services.exporter import ResumeExporter
from services.patcher import PolishPatcher
from services.resume_parser import ResumeParser


class AgentToolRegistry:
    """Register and invoke runtime tools with a stable schema."""

    def __init__(self, *, memory_manager: MemoryManager | None = None) -> None:
        self.memory = memory_manager or MemoryManager()
        self.analyzer = JDAnalyzer()
        self.resume_parser = ResumeParser()
        self.resume_exporter = ResumeExporter()
        self.patcher = PolishPatcher()
        self.scorer = CampusScorerV21()
        self._tool_map = {
            "ingest_jd": self._tool_ingest_jd,
            "track_overview": self._tool_track_overview,
            "resume_score": self._tool_resume_score,
            "resume_generate": self._tool_resume_generate,
            "resume_polish": self._tool_resume_polish,
        }

    def catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "ingest_jd",
                "description": "把 JD 写入项目 JD 库并挂到对应求职方向。",
                "when_to_use": "用户上传新 JD，或在对话里粘贴岗位描述时。",
            },
            {
                "name": "track_overview",
                "description": "查看当前有哪些求职方向以及每个方向积累了多少 JD。",
                "when_to_use": "用户想切换方向、查看方向列表或确认 JD 沉淀情况时。",
            },
            {
                "name": "resume_score",
                "description": "根据当前方向的最新 JD 对简历做匹配分析。",
                "when_to_use": "用户要评分、看差距、做生成前诊断时。",
            },
            {
                "name": "resume_generate",
                "description": "基于方向、JD 和经历生成定制简历草稿。",
                "when_to_use": "用户明确要输出某个方向的简历版本时。",
            },
            {
                "name": "resume_polish",
                "description": "基于 JD 做 block 级 patch 润色并产出新版本。",
                "when_to_use": "用户已有简历，想针对某个方向做局部优化时。",
            },
        ]

    def invoke(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in self._tool_map:
            raise ValueError(f"Tool not found: {tool_name}")
        return self._tool_map[tool_name](payload)

    def _tool_ingest_jd(self, payload: dict[str, Any]) -> dict[str, Any]:
        attachments = payload.get("attachments", [])
        jd_candidates = [item for item in attachments if item.get("type") == "jd"]
        if jd_candidates:
            jd_text = jd_candidates[-1].get("content", "")
            source_name = jd_candidates[-1].get("name", "chat_jd.txt") or "chat_jd.txt"
        else:
            jd_text = payload.get("content", "")
            source_name = "inline_jd.txt"
        if not jd_text.strip():
            return {"ok": False, "message": "没有检测到可入库的 JD 文本。"}

        linked = self.memory.attach_jd_to_track(
            project_id=payload["project_id"],
            jd_text=jd_text,
            source_name=source_name,
            track_name=payload.get("target_track_name", ""),
        )
        return {
            "ok": True,
            "track_id": linked["track_id"],
            "track_name": linked["track_name"],
            "jd_entry_id": linked["jd_entry_id"],
            "keywords": linked["keywords"],
            "source_name": linked["source_name"],
        }

    def _tool_track_overview(self, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot = self.memory.build_snapshot(project_id=payload["project_id"])
        return {
            "ok": True,
            "track_count": len(snapshot["tracks"]),
            "tracks": snapshot["tracks"],
        }

    def _tool_resume_score(self, payload: dict[str, Any]) -> dict[str, Any]:
        track = self.memory.resolve_track(
            project_id=payload["project_id"],
            track_id=payload.get("track_id", ""),
            track_name=payload.get("target_track_name", ""),
        )
        if track is None:
            return {"ok": False, "message": "当前没有可评分的方向，请先上传 JD 或指定方向。"}

        jd_entry = self.memory.latest_jd_for_track(track["id"])
        if jd_entry is None:
            return {"ok": False, "message": f"方向 {track['name']} 还没有关联 JD。"}

        resume_text = self.memory.get_resume_text(payload["project_id"])
        if not resume_text.strip():
            snapshot = self.memory.build_snapshot(project_id=payload["project_id"])
            resume_text = "\n".join(item["summary"] for item in snapshot["experiences"])
        if not resume_text.strip():
            return {"ok": False, "message": "当前没有可评分的简历内容或经历内容。"}

        score_report = self.scorer.score(jd=jd_entry["raw_content"], resume=resume_text)
        analysis = self.analyzer.analyze(resume_text=resume_text, jd_text=jd_entry["raw_content"])
        version = self.memory.next_artifact_version(track_id=track["id"], artifact_type="score_report")
        report_path = self._project_root(payload["project_id"]) / "agent" / "outputs" / (
            f"{track['id']}_score_v{version}.md"
        )
        report_json_path = self._project_root(payload["project_id"]) / "agent" / "outputs" / (
            f"{track['id']}_score_v{version}.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(score_report.to_markdown(), encoding="utf-8")
        score_payload = score_report.to_dict()
        score_payload["analysis"] = {
            "strengths": analysis.strengths,
            "gaps": analysis.gaps,
            "actions": analysis.actions,
        }
        report_json_path.write_text(json.dumps(score_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifact = self.memory.register_artifact(
            project_id=payload["project_id"],
            track_id=track["id"],
            jd_entry_id=jd_entry["id"],
            artifact_type="score_report",
            version=version,
            path=str(report_path.resolve()),
            summary={
                "track_name": track["name"],
                "score": round(score_report.final_score, 1),
                "match_level": score_report.match_level,
                "risk_warning": score_report.risk_warning,
                "quick_improvements": score_report.quick_improvements,
                "report_json_path": str(report_json_path.resolve()),
            },
        )
        return {
            "ok": True,
            "track_id": track["id"],
            "track_name": track["name"],
            "jd_entry_id": jd_entry["id"],
            "score": round(score_report.final_score, 1),
            "match_level": score_report.match_level,
            "suggestion": score_report.suggestion,
            "risk_warning": score_report.risk_warning,
            "quick_improvements": score_report.quick_improvements,
            "long_term_improvements": score_report.long_term_improvements,
            "score_report": score_report.to_dict(),
            "strengths": analysis.strengths,
            "gaps": analysis.gaps,
            "actions": analysis.actions,
            "artifact": artifact,
        }

    def _tool_resume_generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        track = self.memory.resolve_track(
            project_id=payload["project_id"],
            track_id=payload.get("track_id", ""),
            track_name=payload.get("target_track_name", ""),
        )
        if track is None:
            return {"ok": False, "message": "当前没有可生成的方向，请先上传 JD 或指定方向。"}

        snapshot = self.memory.build_snapshot(project_id=payload["project_id"])
        jd_entry = self.memory.latest_jd_for_track(track["id"])
        experiences = self.memory.choose_relevant_experiences(project_id=payload["project_id"], track=track)
        profile = snapshot["profile"]

        if not experiences and not self.memory.get_resume_text(payload["project_id"]).strip():
            return {"ok": False, "message": "缺少经历或基础简历，暂时无法生成定制简历。"}

        version = self.memory.next_artifact_version(track_id=track["id"], artifact_type="generated_resume")
        output_path = self._project_root(payload["project_id"]) / "agent" / "outputs" / (
            f"{track['id']}_generated_v{version}.md"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# {track['name']} 定制简历",
            "",
            "## 求职目标",
            f"- 方向：{track['name']}",
            f"- 方向定位：{track.get('positioning', '')}",
            "",
            "## 候选人摘要",
        ]

        summary = profile.get("summary") or "候选人背景已在多轮对话中持续补充。"
        lines.append(f"- {summary}")
        if profile.get("basics", {}).get("education"):
            lines.append(f"- 教育：{profile['basics']['education']}")
        if profile.get("basics", {}).get("years_of_experience"):
            lines.append(f"- 经验年限：{profile['basics']['years_of_experience']} 年")
        lines.extend(["", "## 相关经历"])

        if experiences:
            for item in experiences:
                metrics = "；".join(item.get("metrics", []))
                suffix = f"（量化结果：{metrics}）" if metrics else ""
                lines.append(f"- {item['title']}：{item['summary']}{suffix}")
        else:
            lines.append("- 暂无结构化经历，建议先补充项目/实习信息。")

        if jd_entry is not None:
            lines.extend(["", "## JD 关键词对齐"])
            for keyword in self.memory.extract_keywords(jd_entry["raw_content"])[:8]:
                lines.append(f"- {keyword}")

        lines.extend(["", "## 结构策略", track.get("default_resume_outline", "")])
        content = "\n".join(lines)
        output_path.write_text(content, encoding="utf-8")

        artifact = self.memory.register_artifact(
            project_id=payload["project_id"],
            track_id=track["id"],
            jd_entry_id=jd_entry["id"] if jd_entry else "",
            artifact_type="generated_resume",
            version=version,
            path=str(output_path),
            summary={
                "track_name": track["name"],
                "experience_count": len(experiences),
                "keywords": self.memory.extract_keywords(jd_entry["raw_content"])[:8] if jd_entry else [],
            },
        )
        return {
            "ok": True,
            "track_id": track["id"],
            "track_name": track["name"],
            "artifact": artifact,
            "content_preview": "\n".join(lines[:16]),
        }

    def _tool_resume_polish(self, payload: dict[str, Any]) -> dict[str, Any]:
        track = self.memory.resolve_track(
            project_id=payload["project_id"],
            track_id=payload.get("track_id", ""),
            track_name=payload.get("target_track_name", ""),
        )
        if track is None:
            return {"ok": False, "message": "当前没有可润色的方向，请先上传 JD 或指定方向。"}

        jd_entry = self.memory.latest_jd_for_track(track["id"])
        if jd_entry is None:
            return {"ok": False, "message": f"方向 {track['name']} 还没有关联 JD。"}

        latest_generated = self.memory.trace_artifact_crud.latest_for_track(track["id"], "generated_resume")
        if latest_generated is not None and Path(latest_generated.path).exists():
            source_text = Path(latest_generated.path).read_text(encoding="utf-8")
        else:
            source_text = self.memory.get_resume_text(payload["project_id"])
        if not source_text.strip():
            return {"ok": False, "message": "缺少可润色的简历文本。"}

        analysis = self.analyzer.analyze(resume_text=source_text, jd_text=jd_entry["raw_content"])
        content_json = self.resume_parser.parse(source_text)
        patches = self.patcher.generate_patches(
            resume_blocks=content_json.get("blocks", []),
            jd_text=jd_entry["raw_content"],
            gaps=analysis.gaps,
        )
        applied = patches[:3]
        for patch in applied:
            content_json = self.resume_parser.apply_patch(
                content_json=content_json,
                block_id=patch.target_block_id,
                new_text=patch.new_text,
            )
        exported = self.resume_exporter.export(content_json)

        version = self.memory.next_artifact_version(track_id=track["id"], artifact_type="polished_resume")
        output_path = self._project_root(payload["project_id"]) / "agent" / "outputs" / (
            f"{track['id']}_polished_v{version}.md"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(exported, encoding="utf-8")

        artifact = self.memory.register_artifact(
            project_id=payload["project_id"],
            track_id=track["id"],
            jd_entry_id=jd_entry["id"],
            artifact_type="polished_resume",
            version=version,
            path=str(output_path),
            summary={
                "track_name": track["name"],
                "patch_count": len(applied),
                "top_gap": analysis.gaps[0]["title"] if analysis.gaps else "",
            },
        )
        return {
            "ok": True,
            "track_id": track["id"],
            "track_name": track["name"],
            "artifact": artifact,
            "patches": [
                {
                    "target_block_id": item.target_block_id,
                    "reason": item.reason,
                    "potential_score": item.potential_score,
                }
                for item in applied
            ],
        }

    @staticmethod
    def _project_root(project_id: str) -> Path:
        return Path(".data") / "artifacts" / project_id
