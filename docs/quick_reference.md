# Repository Quick Reference

This page is a compact map of what the main files and folders in this repository do.

## Root Files

- `README.md` - project overview, setup steps, workflow summary, and the main entry points for reviewers.
- `Dockerfile` - builds the container image for the orchestrator service.
- `docker-compose.yml` - starts the orchestrator and wires up its runtime environment.
- `requirements.txt` - Python dependencies for local and container execution.
- `pytest.ini` - pytest configuration for the test suite.
- `.env.example` - sample environment variables you can copy into a local `.env` file.
- `.gitignore` - excludes local, generated, and build-time files from version control.
- `.env` - local environment configuration used by the app at runtime.
- `orchestrator_runs.db` - local SQLite run-state database created during execution.

## `orchestrator/`

This is the core application package.

### Core Control Flow

- `orchestrator/graph.py` - main orchestration graph, phase routing, retries, fallback behavior, and run finalization.
- `orchestrator/state.py` - shared Pydantic models for requirements, tasks, validations, DAG state, and persisted run state.

### Agents

- `orchestrator/agents/intake.py` - turns plain text into structured requirement analysis.
- `orchestrator/agents/codebase_reasoning.py` - identifies impacted files and areas for brownfield tasks.
- `orchestrator/agents/architect.py` - designs the architecture, data model, and trade-offs.
- `orchestrator/agents/task_decomposer.py` - converts the architecture into a dependency-aware task DAG.
- `orchestrator/agents/code_gen.py` - generates code files for each task.
- `orchestrator/agents/test_gen.py` - generates task-specific tests.
- `orchestrator/agents/validator.py` - runs `pytest`, `py_compile`, and `pyflakes` checks.
- `orchestrator/agents/risk_docs.py` - produces the final engineering summary and risk/trade-off write-up.

### API and Gates

- `orchestrator/api/main.py` - FastAPI app, requirement submission endpoints, run approval/rejection endpoints, and the live demo UI route.
- `orchestrator/gates/human_approval.py` - builds the clarify, plan, and merge approval gate payloads.

### Tools

- `orchestrator/tools/model_provider.py` - provider abstraction, structured output parsing, fallback logic, and OpenAI/OpenRouter/Ollama support.
- `orchestrator/tools/repo_index.py` - repo indexing and AST/import-based codebase lookup for brownfield reasoning.
- `orchestrator/tools/sandbox_runner.py` - sandboxed execution of scoped validation commands.

## `tests/`

These are the automated checks for the orchestrator and its helper tools.

- `tests/test_graph_integration.py` - end-to-end orchestration graph coverage.
- `tests/test_task_dag.py` - task DAG structure and ordering checks.
- `tests/agents/test_intake.py` - requirement classification and intake behavior.
- `tests/agents/test_code_gen.py` - code generation sanitization and file-boundary checks.
- `tests/agents/test_test_gen.py` - test generation behavior and file-boundary checks.
- `tests/agents/test_risk_docs.py` - final summary formatting and required header checks.
- `tests/api/test_main.py` - FastAPI route behavior and live demo UI serving.
- `tests/tools/test_model_provider.py` - provider parsing, fallback, and coercion coverage.
- `tests/tools/test_repo_index.py` - repository indexing behavior.
- `tests/tools/test_sandbox_runner.py` - sandbox execution behavior.

## `examples/`

These are runnable scenario entry points used for demos and evaluation.

- `examples/greenfield_run/run_url_shortener.py` - mandatory greenfield URL shortener flow.
- `examples/brownfield_run/run_add_auth.py` - brownfield auth-enhancement flow.
- `examples/ambiguous_run/run_ambiguous.py` - ambiguous requirement flow with clarification gating.
- `examples/*/transcript.md` - captured output logs for each demo scenario.
- `examples/brownfield_run/fixture_service/` - sample service used by the brownfield run.

## `docs/`

These files explain, demonstrate, and document the project.

- `docs/architecture.md` - system architecture, control flow, and design rationale.
- `docs/guide.md` - reviewer-friendly guide for running and explaining the system.
- `docs/live_demo_checklist.md` - step-by-step demo checklist.
- `docs/live_demo_ui.html` - browser-based live demo runner UI.
- `docs/run_and_evaluate.md` - concise run-and-evaluate playbook.
- `docs/demo_mode_and_production_readiness.md` - demo mode and production-readiness guidance.
- `docs/submission_guide.md` - submission walkthrough and evidence structure.
- `docs/submission_package.md` - packaged submission summary and coverage matrix.
- `docs/engineering_summary_*.md` - captured run summaries and evidence artifacts.

## `generated_projects/`

Generated code, tests, and docs created by completed runs.

- Each subfolder is named after the requirement plus a run-specific suffix.
- These folders are useful as evidence of what the system produced for a given run.

## Quick Reading Order

If you are new to the repo, read these files in order:

1. `README.md`
2. `docs/architecture.md`
3. `docs/run_and_evaluate.md`
4. `docs/live_demo_checklist.md`
5. `orchestrator/graph.py`
6. `orchestrator/agents/intake.py`
7. `tests/test_graph_integration.py`
