from __future__ import annotations

from orchestrator.state import ArchitectureDesign, ImpactedArea, RequirementSpec
from orchestrator.tools.model_provider import ModelProvider


class ArchitectAgent:
	def run(
		self,
		spec: RequirementSpec,
		impacted_areas: list[ImpactedArea],
		model: ModelProvider,
	) -> ArchitectureDesign:
		system_prompt = (
			"You are a senior software architect. Produce a practical architecture design for implementation. "
			"You must return: (1) components list, (2) a concise but complete data model description, "
			"(3) a full OpenAPI 3.0 YAML document string in api_contract_yaml covering all required endpoints, "
			"and (4) 3-5 explicit tradeoffs with decision rationale. "
			"Tradeoffs must follow this pattern: option A vs option B, chosen option, and reason."
		)

		user_prompt = (
			"Design the system using the requirement spec and impacted areas context.\n\n"
			f"Requirement spec JSON:\n{spec.model_dump_json(indent=2)}\n\n"
			f"Impacted areas JSON:\n{[area.model_dump() for area in impacted_areas]}\n\n"
			"Ensure the OpenAPI YAML is valid OpenAPI 3.0 structure and includes paths, methods, request/response schemas, "
			"and error responses required for the described system."
		)

		return model.complete_structured(
			system_prompt=system_prompt,
			user_prompt=user_prompt,
			response_model=ArchitectureDesign,
		)
