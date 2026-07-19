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

		run_state.risks = response.risks
		try:
			run_state.final_summary = self._enforce_required_headers(response.final_summary)
		except ValueError as err:
			run_state.final_summary = self._compose_summary(run_state, response.final_summary, str(err))

		docs_dir = Path.cwd() / "docs"
		docs_dir.mkdir(parents=True, exist_ok=True)
		target = docs_dir / f"engineering_summary_{self._slugify(run_state.requirement.raw_text)}.md"
		target.write_text(run_state.final_summary, encoding="utf-8")

		return run_state

	def _compose_summary(self, run_state: RunState, model_summary: str, error_text: str) -> str:
		artifacts: list[str] = []
		if run_state.dag is not None:
			for task in run_state.dag.tasks:
				artifacts.extend(task.owned_files)
		artifacts = sorted(set(artifacts))[:20]
		validation_issues = sorted({issue for result in run_state.validations for issue in result.issues})
		requirement = run_state.requirement
		design = run_state.design
		risks = run_state.risks or ["Model output formatting instability under strict header constraints"]

		requirement_lines = [
			f"Requirement text: {requirement.raw_text}",
			f"Category: {requirement.category.value}",
			f"Explicit requirements: {', '.join(requirement.explicit_requirements) if requirement.explicit_requirements else 'N/A'}",
			f"Implicit requirements: {', '.join(requirement.implicit_requirements) if requirement.implicit_requirements else 'N/A'}",
		]
		if requirement.ambiguities:
			requirement_lines.append(f"Open ambiguities: {', '.join(requirement.ambiguities)}")

		design_lines = [
			f"Components: {', '.join(design.components) if design else 'N/A'}",
			f"Data model: {design.data_model if design else 'N/A'}",
			f"API contract: {design.api_contract_yaml if design else 'N/A'}",
		]
		if design and design.tradeoffs:
			design_lines.append(f"Trade-offs: {', '.join(design.tradeoffs)}")

		implementation_lines = [
			f"Artifacts: {', '.join(artifacts) if artifacts else 'No artifacts recorded'}",
			f"Tasks completed: {len(run_state.dag.tasks) if run_state.dag else 0}",
		]
		if run_state.dag and run_state.dag.tasks:
			implementation_lines.append(
				"Task breakdown: " + "; ".join(f"{task.id} ({task.title})" for task in run_state.dag.tasks[:8])
			)

		validation_lines = [
			"Validation strategy: pytest, py_compile, and pyflakes across task-owned files.",
			f"Validation issues: {', '.join(validation_issues) if validation_issues else 'No explicit validation issues captured'}",
			f"Fallback reason: {error_text}",
		]
		validation_lines.append(f"Risks: {', '.join(risks)}")

		return (
			"## Implementation Plan and Rationale\n"
			"Analyze and decompose the requirement:\n"
			+ "\n".join(f"- {line}" for line in requirement_lines)
			+ "\n\nDesign the architecture:\n"
			+ "\n".join(f"- {line}" for line in design_lines)
			+ "\n\nGenerate code, APIs, and tests:\n"
			+ "\n".join(f"- {line}" for line in implementation_lines)
			+ "\n\nProvide trade-offs and a validation strategy:\n"
			+ "\n".join(f"- {line}" for line in validation_lines)
			+ "\n\n## Generated Artifacts\n"
			+ ("\n".join(f"- {path}" for path in artifacts) if artifacts else "- No artifacts recorded")
			+ "\n\n## Risks, Trade-offs, and Validation Approach\n"
			+ "\n".join(f"- {risk}" for risk in risks)
			+ "\n"
			+ ("Validation Issues Observed:\n" + ("\n".join(f"- {issue}" for issue in validation_issues) if validation_issues else "- No explicit validation issues captured"))
			+ "\n\n## Assumptions and Limitations\n"
			+ "- Assumes the plain-text requirement can be decomposed into implementation tasks and validation checks.\n"
			+ "- Uses the current run state to summarize architecture, artifacts, and validation evidence.\n"
			+ "- Final summary is synthesized deterministically when model output is incomplete.\n"
			+ f"- Original risk_docs error: {error_text}\n\n"
			+ "Model Notes:\n"
			+ model_summary.strip()
		)

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
