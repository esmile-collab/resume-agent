# Resume Fit Agent Skill

This skill exposes the Resume Fit Agent via a CLI wrapper so it can be used inside coding agent sessions.

## Purpose

- Run the resume fit workflow from the command line
- Return structured results as Markdown

## Command

```bash
resume_agent project init --name <project_name> --resume <path>
resume_agent project ingest-jd --project <project_id> --jd <path>
resume_agent project confirm-allocation --project <project_id> --plan <plan_id>
resume_agent card add-jd --project <project_id> --card <card_id> --jd <path>  # routed to project allocator
resume_agent card run --project <project_id> --card <card_id> --out <path>
```

## Inputs（按卡片执行）

- Project base resume path (text or PDF)
- Project JD path (text or OCR, can be single or batch)
- Optional card-level JD add path (still routed by project allocator)
- Task card supplement info (optional)

## Outputs

- Markdown report with:
  - Scorecard (before/after)
  - Change log with evidence
  - Revised resume (card final version)
  - Interview question set

## Notes

- Single-agent orchestration
- Tools: `jd_parser`, `project_jd_allocator`, `resume_parser`, `scorer`, `improver`, `reviewer`
- Memory: session + user facts
