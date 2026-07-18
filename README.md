# agentic-sde-system

Agentic software engineering orchestrator that turns requirements into architecture, tasks, code, tests, validation results, and risk documentation with human approval gates.

## Setup Instructions

### Environment Variables

Create a `.env` file (or export env vars). If you use Anthropic, set:

- `ANTHROPIC_API_KEY=...`

Optional provider selection:

- `MODEL_PROVIDER=anthropic` (default)
- `MODEL_PROVIDER=ollama`
- `MODEL_PROVIDER=scripted` for deterministic local demo fallback of the mandatory URL shortener flow
- `DEMO_MODE=true` for deterministic hardcoded API responses in Swagger demos

You can use `.env.example` as a template.

### Run with Docker Compose

```bash
docker compose up --build
```

This starts the orchestrator API on port `8000`.

### Run Locally

```bash
pip install -r requirements.txt
uvicorn orchestrator.api.main:app --reload
```

## Mandatory Use Case

Run the required greenfield example:

```bash
python examples/greenfield_run/run_url_shortener.py
```

This script submits the URL shortener requirement, prints gate review payloads, auto-approves pauses, copies final artifacts into `generated_projects/url-shortener/`, and runs tests for the generated project.

## Submission Docs

- `docs/submission_package.md`: submission-ready write-up that maps the implementation directly to the assignment requirements.
- `docs/live_demo_checklist.md`: terminal-by-terminal 5-minute and 10-minute demo scripts with exact commands and talking points.
- `docs/demo_mode_and_production_readiness.md`: hardcoded demo mode usage, sample prompts, and production-readiness plan.

## Submission KT

Primary interviewer-facing KT document:

- `docs/submission_guide.md`

This KT includes:

- assignment requirement mapping
- architecture and orchestration explanation
- sample inputs/outputs for greenfield, brownfield, and ambiguous scenarios
- setup and evaluation steps
- validation and risk-management strategy

## Running Tests

```bash
pytest
```

## Testing Approach

- Unit tests per agent/tool use `FakeModelProvider` for deterministic structured outputs and fast feedback.
- Integration tests cover full graph orchestration flow (state transitions, pauses, resumes, and completion semantics).
- Real end-to-end generation is exercised by the URL shortener example, including execution of the generated project's own test suite.

## Known Limitations

- Generated code execution is not container-sandboxed in this prototype; sandboxing is subprocess-based and not full isolation.
- LLM quality directly affects real-model generation quality for complex prompts; a deterministic scripted provider is included for reliable local demonstration.
- Brownfield repo indexing uses AST + grep/import-graph heuristics, not embedding-based semantic indexing.
- Human approval in examples is simulated via auto-approve-after-printing `review_payload` rather than a dedicated UI.
