# Submission Package

## Executive Summary

This repository implements a stateful agentic software engineering orchestrator that converts plain-English requirements into reviewable engineering outcomes with:

- explicit lifecycle orchestration
- dependency-aware task execution
- validation and bounded repair loops
- human approval gates
- persistent run state and resumability
- engineering-grade final summaries

The implementation supports real-provider operation (OpenRouter), deterministic demo mode, and robust fallback behavior under provider-side failures.

## Objective

Provide a complete, evaluator-ready mapping of implemented capabilities, runtime behavior, and validated scenario evidence.

## Core Requirements Coverage Matrix

1. Requirement understanding
- Intent interpretation and ambiguity handling via structured intake processing.

2. Task decomposition
- Actionable dependency-aware task graph (`TaskDAG`) with execution sequencing.

3. Brownfield codebase reasoning
- Impacted services/modules/files discovered prior to downstream planning.

4. Workflow orchestration
- Multi-step, state-driven execution with approval gates, retries, and recovery behavior.

5. Engineering output generation
- Cohesive outputs including code, API/schema artifacts, tests, and supporting documentation.

6. Validation and risk control
- Validator pipeline plus risk/trade-off/failure reporting in final summaries.

7. Controlled autonomy
- Agents execute independently; humans gate clarify/plan/merge decisions.

8. Final output
- Structured engineering summary with implementation rationale, artifacts, risks, and limitations.

## System Workflow

## 1. Requirement Understanding

- implemented in `orchestrator/agents/intake.py`
- produces structured `RequirementSpec`
- captures category, explicit/implicit requirements, ambiguities, and ambiguity score

## 2. Architecture + Planning

- architecture generation: `orchestrator/agents/architect.py`
- DAG decomposition: `orchestrator/agents/task_decomposer.py`
- execution model: `TaskDAG` in `orchestrator/state.py`

## 3. Brownfield Reasoning

- brownfield impact analysis: `orchestrator/agents/codebase_reasoning.py`
- AST/import indexing: `orchestrator/tools/repo_index.py`

## 4. Code/Test/Validation Loop

- code generation: `orchestrator/agents/code_gen.py`
- test generation: `orchestrator/agents/test_gen.py`
- validation: `orchestrator/agents/validator.py`
- sandbox execution: `orchestrator/tools/sandbox_runner.py`

## 5. Governance and Resilience

- phase orchestration: `orchestrator/graph.py`
- approval gates: `orchestrator/gates/human_approval.py`
- persistence: `RunStateStore` in `orchestrator/state.py`
- provider abstraction and fallback: `orchestrator/tools/model_provider.py`

## OpenRouter Runtime Approach

Primary provider mode:

```env
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=<your_openrouter_key>
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
DEMO_MODE=false
```

Operational behavior:

- structured-response invocation with schema validation
- retry/coercion where appropriate
- safe schema fallback when provider call or parse fails
- sanitized reviewer-facing failure language

Sanitized fallback output now used in summaries:

```text
Provider fallback used because the model provider request was blocked by quota/billing limits. Check provider credits and retry the run.
```

This replaced raw upstream HTTP text in final summaries.

## Scenario Evidence (Required Coverage)

## 1. Greenfield Requirement

Prompt:

```text
Build a scalable URL shortener service with APIs, persistence, and analytics.
```

Evidence:

- run id: `3751c9b4-d1a6-4a0d-95b1-8f06d23b1d6d`
- status: `completed`
- tasks: `11/11`
- validations: `11/11`

Engineering summary excerpt:

```text
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

## 2. Brownfield Requirement

Prompt:

```text
Add JWT auth middleware and role-based access checks to the existing fixture service endpoints.
```

Evidence:

- run id: `4944bf07-2468-4bbc-b07c-d112a29cd79f`
- status: `completed`
- tasks: `7/7`
- validations: `7/7`

Engineering summary excerpt:

```text
## Generated Artifacts
- docs/authentication_and_rbac.md
- src/middleware/jwtAuth.js
- src/rbac/roleManager.js
- src/routes/fixtures.js
- tests/integration/fixtures.test.js
- tests/unit/jwtAuth.test.js
- tests/unit/roleManager.test.js
```

## 3. Ambiguous Requirement

Prompt:

```text
Make the reporting faster.
```

Evidence:

- run id: `f64e1021-6402-4a2d-a3dd-f2bd098d1aad`
- status: `completed`
- category: `ambiguous`
- output summary uses sanitized fallback wording

Engineering summary excerpt:

```text
## Implementation Plan and Rationale
Provider fallback used because the model provider request was blocked by quota/billing limits. Check provider credits and retry the run.

## Generated Artifacts
- No artifacts recorded
```

## Validation and Quality Evidence

Current test baseline:

- `18 passed, 1 warning`

Validation strategy per task:

- runtime tests with `pytest`
- syntax checks with `py_compile`
- lint-style checks with `pyflakes`

Failure handling:

- bounded repair loop per task
- terminal `rejected` state on unrecoverable execution
- final engineering summary preserved for auditability

## Deliverables Coverage Matrix

1. Working prototype
- API + orchestration graph + runnable examples for requirement-to-output transformation.

2. Architecture overview
- Detailed architecture, flow, and design rationale in `docs/architecture.md`.

3. Example scenarios
- Greenfield, brownfield, ambiguous coverage with artifacts and summary excerpts.

4. Setup instructions
- Run/evaluation setup in `README.md` and `docs/live_demo_checklist.md`.

5. Testing approach
- Demonstrated by test suite and task-level validation strategy documented above.

## Reviewer Demo Sequence

- one-click UI: `http://localhost:8000/live-demo`
- API docs: `http://localhost:8000/docs`
- full walkthrough script: `docs/live_demo_checklist.md`

Recommended sequence:

1. Run `pytest -q`.
2. Open `docs/architecture.md` and explain phase routing.
3. Run ambiguous, brownfield, and greenfield demos.
4. Present run IDs and engineering summary excerpts.
5. Highlight sanitized provider fallback behavior.

## Final Positioning

This submission demonstrates not only code generation, but disciplined engineering orchestration:

- structured interpretation of requirements
- decomposition and dependency execution
- validation-driven quality control
- human governance gates
- resilient and reviewer-safe behavior under provider faults

Expectation alignment:

- production-grade system design fundamentals
- multi-step lifecycle orchestration ownership
- explicit output-quality and validation accountability
- clear and defensible technical reasoning
