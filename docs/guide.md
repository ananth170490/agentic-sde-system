# Beginner-Friendly KT Guide

## Purpose of This Document

This guide explains the project from the beginning in simple language for someone who is not a developer or software engineer. By the end, you should understand:

- what problem this system solves
- how the workflow operates from start to finish
- why the mandatory use case matters
- how the project demonstrates engineering quality, validation, and recovery
- how to explain the solution confidently to a reviewer

## What This Project Is

This project is an agentic software engineering orchestrator.

That means it is a system that takes a requirement written in plain English and moves it through the major stages of software delivery:

1. understand the requirement
2. identify what is unclear
3. design the architecture
4. break the work into tasks
5. generate code
6. generate tests
7. validate the output
8. recover from failure when possible
9. pause for human approval when needed
10. produce a final engineering summary

In short: it behaves like a careful engineering workflow, not just a text generator.

## The Mandatory Use Case

The required input for the assignment is:

> Build a scalable URL shortener service with APIs, persistence, and analytics.

This is a very good requirement for evaluation because it is small enough to understand but rich enough to test real engineering thinking.

A strong system must understand that this request implies all of the following:

- a service that creates short links from long URLs
- API endpoints to create and use those links
- persistent storage so data is not lost
- analytics such as tracking how often a short link is used
- scalability considerations so the service can handle growth

This use case is demonstrated by [examples/greenfield_run/run_url_shortener.py](../examples/greenfield_run/run_url_shortener.py).

## What the Evaluator Is Really Looking For

The evaluator is not only checking whether code was generated. They are checking whether the system shows production-style engineering discipline.

### 1. End-to-End Workflow Completeness

The system should handle the full journey from raw requirement to final output.

In this project, that lifecycle is orchestrated in [orchestrator/graph.py](../orchestrator/graph.py).

### 2. Strong Design and Architecture

The system should not jump directly into coding. It should first design a sensible technical solution.

That includes:

- components
- data model
- API contract
- trade-offs
- validation strategy

This is handled by [orchestrator/agents/architect.py](../orchestrator/agents/architect.py).

### 3. Depth of Task Decomposition and Orchestration

The system should break the work into meaningful, dependency-aware tasks rather than vague to-do items.

That logic is handled by [orchestrator/agents/task_decomposer.py](../orchestrator/agents/task_decomposer.py) and the DAG behavior in [orchestrator/state.py](../orchestrator/state.py).

### 4. Quality and Realism of Engineering Outputs

The generated output should look like work a real engineer might produce, including:

- implementation files
- tests
- APIs
- architecture rationale
- risk summary

### 5. Validation and Risk Management

The system must check whether the generated output works. It should not simply assume it is correct.

This project validates output with:

- pytest
- py_compile
- pyflakes

Validation is handled by [orchestrator/agents/validator.py](../orchestrator/agents/validator.py).

### 6. Clear and Defensible Technical Reasoning

The system should explain its decisions. That means it should capture trade-offs, assumptions, risks, and limitations in a structured way.

This is covered by [orchestrator/agents/risk_docs.py](../orchestrator/agents/risk_docs.py).

## High-Level Workflow in Simple Terms

The workflow is:

1. take a requirement
2. structure it into a formal requirement model
3. check whether it is clear or ambiguous
4. if it is brownfield, inspect the existing codebase
5. design the architecture
6. break the work into tasks
7. pause for human review of the plan
8. execute tasks one by one or in valid dependency order
9. generate code and tests
10. validate them
11. repair and retry if validation fails
12. write final risks and summary
13. pause for merge approval
14. mark the run complete

This flow is documented in [docs/architecture.md](./architecture.md).

## The Main Building Block: RunState

Everything revolves around a shared object called `RunState` in [orchestrator/state.py](../orchestrator/state.py).

Think of `RunState` as the project memory for one run.

It stores:

- the original requirement
- the architecture design
- the task list
- validation results
- risks
- final summary
- approval status
- current phase of the workflow
- rejection reason if a run is rejected

Why this matters:

- every stage reads from the same state
- every stage writes back to the same state
- the system can pause and resume safely
- the system can recover after a crash

## The Agents and Their Single Responsibility

Each agent has one main job.

### IntakeAgent

File: [orchestrator/agents/intake.py](../orchestrator/agents/intake.py)

Responsibility:

- convert raw text into a structured `RequirementSpec`
- identify explicit requirements
- infer implicit requirements
- identify ambiguities
- assign an ambiguity score

Example for the URL shortener requirement:

- explicit: build URL shortener, APIs, persistence, analytics
- implicit: scalability may imply horizontal scaling and load balancing

### CodebaseReasoningAgent

File: [orchestrator/agents/codebase_reasoning.py](../orchestrator/agents/codebase_reasoning.py)

Responsibility:

