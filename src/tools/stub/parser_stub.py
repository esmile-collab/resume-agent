"""Parser stub for M3-stub stage."""

from __future__ import annotations

from typing import Any


class ParserStub:
    """Return deterministic fake parser outputs for JD and resume."""

    def parse_jd(self, jd_text: str) -> dict[str, Any]:
        """Return one-entry JD parse result aligned with tool schema shape."""
        summary = jd_text.strip().splitlines()[0] if jd_text.strip() else "Stub JD"
        return {
            "jd_count": 1,
            "jd_entries": [
                {
                    "project_jd_id": "stub_jd_001",
                    "title": "Stub JD Entry",
                    "raw_text_ref": "inline://stub_jd_001",
                }
            ],
            "direction_count": 1,
            "resume_output_count": 1,
            "directions": [
                {
                    "direction_id": "stub_direction_001",
                    "direction_name": "通用方向",
                    "source_jd_ids": ["stub_jd_001"],
                    "keywords": ["沟通", "执行", "协作"],
                    "capabilities": [
                        {"tag": "执行力", "weight": 0.8, "evidence": summary},
                    ],
                    "summary": "Stub: 默认聚为一个方向",
                }
            ],
            "split_preview": [
                {
                    "jd_id": "stub_jd_001",
                    "title": "Stub JD Entry",
                    "mapped_direction_id": "stub_direction_001",
                }
            ],
        }

    def parse_resume(self, resume_text: str) -> dict[str, Any]:
        """Return deterministic fake resume parse result."""
        summary = resume_text.strip().splitlines()[0] if resume_text.strip() else "Stub Resume"
        return {
            "experiences": [
                {
                    "title": "Stub Experience",
                    "time": "2024-01 ~ 2024-12",
                    "summary": summary,
                    "evidence_spans": [summary],
                }
            ],
            "skills": ["沟通", "数据分析", "跨团队协作"],
            "profile_facts": {
                "education": ["本科"],
                "constraints": [],
            },
        }
