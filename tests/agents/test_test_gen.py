import pytest

from orchestrator.agents.test_gen import TestGenAgent
from orchestrator.state import RequirementCategory, RequirementSpec, Task
from orchestrator.tools.model_provider import FakeModelProvider


def _spec() -> RequirementSpec:
    return RequirementSpec(
        raw_text="Build a scalable URL shortener service with APIs, persistence, and analytics.",
        category=RequirementCategory.GREENFIELD,
        explicit_requirements=["Build URL shortener"],
        implicit_requirements=["Scale horizontally"],
        ambiguities=["SLA not defined"],
        ambiguity_score=0.4,
    )


def test_test_gen_rejects_writes_outside_owned_files(tmp_path) -> None:
    task = Task(
        id="tests-api-004",
        title="API tests",
        description="Write API tests",
        owned_files=["tests/test_api.py"],
    )
    model = FakeModelProvider(
        canned_response={
            "files": {
                "tests/test_api.py": "def test_ok() -> None:\n    assert True\n",
                "tests/test_forbidden.py": "def test_bad() -> None:\n    assert False\n",
            }
        }
    )

    agent = TestGenAgent()
    with pytest.raises(ValueError, match="outside owned_files"):
        agent.run(
            task=task,
            generated_files={"app/api.py": "def x() -> None:\n    pass\n"},
            spec=_spec(),
            model=model,
            project_dir=str(tmp_path / "generated"),
        )