- used mainly for brownfield work
- inspect an existing codebase
- identify likely impacted modules/files

This is demonstrated by [examples/brownfield_run/run_add_auth.py](../examples/brownfield_run/run_add_auth.py).

### ArchitectAgent

File: [orchestrator/agents/architect.py](../orchestrator/agents/architect.py)

Responsibility:

- create an architecture design
- define components
- define data model
- define full OpenAPI contract
- explain trade-offs

### TaskDecomposerAgent

File: [orchestrator/agents/task_decomposer.py](../orchestrator/agents/task_decomposer.py)

Responsibility:

- break the design into concrete engineering tasks
- assign dependency relationships
- assign owned file paths so tasks do not collide

### CodeGenAgent

File: [orchestrator/agents/code_gen.py](../orchestrator/agents/code_gen.py)

Responsibility:

- generate implementation files for a task
- only write files that the task is allowed to modify
- support repair when validation fails

### TestGenAgent

File: [orchestrator/agents/test_gen.py](../orchestrator/agents/test_gen.py)

Responsibility:

- generate pytest tests for the same task
- cover both unit-level and integration-level behavior

### ValidationAgent

File: [orchestrator/agents/validator.py](../orchestrator/agents/validator.py)

Responsibility:

- execute tests
- run basic static checks
- return a structured validation result

### RiskDocsAgent

File: [orchestrator/agents/risk_docs.py](../orchestrator/agents/risk_docs.py)

Responsibility:

- produce a risk list
- produce final engineering summary markdown
- write the summary to the docs folder

## Supporting Tools

### ModelProvider

File: [orchestrator/tools/model_provider.py](../orchestrator/tools/model_provider.py)

Purpose:

- connect to Anthropic API for structured model calls
- validate the returned JSON against Pydantic models
- retry once if parsing or validation fails
- provide a fake version for tests

### RepoIndex

File: [orchestrator/tools/repo_index.py](../orchestrator/tools/repo_index.py)

Purpose:

- inspect Python files with AST
- extract top-level symbols and docstrings
- build simple import graph
- help identify impacted files for brownfield changes

### SandboxRunner

File: [orchestrator/tools/sandbox_runner.py](../orchestrator/tools/sandbox_runner.py)

Purpose:

- run pytest in a temp copy of the generated project
- capture logs and issues
- raise explicit timeout error when execution takes too long

## Human Approval Gates

Not every step should run without human oversight.

This project includes human approval points implemented with LangGraph interrupts.

Files involved:

- [orchestrator/gates/human_approval.py](../orchestrator/gates/human_approval.py)
- [orchestrator/graph.py](../orchestrator/graph.py)

The system pauses at:

- clarify gate when a requirement is too ambiguous
- plan review after task decomposition
- merge review after execution and summary

At each pause, the system creates a `review_payload` that explains what a human would review.

## Crash Recovery and Resume

This project was built with recovery in mind.

There are two mechanisms:

### 1. RunStateStore

In [orchestrator/state.py](../orchestrator/state.py), the `RunStateStore` saves each run to SQLite.

This means:

- progress is persisted after node transitions
- a crashed run can be reloaded by `run_id`

### 2. LangGraph Checkpointing

In [orchestrator/graph.py](../orchestrator/graph.py), LangGraph checkpoints the graph and supports interrupt points.

This means:

- the system can resume from an approval pause
- it does not need to start the workflow from zero

## Why the URL Shortener Use Case Is Strong

A URL shortener sounds simple, but it tests several real engineering concerns.

### APIs

A realistic version needs endpoints like:

- create short link
- redirect by code
- retrieve analytics

### Persistence

Data must survive process restarts.

That means the system should design a proper storage model, even in a prototype.

### Analytics

The system must track usage, not only store URLs.

### Scalability

The system should think about:

- stateless API scaling
- short-code uniqueness
- read/write patterns
- future traffic growth

That makes it a good benchmark for system design.

## What “Production-Grade Engineering” Means in This Assignment

This phrase can sound intimidating. Here it simply means the solution should behave like careful engineering work.

In this project that means:

- explicit state management
- structured workflow orchestration
- dependency-aware task execution
- validation before accepting outputs
- repair and retry behavior
- human approval points
- persistence and recovery
- risks and limitations clearly documented

## Repair Loop: Error-Handling Design

One of the strongest architectural features in this project is the repair loop.

What it proves:

- the system can detect bad generated code
- it does not silently continue after failure
- it can call a repair step with validation feedback
- it can retry and recover
- it stops after a bounded number of retries

This behavior is implemented across:

- [orchestrator/agents/code_gen.py](../orchestrator/agents/code_gen.py)
- [orchestrator/agents/validator.py](../orchestrator/agents/validator.py)
- [orchestrator/graph.py](../orchestrator/graph.py)

Why this matters:

