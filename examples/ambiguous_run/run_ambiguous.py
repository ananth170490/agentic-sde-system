from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel

from orchestrator.graph import OrchestrationGraph
from orchestrator.state import RequirementCategory, RequirementSpec, RunState, RunStateStore


REQUIREMENT_TEXT = "Make the reporting faster"


class ScriptedModelProvider:
    def __init__(self) -> None:
        self._responses: dict[str, list[dict]] = {
            "RequirementSpec": [
                {
                    "raw_text": REQUIREMENT_TEXT,
                    "category": "ambiguous",
                    "explicit_requirements": ["Make the reporting faster"],
                    "implicit_requirements": [
                        "Measure/report p95 latency for report endpoint",
                        "Define performance target and baseline",
                    ],
                    "ambiguities": [
                        "Which report endpoint(s) are in scope?",
                        "What exact latency target defines faster?",
                        "What load profile and percentile should be optimized?",
                    ],
                    "ambiguity_score": 0.82,
                }
            ],
            "ArchitectureDesign": [
                {
                    "components": ["reports-api", "report-cache", "metrics"],
                    "data_model": "ReportRequest, ReportResultCache",
                    "api_contract_yaml": "openapi: 3.0.0\ninfo:\n  title: Reports API\n  version: 1.0.0\npaths: {}",
                    "tradeoffs": [
                        "cache freshness vs latency: chose short TTL cache",
                        "sync compute vs precompute: chose selective precompute",
                        "single query vs denormalized table: chose denormalized read model",
                    ],
                }
            ],
            "TaskDAG": [
                {"tasks": []}
            ],
            "_RiskDocsResponse": [
                {
                    "risks": ["Cache staleness risk", "Insufficient baseline data risk"],
                    "final_summary": "\n\n".join(
                        [
                            "## Implementation Plan and Rationale\nPlan focuses on clear SLO-first optimization.",
                            "## Generated Artifacts\n- docs/perf_plan.md",
                            "## Risks, Trade-offs, and Validation Approach\nValidate p95 latency under representative load.",
                            "## Assumptions and Limitations\nAssumes reports endpoint remains stable.",
                        ]
                    ),
                }
            ],
        }

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        del system_prompt, user_prompt
        name = response_model.__name__
        queue = self._responses.get(name)
        if not queue:
            raise RuntimeError(f"No scripted response available for {name}")
        return response_model.model_validate(queue.pop(0))


def main() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    store = RunStateStore(sqlite_path=str((workspace_root / "orchestrator_runs.db").resolve()))
    graph = OrchestrationGraph(
        model_provider=ScriptedModelProvider(),
        store=store,
        repo_root=str(workspace_root),
        generated_root=str((workspace_root / "generated_projects").resolve()),
    )

    run_id = str(uuid4())
    initial = RunState(
        run_id=run_id,
        requirement=RequirementSpec(
            raw_text=REQUIREMENT_TEXT,
            category=RequirementCategory.AMBIGUOUS,
            explicit_requirements=[],
            implicit_requirements=[],
            ambiguities=[],
            ambiguity_score=1.0,
        ),
        current_phase="intake",
        status="running",
    )

    print(f"Starting ambiguous run: {run_id}")
    paused = graph.invoke(initial)
    assert paused.current_phase == "clarify_gate"
    assert paused.awaiting_human is True
    assert paused.requirement.ambiguity_score > 0.5

    payload = json.loads(paused.review_payload or "{}")
    questions = payload.get("clarifying_questions", [])
    assert questions, "Expected explicit clarifying questions"
    assert all("?" in q or len(q) > 20 for q in questions)

    print("Paused at clarify_gate with review payload:")
    print(paused.review_payload)

    paused.human_feedback = "'faster' means p95 API latency under 300ms for the /reports endpoint"
    paused.awaiting_human = False
    resumed = graph.invoke(paused)

    approvals = 0
    while resumed.awaiting_human and resumed.status != "completed":
        approvals += 1
        print(f"Auto-approving phase {resumed.current_phase}")
        if resumed.review_payload:
            print(resumed.review_payload)
        resumed.human_feedback = f"auto-approve-{approvals}"
        resumed.awaiting_human = False
        resumed = graph.invoke(resumed)

    final_state = graph.store.load(run_id)
    if final_state is None:
        raise RuntimeError("Run state missing after completion")

    print(f"Final status: {final_state.status}")
    print(f"Final phase: {final_state.current_phase}")
    assert final_state.status == "completed"


if __name__ == "__main__":
    main()
