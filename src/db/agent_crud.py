# Input: 数据库连接、表模型和 JSON 序列化辅助函数。
# Output: 输出 agent 运行时相关表的 CRUD 仓储。
# Pos: Agent 持久化仓储层。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""CRUD repositories for the new agent runtime."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from .crud import _parse_datetime, generate_short_id
from .database import get_connection, init_db
from .models import (
    AgentArtifact,
    AgentSession,
    CandidateProfile,
    ExperienceItem,
    JobTrack,
    JobTrackJDLink,
    RunTrace,
    SessionMessage,
)


def _json_text(value: Any, *, default: str) -> str:
    if value is None:
        return default
    return json.dumps(value, ensure_ascii=False)


class AgentSessionCRUD:
    """CRUD for agent sessions."""

    def __init__(self) -> None:
        conn = init_db()
        conn.close()

    def create(self, project_id: str, title: str) -> AgentSession:
        conn = get_connection()
        try:
            session_id = f"sess_{generate_short_id(10)}"
            with conn:
                conn.execute(
                    """
                    INSERT INTO agent_sessions (id, project_id, title)
                    VALUES (?, ?, ?)
                    """,
                    (session_id, project_id, title),
                )
            row = conn.execute(
                """
                SELECT id, project_id, title, status, created_at, updated_at
                FROM agent_sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError("Failed to create session.")
            return self._row_to_session(row)
        finally:
            conn.close()

    def get(self, session_id: str) -> Optional[AgentSession]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, project_id, title, status, created_at, updated_at
                FROM agent_sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
            return self._row_to_session(row) if row else None
        finally:
            conn.close()

    def touch(self, session_id: str) -> None:
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE agent_sessions
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (session_id,),
                )
        finally:
            conn.close()

    def list_recent(self, *, limit: int = 30) -> list[AgentSession]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, project_id, title, status, created_at, updated_at
                FROM agent_sessions
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [self._row_to_session(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def _row_to_session(row: sqlite3.Row) -> AgentSession:
        return AgentSession(
            id=row["id"],
            project_id=row["project_id"],
            title=row["title"],
            status=row["status"],
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )


class SessionMessageCRUD:
    """CRUD for session messages."""

    def __init__(self) -> None:
        conn = init_db()
        conn.close()

    def create(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> SessionMessage:
        conn = get_connection()
        try:
            message_id = f"msg_{generate_short_id(10)}"
            with conn:
                conn.execute(
                    """
                    INSERT INTO session_messages (id, session_id, role, content, metadata_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (message_id, session_id, role, content, _json_text(metadata, default="{}")),
                )
            row = conn.execute(
                """
                SELECT id, session_id, role, content, metadata_json, created_at
                FROM session_messages
                WHERE id = ?
                """,
                (message_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError("Failed to create session message.")
            return self._row_to_message(row)
        finally:
            conn.close()

    def list_by_session(self, session_id: str, *, limit: int = 50) -> list[SessionMessage]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, session_id, role, content, metadata_json, created_at
                FROM session_messages
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
            messages = [self._row_to_message(row) for row in rows]
            messages.reverse()
            return messages
        finally:
            conn.close()

    @staticmethod
    def _row_to_message(row: sqlite3.Row) -> SessionMessage:
        return SessionMessage(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            metadata_json=row["metadata_json"],
            created_at=_parse_datetime(row["created_at"]),
        )


class CandidateProfileCRUD:
    """CRUD for per-project candidate profile."""

    def __init__(self) -> None:
        conn = init_db()
        conn.close()

    def get(self, project_id: str) -> Optional[CandidateProfile]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT project_id, summary, basics_json, preferences_json, constraints_json, updated_at
                FROM candidate_profiles
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
            return self._row_to_profile(row) if row else None
        finally:
            conn.close()

    def upsert(
        self,
        project_id: str,
        *,
        summary: str,
        basics: dict[str, Any],
        preferences: dict[str, Any],
        constraints: dict[str, Any],
    ) -> CandidateProfile:
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO candidate_profiles (
                        project_id, summary, basics_json, preferences_json, constraints_json, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(project_id) DO UPDATE SET
                        summary = excluded.summary,
                        basics_json = excluded.basics_json,
                        preferences_json = excluded.preferences_json,
                        constraints_json = excluded.constraints_json,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        project_id,
                        summary,
                        _json_text(basics, default="{}"),
                        _json_text(preferences, default="{}"),
                        _json_text(constraints, default="{}"),
                    ),
                )
            profile = self.get(project_id)
            if profile is None:
                raise RuntimeError("Failed to upsert candidate profile.")
            return profile
        finally:
            conn.close()

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> CandidateProfile:
        return CandidateProfile(
            project_id=row["project_id"],
            summary=row["summary"],
            basics_json=row["basics_json"],
            preferences_json=row["preferences_json"],
            constraints_json=row["constraints_json"],
            updated_at=_parse_datetime(row["updated_at"]),
        )


class ExperienceItemCRUD:
    """CRUD for reusable experience items."""

    def __init__(self) -> None:
        conn = init_db()
        conn.close()

    def create(
        self,
        project_id: str,
        *,
        title: str,
        organization: str = "",
        time_range: str = "",
        summary: str = "",
        tags: list[str] | None = None,
        metrics: list[str] | None = None,
        evidence: list[str] | None = None,
        confidence: float = 0.7,
        source: str = "dialog",
    ) -> ExperienceItem:
        conn = get_connection()
        try:
            item_id = f"exp_{generate_short_id(10)}"
            with conn:
                conn.execute(
                    """
                    INSERT INTO experience_items (
                        id, project_id, title, organization, time_range, summary,
                        tags_json, metrics_json, evidence_json, confidence, source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        project_id,
                        title,
                        organization,
                        time_range,
                        summary,
                        _json_text(tags or [], default="[]"),
                        _json_text(metrics or [], default="[]"),
                        _json_text(evidence or [], default="[]"),
                        confidence,
                        source,
                    ),
                )
            row = conn.execute(
                """
                SELECT id, project_id, title, organization, time_range, summary,
                       tags_json, metrics_json, evidence_json, confidence, source,
                       created_at, updated_at
                FROM experience_items
                WHERE id = ?
                """,
                (item_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError("Failed to create experience item.")
            return self._row_to_experience(row)
        finally:
            conn.close()

    def list_by_project(self, project_id: str) -> list[ExperienceItem]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, project_id, title, organization, time_range, summary,
                       tags_json, metrics_json, evidence_json, confidence, source,
                       created_at, updated_at
                FROM experience_items
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
            return [self._row_to_experience(row) for row in rows]
        finally:
            conn.close()

    def get(self, item_id: str) -> Optional[ExperienceItem]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, project_id, title, organization, time_range, summary,
                       tags_json, metrics_json, evidence_json, confidence, source,
                       created_at, updated_at
                FROM experience_items
                WHERE id = ?
                """,
                (item_id,),
            ).fetchone()
            return self._row_to_experience(row) if row else None
        finally:
            conn.close()

    def update(
        self,
        item_id: str,
        *,
        title: str,
        organization: str,
        time_range: str,
        summary: str,
        tags: list[str],
        metrics: list[str],
        evidence: list[str],
        confidence: float,
        source: str,
    ) -> Optional[ExperienceItem]:
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE experience_items
                    SET title = ?, organization = ?, time_range = ?, summary = ?,
                        tags_json = ?, metrics_json = ?, evidence_json = ?,
                        confidence = ?, source = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        title,
                        organization,
                        time_range,
                        summary,
                        _json_text(tags, default="[]"),
                        _json_text(metrics, default="[]"),
                        _json_text(evidence, default="[]"),
                        confidence,
                        source,
                        item_id,
                    ),
                )
            return self.get(item_id)
        finally:
            conn.close()

    def delete(self, item_id: str) -> bool:
        conn = get_connection()
        try:
            with conn:
                cursor = conn.execute("DELETE FROM experience_items WHERE id = ?", (item_id,))
            return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def _row_to_experience(row: sqlite3.Row) -> ExperienceItem:
        return ExperienceItem(
            id=row["id"],
            project_id=row["project_id"],
            title=row["title"],
            organization=row["organization"],
            time_range=row["time_range"],
            summary=row["summary"],
            tags_json=row["tags_json"],
            metrics_json=row["metrics_json"],
            evidence_json=row["evidence_json"],
            confidence=row["confidence"],
            source=row["source"],
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )


