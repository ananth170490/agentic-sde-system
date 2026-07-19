from __future__ import annotations

import re
import sys
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from orchestrator.agents.architect import ArchitectAgent
from orchestrator.agents.code_gen import CodeGenAgent
from orchestrator.agents.codebase_reasoning import CodebaseReasoningAgent
from orchestrator.agents.intake import IntakeAgent
from orchestrator.agents.risk_docs import RiskDocsAgent
from orchestrator.agents.task_decomposer import TaskDecomposerAgent
from orchestrator.agents.test_gen import TestGenAgent
from orchestrator.agents.validator import ValidationAgent
from orchestrator.gates.human_approval import clarify_gate_payload, merge_approval_gate_node, plan_approval_gate_node
from orchestrator.state import RequirementCategory, RunState, RunStateStore, TaskStatus, ValidationResult
from orchestrator.tools.model_provider import ModelProvider
from orchestrator.tools.sandbox_runner import SandboxRunner


class OrchestrationGraph:
	def __init__(
		self,
		model_provider: ModelProvider,
		store: RunStateStore | None = None,
		repo_root: str | None = None,
		generated_root: str | None = None,
	) -> None:
		self.model = model_provider
		self.store = store or RunStateStore()
		self.repo_root = Path(repo_root or Path.cwd()).resolve()
		self.generated_root = Path(generated_root or (Path.cwd() / "generated_projects")).resolve()

		self.intake_agent = IntakeAgent()
		self.codebase_reasoning_agent = CodebaseReasoningAgent()
		self.architect_agent = ArchitectAgent()
		self.task_decomposer_agent = TaskDecomposerAgent()
		self.code_gen_agent = CodeGenAgent()
		self.test_gen_agent = TestGenAgent()
		self.validator_agent = ValidationAgent()
		self.risk_docs_agent = RiskDocsAgent()
		self.sandbox_runner = SandboxRunner(python_executable=sys.executable)

		self.graph = self._build_graph()

	def invoke(self, state: RunState) -> RunState:
		result = self.graph.invoke(
			state,
			config={"configurable": {"thread_id": state.run_id}},
		)
		if isinstance(result, RunState):
			return result
		return RunState.model_validate(result)

	def resume(self, run_id: str) -> RunState:
		state = self.store.load(run_id)
		if state is None:
			raise ValueError(f"No run state found for run_id={run_id}")
		return self.invoke(state)

	def _persist(self, state: RunState) -> RunState:
		self.store.save(state)
		return state

	def _build_graph(self):
		builder = StateGraph(RunState)

		builder.add_node("intake", self._node_intake)
		builder.add_node("clarify_gate", self._node_clarify_gate)
		builder.add_node("codebase_reasoning", self._node_codebase_reasoning)
		builder.add_node("architect", self._node_architect)
		builder.add_node("task_decomposer", self._node_task_decomposer)
		builder.add_node("plan_approval_gate", self._node_plan_approval_gate)
		builder.add_node("plan_approval_wait", self._node_plan_approval_wait)
		builder.add_node("execute_dag", self._node_execute_dag)
		builder.add_node("risk_docs", self._node_risk_docs)
		builder.add_node("merge_approval_gate", self._node_merge_approval_gate)
		builder.add_node("merge_approval_wait", self._node_merge_approval_wait)
		builder.add_node("finalize", self._node_finalize)

		builder.add_conditional_edges(
			START,
			self._route_from_phase,
			{
				"intake": "intake",
				"clarify_gate": "clarify_gate",
				"codebase_reasoning": "codebase_reasoning",
				"architect": "architect",
				"task_decomposer": "task_decomposer",
				"plan_approval_gate": "plan_approval_gate",
				"plan_review": "plan_approval_gate",
				"execute_dag": "execute_dag",
				"risk_docs": "risk_docs",
				"merge_approval_gate": "merge_approval_gate",
				"finalize": "finalize",
			},
		)

		builder.add_conditional_edges(
			"intake",
			self._route_after_intake,
			{
				"clarify_gate": "clarify_gate",
				"codebase_reasoning": "codebase_reasoning",
			},
		)

		builder.add_conditional_edges(
			"clarify_gate",
			self._route_after_clarify_gate,
			{
				"wait": END,
				"codebase_reasoning": "codebase_reasoning",
			},
		)

		builder.add_edge("codebase_reasoning", "architect")
		builder.add_edge("architect", "task_decomposer")
		builder.add_edge("task_decomposer", "plan_approval_gate")
		builder.add_edge("plan_approval_gate", "plan_approval_wait")

		builder.add_conditional_edges(
			"execute_dag",
			self._route_after_execute_dag,
			{
				"wait": END,
				"risk_docs": "risk_docs",
			},
		)

		builder.add_edge("risk_docs", "merge_approval_gate")
		builder.add_edge("merge_approval_gate", "merge_approval_wait")
		builder.add_edge("finalize", END)

		return builder.compile(
			checkpointer=MemorySaver(),
			interrupt_before=["plan_approval_wait", "merge_approval_wait"],
		)

	def _route_from_phase(self, state: RunState) -> str:
		if state.current_phase == "clarify_gate":
			return "clarify_gate"

		if state.current_phase in {"plan_review", "plan_approval_gate"}:
			if state.human_feedback and state.human_feedback.strip():
				return "execute_dag"
			return "plan_approval_gate"

		if state.current_phase == "merge_approval_gate":
			if state.human_feedback and state.human_feedback.strip():
				return "finalize"
			return "merge_approval_gate"

		if state.current_phase in {
			"intake",
			"codebase_reasoning",
			"architect",
			"task_decomposer",
			"execute_dag",
			"risk_docs",
			"merge_approval_gate",
			"finalize",
		}:
			return state.current_phase

		if state.current_phase == "execute_dag_complete":
			return "risk_docs"

		return "intake"

	def _route_after_intake(self, state: RunState) -> str:
		if state.requirement.ambiguity_score > 0.5:
			return "clarify_gate"
		return "codebase_reasoning"

	def _route_after_clarify_gate(self, state: RunState) -> str:
		if state.awaiting_human:
			return "wait"
		return "codebase_reasoning"

	def _route_after_execute_dag(self, state: RunState) -> str:
		if state.status == "rejected":
			return "wait"
		if state.awaiting_human:
			return "wait"
		return "risk_docs"

	def _node_intake(self, state: RunState) -> RunState:
		state.current_phase = "intake"
		state.status = "running"
		state.requirement = self.intake_agent.run(state.requirement.raw_text, self.model)
		state.awaiting_human = False
		state.human_feedback = None
		state.review_payload = None
		return self._persist(state)

	def _node_clarify_gate(self, state: RunState) -> RunState:
		state.current_phase = "clarify_gate"
		if state.human_feedback and state.human_feedback.strip():
			state.awaiting_human = False
			state.status = "running"
			state.human_feedback = None
			state.review_payload = None
			state.requirement.ambiguity_score = min(state.requirement.ambiguity_score, 0.5)
		else:
			state.awaiting_human = True
			state.status = "awaiting_human"
			state.review_payload = clarify_gate_payload(state)
		return self._persist(state)

	def _node_codebase_reasoning(self, state: RunState) -> RunState:
		state.current_phase = "codebase_reasoning"
		state.status = "running"
		if state.requirement.category != RequirementCategory.BROWNFIELD:
			state.impacted_areas = []
			return self._persist(state)

		state.impacted_areas = self.codebase_reasoning_agent.run(
			spec=state.requirement,
			repo_root=str(self.repo_root),
		)
		return self._persist(state)

	def _node_architect(self, state: RunState) -> RunState:
		state.current_phase = "architect"
		state.status = "running"
		state.design = self.architect_agent.run(state.requirement, state.impacted_areas, self.model)
		return self._persist(state)

	def _node_task_decomposer(self, state: RunState) -> RunState:
		if state.design is None:
			raise ValueError("Cannot decompose tasks without architecture design")
		state.current_phase = "task_decomposer"
		state.status = "running"
		state.dag = self.task_decomposer_agent.run(state.requirement, state.design, self.model)
		return self._persist(state)

	def _node_plan_approval_gate(self, state: RunState) -> RunState:
		if state.human_feedback and state.human_feedback.strip():
			state.awaiting_human = False
			state.status = "running"
			state.human_feedback = None
			state.review_payload = None
			state.current_phase = "execute_dag"
		else:
			state = plan_approval_gate_node(state)
		return self._persist(state)

	def _node_plan_approval_wait(self, state: RunState) -> RunState:
		return self._persist(state)

	def _node_execute_dag(self, state: RunState) -> RunState:
		if state.dag is None:
			raise ValueError("Cannot execute DAG before task decomposition")
		if state.design is None:
			raise ValueError("Cannot execute DAG before architecture design")

		state.current_phase = "execute_dag"
		state.status = "running"
		state.awaiting_human = False
		state.human_feedback = None
		state.review_payload = None
		project_dir = self._project_dir_for_run(state.run_id, state.requirement.raw_text)

		for batch in state.dag.topological_batches():
			for task in batch:
				if task.status == TaskStatus.DONE:
					continue
				if task.status == TaskStatus.FAILED:
					return self._mark_run_failed(
						state=state,
						task=task,
						reason=f"Task already marked failed before execution: {task.id}",
						validation=state.validations[-1] if state.validations else None,
					)

				try:
					dependency_context = self._dependency_context(task_id=task.id, state=state)
					generated_files = self.code_gen_agent.run(
						task=task,
						spec=state.requirement,
						design=state.design,
						context_from_dependencies=dependency_context,
						model=self.model,
						project_dir=project_dir,
					)
					try:
						self.test_gen_agent.run(
							task=task,
							generated_files=generated_files,
							spec=state.requirement,
							model=self.model,
							project_dir=project_dir,
						)
					except ValueError as err:
						task.output_summary = f"Test generation warning: {err}"

					validation = self.validator_agent.run(task=task, project_dir=project_dir, sandbox=self.sandbox_runner)
					state.validations.append(validation)
				except Exception as err:
					task.status = TaskStatus.FAILED
					task.output_summary = f"Execution exception: {err}"
					return self._mark_run_failed(
						state=state,
						task=task,
						reason=f"Task {task.id} failed due to execution error: {err}",
						validation=state.validations[-1] if state.validations else None,
					)

				while not validation.passed:
					if task.retry_count >= 3:
						task.status = TaskStatus.FAILED
						task.output_summary = f"Validation failed after retries: {validation.issues}"
						return self._mark_run_failed(
							state=state,
							task=task,
							reason=f"Validation failed after 3 retries for task {task.id}: {validation.issues}",
							validation=validation,
						)

					task.retry_count += 1
					try:
						repaired_files = self.code_gen_agent.repair(
							task=task,
							validation_result=validation,
							spec=state.requirement,
							design=state.design,
							model=self.model,
						)
					except Exception as err:
						task.status = TaskStatus.FAILED
						task.output_summary = f"Repair exception: {err}"
						return self._mark_run_failed(
							state=state,
							task=task,
							reason=f"Repair failed for task {task.id}: {err}",
							validation=validation,
						)
					self._write_files(project_dir=project_dir, files=repaired_files)
					generated_files.update(repaired_files)
					try:
						self.test_gen_agent.run(
							task=task,
							generated_files=generated_files,
							spec=state.requirement,
							model=self.model,
							project_dir=project_dir,
						)
					except ValueError as err:
						task.output_summary = f"Test generation warning during repair: {err}"

					validation = self.validator_agent.run(task=task, project_dir=project_dir, sandbox=self.sandbox_runner)
					state.validations.append(validation)

				task.status = TaskStatus.DONE
				task.output_summary = "Validated successfully"

		state.current_phase = "execute_dag_complete"
		state.status = "running"
		state.awaiting_human = False
		return self._persist(state)

	def _mark_run_failed(self, state: RunState, task, reason: str, validation: ValidationResult | None = None) -> RunState:
		state.current_phase = "execute_dag"
		state.status = "rejected"
		state.awaiting_human = False
		state.review_payload = None
		state.rejection_reason = reason

		task_id = getattr(task, "id", "unknown-task")
		task_title = getattr(task, "title", "Unknown task")
		task_details = getattr(task, "output_summary", None) or reason
		validation_tail = ""
		if validation is not None and validation.logs:
			validation_tail = "\n\nRecent Validation Logs (tail):\n" + "\n".join(validation.logs.splitlines()[-20:])
		state.final_summary = (
			"## Execution Halted During DAG Phase\n"
			f"- Failed Task: {task_id} ({task_title})\n"
			f"- Failure Reason: {reason}\n\n"
			"## Engineering Assessment\n"
			"The run reached execution but failed on a task that could not be auto-repaired within retry limits.\n"
			"No further autonomous approvals can progress this run.\n\n"
			"## Actionable Next Steps\n"
			"1. Review generated files and test outputs for the failed task.\n"
			"2. Adjust task owned_files/contracts or prompt constraints for that task.\n"
			"3. Re-run from intake with the corrected task boundaries.\n\n"
			f"## Failure Context\n{task_details}{validation_tail}"
		)
		return self._persist(state)

	def _node_risk_docs(self, state: RunState) -> RunState:
		state.current_phase = "risk_docs"
		state.status = "running"
		try:
			state = self.risk_docs_agent.run(state, self.model)
		except Exception as err:
			state.risks = state.risks or [f"Risk documentation generation fallback triggered: {err}"]
			state.final_summary = self._fallback_engineering_summary(state, str(err))
		else:
			state.final_summary = self._compose_engineering_summary(state, state.final_summary)
		return self._persist(state)

	def _compose_engineering_summary(self, state: RunState, model_summary: str | None = None) -> str:
		requirement = state.requirement
		design = state.design
		tasks = state.dag.tasks if state.dag is not None else []
		artifacts = sorted({path for task in tasks for path in task.owned_files})
		validation_issues = sorted({issue for result in state.validations for issue in result.issues})
		risks = state.risks or []

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
			f"Tasks completed: {len(tasks)}",
		]
		if tasks:
			implementation_lines.append(
				"Task breakdown: " + "; ".join(f"{task.id} ({task.title})" for task in tasks[:8])
			)

		validation_lines = [
			"Validation strategy: pytest, py_compile, and pyflakes across task-owned files.",
			f"Validation issues: {', '.join(validation_issues) if validation_issues else 'No explicit validation issues captured'}",
		]
		if risks:
			validation_lines.append(f"Risks: {', '.join(risks)}")

		model_notes = f"\n\nModel Notes:\n{model_summary.strip()}" if model_summary and model_summary.strip() else ""

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
			+ model_notes
			+ "\n\n## Generated Artifacts\n"
			+ ("\n".join(f"- {path}" for path in artifacts) if artifacts else "- No artifacts recorded")
			+ "\n\n## Risks, Trade-offs, and Validation Approach\n"
			+ ("\n".join(f"- {risk}" for risk in risks) if risks else "- No explicit risks recorded")
			+ "\n"
			+ ("Validation Issues Observed:\n" + ("\n".join(f"- {issue}" for issue in validation_issues) if validation_issues else "- No explicit validation issues captured"))
			+ "\n\n## Assumptions and Limitations\n"
			+ "- Assumes the plain-text requirement can be decomposed into implementation tasks and validation checks.\n"
			+ "- Uses the current run state to summarize architecture, artifacts, and validation evidence.\n"
			+ "- Final summary is synthesized deterministically so it remains readable even when model output is partial."
			+ model_notes
		)

	def _fallback_engineering_summary(self, state: RunState, error_text: str) -> str:
		artifacts: list[str] = []
		if state.dag is not None:
			for task in state.dag.tasks:
				artifacts.extend(task.owned_files)
		artifacts = sorted(set(artifacts))[:20]

		validation_issues: list[str] = []
		for result in state.validations:
			validation_issues.extend(result.issues)

		artifacts_md = "\n".join(f"- {path}" for path in artifacts) or "- No artifacts recorded"
		risk_items = state.risks or ["Model output formatting instability under strict header constraints"]
		risk_md = "\n".join(f"- {risk}" for risk in risk_items)
		issues_md = "\n".join(f"- {issue}" for issue in sorted(set(validation_issues))[:10]) or "- No explicit validation issues captured"

		return (
			"## Implementation Plan and Rationale\n"
			"The run executed the intake, planning, and DAG workflow with automated gating. "
			"A fallback summary was generated because risk documentation formatting failed at runtime.\n\n"
			"## Generated Artifacts\n"
			f"{artifacts_md}\n\n"
			"## Risks, Trade-offs, and Validation Approach\n"
			f"{risk_md}\n"
			"Validation Issues Observed:\n"
			f"{issues_md}\n\n"
			"## Assumptions and Limitations\n"
			"- Assumes model outputs may occasionally violate strict formatting contracts.\n"
			"- Uses fallback summary synthesis to preserve run continuity.\n"
			f"- Original risk_docs error: {error_text}\n"
		)

	def _node_merge_approval_gate(self, state: RunState) -> RunState:
		if state.human_feedback and state.human_feedback.strip():
			state.awaiting_human = False
			state.status = "running"
			state.human_feedback = None
			state.review_payload = None
			state.current_phase = "finalize"
		else:
			state = merge_approval_gate_node(state)
		return self._persist(state)

	def _node_merge_approval_wait(self, state: RunState) -> RunState:
		return self._persist(state)

	def _node_finalize(self, state: RunState) -> RunState:
		state.current_phase = "completed"
		state.status = "completed"
		state.awaiting_human = False
		state.review_payload = None
		return self._persist(state)

	def _dependency_context(self, task_id: str, state: RunState) -> str:
		if state.dag is None:
			return ""
		task_map = {task.id: task for task in state.dag.tasks}
		target = task_map.get(task_id)
		if target is None:
			return ""

		parts: list[str] = []
		for dep_id in target.depends_on:
			dep_task = task_map.get(dep_id)
			if dep_task is None:
				continue
			parts.append(f"{dep_id}: {dep_task.output_summary or ''}")
		return "\n".join(parts)

	def _project_dir_for_run(self, run_id: str, requirement_text: str) -> str:
		slug = self._slugify(requirement_text)
		path = (self.generated_root / f"{slug}-{run_id[:8]}").resolve()
		path.mkdir(parents=True, exist_ok=True)
		return str(path)

	def _write_files(self, project_dir: str, files: dict[str, str]) -> None:
		base = Path(project_dir).resolve()
		for rel_path, content in files.items():
			target = base / rel_path
			target.parent.mkdir(parents=True, exist_ok=True)
			target.write_text(content, encoding="utf-8")

	def _extract_keywords(self, state: RunState) -> list[str]:
		raw_parts = state.requirement.explicit_requirements + state.requirement.implicit_requirements
		if not raw_parts:
			raw_parts = [state.requirement.raw_text]
		text = " ".join(raw_parts).lower()
		tokens = re.findall(r"[a-z]{4,}", text)
		seen: list[str] = []
		for token in tokens:
			if token not in seen:
				seen.append(token)
		return seen[:15]

	def _slugify(self, text: str) -> str:
		slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
		return slug[:80] or "generated-project"
