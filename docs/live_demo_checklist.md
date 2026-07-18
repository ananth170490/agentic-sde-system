# Live Demo Checklist

This checklist is tuned for the current validated system state, including OpenRouter provider behavior, human approval gates, fallback resilience, and engineering-grade final summaries.

## Current Baseline

- test baseline: `18 passed, 1 warning`
- API/UI endpoint: `http://localhost:8000/live-demo`
- preferred provider mode: OpenRouter
- fallback mode: deterministic demo mode (`DEMO_MODE=true`)

## Environment Setup (OpenRouter)

Set `.env`:

```env
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=<your_openrouter_key>
OPENROUTER_MODEL=openai/gpt-4o-mini
DEMO_MODE=false
```

Start service:

```bash
docker compose up -d --build orchestrator
```

## Health Proof (Always Start Here)

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Expected:

- `18 passed, 1 warning`

## One-Click Live Demo Path

Open:

- `http://localhost:8000/live-demo`

Demo flow:

1. Submit a requirement.
2. Watch phase transitions and gate pauses.
3. Approve plan and merge gates from the UI.
4. Review final status and output summary.

## Scripted Scenario Commands

## Greenfield (mandatory use case)

```bash
PYTHONPATH=. .venv/bin/python examples/greenfield_run/run_url_shortener.py
```

Expected highlights:

- category `greenfield`
- full DAG execution
- generated artifacts under `generated_projects/url-shortener`
- validation passes for generated project

## Brownfield

```bash
PYTHONPATH=. .venv/bin/python examples/brownfield_run/run_add_auth.py
```

Expected highlights:

- category `brownfield`
- impacted-area reasoning before downstream planning
- completed run with engineering summary

## Ambiguous

```bash
PYTHONPATH=. .venv/bin/python examples/ambiguous_run/run_ambiguous.py
```

Expected highlights:

- clarify gate pause with explicit questions
- resume after approval feedback
- if provider call is blocked, run still completes with safe fallback summary

## Verified Artifact Evidence

## Greenfield

- run id: `3751c9b4-d1a6-4a0d-95b1-8f06d23b1d6d`
- status: `completed`
- tasks: `11/11`
- validations: `11/11`

## Brownfield

- run id: `4944bf07-2468-4bbc-b07c-d112a29cd79f`
- status: `completed`
- tasks: `7/7`
- validations: `7/7`

## Ambiguous (sanitized fallback)

- run id: `f64e1021-6402-4a2d-a3dd-f2bd098d1aad`
- status: `completed`
- category: `ambiguous`
- summary includes:

```text
Provider fallback used because the model provider request was blocked by quota/billing limits. Check provider credits and retry the run.
```

## 5-Minute Talk Track

1. Show tests passing.
2. Show architecture flow in `docs/architecture.md`.
3. Run ambiguous scenario to prove controlled autonomy.
4. Run mandatory URL shortener scenario to prove full SDLC orchestration.
5. Close with evidence that provider failures are handled with engineering-grade summaries.

## 10-Minute Talk Track

1. Health baseline (`pytest -q`).
2. Architecture walk-through (`graph.py`, `state.py`, `model_provider.py`).
3. Ambiguous run (clarify gate + resume).
4. Brownfield run (codebase reasoning path).
5. Greenfield run (mandatory use case + artifacts + validation).
6. API/UI flow via `/live-demo`.
7. End with run IDs and summary excerpts.

## Backup Plan

If OpenRouter is unavailable:

```env
DEMO_MODE=true
```

Restart:

```bash
docker compose up -d --build orchestrator
```

Continue demo with deterministic gate behavior and the same lifecycle narrative.
