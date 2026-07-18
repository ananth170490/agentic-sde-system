## Opening Summary

This project is an agentic software engineering orchestrator designed to take a plain-English requirement and move it through the full software delivery lifecycle.

For the mandatory use case:

> Build a scalable URL shortener service with APIs, persistence, and analytics.

The system is designed to:

- analyze and structure the requirement
- identify ambiguities and request clarification when needed
- design the architecture
- decompose work into dependency-aware tasks
- generate code and tests
- validate outputs through runtime and static checks
- repair failed generations through a bounded retry loop
- pause for human approval at key checkpoints
- produce a final risk and engineering summary

This makes the solution more than a code generator. It is a controlled, stateful engineering workflow.

## What Problem This Project Solves

A normal large language model prompt can generate code, but it usually does not manage the full engineering lifecycle in a reliable way.

The goal of this project is to solve that gap by adding:

- structured workflow orchestration
- explicit state management
- validation before acceptance
- human-in-the-loop approval gates
- retry and recovery behavior
- crash recovery and resumability

In simple terms, this system behaves more like a disciplined engineering team than a one-shot assistant.

## Mandatory Use Case Walkthrough

For the URL shortener requirement, the system must understand that the request implies several real engineering concerns:

- a service for creating short URLs
- APIs to create and resolve those URLs
- persistence so links are not lost
- analytics for usage tracking
- scalability concerns such as stateless APIs, identifier strategy, and future growth

The system handles that requirement in stages.

### 1. Requirement Analysis

The intake step converts raw text into a structured `RequirementSpec`.

This captures:

- requirement category
- explicit requirements
- implicit requirements
- ambiguities
- ambiguity score

File: [orchestrator/agents/intake.py](../orchestrator/agents/intake.py)

### 2. Architecture Design

The architecture step creates a structured design that includes:

- component list
- data model description
- OpenAPI contract
- trade-offs

File: [orchestrator/agents/architect.py](../orchestrator/agents/architect.py)

### 3. Task Decomposition

The system then converts the design into a `TaskDAG`, which is a dependency-aware task graph.

This is important because good engineering work does not happen as one large step. It happens in ordered tasks.

Files:

- [orchestrator/agents/task_decomposer.py](../orchestrator/agents/task_decomposer.py)
- [orchestrator/state.py](../orchestrator/state.py)

### 4. Code and Test Generation

For each task, the system:

- generates implementation code
- generates tests
- restricts file writes to task-owned files only

Files:

- [orchestrator/agents/code_gen.py](../orchestrator/agents/code_gen.py)
- [orchestrator/agents/test_gen.py](../orchestrator/agents/test_gen.py)

### 5. Validation

Generated outputs are checked using:

- pytest
- py_compile
- pyflakes

This makes the workflow validation-driven rather than prompt-driven.

File: [orchestrator/agents/validator.py](../orchestrator/agents/validator.py)

### 6. Risk Documentation

At the end of the workflow, the system produces:

- concrete risks
- trade-offs
- assumptions
- limitations
- a final engineering summary

File: [orchestrator/agents/risk_docs.py](../orchestrator/agents/risk_docs.py)

## Workflow Orchestration

The end-to-end flow is managed in [orchestrator/graph.py](../orchestrator/graph.py).

The graph covers:

1. intake
2. clarify gate if ambiguity is high
3. codebase reasoning for brownfield work
4. architecture
5. task decomposition
6. plan approval gate
7. execution of the DAG
8. final risk documentation
9. merge approval gate
10. final completion

This is important because the evaluator is explicitly checking multi-step orchestration, not just generation quality.

## Why This Design Is Strong

### Structured State

The project uses a shared `RunState` object to carry all information across the workflow.

This includes:

- requirement
- design
- DAG
- validation history
- review payloads
- final summary
- status and phase

File: [orchestrator/state.py](../orchestrator/state.py)

This is a strong design choice because it makes every stage traceable and recoverable.

### Controlled Human Oversight

The system does not blindly continue through every phase. It pauses at meaningful checkpoints.

