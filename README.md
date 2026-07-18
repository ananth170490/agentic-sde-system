# agentic-sde-system

Agentic software engineering orchestrator that converts a natural-language requirement into:

- structured requirement analysis
- architecture design
- dependency-aware task DAG
- generated code and tests
- validation with bounded repair loops
- risk documentation and final engineering summary

Human approval gates are built into the workflow so generation is controlled, auditable, and resumable.

## What This Project Delivers

Given a requirement like:

> Build a scalable URL shortener service with APIs, persistence, and analytics.

the system executes a full SDLC-style pipeline:

1. Intake and requirement structuring
2. Clarification gate for ambiguous input
3. Brownfield codebase reasoning when needed
4. Architecture design
5. Task DAG decomposition
6. Plan approval gate
7. Code + test generation per task
8. Validation + bounded repair retries
9. Risk documentation and engineering summary
10. Merge approval gate and finalization

## Repository Layout

- `orchestrator/`: graph, agents, API, tools, and gates
- `tests/`: unit and integration coverage
- `examples/`: greenfield, brownfield, and ambiguous runs
- `generated_projects/`: generated artifacts from demo runs
- `docs/`: architecture, guide, checklist, and submission material

## Prerequisites

- Python 3.11+
- Docker + Docker Compose (recommended)

## Configuration

Create `.env` in repo root.

### OpenRouter (recommended for live demos)

```env
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=<your_openrouter_key>
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

Optional provider metadata:

```env
OPENROUTER_SITE_URL=http://localhost:8000
OPENROUTER_APP_NAME=agentic-sde-system
```

### Other providers

```env
MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=<your_key>
```

```env
MODEL_PROVIDER=ollama
```

### Deterministic demo mode

```env
DEMO_MODE=true
```

## Quick Start (Docker)

```bash
docker compose up --build -d
```

Endpoints:

- `http://localhost:8000/docs` (Swagger)
- `http://localhost:8000/openapi.json` (OpenAPI)
- `http://localhost:8000/live-demo` (one-click runner)

Stop services:

```bash
docker compose down
```

## Quick Start (Local)

```bash
pip install -r requirements.txt
uvicorn orchestrator.api.main:app --reload
```

## Core API Endpoints

- `POST /requirements`
- `GET /runs/{run_id}`
- `POST /runs/{run_id}/approve`
- `POST /runs/{run_id}/reject`

## Run the Example Scenarios

Greenfield (mandatory URL shortener):

```bash
python examples/greenfield_run/run_url_shortener.py
```

Brownfield enhancement:

```bash
python examples/brownfield_run/run_add_auth.py
```

Ambiguous requirement:

```bash
python examples/ambiguous_run/run_ambiguous.py
```

## Testing

Run full suite:

```bash
pytest -q
```

Latest validated baseline:

- `18 passed, 1 warning`

## Engineering-Grade Output Evidence

### Greenfield Run Evidence

- Run ID: `3751c9b4-d1a6-4a0d-95b1-8f06d23b1d6d`
- Status: `completed`
- Category: `greenfield`
- Tasks: `11/11` completed
- Validations: `11/11` passed

Output summary excerpt:

```text
## Implementation Plan and Rationale
The run executed the intake, planning, and DAG workflow with automated gating.

## Generated Artifacts
- analytics/analytics_service.js
- api/analytics_api.js
- api/url_shortener_api.js
- caching/redis_setup.js
- docs/api_documentation.md
- monitoring/logging_setup.js
- persistence/url_repository.js
- schemas/url_analytics_schema.sql
- tests/analytics_api.test.js
- tests/integration_tests.js
- tests/url_shortener_api.test.js
```

### Brownfield Run Evidence

- Run ID: `4944bf07-2468-4bbc-b07c-d112a29cd79f`
- Status: `completed`
- Category: `brownfield`
- Tasks: `7/7` completed
- Validations: `7/7` passed

Output summary excerpt:

```text
## Implementation Plan and Rationale
The run executed the intake, planning, and DAG workflow with automated gating.

## Generated Artifacts
- docs/authentication_and_rbac.md
- src/middleware/jwtAuth.js
- src/rbac/roleManager.js
- src/routes/fixtures.js
- tests/integration/fixtures.test.js
- tests/unit/jwtAuth.test.js
- tests/unit/roleManager.test.js
```

### Ambiguous Run Evidence (OpenRouter Quota/Provider Fallback)

- Run ID: `f64e1021-6402-4a2d-a3dd-f2bd098d1aad`
- Status: `completed`
- Category: `ambiguous`
- Tasks: `0/0` completed (safe fallback path)
- Validations: `0/0` (no generated tasks)

Output summary excerpt:

```text
## Implementation Plan and Rationale
Provider fallback used because the model provider request was blocked by quota/billing limits. Check provider credits and retry the run.

## Generated Artifacts
- No artifacts recorded

## Risks, Trade-offs, and Validation Approach
- Provider fallback used because the model provider request was blocked by quota/billing limits. Check provider credits and retry the run.

## Assumptions and Limitations
- Fallback output was synthesized from schema defaults.
```

Note: raw upstream HTTP messages are intentionally sanitized from reviewer-facing summaries.

## Key Architecture References

- `orchestrator/graph.py`
- `orchestrator/state.py`
- `orchestrator/gates/human_approval.py`
- `orchestrator/tools/model_provider.py`

## Documentation

- `docs/architecture.md`
- `docs/guide.md`
- `docs/live_demo_checklist.md`
- `docs/demo_mode_and_production_readiness.md`
- `docs/submission_guide.md`
- `docs/submission_package.md`
