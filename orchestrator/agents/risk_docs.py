from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from orchestrator.state import RunState
from orchestrator.tools.model_provider import ModelProvider


REQUIRED_HEADERS = [
	"## Implementation Plan and Rationale",
	"## Generated Artifacts",
	"## Risks, Trade-offs, and Validation Approach",
	"## Assumptions and Limitations",
]


class _RiskDocsResponse(BaseModel):
	risks: list[str] = Field(default_factory=list)
	final_summary: str


class RiskDocsAgent:
	def run(self, run_state: RunState, model: ModelProvider) -> RunState:
		system_prompt = (
			"You are a principal engineer preparing final delivery notes. "
			"Produce concrete risks/trade-offs/failure scenarios from the architecture and validations. "
			"Return a markdown summary with exactly these section headers in this order: "
			"## Implementation Plan and Rationale, "
			"## Generated Artifacts, "
			"## Risks, Trade-offs, and Validation Approach, "
			"## Assumptions and Limitations."
		)

		validation_issues = [issue for result in run_state.validations for issue in result.issues]
		user_prompt = (
			"Generate final project risk and engineering summary output for this run.\n\n"
			f"Requirement:\n{run_state.requirement.model_dump_json(indent=2)}\n\n"
			f"Design:\n{run_state.design.model_dump_json(indent=2) if run_state.design else '{}'}\n\n"
			f"Task DAG:\n{run_state.dag.model_dump_json(indent=2) if run_state.dag else '{}'}\n\n"
			f"Validation issues:\n{validation_issues}\n\n"
			"Ensure the final summary uses the required headers exactly."
		)

		response = model.complete_structured(
			system_prompt=system_prompt,
			user_prompt=user_prompt,
			response_model=_RiskDocsResponse,
		)

		final_summary = self._enforce_required_headers(response.final_summary)
		run_state.risks = response.risks
		run_state.final_summary = final_summary

		docs_dir = Path.cwd() / "docs"
		docs_dir.mkdir(parents=True, exist_ok=True)
		target = docs_dir / f"engineering_summary_{self._slugify(run_state.requirement.raw_text)}.md"
		target.write_text(final_summary, encoding="utf-8")

		return run_state

	def _enforce_required_headers(self, summary: str) -> str:
		text = summary.strip()
		for header in REQUIRED_HEADERS:
			if header not in text:
				raise ValueError(f"Missing required header in final_summary: {header}")

		positions = [text.index(header) for header in REQUIRED_HEADERS]
		if positions != sorted(positions):
			raise ValueError("final_summary headers are not in the required order")
		return text

	def _slugify(self, text: str) -> str:
		slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
		return slug[:80] or "generated-project"
