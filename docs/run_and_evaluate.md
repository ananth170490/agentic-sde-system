# Run and Evaluate Guide

This guide provides clear, repeatable steps to run and evaluate the Agentic SDE system.

## 1. Prerequisites

- Python 3.11+
- Docker + Docker Compose
- OpenAI API key

## 2. Configure Environment

Create or update `.env` at repository root:

```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=<your_openai_key>
OPENAI_MODEL=gpt-4o-mini
DEMO_MODE=false
```

Optional endpoint override:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
```

## 3. Start the System

```bash
docker compose up -d --build orchestrator
```

Verify API/UI:

- API docs: `http://localhost:8000/docs`
- Live demo UI: `http://localhost:8000/live-demo`

## 4. Validate Baseline

Run test baseline:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Expected: test suite passes (warnings are acceptable if already known).

## 5. Evaluate the Three Required Scenarios

### 5.1 Greenfield (Mandatory)

```bash
PYTHONPATH=. .venv/bin/python examples/greenfield_run/run_url_shortener.py
```

Evaluate:

- Run completes (`status=completed`)
- DAG tasks complete
- Validation checks pass
- Final output summary includes:
  - Analyze and decompose the requirement
  - Design the architecture
  - Generate code, APIs, and tests
  - Provide trade-offs and a validation strategy

### 5.2 Brownfield

```bash
PYTHONPATH=. .venv/bin/python examples/brownfield_run/run_add_auth.py
```

Evaluate:

- Run completes (`status=completed`)
- Brownfield reasoning path is exercised
- Artifacts and summary are produced

### 5.3 Ambiguous

```bash
PYTHONPATH=. .venv/bin/python examples/ambiguous_run/run_ambiguous.py
```

Evaluate:

- Clarification gate appears
- Approval resumes execution
- Final summary is generated (completed or explicit failure context)

## 6. Evaluate from the Live Demo UI

Open `http://localhost:8000/live-demo`.

For each requirement:

1. Paste requirement text
2. Click **Run Full Demo**
3. Approve human gates in popups
4. Check Execution Log and Output Summary

Use these requirement prompts:

- Greenfield: `Build a scalable URL shortener service with APIs, persistence, and analytics.`
- Brownfield: `Add JWT auth middleware and role-based access checks to the existing fixture service endpoints.`
- Ambiguous: `Make the reporting faster.`

## 7. API-Level Verification (Optional)

Submit requirement:

```bash
curl -s -X POST http://127.0.0.1:8000/requirements \
  -H "Content-Type: application/json" \
  -d '{"text":"Build a scalable URL shortener service with APIs, persistence, and analytics."}'
```

Get run state:

```bash
curl -s http://127.0.0.1:8000/runs/<RUN_ID>
```

Approve gate:

```bash
curl -s -X POST http://127.0.0.1:8000/runs/<RUN_ID>/approve \
  -H "Content-Type: application/json" \
  -d '{"feedback":"approved"}'
```

## 8. What to Capture for Evaluation Evidence

For each scenario, capture:

- Requirement prompt
- Run ID
- Final status and phase
- Task/validation completion counts
- Final output summary excerpt
- Generated artifact list

## 9. Troubleshooting

- Provider/auth errors:
  - Verify `OPENAI_API_KEY` and `OPENAI_MODEL`
  - Rebuild/restart service:

```bash
docker compose up -d --build orchestrator
```

- UI seems stale or mixed:
  - Hard refresh browser or open a fresh tab

- Re-run cleanly:
  - Submit a new requirement; do not reuse old run IDs

## 10. Stop the System

```bash
docker compose down
```
