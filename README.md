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

### Objective

This prototype is built to transform a software requirement into a reviewable engineering outcome through end-to-end SDLC orchestration, not chatbot-style Q and A.

### Scope

- Greenfield scenarios: new feature/system development
- Brownfield scenarios: enhancements, refactoring, and bug-fix style updates
- Test and documentation improvements as first-class workflow outputs
- Well-defined and ambiguous requirement handling

### Core Requirements Coverage

1. Requirement understanding
- Interprets intent, ambiguity, and implicit constraints in `RequirementSpec`.
- Implemented in `orchestrator/agents/intake.py`.

2. Task decomposition
- Produces structured `TaskDAG` with dependencies and execution sequence.
- Implemented in `orchestrator/agents/task_decomposer.py` and `orchestrator/state.py`.

3. Codebase reasoning (brownfield)
- Identifies impacted files/modules and likely change surface.
- Implemented in `orchestrator/agents/codebase_reasoning.py` and `orchestrator/tools/repo_index.py`.

4. Workflow orchestration
- Coordinates multi-step execution with phase routing, dependency gating, and retries.
- Implemented in `orchestrator/graph.py`.

5. Engineering output generation
- Produces code changes, API/schema content, tests, and supporting documentation.
- Implemented across `orchestrator/agents/architect.py`, `orchestrator/agents/code_gen.py`, and `orchestrator/agents/test_gen.py`.

6. Validation and risk control
- Validates using `pytest`, `py_compile`, and `pyflakes`; records risks and trade-offs.
- Implemented in `orchestrator/agents/validator.py` and `orchestrator/agents/risk_docs.py`.

7. Controlled autonomy
- Agents execute independently across phases while humans approve clarify/plan/merge gates.
- Implemented in `orchestrator/gates/human_approval.py` and `orchestrator/api/main.py`.

8. Final structured output
- Emits engineering summary sections: implementation rationale, artifacts, risks/trade-offs/validation, assumptions.
- Implemented in `orchestrator/agents/risk_docs.py`.

### Deliverables Coverage

1. Working prototype
- Runnable API + scripts that accept requirements and produce structured outputs.

2. Architecture overview
- See `docs/architecture.md` for components, control flow, and design decisions.

3. Example scenarios
- Greenfield: `examples/greenfield_run/run_url_shortener.py`
- Brownfield: `examples/brownfield_run/run_add_auth.py`
- Ambiguous: `examples/ambiguous_run/run_ambiguous.py`

4. Setup instructions
- This README and `docs/live_demo_checklist.md` provide run/evaluation steps.

5. Testing approach
- See "Testing" in this README and quality details in `docs/submission_guide.md`.

### Mandatory Use Case Coverage

Requirement:

> Build a scalable URL shortener service with APIs, persistence, and analytics.

The system demonstrates requirement analysis, decomposition, architecture planning, code/test generation, and engineering summary output for this use case via `examples/greenfield_run/run_url_shortener.py`.

### Evaluation Criteria Traceability

- End-to-end completeness: phase-routed orchestration from intake to final summary.
- System design strength: explicit separation of agents, tools, state, and gates.
- Decomposition and orchestration depth: dependency-aware DAG with bounded repairs.
- Output quality and realism: code/test/docs artifacts plus structured summaries.
- Validation and risk management: test/static checks with risk and limitation reporting.
- Clarity and defensibility: persisted run state and reviewer-visible payloads/summaries.

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

### OpenAI (recommended for live demos)

```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=<your_openai_key>
OPENAI_MODEL=gpt-4o-mini
```

Optional provider endpoint override:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
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

### Ambiguous Run Evidence (OpenAI Quota/Provider Fallback)

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
