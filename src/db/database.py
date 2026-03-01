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

    conn.commit()
    return conn
