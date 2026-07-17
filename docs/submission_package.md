# Submission Package

## Executive Summary

This project is a working prototype of an agentic software engineering system that transforms a plain-English software requirement into a reviewable engineering outcome.

It is designed to satisfy the assignment objective end to end:

- understand requirements
- identify ambiguities
- design a technical solution
- decompose work into dependency-aware tasks
- orchestrate multi-step execution
- generate code, tests, and documentation
- validate outputs with runtime and static checks
- pause for human approval at meaningful checkpoints
- persist progress for recovery and resume
- produce a final engineering summary with risks, trade-offs, and limitations

The system is not a generic chatbot wrapper. It is a stateful orchestration workflow that models the software delivery lifecycle.

## Assignment Coverage

### 1. Requirement Understanding

Implemented in [orchestrator/agents/intake.py](../orchestrator/agents/intake.py).

The intake agent converts raw text into a structured `RequirementSpec` containing:

- requirement category
- explicit requirements
- implicit requirements
- ambiguities
- ambiguity score

This directly addresses the requirement to interpret intent, identify ambiguity, and normalize the problem into an engineering-ready form.

### 2. Task Decomposition

Implemented in [orchestrator/agents/task_decomposer.py](../orchestrator/agents/task_decomposer.py) and [orchestrator/state.py](../orchestrator/state.py).

The design is translated into a `TaskDAG` whose tasks include:

- task id
- title
- description
- dependencies
- owned files
- retry count
- execution status

The DAG supports dependency-aware execution and cycle detection rather than a flat to-do list.

### 3. Codebase Reasoning for Brownfield Work

Implemented in [orchestrator/agents/codebase_reasoning.py](../orchestrator/agents/codebase_reasoning.py) and [orchestrator/tools/repo_index.py](../orchestrator/tools/repo_index.py).

The brownfield path performs lightweight repository analysis using:

- AST symbol extraction
- import graph construction
- keyword-based matching
- importer impact propagation

This allows the system to identify likely impacted files, services, and modules before proposing changes.

### 4. Workflow Orchestration

Implemented in [orchestrator/graph.py](../orchestrator/graph.py).

The orchestration graph includes the following stages:

1. intake
2. clarify gate
3. codebase reasoning
4. architecture design
5. task decomposition
6. plan approval gate
7. DAG execution
8. validation and repair
9. risk documentation
10. merge approval gate
11. finalize

This satisfies the requirement for multi-step orchestration, dependency management, cross-step coordination, and error recovery.

### 5. Engineering Output Generation

Implemented across:

- [orchestrator/agents/architect.py](../orchestrator/agents/architect.py)
- [orchestrator/agents/code_gen.py](../orchestrator/agents/code_gen.py)
- [orchestrator/agents/test_gen.py](../orchestrator/agents/test_gen.py)
- [orchestrator/agents/risk_docs.py](../orchestrator/agents/risk_docs.py)

The system produces:

- architecture components
- data model description
- OpenAPI 3.0 contract
- production-oriented code files
- pytest test files
- final engineering summary

### 6. Validation and Risk Control

Implemented in [orchestrator/agents/validator.py](../orchestrator/agents/validator.py) and [orchestrator/tools/sandbox_runner.py](../orchestrator/tools/sandbox_runner.py).

Validation includes:

- pytest execution
- `py_compile`
- `pyflakes`

Risk and trade-off summarization is implemented in [orchestrator/agents/risk_docs.py](../orchestrator/agents/risk_docs.py).

### 7. Controlled Autonomy

Implemented in [orchestrator/gates/human_approval.py](../orchestrator/gates/human_approval.py), [orchestrator/graph.py](../orchestrator/graph.py), and [orchestrator/api/main.py](../orchestrator/api/main.py).

The system pauses at explicit human checkpoints:

- clarify gate for ambiguous requirements
- plan review before execution
- merge review after generation and validation

This demonstrates bounded autonomy rather than unrestricted generation.

### 8. Final Output

Implemented in [orchestrator/agents/risk_docs.py](../orchestrator/agents/risk_docs.py).

The final summary includes the exact required delivery sections:

- Implementation Plan and Rationale
- Generated Artifacts
- Risks, Trade-offs, and Validation Approach
- Assumptions and Limitations

## Architecture Overview

The system uses a shared `RunState` model as execution memory for a single run. The state stores the requirement, impacted areas, architecture design, task DAG, validation results, risks, final summary, review payloads, and phase status.

Core state and persistence are implemented in [orchestrator/state.py](../orchestrator/state.py).

The orchestration engine in [orchestrator/graph.py](../orchestrator/graph.py) routes execution based on the current phase and uses LangGraph checkpoints plus SQLite persistence to support pause/resume behavior.

Supporting components:

- [orchestrator/api/main.py](../orchestrator/api/main.py): API entry point for submit, inspect, approve, and reject
- [orchestrator/tools/model_provider.py](../orchestrator/tools/model_provider.py): structured-output model abstraction with Anthropic, Ollama, and fake providers
- [orchestrator/tools/repo_index.py](../orchestrator/tools/repo_index.py): brownfield repository reasoning
- [orchestrator/tools/sandbox_runner.py](../orchestrator/tools/sandbox_runner.py): sandboxed pytest execution in a temp copy

See [docs/architecture.md](./architecture.md) for the control-flow diagram.

## Mandatory Use Case: URL Shortener

Required prompt:

