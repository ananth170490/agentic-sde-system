# agentic-sde-system

Agentic software engineering orchestrator that converts a natural-language requirement into:

- structured requirement analysis
- architecture design
- dependency-aware task DAG
- generated code and tests
- validation and bounded repair loops
- risk documentation and final summary

Human approval gates are built into the workflow so generation is controlled, not fully autonomous.

## What This Project Does

Given a requirement like:

> Build a scalable URL shortener service with APIs, persistence, and analytics.

the system runs a full engineering pipeline:

1. Intake and requirement structuring
2. Clarification gate for ambiguous input
3. Architecture design
4. Task decomposition into a DAG
5. Plan approval gate
6. Code + test generation per task
7. Validation + repair retries
8. Risk documentation
9. Merge approval gate
10. Finalization

## Repository Layout

- `orchestrator/`: workflow graph, agents, API, tools, and gates
- `tests/`: unit and integration tests for agents, graph, API, and tools
- `examples/`: runnable greenfield, brownfield, and ambiguous demonstrations
- `generated_projects/`: generated artifacts from sample runs
- `docs/`: architecture docs, demo checklist, and submission material

## Prerequisites

- Python 3.11+
- Docker + Docker Compose (recommended path)

## Configuration

Create a `.env` file in the repo root (or export env vars).

Core options:

- `MODEL_PROVIDER=anthropic` (default)
- `MODEL_PROVIDER=ollama`
- `MODEL_PROVIDER=scripted` (deterministic demo-friendly mode)
- `DEMO_MODE=true` (deterministic API responses for live demos)

If using Anthropic:

- `ANTHROPIC_API_KEY=<your_key>`

## Quick Start (Docker)

```bash
docker compose up --build -d
```

API is available at:

- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/openapi.json` (OpenAPI spec)
- `http://localhost:8000/live-demo` (one-click live demo runner with approval/reject popups)

Stop services:

```bash
docker compose down
```

## Quick Start (Local)

```bash
pip install -r requirements.txt
uvicorn orchestrator.api.main:app --reload
```

## Live Demo UI (Auto Progress + Human Gate Popups)

Use this page for interview/demo flow without manually stepping each phase in Swagger:

- `http://localhost:8000/live-demo`

How it behaves:

1. Submit requirement once
2. Workflow auto-advances
3. At each gate, browser popup appears
4. Choose approve or reject
5. Execution log and final status are shown on-screen

This is intended for fast demonstrations of human-in-the-loop orchestration.

## API Endpoints

- `POST /requirements`: create and start a run
- `GET /runs/{run_id}`: inspect persisted run state
- `POST /runs/{run_id}/approve`: approve and resume from gate
- `POST /runs/{run_id}/reject`: reject and end run

## Run the Mandatory Greenfield Example

```bash
python examples/greenfield_run/run_url_shortener.py
```

This script:

- submits the URL shortener requirement
- prints review payloads at gates
- auto-approves for scripted demo flow
- copies generated artifacts into `generated_projects/url-shortener/`
- runs generated project tests

## Other Example Runs

Ambiguous requirement flow:

```bash
python examples/ambiguous_run/run_ambiguous.py
```

Brownfield enhancement flow:

```bash
python examples/brownfield_run/run_add_auth.py
```

## Testing

Run full test suite:

```bash
pytest
```

Testing strategy:

- unit tests for agents/tools with deterministic fake provider responses
- integration tests for graph transitions, pause/resume, and completion
- API tests for submission, approval, and end-to-end lifecycle behavior

## Architecture Notes

Core orchestration lives in a phase-routed graph with persistent state:

- graph: `orchestrator/graph.py`
- state model/store: `orchestrator/state.py`
- human gates: `orchestrator/gates/human_approval.py`
- API surface: `orchestrator/api/main.py`

## Known Limitations

- execution sandboxing is subprocess-based, not full container isolation per task
- model quality influences non-scripted generation quality
- brownfield impact analysis uses AST/import/grep heuristics (not embeddings)

## Documentation

- `docs/submission_guide.md`: review-ready walkthrough and knowledge transfer guide
- `docs/live_demo_checklist.md`: Live demo scripts
- `docs/submission_package.md`: assignment mapping and implementation summary
- `docs/demo_mode_and_production_readiness.md`: demo mode and production hardening notes