- it shows cross-step coordination
- it shows validation-driven recovery
- it proves the system is more than prompt chaining
- it keeps automation bounded when quality checks fail

## Example Scenarios Included in the Repo

### Greenfield Example

Files:

- [examples/greenfield_run/run_url_shortener.py](../examples/greenfield_run/run_url_shortener.py)
- [examples/greenfield_run/transcript.md](../examples/greenfield_run/transcript.md)

What it demonstrates:

- new system creation from scratch
- human gate printing and auto-approval
- generated output copied into `generated_projects/url-shortener`
- generated project tests executed

### Brownfield Example

Files:

- [examples/brownfield_run/fixture_service/app.py](../examples/brownfield_run/fixture_service/app.py)
- [examples/brownfield_run/run_add_auth.py](../examples/brownfield_run/run_add_auth.py)
- [examples/brownfield_run/transcript.md](../examples/brownfield_run/transcript.md)

What it demonstrates:

- requirement correctly classified as brownfield
- existing codebase inspection
- impacted file identification for write endpoints

Current scope note:

- this checked-in example focuses on brownfield reasoning and impact analysis rather than full code generation and validation

### Ambiguous Example

Files:

- [examples/ambiguous_run/run_ambiguous.py](../examples/ambiguous_run/run_ambiguous.py)
- [examples/ambiguous_run/transcript.md](../examples/ambiguous_run/transcript.md)

What it demonstrates:

- high ambiguity score
- pause at clarify gate
- specific clarifying questions in review payload
- resume after human clarification
- non-empty task decomposition after clarification
- generated implementation/tests and validation before completion

## Testing Strategy in Simple Terms

The test strategy is layered.

### Unit Tests

Used for:

- each agent
- each tool
- path restrictions
- repo indexing
- DAG logic

These use `FakeModelProvider` so tests are fast and deterministic.

### Integration Tests

Used for:

- full graph flow
- pause/resume behavior
- API flow

### End-to-End Demonstrations

Used for:

- real workflow examples
- proof that the system can run in realistic sequences

The test suite currently passes across the repository.

## How To Explain This Project to a Reviewer in One Minute

You can say:

> This project is a stateful agentic engineering orchestrator. It converts a plain-English requirement into a structured requirement model, architecture, task DAG, generated code, generated tests, validation results, and final risk documentation. The workflow is controlled through LangGraph, supports human approval interrupts, persists state for crash recovery, and includes a bounded repair loop so generated failures can be detected and corrected rather than silently accepted.

That is a strong, reviewer-friendly summary.

## Beginner-Friendly Interview Script

If someone asks you to explain the project in plain English, you can say:

> The system works like a disciplined engineering team. It first understands the requirement, then designs the system, breaks the work into steps, generates code and tests, validates the results, retries when something fails, pauses for approval when needed, and finally produces a summary of risks and decisions.

## Common Questions and Safe Answers

### Why is this better than a single prompt to an LLM?

Because a single prompt may generate code, but it does not naturally provide:

- structured workflow control
- per-step validation
- bounded retries
- pause/resume approval flow
- persistent run state
- dependency-aware task execution

### Why use a URL shortener as the demo?

Because it is simple enough to understand but still requires real engineering decisions around APIs, storage, analytics, and scaling.

### What proves the system can recover from mistakes?

The repair loop demonstration, where generated code intentionally failed validation and the system repaired it successfully on retry.

### What proves the system handles ambiguity responsibly?

The ambiguous example, which pauses and asks clarifying questions instead of guessing blindly.

## Known Limitations

Be ready to say these clearly.

- generated code execution is subprocess-based, not full container sandbox isolation
- real-model generation quality depends on provider capability/latency; a deterministic scripted provider path is included for reliable demos
- brownfield codebase reasoning uses AST and grep heuristics, not embedding search
- example approvals are simulated through scripts rather than a real UI
- real-model greenfield runs depend on model configuration, but `MODEL_PROVIDER=scripted` provides a deterministic no-key demonstration path

These limitations are honest and reasonable for a prototype.

## Practical Runbook for a New Reviewer

If someone wants to explore the project hands-on, recommend this order:

1. read [README.md](../README.md)
2. read [docs/architecture.md](./architecture.md)
3. inspect [orchestrator/state.py](../orchestrator/state.py)
4. inspect [orchestrator/graph.py](../orchestrator/graph.py)
5. run the test suite
6. read the example transcripts
7. run brownfield and ambiguous examples locally
8. run greenfield example using either a real model provider or the deterministic scripted path

## Final Takeaway

The main value of this project is not just that it can generate code.

The value is that it shows controlled autonomy across the software lifecycle:

- requirement understanding
- architecture design
- task orchestration
- code and test generation
- validation and recovery
- human oversight
- risk documentation
- crash recovery

That is exactly what makes it strong against the assignment criteria.
