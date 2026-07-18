# Beginner-Friendly Knowledge Transfer Guide

## Objective

Provide a clear, reviewer-friendly explanation of how this system works end-to-end and why the output quality is engineering-grade.

## What This System Is

This project is an engineering workflow orchestrator. It does not just generate code from one prompt. It performs a full, stateful delivery lifecycle with approvals, validation, retries, and final reporting.

## System Workflow

For any incoming requirement, it:

1. structures requirement intent
2. detects ambiguity and pauses for clarification
3. performs brownfield reasoning when needed
4. designs architecture and APIs
5. decomposes work into a dependency-aware task DAG
6. generates code and tests per task
7. validates outputs with runtime and static checks
8. retries failed tasks with repair feedback (bounded)
9. pauses for merge approval
10. emits engineering-grade final summary

## Why This Matters

A simple code-generation prompt can produce output, but it cannot reliably:

- coordinate multi-step dependencies
- guarantee validation before acceptance
- preserve human checkpoints
- recover cleanly from provider or generation failures

This system handles those concerns explicitly.

## Core Concepts

## 1. RunState (Single Source of Truth)

`RunState` in `orchestrator/state.py` stores requirement, architecture, tasks, validation results, review payloads, final summary, and phase status.

Why this is important:

- every phase reads/writes one shared state model
- phase transitions are traceable
- pause/resume is reliable

## 2. Human Approval Gates

The graph pauses at:

- clarify gate
- plan approval gate
- merge approval gate

This creates controlled autonomy, not blind automation.

## 3. Validation-Driven Execution

Each task executes with:

- generated code
- generated tests
- validator checks (`pytest`, `py_compile`, `pyflakes`)

Failures trigger repair loops up to a bounded retry limit.

## 4. Provider Resilience

OpenRouter and other providers can fail due to quota, billing, network, or schema mismatch. The system now uses schema-safe fallbacks so runs remain coherent and summaries stay reviewer-friendly.

Sanitized example:

```text
Provider fallback used because the model provider request was blocked by quota/billing limits. Check provider credits and retry the run.
```

## OpenRouter Runtime Approach

`.env` example:

```env
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=<your_openrouter_key>
OPENROUTER_MODEL=openai/gpt-4o-mini
DEMO_MODE=false
```

Start runtime:

```bash
docker compose up -d --build orchestrator
```

Open:

- `http://localhost:8000/docs`
- `http://localhost:8000/live-demo`

## Scenario Evidence (Required Coverage)

## 1. Greenfield Requirement

- run script: `examples/greenfield_run/run_url_shortener.py`
- run id: `3751c9b4-d1a6-4a0d-95b1-8f06d23b1d6d`
- result: completed, 11/11 tasks validated

## 2. Brownfield Requirement

- run script: `examples/brownfield_run/run_add_auth.py`
- run id: `4944bf07-2468-4bbc-b07c-d112a29cd79f`
- result: completed, 7/7 tasks validated

## 3. Ambiguous Requirement

- run script: `examples/ambiguous_run/run_ambiguous.py`
- run id: `f64e1021-6402-4a2d-a3dd-f2bd098d1aad`
- result: completed via safe fallback, no raw provider HTTP string in summary

## Reviewer Demo Sequence

Use this short narrative:

1. The orchestrator classifies and structures the requirement.
2. It pauses at explicit human gates when confidence/control is needed.
3. It executes a dependency-aware task graph with validation and bounded repair.
4. It persists every phase for resumability.
5. It always ends with an engineering-grade summary, including controlled fallback semantics.

## Conclusion

The implementation demonstrates controlled autonomy, deterministic orchestration phases, task-level validation, and resilient completion behavior even when external providers fail.

## Useful File Map

- `orchestrator/graph.py`: phase routing and execution semantics
- `orchestrator/state.py`: typed state + persistence model
- `orchestrator/tools/model_provider.py`: provider integration + fallback synthesis
- `orchestrator/agents/validator.py`: validation pipeline
- `docs/architecture.md`: architecture and flow diagram
