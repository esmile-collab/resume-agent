<p align="center">
  <strong>Resume Agent</strong>
</p>

<p align="center">
  <em>A conversational workspace for resume optimization — score, generate, polish, and export with full traceability.</em>
</p>

<p align="center">
  <!-- placeholders — replace <hash> with real badge URLs after CI/coverage is wired -->
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/React-18-61dafb.svg" alt="React 18" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT" />
</p>

---

## Overview

**Resume Agent** is an end-to-end resume optimization platform built around a session-based conversational workflow. Unlike simple chatbots, it is designed as a deployable system that preserves every decision, artifact version, and scoring trace throughout the job application pipeline.

Upload your base resume and target JDs. The system analyzes gaps, scores fit, generates tailored versions, polishes expression, and exports — all within a single workspace backed by structured memory and full audit trails.

## Features

- **Session Management** — Create, restore, and switch between job-application sessions with full state persistence.
- **Resume Scoring** — Hybrid scoring engine combining hard metrics (keywords, structure, experience density) with LLM-powered soft evaluation. Supports JD implicit-requirement inference.
- **Smart Generation** — Generate JD-aligned resume versions while preserving factual accuracy.
- **Block-Level Polishing** — Targeted expression improvements with change tracking and diff visualization.
- **Multi-Format Export** — Export resumes as PDF or DOCX with versioned artifacts.
- **Structured Memory** — Career profile, experience entries, and job tracks are stored as queryable structured data, not raw conversation history.
- **Full Traceability** — Every agent action is logged as an observable trace with snapshot diffs and artifact versioning.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│   ChatPanel · ScorePanel · MemoryPanel · ArtifactPanel  │
└─────────────────────────┬───────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────┐
│                  API Layer (FastAPI)                      │
│              Sessions · Messages · Artifacts              │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   Agent Runtime                           │
│   Planner → Memory → Tool Registry → Runtime Pipeline    │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┘
   │          │          │          │          │
┌──▼──┐  ┌───▼───┐ ┌────▼───┐ ┌───▼───┐ ┌───▼────┐
│Scoring│  │ JD    │ │Resume  │ │Polish │ │Export  │
│Engine │  │Analyzer│ │Parser  │ │Patcher│ │Service │
└──┬───┘  └───┬───┘ └────┬───┘ └───┬───┘ └───┬────┘
   │          │          │          │          │
┌──▼──────────▼──────────▼──────────▼──────────▼────────┐
│               Persistence (SQLite)                      │
│         Sessions · Artifacts · Snapshots                │
└────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm

### Install & Run

```bash
# Clone the repository
git clone git@github.com:esmile-collab/resume-agent.git
cd resume-agent

# Configure environment
cp .env.example .env
# Edit .env — set your LLM API key (Anthropic or OpenAI)

# One-click start (installs deps, inits DB, launches both services)
./start.sh
```

Services will be available at:

| Service  | URL                              |
| -------- | -------------------------------- |
| Frontend | http://127.0.0.1:5173            |
| Backend  | http://127.0.0.1:8000            |
| API Docs | http://127.0.0.1:8000/docs       |

### Selective Start

```bash
./start.sh backend    # API server only
./start.sh frontend   # Dev server only
```

### Docker

```bash
docker build -t resume-agent .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v resume-data:/app/.data \
  resume-agent
```

## Project Structure

```
resume-agent/
├── frontend/                 # React workspace (Vite + TypeScript)
│   └── src/
│       ├── components/       # UI panels: Chat, Score, Memory, Artifact, etc.
│       ├── api/              # Frontend API client
│       └── types.ts          # Shared TypeScript types
├── src/                      # Backend Python package
│   ├── api/                  # FastAPI HTTP layer & endpoints
│   ├── agent/                # Core runtime: planner, memory, tools
│   ├── services/             # Domain logic: JD analysis, parsing, polish, export
│   ├── scoring/              # Hybrid scoring engine
│   ├── db/                   # SQLite schema & CRUD repositories
│   ├── observability/        # Long-context compression & trace logging
│   ├── cli/                  # Click-based CLI
│   └── tools/                # Tool implementations
├── tests/                    # Acceptance, unit, integration & e2e tests
├── docs/                     # Product & technical documentation
├── scripts/                  # Bootstrap, evaluation, regression & doc guards
├── config/                   # Default configuration (YAML)
├── Dockerfile                # Production container image
├── render.yaml               # Render.com deployment spec
└── pyproject.toml            # Python package manifest
```

## Workflow

1. **Create Session** — Start a workspace, optionally attaching a base resume.
2. **Build Profile** — System extracts and stores structured profile, experiences, and career tracks.
3. **Ingest JDs** — Upload job descriptions; system analyzes and archives them per track.
4. **Score** — Run fit analysis to get a detailed scorecard with gap identification.
5. **Generate / Polish** — Produce JD-targeted resume versions with tracked changes.
6. **Export** — Download polished resumes as PDF or DOCX with full version history.
7. **Review** — Browse snapshots, execution traces, and artifact diffs at any point.

## Development

### Environment Setup

```bash
# Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install
```

### Running Tests

```bash
# All tests
python -m pytest tests/

# Acceptance + unit
python -m pytest tests/acceptance tests/unit/

# With coverage
python -m pytest --cov=src --cov-report=html tests/
```

### Linting & Formatting

```bash
python -m black src/ tests/
python -m mypy src/
```

### Build Frontend

```bash
cd frontend && npm run build
```

## Documentation

| Document | Description |
| -------- | ----------- |
| [Product PRD](docs/product/MVP_PRD_Resume_Fit_Agent.md) | Product requirements & scope |
| [Architecture](docs/technical/ARCHITECTURE.md) | System design & module responsibilities |
| [Scoring System](docs/product/评分系统设计_v2_混合评分_校招版_v2.1.md) | Scoring engine design & methodology |
| [Deployment Guide](docs/DEPLOYMENT.md) | Production deployment instructions |
| [UI Design](docs/product/UI交互设计.md) | Interface interaction flows |

## Tech Stack

| Layer | Technology |
| ----- | ---------- |
| Frontend | React 18 · TypeScript · Vite |
| Backend | Python 3.11 · FastAPI · Uvicorn |
| Database | SQLite |
| LLM | Anthropic Claude / OpenAI GPT |
| Document | pypdf · python-docx · reportlab |
| CLI | Click |
| Testing | pytest · pytest-cov · pytest-asyncio |
| Deployment | Docker · Render.com |

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