class JobTrackCRUD:
    """CRUD for job tracks."""

    def __init__(self) -> None:
        conn = init_db()
        conn.close()

    def get(self, track_id: str) -> Optional[JobTrack]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, project_id, name, positioning, core_keywords_json,
                       resume_strategy, default_resume_outline, primary_jd_entry_id,
                       created_at, updated_at
                FROM job_tracks
                WHERE id = ?
                """,
                (track_id,),
            ).fetchone()
            return self._row_to_track(row) if row else None
        finally:
            conn.close()

    def get_by_name(self, project_id: str, name: str) -> Optional[JobTrack]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, project_id, name, positioning, core_keywords_json,
                       resume_strategy, default_resume_outline, primary_jd_entry_id,
                       created_at, updated_at
                FROM job_tracks
                WHERE project_id = ? AND name = ?
                """,
                (project_id, name),
            ).fetchone()
            return self._row_to_track(row) if row else None
        finally:
            conn.close()

    def create(
        self,
        project_id: str,
        *,
        name: str,
        positioning: str = "",
        core_keywords: list[str] | None = None,
        resume_strategy: str = "",
        default_resume_outline: str = "",
    ) -> JobTrack:
        conn = get_connection()
        try:
            track_id = f"track_{generate_short_id(10)}"
            with conn:
                conn.execute(
                    """
                    INSERT INTO job_tracks (
                        id, project_id, name, positioning, core_keywords_json,
                        resume_strategy, default_resume_outline, primary_jd_entry_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, '')
                    """,
                    (
                        track_id,
                        project_id,
                        name,
                        positioning,
                        _json_text(core_keywords or [], default="[]"),
                        resume_strategy,
                        default_resume_outline,
                    ),
                )
            track = self.get(track_id)
            if track is None:
                raise RuntimeError("Failed to create job track.")
            return track
        finally:
            conn.close()

    def get_or_create(
        self,
        project_id: str,
        *,
        name: str,
        positioning: str = "",
        core_keywords: list[str] | None = None,
        resume_strategy: str = "",
        default_resume_outline: str = "",
    ) -> JobTrack:
        existing = self.get_by_name(project_id, name)
        if existing is not None:
            if positioning or core_keywords or resume_strategy or default_resume_outline:
                self.update(
                    existing.id,
                    name=existing.name,
                    positioning=positioning or existing.positioning,
                    core_keywords=core_keywords
                    or json.loads(existing.core_keywords_json or "[]"),
                    resume_strategy=resume_strategy or existing.resume_strategy,
                    default_resume_outline=default_resume_outline or existing.default_resume_outline,
                    primary_jd_entry_id=existing.primary_jd_entry_id,
                )
            refreshed = self.get(existing.id)
            if refreshed is None:
                raise RuntimeError("Failed to refresh existing track.")
            return refreshed

        conn = get_connection()
        try:
            track_id = f"track_{generate_short_id(10)}"
            with conn:
                conn.execute(
                    """
                    INSERT INTO job_tracks (
                        id, project_id, name, positioning, core_keywords_json,
                        resume_strategy, default_resume_outline, primary_jd_entry_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, '')
                    """,
                    (
                        track_id,
                        project_id,
                        name,
                        positioning,
                        _json_text(core_keywords or [], default="[]"),
                        resume_strategy,
                        default_resume_outline,
                    ),
                )
            track = self.get(track_id)
            if track is None:
                raise RuntimeError("Failed to create job track.")
            return track
        finally:
            conn.close()

    def update(
        self,
        track_id: str,
        *,
        name: str,
        positioning: str,
        core_keywords: list[str],
        resume_strategy: str,
        default_resume_outline: str,
        primary_jd_entry_id: str,
    ) -> Optional[JobTrack]:
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE job_tracks
                    SET name = ?, positioning = ?, core_keywords_json = ?, resume_strategy = ?,
                        default_resume_outline = ?, primary_jd_entry_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        name,
                        positioning,
                        _json_text(core_keywords, default="[]"),
                        resume_strategy,
                        default_resume_outline,
                        primary_jd_entry_id,
                        track_id,
                    ),
                )
            return self.get(track_id)
        finally:
            conn.close()

    def delete(self, track_id: str) -> bool:
        conn = get_connection()
        try:
            with conn:
                cursor = conn.execute("DELETE FROM job_tracks WHERE id = ?", (track_id,))
            return cursor.rowcount > 0
        finally:
            conn.close()

    def list_by_project(self, project_id: str) -> list[JobTrack]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, project_id, name, positioning, core_keywords_json,
                       resume_strategy, default_resume_outline, primary_jd_entry_id,
                       created_at, updated_at
                FROM job_tracks
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
            return [self._row_to_track(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def _row_to_track(row: sqlite3.Row) -> JobTrack:
        return JobTrack(
            id=row["id"],
            project_id=row["project_id"],
            name=row["name"],
            positioning=row["positioning"],
            core_keywords_json=row["core_keywords_json"],
            resume_strategy=row["resume_strategy"],
            default_resume_outline=row["default_resume_outline"],
            primary_jd_entry_id=row["primary_jd_entry_id"],
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )


class JobTrackJDLinkCRUD:
    """CRUD for track to JD links."""

    def __init__(self) -> None:
        conn = init_db()
        conn.close()

    def link(
        self,
        track_id: str,
        project_jd_entry_id: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> JobTrackJDLink:
        conn = get_connection()
        try:
            link_id = f"link_{generate_short_id(10)}"
            with conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO job_track_jd_links (
                        id, track_id, project_jd_entry_id, metadata_json
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (link_id, track_id, project_jd_entry_id, _json_text(metadata, default="{}")),
                )
            row = conn.execute(
                """
                SELECT id, track_id, project_jd_entry_id, metadata_json, created_at
                FROM job_track_jd_links
                WHERE track_id = ? AND project_jd_entry_id = ?
                """,
                (track_id, project_jd_entry_id),
            ).fetchone()
            if row is None:
                raise RuntimeError("Failed to create track/JD link.")
            return self._row_to_link(row)
        finally:
            conn.close()

    def list_by_track(self, track_id: str) -> list[JobTrackJDLink]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, track_id, project_jd_entry_id, metadata_json, created_at
                FROM job_track_jd_links
                WHERE track_id = ?
                ORDER BY created_at ASC
                """,
                (track_id,),
            ).fetchall()
            return [self._row_to_link(row) for row in rows]
        finally:
            conn.close()

    def list_by_jd_entry(self, jd_entry_id: str) -> list[JobTrackJDLink]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, track_id, project_jd_entry_id, metadata_json, created_at
                FROM job_track_jd_links
                WHERE project_jd_entry_id = ?
                ORDER BY created_at ASC
                """,
                (jd_entry_id,),
            ).fetchall()
            return [self._row_to_link(row) for row in rows]
        finally:
            conn.close()

    def delete(self, track_id: str, project_jd_entry_id: str) -> bool:
        conn = get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    DELETE FROM job_track_jd_links
                    WHERE track_id = ? AND project_jd_entry_id = ?
                    """,
                    (track_id, project_jd_entry_id),
                )
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_by_track(self, track_id: str) -> int:
        conn = get_connection()
        try:
            with conn:
                cursor = conn.execute("DELETE FROM job_track_jd_links WHERE track_id = ?", (track_id,))
            return cursor.rowcount
        finally:
            conn.close()

    def delete_by_jd_entry(self, jd_entry_id: str) -> int:
        conn = get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM job_track_jd_links WHERE project_jd_entry_id = ?",
                    (jd_entry_id,),
                )
            return cursor.rowcount
        finally:
            conn.close()

    @staticmethod
    def _row_to_link(row: sqlite3.Row) -> JobTrackJDLink:
        return JobTrackJDLink(
            id=row["id"],
            track_id=row["track_id"],
            project_jd_entry_id=row["project_jd_entry_id"],
            metadata_json=row["metadata_json"],
            created_at=_parse_datetime(row["created_at"]),
        )


class RunTraceCRUD:
    """CRUD for runtime traces."""

    def __init__(self) -> None:
        conn = init_db()
        conn.close()

    def create(
        self,
        *,
        project_id: str,
        session_id: str,
        message_id: str,
        step_index: int,
        kind: str,
        payload: dict[str, Any],
    ) -> RunTrace:
        conn = get_connection()
        try:
            trace_id = f"trace_{generate_short_id(10)}"
            with conn:
                conn.execute(
                    """
                    INSERT INTO run_traces (
                        id, project_id, session_id, message_id, step_index, kind, payload_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trace_id,
                        project_id,
                        session_id,
                        message_id,
                        step_index,
                        kind,
                        _json_text(payload, default="{}"),
                    ),
                )
            row = conn.execute(
                """
                SELECT id, project_id, session_id, message_id, step_index, kind,
                       payload_json, created_at
                FROM run_traces
                WHERE id = ?
                """,
                (trace_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError("Failed to create trace.")
            return self._row_to_trace(row)
        finally:
            conn.close()

    def list_by_session(self, session_id: str, *, limit: int = 100) -> list[RunTrace]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, project_id, session_id, message_id, step_index, kind,
                       payload_json, created_at
                FROM run_traces
                WHERE session_id = ?
                ORDER BY created_at ASC, step_index ASC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
            return [self._row_to_trace(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def _row_to_trace(row: sqlite3.Row) -> RunTrace:
        return RunTrace(
            id=row["id"],
            project_id=row["project_id"],
            session_id=row["session_id"],
            message_id=row["message_id"],
            step_index=row["step_index"],
            kind=row["kind"],
            payload_json=row["payload_json"],
            created_at=_parse_datetime(row["created_at"]),
        )


class AgentArtifactCRUD:
    """CRUD for generated artifacts."""

    def __init__(self) -> None:
        conn = init_db()
        conn.close()

    def create(
        self,
        *,
        project_id: str,
        track_id: str,
        jd_entry_id: str = "",
        artifact_type: str,
        version: int,
        path: str,
        summary: dict[str, Any] | None = None,
    ) -> AgentArtifact:
        conn = get_connection()
        try:
            artifact_id = f"artifact_{generate_short_id(10)}"
            with conn:
                conn.execute(
                    """
                    INSERT INTO agent_artifacts (
                        id, project_id, track_id, jd_entry_id, artifact_type,
                        version, path, summary_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        artifact_id,
                        project_id,
                        track_id,
                        jd_entry_id,
                        artifact_type,
                        version,
                        path,
                        _json_text(summary, default="{}"),
                    ),
                )
            artifact = self.get(artifact_id)
            if artifact is None:
                raise RuntimeError("Failed to create artifact record.")
            return artifact
        finally:
            conn.close()

    def get(self, artifact_id: str) -> Optional[AgentArtifact]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, project_id, track_id, jd_entry_id, artifact_type,
                       version, path, summary_json, created_at
                FROM agent_artifacts
                WHERE id = ?
                """,
                (artifact_id,),
            ).fetchone()
            return self._row_to_artifact(row) if row else None
        finally:
            conn.close()

    def list_by_project(self, project_id: str, *, limit: int = 20) -> list[AgentArtifact]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, project_id, track_id, jd_entry_id, artifact_type,
                       version, path, summary_json, created_at
                FROM agent_artifacts
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (project_id, limit),
            ).fetchall()
            return [self._row_to_artifact(row) for row in rows]
        finally:
            conn.close()

    def latest_for_track(self, track_id: str, artifact_type: str) -> Optional[AgentArtifact]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, project_id, track_id, jd_entry_id, artifact_type,
                       version, path, summary_json, created_at
                FROM agent_artifacts
                WHERE track_id = ? AND artifact_type = ?
                ORDER BY version DESC, created_at DESC
                LIMIT 1
                """,
                (track_id, artifact_type),
            ).fetchone()
            return self._row_to_artifact(row) if row else None
        finally:
            conn.close()

    def list_by_track_and_type(
        self,
        track_id: str,
        artifact_type: str,
        *,
        limit: int = 20,
    ) -> list[AgentArtifact]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, project_id, track_id, jd_entry_id, artifact_type,
                       version, path, summary_json, created_at
                FROM agent_artifacts
                WHERE track_id = ? AND artifact_type = ?
                ORDER BY version DESC, created_at DESC
                LIMIT ?
                """,
                (track_id, artifact_type, limit),
            ).fetchall()
            return [self._row_to_artifact(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def _row_to_artifact(row: sqlite3.Row) -> AgentArtifact:
        return AgentArtifact(
            id=row["id"],
            project_id=row["project_id"],
            track_id=row["track_id"],
            jd_entry_id=row["jd_entry_id"],
            artifact_type=row["artifact_type"],
            version=row["version"],
            path=row["path"],
            summary_json=row["summary_json"],
            created_at=_parse_datetime(row["created_at"]),
        )