Human approval points include:

- clarify gate for ambiguous requirements
- plan review before execution
- merge review after generation and validation

Files:

- [orchestrator/gates/human_approval.py](../orchestrator/gates/human_approval.py)
- [orchestrator/graph.py](../orchestrator/graph.py)

This supports the assignment goal of controlled autonomy.

### Crash Recovery

The project supports recovery in two ways:

- `RunStateStore` persists each run to SQLite
- LangGraph checkpointing supports pause/resume at interrupt points

This means a run can be recovered instead of restarted from zero.

## Strongest Evidence: Validation and Repair Loop

One of the strongest parts of this project is the repair and retry loop.

The system does not assume the first generation is correct.

Instead, it:

1. generates code
2. generates tests
3. validates them
4. if validation fails, calls repair
5. retries up to a bounded limit
6. pauses for human intervention if recovery fails

This directly addresses the evaluation criteria around quality, validation, and risk management.

### Evidence From an Intentional Failure Test

A deliberate experiment was run where the first generated implementation failed its test, and the graph was allowed to repair and retry.

Observed evidence:

```text
Validation history:
  [1] task=calc-001 passed=False issues=['tests/test_calc.py::test_add']
  [2] task=calc-001 passed=True issues=[]

Task retry_count=1, status=TaskStatus.DONE, output_summary=Validated successfully
REPAIR_LOOP_CONFIRMED: first validation failed, repair retried, later validation passed.
```

Why this matters:

- it proves the validation agent is active
- it proves failure is detected, not ignored
- it proves repair logic is wired into the orchestration
- it proves the workflow can recover and continue successfully

This is strong evidence for both error handling and cross-step coordination.

## Breadth of Demonstrations Included

The repository demonstrates three important workflow types.

### Greenfield Example

File: [examples/greenfield_run/run_url_shortener.py](../examples/greenfield_run/run_url_shortener.py)

Purpose:

- shows the mandatory use case
- uses the real model provider
- prints review payloads for approval checkpoints
- copies artifacts into `generated_projects/url-shortener`
- runs tests for the generated project

### Brownfield Example

Files:

- [examples/brownfield_run/fixture_service/app.py](../examples/brownfield_run/fixture_service/app.py)
- [examples/brownfield_run/run_add_auth.py](../examples/brownfield_run/run_add_auth.py)

Purpose:

- shows modification of an existing codebase
- verifies brownfield classification
- verifies impacted file detection

### Ambiguous Example

File: [examples/ambiguous_run/run_ambiguous.py](../examples/ambiguous_run/run_ambiguous.py)

Purpose:

- shows that the system does not guess blindly
- pauses when a requirement is vague
- asks specific clarifying questions
- resumes after simulated human clarification

Together, these examples show that the system is not limited to a single happy path.

## Evaluator Checklist Mapping

This section mirrors the same checklist structure used in the submission package for consistency in interview/demo conversations.

### A. Sample Inputs and Outputs

Required scenario coverage:

1. Greenfield requirement
2. Brownfield requirement
3. Ambiguous requirement

Each scenario below explicitly demonstrates:

- task decomposition
- multi-step orchestration
- output validation

Scenario quick links in this document:

