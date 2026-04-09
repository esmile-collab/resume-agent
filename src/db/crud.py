# Input: 数据库连接、项目表和 JD 表。
# Output: 输出项目与 JD 的基础 CRUD 能力。
# Pos: 项目级基础仓储层。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""CRUD repositories for M1 persistence layer."""

from __future__ import annotations

import secrets
import sqlite3
import string
from datetime import datetime
from typing import Optional

from .database import get_connection, init_db
from .models import Project, ProjectJDEntry

_ID_ALPHABET = string.ascii_lowercase + string.digits


def _parse_datetime(raw_value: Optional[str]) -> Optional[datetime]:
    """Convert SQLite timestamp string to datetime."""
    if raw_value is None:
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        # SQLite default CURRENT_TIMESTAMP format: YYYY-MM-DD HH:MM:SS
        return datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S")


def generate_short_id(length: int = 8) -> str:
    """Generate a short random ID containing lowercase letters and digits."""
    return "".join(secrets.choice(_ID_ALPHABET) for _ in range(length))


class ProjectCRUD:
    """Repository for project CRUD operations."""

    def __init__(self) -> None:
        # Ensures DB and tables exist for each repository instance.
        conn = init_db()
        conn.close()

    def create(self, name: str, cycle: str = "") -> Project:
        """Create a project with auto-generated 8-char short ID."""
        conn = get_connection()
        try:
            cursor = conn.cursor()

            # Retry on very rare ID collision.
            project_id = generate_short_id(8)
            while (
                cursor.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
                is not None
            ):
                project_id = generate_short_id(8)

            with conn:
                cursor.execute(
                    """
                    INSERT INTO projects (id, name, cycle)
                    VALUES (?, ?, ?)
                    """,
                    (project_id, name, cycle),
                )

            created = cursor.execute(
                """
                SELECT id, name, cycle, base_resume_path, created_at
                FROM projects
                WHERE id = ?
                """,
                (project_id,),
            ).fetchone()
            if created is None:
                raise RuntimeError("Failed to create project record.")
            return self._row_to_project(created)
        finally:
            conn.close()

    def get(self, id: str) -> Optional[Project]:
        """Get one project by ID."""
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, name, cycle, base_resume_path, created_at
                FROM projects
                WHERE id = ?
                """,
                (id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_project(row)
        finally:
            conn.close()

    def list_all(self) -> list[Project]:
        """List all projects sorted by creation time descending."""
        conn = get_connection()
        try:
            rows = conn.execute("""
                SELECT id, name, cycle, base_resume_path, created_at
                FROM projects
                ORDER BY created_at DESC
                """).fetchall()
            return [self._row_to_project(row) for row in rows]
        finally:
            conn.close()

    def delete(self, id: str) -> bool:
        """Delete project by ID."""
        conn = get_connection()
        try:
            with conn:
                cursor = conn.execute("DELETE FROM projects WHERE id = ?", (id,))
            return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> Project:
        """Map DB row to Project dataclass."""
        return Project(
            id=row["id"],
            name=row["name"],
            cycle=row["cycle"],
            base_resume_path=row["base_resume_path"],
            created_at=_parse_datetime(row["created_at"]),
        )


class ProjectJDEntryCRUD:
    """Repository for project JD entry CRUD operations."""

    def __init__(self) -> None:
        conn = init_db()
        conn.close()

    def create(self, project_id: str, content: str, source_file: str = "") -> ProjectJDEntry:
        """Create a JD entry for a project."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            jd_id = generate_short_id(12)

            with conn:
                cursor.execute(
                    """
                    INSERT INTO project_jd_entries (id, project_id, raw_content, source_file)
                    VALUES (?, ?, ?, ?)
                    """,
                    (jd_id, project_id, content, source_file),
                )

            created = cursor.execute(
                """
                SELECT id, project_id, raw_content, source_file, created_at
                FROM project_jd_entries
                WHERE id = ?
                """,
                (jd_id,),
            ).fetchone()
            if created is None:
                raise RuntimeError("Failed to create project JD entry.")
            return self._row_to_jd_entry(created)
        finally:
            conn.close()

    def get(self, id: str) -> Optional[ProjectJDEntry]:
        """Get one JD entry by ID."""
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, project_id, raw_content, source_file, created_at
                FROM project_jd_entries
                WHERE id = ?
                """,
                (id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_jd_entry(row)
        finally:
            conn.close()

    def list_by_project(self, project_id: str) -> list[ProjectJDEntry]:
        """List JD entries under one project."""
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, project_id, raw_content, source_file, created_at
                FROM project_jd_entries
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,),
            ).fetchall()
            return [self._row_to_jd_entry(row) for row in rows]
        finally:
            conn.close()

    def update(
        self,
        id: str,
        *,
        content: str | None = None,
        source_file: str | None = None,
    ) -> Optional[ProjectJDEntry]:
        """Update one JD entry."""
        current = self.get(id)
        if current is None:
            return None

        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE project_jd_entries
                    SET raw_content = ?, source_file = ?
                    WHERE id = ?
                    """,
                    (
                        content if content is not None else current.raw_content,
                        source_file if source_file is not None else current.source_file,
                        id,
                    ),
                )
            return self.get(id)
        finally:
            conn.close()

    def delete(self, id: str) -> bool:
        """Delete one JD entry."""
        conn = get_connection()
        try:
            with conn:
                cursor = conn.execute("DELETE FROM project_jd_entries WHERE id = ?", (id,))
            return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def _row_to_jd_entry(row: sqlite3.Row) -> ProjectJDEntry:
        """Map DB row to ProjectJDEntry dataclass."""
        return ProjectJDEntry(
            id=row["id"],
            project_id=row["project_id"],
            raw_content=row["raw_content"],
            source_file=row["source_file"],
            created_at=_parse_datetime(row["created_at"]),
        )
