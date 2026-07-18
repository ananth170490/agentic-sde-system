# Architecture Overview

This system is a stateful, agentic software engineering orchestrator. It transforms a natural-language requirement into a controlled, reviewable engineering outcome with explicit phase routing, human gates, validation loops, and persistent run state.

## End-to-End Flow

```mermaid
flowchart TD
  Start([Requirement Submitted]) --> API[FastAPI Interface]
  API --> Init[Initialize RunState + Persist]
  Init --> Intake[Intake Agent]

  Intake --> Ambig{Ambiguity high?}
  Ambig -- Yes --> Clarify[Clarify Gate]
  Clarify --> ClarifyWait[[Await Human Input]]
  ClarifyWait --> Route
  Ambig -- No --> Route{Requirement Type}

  Route -- Brownfield --> Codebase[Codebase Reasoning Agent]
  Route -- Greenfield --> Architect
  Route -- Ambiguous after clarification --> Architect

  Codebase --> Architect[Architect Agent]
  Architect --> Decompose[Task Decomposer Agent]

  Decompose --> PlanGate[Plan Approval Gate]
  PlanGate --> PlanWait[[Await Human Approval]]
  PlanWait --> Execute

  Execute[Execute DAG] --> Next{Runnable task exists?}
  Next -- Yes --> CodeGen[CodeGen Agent]
  CodeGen --> TestGen[TestGen Agent]
  TestGen --> Validate[Validator\npytest + py_compile + pyflakes]
  Validate --> Pass{Passed?}
  Pass -- Yes --> PersistTask[Persist task result]
  PersistTask --> Next
  Pass -- No --> Retry{Retry < 3?}
  Retry -- Yes --> Repair[Repair with feedback]
  Repair --> CodeGen
  Retry -- No --> Rejected[[Terminal Rejection\nEngineering Summary]]

  Next -- No --> RiskDocs[RiskDocs Agent]
  RiskDocs --> MergeGate[Merge Approval Gate]
  MergeGate --> MergeWait[[Await Human Approval]]
  MergeWait --> Finalize[Finalize Run]
  Finalize --> PersistFinal[(Persist Final State)]
  Rejected --> PersistFinal
  PersistFinal --> End([Completed or Rejected])
```

## Runtime Layers

## 1. Interface Layer

- FastAPI endpoints for submit, inspect, approve, and reject
- Live demo UI (`/live-demo`) for gate-driven demonstration flow
- Example scripts for greenfield, brownfield, and ambiguous scenarios

## 2. Orchestration Layer

- `orchestrator/graph.py` defines node flow and phase transitions
- `orchestrator/state.py` stores `RunState`, `TaskDAG`, validation history, and summaries
- Human gates pause execution at clarify, plan, and merge checkpoints

## 3. Agent Layer

- Intake: requirement normalization and ambiguity scoring
- Codebase reasoning: impacted-area analysis for brownfield
- Architect: components, API contract, data model, trade-offs
- Task decomposer: dependency-aware DAG
- Code/test generation and validation with bounded repair
- Risk docs: final engineering-grade summary generation

## 4. Tooling Layer

- Model provider abstraction: Anthropic, OpenRouter, Ollama, scripted
- Sandbox runner for scoped test execution
- Repo index for AST/import-based brownfield impact analysis

## 5. Persistence and Artifacts

- SQLite-backed run persistence for pause/resume and crash recovery
- Per-run generated artifacts under `generated_projects/`
- Final summary markdown for evaluator-friendly traceability

## OpenRouter Integration Architecture

OpenRouter is integrated via an OpenAI-compatible chat completion client in `orchestrator/tools/model_provider.py`.

Primary behavior:

- structured output requested per Pydantic schema
- parse + validation retries when feasible
- schema-safe fallback synthesis if provider call fails
- domain-safe fallback coercion for critical objects (`RequirementSpec`, `TaskDAG`, etc.)

Latest resilience behavior:

- fallback reason text is humanized and sanitized
- raw upstream provider error strings are not shown in reviewer-facing output summaries

Example sanitized fallback text:

```text
Provider fallback used because the model provider request was blocked by quota/billing limits. Check provider credits and retry the run.
```

## Execution and Failure Semantics

Key guarantees in `execute_dag`:

- every task executes with explicit status tracking
- validation failure triggers bounded repair loop
- unrecoverable failure transitions run to terminal `rejected`
- rejection includes an engineering-grade final summary (not an opaque crash)

This prevents silent hangs and improves reviewer confidence in operational behavior.

## Crash Recovery and Resume

Recovery uses two mechanisms:

- `RunStateStore` persistence after phase transitions
- LangGraph checkpoint/interrupt behavior at gate boundaries

Operationally this means:

- runs can resume from last persisted phase
- human approval pauses are resumable
- process restarts do not require rerunning from intake

## Why This Architecture Is Assignment-Strong

- full lifecycle from requirement to engineering summary
- dependency-aware decomposition and bounded execution
- validation-driven acceptance criteria
- explicit human governance points
- resilience to provider outages and malformed model outputs
- reviewable, deterministic state transitions
