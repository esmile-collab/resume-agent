"""Intent and task-state enums used by task routing."""

from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    """Supported user intents for the MVP router."""

    INGEST_JD = "ingest_jd"
    UPDATE_RESUME = "update_resume"
    ADD_INFO = "add_info"
    GENERATE = "generate"
    COMPARE = "compare"
    ABANDON = "abandon"


class TaskState(str, Enum):
    """Task card state machine states."""

    PENDING = "pending"
    SCORED = "scored"
    GENERATING = "generating"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