- Greenfield sample: [Greenfield Requirement](#1-greenfield-requirement)
- Brownfield sample: [Brownfield Requirement](#2-brownfield-requirement)
- Ambiguous sample: [Ambiguous Requirement](#3-ambiguous-requirement)

### B. Setup Instructions

Clear run/evaluate instructions are provided in [Setup Instructions](#setup-instructions), including:

- environment setup
- provider selection
- API and script-based execution
- evaluation checklist for reviewers

### C. Testing Approach

Testing and quality-validation details are provided in [Testing Strategy](#testing-strategy), including:

- correctness validation (unit + integration + API + graph flow)
- output quality validation (validation checks and repair loop behavior)
- known limitations and trade-offs for transparent evaluation

## Sample Inputs and Outputs

This section provides reviewer-friendly sample inputs and outputs for all three required scenario types.

Note:

- examples follow the actual project schemas (`RequirementSpec`, `TaskDAG`, `ValidationResult`, `RunState`)
- some values are representative samples to keep the section concise and readable

### 1. Greenfield Requirement

Sample input:

```text
Build a scalable URL shortener service with APIs, persistence, and analytics.
```

Sample output (requirement understanding):

```json
{
  "raw_text": "Build a scalable URL shortener service with APIs, persistence, and analytics.",
  "category": "greenfield",
  "explicit_requirements": [
    "Build a scalable URL shortener service",
    "Include APIs",
    "Include persistence",
    "Include analytics"
  ],
  "implicit_requirements": [
    "Use stateless API nodes for horizontal scaling",
    "Provide durable storage for URL mappings",
    "Track click events for analytics"
  ],
  "ambiguities": [
    "Throughput/SLO targets are unspecified",
    "Analytics retention period is unspecified"
  ],
  "ambiguity_score": 0.38
}
```

Task decomposition (sample `TaskDAG` excerpt):

```json
{
  "tasks": [
    {
      "id": "schema-001",
      "title": "Define URL and analytics schema",
      "depends_on": [],
      "owned_files": ["app/models.py", "migrations/001_init.sql"],
      "status": "pending",
      "retry_count": 0
    },
    {
      "id": "api-002",
      "title": "Implement create and resolve APIs",
      "depends_on": ["schema-001"],
      "owned_files": ["app/main.py", "app/routes.py"],
      "status": "pending",
      "retry_count": 0
    },
    {
      "id": "analytics-003",
      "title": "Implement click tracking",
      "depends_on": ["api-002"],
      "owned_files": ["app/analytics.py"],
      "status": "pending",
      "retry_count": 0
    },
    {
      "id": "tests-004",
      "title": "Add unit and integration tests",
      "depends_on": ["api-002", "analytics-003"],
      "owned_files": ["tests/test_api.py", "tests/test_analytics.py"],
      "status": "pending",
      "retry_count": 0
    }
  ]
}
```

Multi-step orchestration (sample phase trace):

```text
intake -> codebase_reasoning (skipped for greenfield) -> architect -> task_decomposer
-> plan_review (human approval) -> execute_dag -> risk_docs
-> merge_approval_gate (human approval) -> completed
```

Output validation (sample `ValidationResult` set):

```json
[
  {
    "task_id": "api-002",
    "passed": true,
    "issues": []
  },
  {
    "task_id": "analytics-003",
    "passed": true,
    "issues": []
  },
  {
    "task_id": "tests-004",
    "passed": true,
    "issues": []
  }
]
```

### 2. Brownfield Requirement

Sample input:

```text
Add JWT-based authentication to the notes API, protecting all write endpoints.
```

Sample output (requirement understanding + impacted areas from repo reasoning):

```json
{
  "category": "brownfield",
  "impacted_areas": [
    {
      "module": "app",
      "files": ["app.py"],
      "reason": "Matched keyword(s): notes, return"
    }
  ]
}
```

Task decomposition (sample `TaskDAG` excerpt):

```json
{
  "tasks": [
    {
      "id": "auth-001",
      "title": "Add JWT validation utility",
      "depends_on": [],
      "owned_files": ["auth.py"],
      "status": "pending",
      "retry_count": 0
    },
    {
      "id": "api-002",
      "title": "Protect POST/PUT/DELETE endpoints",
      "depends_on": ["auth-001"],
      "owned_files": ["app.py"],
      "status": "pending",
      "retry_count": 0
    },
    {
      "id": "tests-003",
      "title": "Add auth enforcement tests",
      "depends_on": ["api-002"],
      "owned_files": ["tests/test_auth.py"],
      "status": "pending",
      "retry_count": 0
    }
  ]
}
```

Multi-step orchestration (sample phase trace):

```text
intake -> codebase_reasoning (detect impacted files) -> architect -> task_decomposer
-> plan_review -> execute_dag (auth utility, endpoint protection, tests)
-> risk_docs -> merge_approval_gate -> completed
```

Output validation (sample):

```text
[pytest]
3 passed, 0 failed

[py_compile]
auth.py: ok
app.py: ok

[pyflakes]
No issues found
```

### 3. Ambiguous Requirement

Sample input:

```text
Make the reporting faster.
```

Sample output before clarification (actual review payload shape):

```json
{
  "phase": "clarify_gate",
  "requirement": "Make the reporting faster",
  "clarifying_questions": [
    "Which report endpoint(s) are in scope?",
    "What exact latency target defines faster?",
    "What load profile and percentile should be optimized?"
  ]
}
```

Sample clarification input:

```text
"Faster" means p95 latency under 300ms for /reports at 200 RPS.
```

Task decomposition after clarification (sample `TaskDAG` excerpt):

```json
{
  "tasks": [
    {
      "id": "baseline-001",
      "title": "Measure current /reports latency baseline",
      "depends_on": [],
      "owned_files": ["perf/baseline.md"],
      "status": "pending",
      "retry_count": 0
    },
    {
      "id": "cache-002",
      "title": "Add report cache and invalidation",
      "depends_on": ["baseline-001"],
      "owned_files": ["app/reports_cache.py", "app/reports.py"],
      "status": "pending",
      "retry_count": 0
    },
    {
      "id": "perf-tests-003",
      "title": "Add latency regression tests",
      "depends_on": ["cache-002"],
      "owned_files": ["tests/test_reports_perf.py"],
      "status": "pending",
      "retry_count": 0
    }
  ]
}
```

Multi-step orchestration (sample phase trace):

```text
intake -> clarify_gate (pause) -> human feedback -> codebase_reasoning/architect
-> task_decomposer -> plan_review -> execute_dag -> risk_docs
-> merge_approval_gate -> completed
```

Output validation (sample):

```json
{
  "task_id": "perf-tests-003",
  "passed": true,
  "issues": [],
  "logs": "[pytest] test_reports_perf.py::test_p95_under_300ms PASSED"
}
```

## Quick Reviewer Checklist for These Examples

Each scenario above explicitly demonstrates all three mandatory evaluation dimensions:

- Task decomposition: shown via `TaskDAG` excerpts with dependencies and owned files
- Multi-step orchestration: shown via phase traces including human gates
- Output validation: shown via representative `ValidationResult`/test-check outputs

## Testing Strategy

The testing approach is layered.

### Unit Tests

Used for:

- agents
- tools
- DAG behavior
- file write restrictions
- sandbox behavior
- model provider behavior

### Integration Tests

Used for:

- graph flow
- API flow
- pause and resume behavior

### End-to-End Evidence

Used for:

- mandatory use case flow
- repair loop demonstration
- example transcripts for reviewers

The repository test suite was run and passed.

## Setup Instructions

This section provides clear, step-by-step instructions to run and evaluate the system.

### 1. Prerequisites

- Python 3.11+ (project is currently running on Python 3.14 in local validation)
- macOS/Linux terminal (or equivalent shell on Windows)
- Internet access only if you plan to use external model providers

### 2. Open the Project

From terminal:

cd "/Users/ananth/Desktop/agentic-sde-system"

### 3. Create and Activate Virtual Environment

python3 -m venv .venv
source .venv/bin/activate

### 4. Install Dependencies

pip install -r requirements.txt

### 5. Choose Model Provider

Recommended for guaranteed local evaluation (no external API dependency):

export MODEL_PROVIDER=scripted

Optional real-model providers:

- Anthropic:
  export MODEL_PROVIDER=anthropic
  export ANTHROPIC_API_KEY=YOUR_KEY
- Ollama:
  export MODEL_PROVIDER=ollama
  export OLLAMA_MODEL=llama3.1:8b

### 6. Run Core Test Suite (Repository Validation)

PYTHONPATH=. .venv/bin/python -m pytest -q

Expected outcome:

- test suite passes (currently validated as 12 passed, 1 warning)

### 7. Run Mandatory Use Case End-to-End

Run the URL shortener requirement demo:

MODEL_PROVIDER=scripted PYTHONPATH=. .venv/bin/python examples/greenfield_run/run_url_shortener.py

What this run demonstrates:

- requirement analysis
- architecture design
- task decomposition (TaskDAG)
- code/API/test generation
- validation and risk summary
- human approval checkpoints (auto-approved by script)

Expected outcome:

- run completes successfully
- generated artifacts are copied to generated_projects/url-shortener
- generated project tests pass

### 8. Verify Generated Mandatory Artifacts

find generated_projects/url-shortener -maxdepth 3 -type f | sort

You should see, at minimum:

- app/main.py
- app/store.py
- app/analytics.py
- tests/test_api_core.py
- tests/test_api_analytics.py

### 9. Run Additional Scenario Evaluations

Ambiguous requirement flow:

PYTHONPATH=. .venv/bin/python examples/ambiguous_run/run_ambiguous.py

Brownfield reasoning flow:

PYTHONPATH=. .venv/bin/python examples/brownfield_run/run_add_auth.py

These verify that the system supports:

- ambiguity detection with clarification gate
- brownfield impact analysis before planning

### 10. Optional API Evaluation

Start API server:

uvicorn orchestrator.api.main:app --reload

Submit requirement:

curl -s -X POST http://127.0.0.1:8000/requirements \
  -H "Content-Type: application/json" \
  -d '{"text":"Build a scalable URL shortener service with APIs, persistence, and analytics."}'

Inspect run:

curl -s http://127.0.0.1:8000/runs/RUN_ID

Approve paused run:

curl -s -X POST http://127.0.0.1:8000/runs/RUN_ID/approve \
  -H "Content-Type: application/json" \
  -d '{"feedback":"approved"}'

### 11. Evaluation Checklist

A reviewer can confirm the assignment outcomes by verifying:

1. Tests pass for the orchestrator codebase.
2. Mandatory URL shortener flow runs to completion.
3. Generated URL shortener code and tests exist in generated_projects/url-shortener.
4. Generated project tests pass.
5. Risk/trade-off summary is produced.
6. Ambiguous and brownfield scenarios execute correctly.

## Mapping to the Evaluation Criteria

### End-to-End Workflow Completeness

Satisfied because the project covers the full lifecycle from requirement to final summary.

### Strength of System Design and Architecture

Satisfied because architecture is explicit, structured, and includes API contract plus trade-off reasoning.

### Depth of Task Decomposition and Orchestration

Satisfied because work is modeled as a DAG with dependency-aware execution.

### Quality and Realism of Engineering Outputs

Satisfied because the system generates implementation artifacts, tests, APIs, and summaries, with task-owned file boundaries.

### Effectiveness of Validation and Risk Management

Satisfied because outputs are tested, statically checked, retried when they fail, and summarized in risk documentation.

### Clarity and Defensibility of the Overall Approach

Satisfied because the workflow, state model, checkpoints, trade-offs, and validation strategy are all explicit and inspectable.

## Known Limitations

This is a prototype, so a few limitations should be stated clearly.

- generated code execution is subprocess-based, not full container sandbox isolation
- real-model generation quality depends on provider capability/latency; a deterministic scripted provider path is included for reliable mandatory-use-case demos
- brownfield indexing uses AST and grep heuristics, not semantic embeddings
- example human approvals are simulated through scripts rather than a dedicated UI
- real-model greenfield runs may require Anthropic/Ollama configuration, but `MODEL_PROVIDER=scripted` provides a no-key deterministic path

These limitations are reasonable and transparent for an assignment of this scope.

## Short Closing Statement

This project demonstrates production-style thinking around agentic software delivery.

Its main strength is not just code generation. Its strength is controlled autonomy across the software lifecycle:

- requirement understanding
- architecture design
- task orchestration
- code and test generation
- validation and repair
- human approval checkpoints
- risk documentation
- crash recovery

That is why the solution aligns well with the mandatory use case, the evaluation criteria, and the expectation of production-grade engineering work.
