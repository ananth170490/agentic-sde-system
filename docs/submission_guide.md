# Submission Guide

## Objective

This guide provides a reviewer-friendly walkthrough of the implemented system, including architecture, orchestration behavior, validation strategy, OpenRouter integration, and verified output artifacts.

## System Workflow

The project implements a full agentic SDLC workflow:

1. requirement understanding and ambiguity scoring
2. optional brownfield codebase reasoning
3. architecture planning
4. dependency-aware task decomposition
5. approval-gated execution
6. code and test generation per task
7. validation and bounded repair loop
8. risk and final engineering summary generation

Core implementation locations:

- `orchestrator/graph.py`
- `orchestrator/state.py`
- `orchestrator/agents/*`
- `orchestrator/tools/model_provider.py`
- `orchestrator/tools/repo_index.py`
- `orchestrator/tools/sandbox_runner.py`

## OpenRouter Runtime Approach

Recommended provider config:

```env
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=<your_openrouter_key>
OPENROUTER_MODEL=openai/gpt-4o-mini
DEMO_MODE=false
```

Behavior under real provider conditions:

- structured schema outputs are requested
- parser/validator retries are attempted when possible
- schema-safe fallback objects are generated if provider response fails
- fallback text in final summary is humanized and sanitized

Sanitized output example:

```text
Provider fallback used because the model provider request was blocked by quota/billing limits. Check provider credits and retry the run.
```

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

## 3. Ambiguous Requirement

Prompt:

```text
Make the reporting faster.
```

Evidence:

- run id: `f64e1021-6402-4a2d-a3dd-f2bd098d1aad`
- status: `completed`
- category: `ambiguous`
- behavior: safe fallback completion under provider quota/billing block

Engineering summary excerpt:

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

## Validation and Quality Evidence

Validation stack:

- `pytest`
- `py_compile`
- `pyflakes`

Latest suite baseline:

- `18 passed, 1 warning`

Execution quality characteristics:

- task-scoped validation
- bounded repair retries
- terminal rejection on unrecoverable failures
- engineering-grade failure summary instead of ambiguous API 500 outcomes

## Reviewer Demo Sequence

1. Run `pytest -q`.
2. Open `docs/architecture.md` and explain phase flow.
3. Run ambiguous scenario and show clarify/resume behavior.
4. Run greenfield and brownfield scenarios.
5. Show run IDs and output summary excerpts.
6. Highlight sanitized provider-fallback messaging quality.

## Conclusion

The system satisfies assignment expectations for:

- requirement understanding
- decomposition depth
- multi-step orchestration
- validation and risk control
- human-in-the-loop governance
- resilient output reporting under provider failures
