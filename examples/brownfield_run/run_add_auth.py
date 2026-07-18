from __future__ import annotations

import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from orchestrator.agents.codebase_reasoning import CodebaseReasoningAgent
from orchestrator.state import RequirementCategory, RequirementSpec
from orchestrator.tools.model_provider import FakeModelProvider


REQUIREMENT_TEXT = "Add JWT-based authentication to the notes API, protecting all write endpoints"


def main() -> None:
    workspace_root = WORKSPACE_ROOT
    fixture_repo = workspace_root / "examples" / "brownfield_run" / "fixture_service"

    intake_model = FakeModelProvider(
        canned_response={
            "raw_text": REQUIREMENT_TEXT,
            "category": "brownfield",
            "explicit_requirements": [
                "Add JWT-based authentication to the notes API",
                "Protect all write endpoints",
            ],
            "implicit_requirements": [
                "Validate JWT token signatures",
                "Return 401 for missing/invalid tokens",
                "Keep read endpoints accessible unless otherwise specified",
            ],
            "ambiguities": [
                "JWT issuer/audience requirements are unspecified",
                "Token expiration and refresh strategy are unspecified",
            ],
            "ambiguity_score": 0.35,
        }
    )

    spec = intake_model.complete_structured(
        system_prompt="Classify requirement",
        user_prompt=REQUIREMENT_TEXT,
        response_model=RequirementSpec,
    )

    print(f"Requirement category: {spec.category}")
    assert spec.category == RequirementCategory.BROWNFIELD

    reasoning = CodebaseReasoningAgent()
    impacted_areas = reasoning.run(spec=spec, repo_root=str(fixture_repo))

    print("\nImpacted areas:")
    for area in impacted_areas:
        print(f"- module={area.module}, files={area.files}, reason={area.reason}")

    impacted_files = {file for area in impacted_areas for file in area.files}
    assert "app.py" in impacted_files

    app_source = (fixture_repo / "app.py").read_text(encoding="utf-8")
    assert "@app.post" in app_source and "@app.put" in app_source

    print("\nBrownfield verification passed.")


if __name__ == "__main__":
    main()
