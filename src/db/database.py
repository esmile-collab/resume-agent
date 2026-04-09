# Input: SQLite 路径配置与 schema 初始化 SQL。
# Output: 输出数据库连接和初始化函数。
# Pos: SQLite 连接与建表入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""SQLite database initialization and connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = ".data/resume_agent.db"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create a SQLite connection with foreign key constraints enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Initialize SQLite database and required M1 tables."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(str(path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            cycle TEXT,
            base_resume_path TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_jd_entries (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            raw_content TEXT NOT NULL,
            source_file TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_sessions (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_profiles (
            project_id TEXT PRIMARY KEY,
            summary TEXT NOT NULL DEFAULT '',
            basics_json TEXT NOT NULL DEFAULT '{}',
            preferences_json TEXT NOT NULL DEFAULT '{}',
            constraints_json TEXT NOT NULL DEFAULT '{}',
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experience_items (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            title TEXT NOT NULL,
            organization TEXT NOT NULL DEFAULT '',
            time_range TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            tags_json TEXT NOT NULL DEFAULT '[]',
            metrics_json TEXT NOT NULL DEFAULT '[]',
            evidence_json TEXT NOT NULL DEFAULT '[]',
            confidence REAL NOT NULL DEFAULT 0.7,
            source TEXT NOT NULL DEFAULT 'dialog',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_tracks (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            name TEXT NOT NULL,
            positioning TEXT NOT NULL DEFAULT '',
            core_keywords_json TEXT NOT NULL DEFAULT '[]',
            resume_strategy TEXT NOT NULL DEFAULT '',
            default_resume_outline TEXT NOT NULL DEFAULT '',
            primary_jd_entry_id TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, name),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

    track_columns = {
        row["name"] for row in cursor.execute("PRAGMA table_info(job_tracks)").fetchall()
    }
    if "primary_jd_entry_id" not in track_columns:
        cursor.execute(
            """
            ALTER TABLE job_tracks
            ADD COLUMN primary_jd_entry_id TEXT NOT NULL DEFAULT ''
            """
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_track_jd_links (
            id TEXT PRIMARY KEY,
            track_id TEXT NOT NULL,
            project_jd_entry_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(track_id, project_jd_entry_id),
            FOREIGN KEY (track_id) REFERENCES job_tracks(id) ON DELETE CASCADE,
            FOREIGN KEY (project_jd_entry_id) REFERENCES project_jd_entries(id) ON DELETE CASCADE
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS run_traces (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            step_index INTEGER NOT NULL,
            kind TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
        )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_artifacts (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            track_id TEXT NOT NULL,
            jd_entry_id TEXT NOT NULL DEFAULT '',
            artifact_type TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            path TEXT NOT NULL,
            summary_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (track_id) REFERENCES job_tracks(id) ON DELETE CASCADE
        )
        """)

    conn.commit()
    return conn
