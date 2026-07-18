from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import cast
from uuid import uuid4

from pydantic import BaseModel


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from orchestrator.graph import OrchestrationGraph
from orchestrator.state import RequirementCategory, RequirementSpec, RunState, RunStateStore
from orchestrator.tools.model_provider import ModelProvider


REQUIREMENT_TEXT = "Make the reporting faster"


def _slugify(text: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:80] or "generated-project"


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
                {
                    "tasks": [
                        {
                            "id": "perf-001",
                            "title": "Add reporting latency analyzer",
                            "description": "Implement a small analyzer that flags slow reports against a p95 latency target.",
                            "depends_on": [],
                            "status": "pending",
                            "owned_files": ["app/reporting.py", "tests/test_reporting.py"],
                            "output_summary": None,
                            "retry_count": 0,
                        },
                        {
                            "id": "perf-002",
                            "title": "Add bounded in-memory cache helper",
                            "description": "Implement a deterministic cache helper to support future reporting optimization work.",
                            "depends_on": ["perf-001"],
                            "status": "pending",
                            "owned_files": ["app/cache.py", "tests/test_cache.py"],
                            "output_summary": None,
                            "retry_count": 0,
                        },
                    ]
                }
            ],
            "_GeneratedFilesResponse": [
                {
                    "files": {
                        "app/reporting.py": "from __future__ import annotations\n\n\ndef classify_latency(latencies_ms: list[int], target_p95_ms: int) -> dict[str, int | bool]:\n    if not latencies_ms:\n        return {\"sample_size\": 0, \"p95_ms\": 0, \"meets_target\": True}\n\n    ordered = sorted(latencies_ms)\n    index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))\n    p95_value = ordered[index]\n    return {\"sample_size\": len(ordered), \"p95_ms\": p95_value, \"meets_target\": p95_value <= target_p95_ms}\n"
                    }
                },
                {
                    "files": {
                        "app/cache.py": "from __future__ import annotations\n\n\nclass ReportCache:\n    def __init__(self, max_entries: int = 3) -> None:\n        self._max_entries = max_entries\n        self._items: dict[str, str] = {}\n        self._order: list[str] = []\n\n    def put(self, key: str, value: str) -> None:\n        if key in self._items:\n            self._order.remove(key)\n        elif len(self._order) >= self._max_entries:\n            oldest = self._order.pop(0)\n            del self._items[oldest]\n\n        self._items[key] = value\n        self._order.append(key)\n\n    def get(self, key: str) -> str | None:\n        return self._items.get(key)\n"
                    }
                },
            ],
            "_GeneratedTestsResponse": [
                {
                    "files": {
                        "tests/test_reporting.py": "from app.reporting import classify_latency\n\n\ndef test_classify_latency_detects_slo_breach() -> None:\n    result = classify_latency([120, 180, 220, 310, 450], target_p95_ms=300)\n    assert result[\"sample_size\"] == 5\n    assert result[\"p95_ms\"] >= 310\n    assert result[\"meets_target\"] is False\n\n\ndef test_classify_latency_handles_empty_samples() -> None:\n    result = classify_latency([], target_p95_ms=300)\n    assert result == {\"sample_size\": 0, \"p95_ms\": 0, \"meets_target\": True}\n"
                    }
                },
                {
                    "files": {
                        "tests/test_cache.py": "from app.cache import ReportCache\n\n\ndef test_report_cache_evicts_oldest_entry() -> None:\n    cache = ReportCache(max_entries=2)\n    cache.put(\"r1\", \"first\")\n    cache.put(\"r2\", \"second\")\n    cache.put(\"r3\", \"third\")\n\n    assert cache.get(\"r1\") is None\n    assert cache.get(\"r2\") == \"second\"\n    assert cache.get(\"r3\") == \"third\"\n"
                    }
                },
            ],
            "_RiskDocsResponse": [
                {
                    "risks": ["Cache staleness risk", "Insufficient baseline data risk"],
                    "final_summary": "\n\n".join(
                        [
                            "## Implementation Plan and Rationale\nPlan focuses on clarifying the target first, then implementing measurable latency analysis and a bounded cache helper.",
                            "## Generated Artifacts\n- app/reporting.py\n- app/cache.py\n- tests/test_reporting.py\n- tests/test_cache.py",
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
    workspace_root = WORKSPACE_ROOT
    generated_root = (workspace_root / "generated_projects").resolve()
    project_dir = generated_root / _slugify(REQUIREMENT_TEXT)
    store = RunStateStore(sqlite_path=str((workspace_root / "orchestrator_runs.db").resolve()))
    graph = OrchestrationGraph(
        model_provider=cast(ModelProvider, ScriptedModelProvider()),
        store=store,
        repo_root=str(workspace_root),
        generated_root=str(generated_root),
    )

    if project_dir.exists():
        shutil.rmtree(project_dir)

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

    assert final_state.dag is not None
    assert len(final_state.dag.tasks) == 2
    assert all(task.status == "done" for task in final_state.dag.tasks)
    assert final_state.validations, "Expected validation results after execution"
    assert all(result.passed for result in final_state.validations)

    print("Executed task DAG:")
    for task in final_state.dag.tasks:
        print(f"- {task.id}: {task.title} [{task.status}]")

    print("Validation results:")
    for result in final_state.validations:
        print(f"- {result.task_id}: passed={result.passed}, issues={result.issues}")

    print(f"Final status: {final_state.status}")
    print(f"Final phase: {final_state.current_phase}")
    assert final_state.status == "completed"


if __name__ == "__main__":
    main()
