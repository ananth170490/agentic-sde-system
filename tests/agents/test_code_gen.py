import pytest

from orchestrator.agents.code_gen import CodeGenAgent
from orchestrator.state import ArchitectureDesign, RequirementSpec, RequirementCategory, Task
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


def _design() -> ArchitectureDesign:
    return ArchitectureDesign(
        components=["api", "service", "db"],
        data_model="ShortLink(id, code, target_url)",
        api_contract_yaml="openapi: 3.0.0\ninfo:\n  title: URL API\n  version: 1.0.0\npaths: {}",
        tradeoffs=["A vs B: choose A"],
    )


def test_code_gen_rejects_writes_outside_owned_files(tmp_path) -> None:
    task = Task(
        id="api-003",
        title="Build API",
        description="Implement API endpoints",
        owned_files=["app/api.py"],
    )
    model = FakeModelProvider(
        canned_response={
            "files": {
                "app/api.py": "def ok() -> None:\n    pass\n",
                "app/evil.py": "print('outside scope')\n",
            }
        }
    )

    agent = CodeGenAgent()
    with pytest.raises(ValueError, match="outside owned_files"):
        agent.run(
            task=task,
            spec=_spec(),
            design=_design(),
            context_from_dependencies="",
            model=model,
            project_dir=str(tmp_path / "generated"),
        )
