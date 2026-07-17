from __future__ import annotations

from orchestrator.state import ArchitectureDesign, RequirementSpec, TaskDAG
from orchestrator.tools.model_provider import ModelProvider


class TaskDecomposerAgent:
	def run(
		self,
		spec: RequirementSpec,
		design: ArchitectureDesign,
		model: ModelProvider,
	) -> TaskDAG:
		system_prompt = (
			"You are a staff engineer planning execution. Break design into 6-12 concrete engineering tasks. "
			"Each task must have: id, title, description, depends_on, status, owned_files, output_summary, retry_count. "
			"Use explicit task ids and explicit dependency references by id. "
			"Use practical sequencing patterns, for example schema then persistence, then APIs and analytics, then tests/docs. "
			"Tests tasks must depend on their corresponding implementation task. "
			"A docs task should depend on all implementation and test tasks. "
			"owned_files must be specific file paths and should avoid overlap across tasks to reduce collisions. "
			"Set status to pending for all tasks and retry_count to 0."
		)

		user_prompt = (
			"Generate a TaskDAG for this requirement and architecture.\n\n"
			f"Requirement spec JSON:\n{spec.model_dump_json(indent=2)}\n\n"
			f"Architecture design JSON:\n{design.model_dump_json(indent=2)}"
		)

		return model.complete_structured(
			system_prompt=system_prompt,
			user_prompt=user_prompt,
			response_model=TaskDAG,
		)
