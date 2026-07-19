from __future__ import annotations

from pathlib import Path

from orchestrator.agents.risk_docs import REQUIRED_HEADERS, RiskDocsAgent
from orchestrator.state import (
    ArchitectureDesign,
    RequirementCategory,
    RequirementSpec,
    RunState,
    ValidationResult,
)
from orchestrator.tools.model_provider import FakeModelProvider


def test_risk_docs_agent_writes_summary_and_contains_required_headers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    summary = "\n\n".join(
        [
            "## Implementation Plan and Rationale\nPlanned iterative implementation.",
            "## Generated Artifacts\n- app/main.py\n- tests/test_main.py",
            "## Risks, Trade-offs, and Validation Approach\n- Risk: cache consistency.",
            "## Assumptions and Limitations\n- Assumes single region deployment.",
        ]
    )

    model = FakeModelProvider(
        canned_response={
            "risks": ["Cache invalidation risk", "Analytics lag under load"],
            "final_summary": summary,
        }
    )

    run_state = RunState(
        run_id="risk-docs-001",
        requirement=RequirementSpec(
            raw_text="Build a scalable URL shortener service with APIs, persistence, and analytics.",
            category=RequirementCategory.GREENFIELD,
            explicit_requirements=["Build URL shortener"],
            implicit_requirements=["Scale horizontally"],
            ambiguities=["SLOs missing"],
            ambiguity_score=0.3,
        ),
        design=ArchitectureDesign(
            components=["api", "service", "db"],
            data_model="ShortUrl(code, target)",
            api_contract_yaml="openapi: 3.0.0\ninfo:\n  title: URL API\n  version: 1.0.0\npaths: {}",
            tradeoffs=["counter vs hash"],
        ),
        validations=[
            ValidationResult(task_id="t1", passed=True, logs="ok", issues=[]),
            ValidationResult(task_id="t2", passed=False, logs="failed", issues=["flake error"]),
        ],
        current_phase="risk_docs",
        status="running",
    )

    updated = RiskDocsAgent().run(run_state, model)

    for header in REQUIRED_HEADERS:
        assert header in updated.final_summary

    docs_file = Path("docs") / "engineering_summary_build-a-scalable-url-shortener-service-with-apis-persistence-and-analytics.md"
    assert docs_file.exists()
    content = docs_file.read_text(encoding="utf-8")
    for header in REQUIRED_HEADERS:
        assert header in content


def test_risk_docs_agent_synthesizes_summary_when_headers_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    model = FakeModelProvider(
        canned_response={
            "risks": ["Cache invalidation risk"],
            "final_summary": "Model gave a short note without the required headers.",
        }
    )

    run_state = RunState(
        run_id="risk-docs-002",
        requirement=RequirementSpec(
            raw_text="Build a scalable URL shortener service with APIs, persistence, and analytics.",
            category=RequirementCategory.GREENFIELD,
            explicit_requirements=["Build URL shortener", "Provide APIs"],
            implicit_requirements=["Scale horizontally"],
            ambiguities=["SLOs missing"],
            ambiguity_score=0.3,
        ),
        design=ArchitectureDesign(
            components=["api", "service", "db"],
            data_model="ShortLink(code, target)",
            api_contract_yaml="openapi: 3.0.0\ninfo:\n  title: URL API\n  version: 1.0.0\npaths: {}",
            tradeoffs=["counter vs hash"],
        ),
        current_phase="risk_docs",
        status="running",
    )

    updated = RiskDocsAgent().run(run_state, model)

    assert "Analyze and decompose the requirement" in updated.final_summary
    assert "Design the architecture" in updated.final_summary
    assert "Generate code, APIs, and tests" in updated.final_summary
    assert "Provide trade-offs and a validation strategy" in updated.final_summary
