from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import BaseModel

from orchestrator.api.main import app, get_orchestration_graph
from orchestrator.graph import OrchestrationGraph
from orchestrator.state import RunStateStore


class ScriptedModelProvider:
    def __init__(self, scripted_by_model: dict[str, list[dict]]) -> None:
        self._scripted = {name: list(values) for name, values in scripted_by_model.items()}

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        del system_prompt, user_prompt
        model_name = response_model.__name__
        queue = self._scripted.get(model_name)
        if not queue:
            raise AssertionError(f"No scripted response for model {model_name}")
        return response_model.model_validate(queue.pop(0))


def test_api_happy_path_submit_approve_plan_approve_merge_completed(tmp_path: Path) -> None:
    scripted = {
        "RequirementSpec": [
            {
                "raw_text": "Build a scalable URL shortener service with APIs, persistence, and analytics.",
                "category": "greenfield",
                "explicit_requirements": ["Build URL shortener"],
                "implicit_requirements": ["Scale horizontally"],
                "ambiguities": [],
                "ambiguity_score": 0.2,
            }
        ],
        "ArchitectureDesign": [
            {
                "components": ["api"],
                "data_model": "ShortUrl(code, target)",
                "api_contract_yaml": "openapi: 3.0.0\\ninfo:\\n  title: URL API\\n  version: 1.0.0\\npaths: {}",
                "tradeoffs": [
                    "counter vs hash: chose counter",
                    "sql vs nosql: chose sql",
                    "sync vs async analytics: chose async",
                ],
            }
        ],
        "TaskDAG": [
            {
                "tasks": []
            }
        ],
        "_RiskDocsResponse": [
            {
                "risks": ["Potential cache staleness"],
                "final_summary": "\n\n".join(
                    [
                        "## Implementation Plan and Rationale\nExecute minimal validated pipeline.",
                        "## Generated Artifacts\n- app module\n- tests module",
                        "## Risks, Trade-offs, and Validation Approach\nValidation via pytest and static checks.",
                        "## Assumptions and Limitations\nAssumes representative local test environment.",
                    ]
                ),
            }
        ],
    }

    store = RunStateStore(sqlite_path=str(tmp_path / "api-runs.db"))
    graph = OrchestrationGraph(
        model_provider=ScriptedModelProvider(scripted),
        store=store,
        repo_root=str(tmp_path),
        generated_root=str(tmp_path / "generated_projects"),
    )

    app.dependency_overrides[get_orchestration_graph] = lambda: graph
    client = TestClient(app)

    submit = client.post(
        "/requirements",
        json={"text": "Build a scalable URL shortener service with APIs, persistence, and analytics."},
    )
    assert submit.status_code == 200
    submit_payload = submit.json()
    assert submit_payload["status"] == "awaiting_human"
    run_id = submit_payload["run_id"]
    assert "review_payload" in submit_payload

    approve_plan = client.post(f"/runs/{run_id}/approve", json={"feedback": "approved"})
    assert approve_plan.status_code == 200
    approve_plan_payload = approve_plan.json()
    assert approve_plan_payload["status"] == "awaiting_human"
    assert json.loads(approve_plan_payload["review_payload"])["phase"] == "merge_review"

    approve_merge = client.post(f"/runs/{run_id}/approve", json={"feedback": "ship it"})
    assert approve_merge.status_code == 200
    assert approve_merge.json()["status"] == "completed"

    run_state = client.get(f"/runs/{run_id}")
    assert run_state.status_code == 200
    run_state_payload = run_state.json()
    assert run_state_payload["status"] == "completed"
    assert run_state_payload["current_phase"] == "completed"

    app.dependency_overrides.clear()
