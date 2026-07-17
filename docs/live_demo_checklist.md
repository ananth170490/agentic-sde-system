# Live Demo Checklist

This document gives a precise, terminal-by-terminal live demo plan for either a 5-minute presentation or a 10-minute presentation.

Assumptions:

- current directory is the repository root
- virtual environment already exists at `.venv`
- dependencies are already installed
- you want a reliable demo that emphasizes what has already been validated in this repository

Repository root:

```bash
cd "/Users/ananth/Desktop/Terraform/Assignment - Agentic software engineer/agentic-sde-system"
```

## Demo Strategy

For live presentations, use the deterministic scripted provider for the mandatory URL shortener flow when you need guaranteed reliability.

Why:

- automated tests pass consistently
- the ambiguous flow completes successfully
- the brownfield flow completes successfully
- the mandatory URL shortener flow can be run deterministically with `MODEL_PROVIDER=scripted`

Use the mandatory use case as the centerpiece with the scripted provider, and optionally discuss real-model trade-offs separately.

## 5-Minute Demo

### Goal

Show the interviewer that the system is real, tested, multi-step, and supports ambiguity handling plus brownfield reasoning.

### Terminal Layout

- Terminal 1: commands and examples
- Editor: open architecture and graph files for quick visual references

### Step 1: Prove the repo is healthy

Terminal 1:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

What to say:

- "This validates the orchestration logic, API flow, DAG behavior, guardrails, and summary generation."
- "The current suite passes with 12 tests."

Expected result:

- `12 passed, 1 warning`

### Step 2: Show the architecture in the editor

Open these files in the editor:

- [docs/architecture.md](../docs/architecture.md)
- [orchestrator/graph.py](../orchestrator/graph.py)
- [orchestrator/state.py](../orchestrator/state.py)

What to say:

- "The system is implemented as a LangGraph workflow, not a single prompt."
- "Each run is persisted in SQLite through RunStateStore and routed by current phase."
- "Human checkpoints are modeled explicitly through clarify, plan approval, and merge approval gates."

### Step 3: Run the ambiguous scenario

Terminal 1:

```bash
PYTHONPATH=. .venv/bin/python examples/ambiguous_run/run_ambiguous.py
```

What to say while it runs:

- "This proves controlled autonomy."
- "The system detects ambiguity, pauses, asks clarifying questions, and only resumes after human feedback."

Call out these observed outputs:

- paused at `clarify_gate`
- review payload includes explicit clarifying questions
- later pauses at plan review and merge review
- final status is completed

### Step 4: Run the mandatory use case directly

Terminal 1:

```bash
MODEL_PROVIDER=scripted PYTHONPATH=. .venv/bin/python examples/greenfield_run/run_url_shortener.py
```

Open this file in the editor:

- [examples/greenfield_run/run_url_shortener.py](../examples/greenfield_run/run_url_shortener.py)

What to say:

- "This is the mandatory URL shortener entry point."
- "It goes through intake, architecture, task decomposition, approvals, generation, validation, and summary."
- "For live reliability, I am using the scripted provider path that still exercises the full orchestration and validation lifecycle."

### 5-Minute Demo Exit Line

Use this closing sentence:

- "The important result is that the orchestration, validation, approval, and recovery model are fully implemented and verified; the remaining runtime constraint is the capability of the local model used for the mandatory greenfield path."

## 10-Minute Demo

### Goal

Show the full breadth of the system: tests, architecture, ambiguous handling, brownfield reasoning, and API-driven control flow.

### Terminal Layout

- Terminal 1: test runs and example scripts
- Terminal 2: API server
- Terminal 3: API requests with `curl`
- Editor: code walkthrough and architecture diagram

### Step 1: Start with health check

Terminal 1:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

What to say:

- "This gives us a verified baseline before I show interactive flows."
- "The tests cover agents, API behavior, graph transitions, DAG logic, repo reasoning, and sandbox behavior."

Expected result:

- `12 passed, 1 warning`

### Step 2: Show architecture and state model

Open these files in the editor:

- [docs/architecture.md](../docs/architecture.md)
- [orchestrator/graph.py](../orchestrator/graph.py)
- [orchestrator/state.py](../orchestrator/state.py)
- [orchestrator/gates/human_approval.py](../orchestrator/gates/human_approval.py)

What to say:

- "The graph routes by phase and supports pause/resume."
- "RunState is the shared execution memory for requirement, design, tasks, validations, and approvals."
- "This is how the system demonstrates controlled autonomy instead of unbounded generation."

### Step 3: Run the ambiguous scenario

Terminal 1:

