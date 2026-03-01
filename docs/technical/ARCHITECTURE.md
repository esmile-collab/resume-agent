# Architecture - Resume Fit Agent

## Summary

The system is a single-agent core that orchestrates modular tools. The same core powers two entry points:
1. Coding agent skill (CLI wrapper)
2. Frontend via HTTP API

Key goals:
- Intent recognition and gated routing
- Memory for session and user facts
- Evidence-bound outputs with score-based decisions
- Stateful conversation management for out-of-order user input
- Multi-direction JD split and multi-result output
- Project-owned JD repository with centralized allocation
- Deterministic counting: `jd_count`, `direction_count`, `resume_output_count`

---

## Layered Design

### 1. Core Engine (Claude Agent SDK)

Responsibilities:
- Intent recognition and routing
- Tool orchestration
- Score-based recommendation and risk-confirmed execution
- Structured JSON output for UI/CLI
- Session state transition on every user event

### 2. Tools / Skills Modules

Each module is a tool with strict input/output schema.

1. `jd_parser`
- Input: JD text (or OCR text)
- Output: project JD entries, split result, direction clusters (based on narrative framework difference), direction tags
- **Key Logic**: Clusters JDs by "resume preparation cost" rather than keyword overlap
  - Analyzes narrative framework (core competency story, experience focus, skill focus)
  - Groups JDs that require the same resume narrative, even if business scenarios differ
  - Does not enforce hard card count limit in MVP
  - Outputs clustering rationale for user understanding

2. `resume_parser`
- Input: resume text/PDF
- Output: structured experiences, skills, evidence spans

3. `scorer`
- Input: parsed JD + parsed resume
- Output: total score + sub-scores (fit,真实性风险,可复述性)
- Output: match level (`high|medium|low`) for recommendation

4. `improver`
- Input: mapped experiences + JD tags
- Output: revised resume + change log + evidence bindings

5. `reviewer`
- Input: before/after resume + evidence
- Output: post scores, pass/fail, guidance

6. `project_jd_allocator`
- Input: source scope (`project|task_card`) + parsed JD entries + existing task cards
- Output: allocation decisions (`assign_current_card|assign_existing_card|create_new_card`) + preview/confirm plan

---

## Conversation State Model

The core keeps an explicit state machine instead of a single linear run.

### Entities

- `project`: one recruiting cycle context (e.g., internship / campus hiring)
- `project_jd_entry`: project-owned JD source of truth
- `task_card`: one JD direction card under project
- `card_jd_link`: mapping between project JD entries and task cards
- `artifact_version`: immutable JD/resume/output snapshots
- `memory`: scoped memory (project shared + task-card private)
- `metrics`: `jd_count`, `direction_count`, `resume_output_count`

### Task Status

- `pending`
- `scored`
- `generating`
- `completed`
- `abandoned`

### Score Recommendation

- `high`: recommend normal generate
- `medium`: recommend supplement then generate
- `low`: require risk acknowledgement before compensation generate
- Note: score is recommendation signal, not a hard gate

---

## Event Handling (Out-of-Order Input)

Every user message first goes through an input router.

Message types:
- `resume_update`
- `ingest_jd`
- `profile_supplement`
- `command`

Rules:
1. If user sends a new JD while editing another card:
- write JD into `project_jd_entry`
- run `project_jd_allocator` to decide assign current / assign existing / create new card
2. If user sends supplement after scoring:
- write supplement to current `task_card` memory only
- do not auto-sync to project or other cards
3. If user sends multiple JD directions in one message:
- split and cluster first, show preview, wait for user confirmation
- create/update task cards after confirmation
4. If user sends multiple JD entries of same direction:
- keep per-JD records for scoring evidence
- link them to one direction card for resume generation

---

## Intent Recognition

Minimal but explicit:
1. Intent label from router (`ingest_jd|update_resume|add_info|generate|compare|abandon`)
2. State compatibility check
3. Candidate intents for clarification traceability

Intent output schema:
- `intent`: one of 6 core intents
- `reason`: short rationale
- `candidates`: optional alternative intents for clarification
- `need_clarification`: whether to ask a follow-up question

---

## Memory Design

### Project Shared Memory
- Base resume versions uploaded by user
- Project-level metadata (name, target cycle)
- Project JD repository (raw JD + parsed structure)
- JD allocation logs (decision + reason + target card)

### Task-Card Private Memory
- JD-specific supplement facts from conversation
- JD-specific clarifications and constraints
- Card-level notes for generation
- Does not store JD raw source, only references via `card_jd_link`

MVP storage: `SQLite` preferred (supports task states and retries) or `JSONL`.

Recommended tables:
- `projects`
- `project_jd_entries`
- `task_cards`
- `card_jd_links`
- `jd_allocation_logs`
- `artifact_versions`
- `runs`
- `task_memory_facts`
- `messages`

---

## Data Flow

1. Ingest user message
2. Route message type and upsert artifacts
3. For `ingest_jd`, write JD entries into project repository and compute `jd_count`
4. Split/cluster JD entries and compute `direction_count`
5. Build preview allocation plan and wait for user confirmation (batch case)
6. Run `project_jd_allocator` and update `card_jd_link`
7. Set resume plan and compute `resume_output_count` (default equals `direction_count`)
8. Score affected task cards and compute match level
9. User chooses generate action on selected task card
10. Improve + review on selected task card
11. Output per-card artifacts and status

---

## Output Artifacts

- Aggregated counts: `jd_count`, `direction_count`, `resume_output_count`
- Direction-level scorecards
- Revised resume per direction
- Change log with evidence per direction
- Interview question set per direction
- Abandoned directions with improvement advice

Example:
- input 10 JD entries (5 strategy + 5 feature) -> `jd_count=10`
- clustered to 2 directions -> `direction_count=2`
- user confirms allocation -> create/update 2 direction cards
- output 2 resumes -> `resume_output_count=2`

---

## Entry Points

### A. Coding Agent Skill

A CLI wrapper calls the core engine and returns Markdown.

Example CLI:
`resume_agent project ingest-jd --project <project_id> --jd <path> && resume_agent project confirm-allocation --project <project_id> --plan <plan_id>`

### B. Frontend API

HTTP endpoint wraps the same core engine:
- `POST /run`

---

## Constraints

- Single agent workflow
- Evidence binding for every change
- Deterministic state transition per message (no hidden state jump)
