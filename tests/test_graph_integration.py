from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from orchestrator.graph import OrchestrationGraph
from orchestrator.state import (
    ArchitectureDesign,
    RequirementCategory,
    RequirementSpec,
    RunState,
    RunStateStore,
    TaskDAG,
    TaskStatus,
)


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
        payload = queue.pop(0)
        return response_model.model_validate(payload)


def test_orchestration_graph_end_to_end_reaches_merge_gate(tmp_path: Path) -> None:
    requirement_text = "Build a scalable URL shortener service with APIs, persistence, and analytics."

    scripted = {
        "RequirementSpec": [
            {
                "raw_text": requirement_text,
                "category": "greenfield",
                "explicit_requirements": ["Build URL shortener", "Provide APIs", "Store data"],
                "implicit_requirements": ["Scale horizontally"],
                "ambiguities": ["SLOs missing"],
                "ambiguity_score": 0.2,
            }
        ],
        "ArchitectureDesign": [
            {
                "components": ["api", "service", "storage"],
                "data_model": "ShortUrl(id, code, target_url)",
                "api_contract_yaml": "openapi: 3.0.0\ninfo:\n  title: URL API\n  version: 1.0.0\npaths: {}",
                "tradeoffs": [
                    "hash vs counter: chose counter for uniqueness",
                    "sql vs nosql: chose sql for consistency",
                    "sync vs async analytics: chose async for latency",
                ],
            }
        ],
        "TaskDAG": [
            {
                "tasks": [
                    {
                        "id": "core-001",
                        "title": "Core implementation",
                        "description": "Build core module",
                        "depends_on": [],
                        "status": "pending",
                        "owned_files": ["app/core.py", "tests/test_core.py"],
                        "output_summary": None,
                        "retry_count": 0,
                    },
                    {
                        "id": "util-002",
                        "title": "Util implementation",
                        "description": "Build utility module",
                        "depends_on": ["core-001"],
                        "status": "pending",
                        "owned_files": ["app/util.py", "tests/test_util.py"],
                        "output_summary": None,
                        "retry_count": 0,
                    },
                ]
            }
        ],
        "_GeneratedFilesResponse": [
            {
                "files": {
                    "app/core.py": "def core_value() -> int:\n    return 1\n",
                }
            },
            {
                "files": {
                    "app/util.py": "def util_value() -> int:\n    return 2\n",
                }
            },
        ],
        "_GeneratedTestsResponse": [
            {
                "files": {
                    "tests/test_core.py": "def test_core() -> None:\n    assert True\n",
                }
            },
            {
                "files": {
                    "tests/test_util.py": "def test_util() -> None:\n    assert True\n",
                }
            },
        ],
        "_RiskDocsResponse": [
            {
                "risks": ["Possible scaling limits under burst traffic"],
                "final_summary": "\n\n".join(
                    [
                        "## Implementation Plan and Rationale\nComplete core then dependent utility behavior.",
                        "## Generated Artifacts\n- app/core.py\n- app/util.py\n- tests",
                        "## Risks, Trade-offs, and Validation Approach\nTrade-off between speed and robustness validated by tests.",
                        "## Assumptions and Limitations\nAssumes in-memory style test data setup.",
                    ]
                ),
            }
        ],
    }

    store = RunStateStore(sqlite_path=str(tmp_path / "runs.db"))
    model = ScriptedModelProvider(scripted)
    orchestrator = OrchestrationGraph(
        model_provider=model,
        store=store,
        repo_root=str(tmp_path),
        generated_root=str(tmp_path / "generated_projects"),
    )

    initial_state = RunState(
        run_id="integration-run-1",
        requirement=RequirementSpec(
            raw_text=requirement_text,
            category=RequirementCategory.AMBIGUOUS,
            explicit_requirements=[],
            implicit_requirements=[],
            ambiguities=[],
            ambiguity_score=1.0,
        ),
        current_phase="intake",
        awaiting_human=False,
    )

    paused_state = orchestrator.invoke(initial_state)
    assert paused_state.current_phase == "plan_review"
    assert paused_state.awaiting_human is True

    paused_state.human_feedback = "Plan approved"
    paused_state.awaiting_human = False
    final_state = orchestrator.invoke(paused_state)

    assert final_state.current_phase == "merge_approval_gate"
    assert all(task.status == TaskStatus.DONE for task in final_state.dag.tasks)
    assert final_state.final_summary is not None
    assert final_state.final_summary.count("## Implementation Plan and Rationale") == 1
    assert final_state.final_summary.count("## Generated Artifacts") == 1
    assert final_state.final_summary.count("## Risks, Trade-offs, and Validation Approach") == 1
    assert "Runnable service smoke test" in final_state.final_summary