```bash
PYTHONPATH=. .venv/bin/python examples/ambiguous_run/run_ambiguous.py
```

What to say:

- "This requirement is intentionally vague, so the system should stop and ask questions before building anything."
- "That is one of the main assignment asks: it must handle ambiguous requirements safely."

Expected highlights:

- clarify gate payload appears
- human feedback is applied
- plan review and merge review are shown
- final state becomes completed

### Step 4: Run the brownfield scenario

Terminal 1:

```bash
PYTHONPATH=. .venv/bin/python examples/brownfield_run/run_add_auth.py
```

What to say:

- "This proves the brownfield path is different from greenfield."
- "The system first reasons about the current codebase and identifies likely impacted files before proposing execution."

Expected highlights:

- requirement category is brownfield
- impacted areas are printed
- `app.py` is identified as impacted

### Step 5: Start the API

Terminal 2:

```bash
uvicorn orchestrator.api.main:app --reload
```

What to say:

- "The same orchestration is available as an API, which makes the prototype externally controllable and easier to evaluate."

### Step 6: Submit a requirement through the API

Terminal 3:

```bash
curl -s -X POST http://127.0.0.1:8000/requirements \
  -H "Content-Type: application/json" \
  -d '{"text":"Make the reporting faster"}'
```

What to say:

- "This creates a run and immediately starts orchestration."
- "If the system determines the requirement is ambiguous, it returns a review payload instead of pretending it understands enough to continue."

Expected result:

- JSON response with `run_id`
- `status` likely `awaiting_human`
- `review_payload` present

### Step 7: Inspect the paused run

Replace `<RUN_ID>` with the actual value returned from the previous step.

Terminal 3:

```bash
curl -s http://127.0.0.1:8000/runs/<RUN_ID>
```

What to say:

- "This exposes the persisted run state, including phase, requirement structure, and review metadata."

### Step 8: Approve and resume

Terminal 3:

```bash
curl -s -X POST http://127.0.0.1:8000/runs/<RUN_ID>/approve \
  -H "Content-Type: application/json" \
  -d '{"feedback":"Optimize p95 latency for /reports to under 300ms"}'
```

What to say:

- "A human can resume the workflow with explicit feedback, which is the controlled-autonomy mechanism."

Expected result:

- updated JSON response
- either another review payload or a running/completed status depending on stage

### Step 9: Show the mandatory use case honestly

Open these files in the editor:

- [examples/greenfield_run/run_url_shortener.py](../examples/greenfield_run/run_url_shortener.py)
- [orchestrator/agents/architect.py](../orchestrator/agents/architect.py)
- [orchestrator/agents/task_decomposer.py](../orchestrator/agents/task_decomposer.py)

What to say:

- "This is the exact mandatory use case flow."
- "The implementation supports the required stages: requirement analysis, architecture, decomposition, code generation, tests, validation, trade-offs, and final summary."
- "For guaranteed live reliability, I use `MODEL_PROVIDER=scripted`, and I can discuss Anthropic/Ollama trade-offs separately."

### 10-Minute Demo Exit Line

Use this closing sentence:

- "What I want you to take away is that the prototype already demonstrates the engineering workflow the assignment asks for: structured requirement handling, dependency-aware planning, guarded generation, validation, human oversight, and resumable orchestration."

## Backup Plan If Time Is Tight

If you are running out of time, use this shortened sequence:

### Backup 3-Minute Sequence

Terminal 1:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python examples/ambiguous_run/run_ambiguous.py
```

Talk track:

- show tests passing
- show ambiguity gating and approval flow
- point to [examples/greenfield_run/run_url_shortener.py](../examples/greenfield_run/run_url_shortener.py) for the mandatory use case implementation
- mention the deterministic scripted path for guaranteed live execution

## Commands Summary

### Health Check

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

### Ambiguous Flow

```bash
PYTHONPATH=. .venv/bin/python examples/ambiguous_run/run_ambiguous.py
```

### Brownfield Flow

```bash
PYTHONPATH=. .venv/bin/python examples/brownfield_run/run_add_auth.py
```

### Start API

```bash
uvicorn orchestrator.api.main:app --reload
```

### Submit Requirement

```bash
curl -s -X POST http://127.0.0.1:8000/requirements \
  -H "Content-Type: application/json" \
  -d '{"text":"Make the reporting faster"}'
```

### Inspect Run

```bash
curl -s http://127.0.0.1:8000/runs/<RUN_ID>
```

### Approve Run

```bash
curl -s -X POST http://127.0.0.1:8000/runs/<RUN_ID>/approve \
  -H "Content-Type: application/json" \
  -d '{"feedback":"approved"}'
```
