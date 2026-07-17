from __future__ import annotations

from orchestrator.state import RequirementSpec
from orchestrator.tools.model_provider import ModelProvider


class IntakeAgent:
	def run(self, requirement_text: str, model: ModelProvider) -> RequirementSpec:
		system_prompt = (
			"You are a senior requirements analyst for software delivery projects. "
			"Classify the incoming requirement into exactly one category: "
			"greenfield, brownfield, ambiguous, or test_or_docs. "
			"Extract explicit requirements in near-verbatim language from the user text. "
			"Infer reasonable implicit requirements from engineering best practices "
			"(for example: scalable implies horizontal scaling and load-balancing considerations). "
			"List concrete ambiguities that block design or implementation decisions. "
			"Return an ambiguity_score between 0 and 1 where 0 means fully clear and 1 means highly ambiguous."
		)

		user_prompt = (
			"Analyze this product/engineering requirement and return a structured result.\n\n"
			f"Requirement text:\n{requirement_text}"
		)

		return model.complete_structured(
			system_prompt=system_prompt,
			user_prompt=user_prompt,
			response_model=RequirementSpec,
		)
