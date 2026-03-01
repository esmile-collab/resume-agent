"""Database entity models for M1 persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    """Project model."""

    id: str
    name: str
    cycle: Optional[str] = None
    base_resume_path: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class ProjectJDEntry:
    """Project JD entry model."""

    id: str
    project_id: str
    raw_content: str
    source_file: Optional[str] = None
    created_at: Optional[datetime] = None