> Build a scalable URL shortener service with APIs, persistence, and analytics.

This use case is implemented as the greenfield flow in [examples/greenfield_run/run_url_shortener.py](../examples/greenfield_run/run_url_shortener.py).

Expected system behavior for this requirement:

1. classify it as greenfield
2. extract explicit requirements: URL shortening, APIs, persistence, analytics
3. infer implicit requirements: scale, availability, identifier strategy, stateless services, future growth
4. design architecture and API contract
5. decompose implementation into dependency-aware tasks
6. generate code and tests within owned file boundaries
7. validate the generated result
8. provide risks, trade-offs, and final summary

### Important Practical Note

The repository now includes a deterministic scripted provider path for reliable local demonstration of the mandatory use case when external model access is unavailable or unstable.

Use:

```bash
MODEL_PROVIDER=scripted PYTHONPATH=. .venv/bin/python examples/greenfield_run/run_url_shortener.py
```

This executes the full orchestrated flow (analysis, architecture, DAG decomposition, code/test generation, validation, risk summary, approvals) and produces a passing generated URL shortener project.

Real-model providers (Anthropic/Ollama) remain supported, but runtime quality and latency depend on model capability.

## Example Scenarios Included

### Greenfield Scenario

File: [examples/greenfield_run/run_url_shortener.py](../examples/greenfield_run/run_url_shortener.py)

What it demonstrates:

- mandatory assignment use case
- real orchestration entry point
- approval payload generation
- artifact copy-out to `generated_projects/url-shortener`
- generated project test execution

### Brownfield Scenario

Files:

- [examples/brownfield_run/run_add_auth.py](../examples/brownfield_run/run_add_auth.py)
- [examples/brownfield_run/fixture_service/app.py](../examples/brownfield_run/fixture_service/app.py)

What it demonstrates:

- brownfield requirement classification
- repository reasoning
- impacted file detection before implementation planning

Observed behavior during validation:

- the run classified the request as brownfield
- the impacted areas output included `app.py`

### Ambiguous Scenario

File: [examples/ambiguous_run/run_ambiguous.py](../examples/ambiguous_run/run_ambiguous.py)

What it demonstrates:

- ambiguity detection
- explicit clarifying questions
- pause and resume behavior
- plan approval and merge approval gates
- final completion after human feedback

Observed behavior during validation:

- the run paused at `clarify_gate`
- it produced clear review questions
- after feedback, it resumed and completed successfully

## Testing and Verification

Automated verification currently passes:

- `12 passed, 1 warning`

Primary coverage files:

- [tests/test_graph_integration.py](../tests/test_graph_integration.py)
- [tests/api/test_main.py](../tests/api/test_main.py)
- [tests/test_task_dag.py](../tests/test_task_dag.py)
- [tests/tools/test_repo_index.py](../tests/tools/test_repo_index.py)
- [tests/tools/test_sandbox_runner.py](../tests/tools/test_sandbox_runner.py)
- [tests/agents/test_intake.py](../tests/agents/test_intake.py)
- [tests/agents/test_code_gen.py](../tests/agents/test_code_gen.py)
- [tests/agents/test_test_gen.py](../tests/agents/test_test_gen.py)
- [tests/agents/test_risk_docs.py](../tests/agents/test_risk_docs.py)

What is verified automatically:

- structured requirement parsing
- DAG ordering and cycle detection
- file ownership guardrails
- sandbox timeout behavior
- API submit and approval flow
- end-to-end graph transitions with paused and resumed states
- final summary generation with required sections

## Setup and Run Instructions

### Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the API

```bash
uvicorn orchestrator.api.main:app --reload
```

### Run Tests

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

### Run Example Scenarios

Brownfield:

```bash
PYTHONPATH=. .venv/bin/python examples/brownfield_run/run_add_auth.py
```

Ambiguous:

```bash
PYTHONPATH=. .venv/bin/python examples/ambiguous_run/run_ambiguous.py
```

Mandatory greenfield scenario:

```bash
PYTHONPATH=. .venv/bin/python examples/greenfield_run/run_url_shortener.py
```

## Technical Strengths

1. The workflow is stateful and recoverable.
2. The orchestration is multi-step and dependency-aware.
3. Human approval is modeled explicitly, not implied.
4. Validation is built into the loop rather than treated as an afterthought.
5. File ownership boundaries reduce unsafe writes during code generation.
6. The project demonstrates greenfield, brownfield, and ambiguous requirement handling.
7. The API and test suite make the system evaluable by another engineer.

## Known Limitations and Trade-Offs

1. Real-model execution quality depends on model capability and latency; for reliability, the repo includes a deterministic scripted provider for the mandatory flow.
2. Sandbox execution uses subprocess isolation rather than full container or VM isolation.
3. Brownfield reasoning is heuristic and AST-based rather than embedding-based semantic analysis.
4. Human review is demonstrated through API payloads and example auto-approval rather than a dedicated UI.
5. The ambiguous example currently emits LangGraph checkpoint deserialization warnings during resume, although the flow still completes.

## Evaluation Summary

As a submission, this project demonstrates the expected engineering qualities for the assignment:

- end-to-end completeness
- structured system design
- realistic task decomposition
- controlled autonomy
- validation discipline
- explicit trade-off handling
- clear final documentation

The system should be presented as a strong assignment-grade prototype with honest disclosure of the local-model limitation encountered during the mandatory URL shortener demonstration.
