from __future__ import annotations

from pydantic import BaseModel, Field

from orchestrator.state import RequirementCategory, RequirementSpec, TaskDAG
from orchestrator.tools.model_provider import _StructuredOutputMixin


class _FailingProvider(_StructuredOutputMixin):
    def complete_structured(self, system_prompt: str, user_prompt: str, response_model):
        return self._complete_structured_with_retry(system_prompt, user_prompt, response_model)

    def _invoke(self, system_prompt: str, user_prompt: str) -> str:
        del system_prompt, user_prompt
        raise RuntimeError("OpenRouter HTTP error 402: Payment Required")


class _SummaryModel(BaseModel):
    final_summary: str
    risks: list[str] = Field(default_factory=list)


def test_fallback_yields_valid_requirement_spec_on_provider_error() -> None:
    provider = _FailingProvider()

    result = provider.complete_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=RequirementSpec,
    )

    assert isinstance(result, RequirementSpec)
    assert result.category == RequirementCategory.AMBIGUOUS
    assert result.ambiguities
    assert "Provider fallback used" in result.ambiguities[0]
    assert "HTTP Error 402" not in result.ambiguities[0]


def test_fallback_injects_engineering_summary_shape() -> None:
    provider = _FailingProvider()

    result = provider.complete_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=_SummaryModel,
    )

    assert result.final_summary.startswith("## Implementation Plan and Rationale")
    assert result.risks
    assert "Provider fallback used" in result.risks[0]
    assert "HTTP Error 402" not in result.final_summary


def test_fallback_builds_valid_task_dag_on_provider_error() -> None:
    provider = _FailingProvider()

    result = provider.complete_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=TaskDAG,
    )

    assert isinstance(result, TaskDAG)
    assert result.tasks == []
    assert result.topological_batches() == []
