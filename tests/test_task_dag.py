import pytest

from orchestrator.state import Task, TaskDAG


def test_topological_batches_parallel_groups() -> None:
    dag = TaskDAG(
        tasks=[
            Task(id="schema-001", title="Schema", description="Define schema"),
            Task(
                id="persistence-002",
                title="Persistence",
                description="Implement storage",
                depends_on=["schema-001"],
            ),
            Task(
                id="api-003",
                title="API",
                description="Implement API",
                depends_on=["persistence-002"],
            ),
            Task(
                id="analytics-004",
                title="Analytics",
                description="Implement analytics",
                depends_on=["persistence-002"],
            ),
            Task(
                id="tests-api-005",
                title="API tests",
                description="Test API",
                depends_on=["api-003"],
            ),
            Task(
                id="tests-analytics-006",
                title="Analytics tests",
                description="Test analytics",
                depends_on=["analytics-004"],
            ),
            Task(
                id="docs-007",
                title="Docs",
                description="Write docs",
                depends_on=[
                    "api-003",
                    "analytics-004",
                    "tests-api-005",
                    "tests-analytics-006",
                ],
            ),
        ]
    )

    batches = dag.topological_batches()
    batch_ids = [[task.id for task in batch] for batch in batches]

    assert batch_ids[0] == ["schema-001"]
    assert batch_ids[1] == ["persistence-002"]
    assert batch_ids[2] == ["analytics-004", "api-003"]
    assert batch_ids[3] == ["tests-analytics-006", "tests-api-005"]
    assert batch_ids[4] == ["docs-007"]


def test_topological_batches_cycle_detection() -> None:
    dag = TaskDAG(
        tasks=[
            Task(id="a-001", title="A", description="A", depends_on=["c-003"]),
            Task(id="b-002", title="B", description="B", depends_on=["a-001"]),
            Task(id="c-003", title="C", description="C", depends_on=["b-002"]),
        ]
    )

    with pytest.raises(ValueError, match="Circular dependency"):
        dag.topological_batches()
