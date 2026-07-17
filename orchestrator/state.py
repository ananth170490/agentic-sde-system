from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


class RequirementCategory(str, Enum):
	GREENFIELD = "greenfield"
	BROWNFIELD = "brownfield"
	AMBIGUOUS = "ambiguous"
	TEST_OR_DOCS = "test_or_docs"


class TaskStatus(str, Enum):
	PENDING = "pending"
	RUNNING = "running"
	BLOCKED = "blocked"
	DONE = "done"
	FAILED = "failed"


class RequirementSpec(BaseModel):
	raw_text: str
	category: RequirementCategory
	explicit_requirements: list[str] = Field(default_factory=list)
	implicit_requirements: list[str] = Field(default_factory=list)
	ambiguities: list[str] = Field(default_factory=list)
	ambiguity_score: float = 0.0


class ImpactedArea(BaseModel):
	module: str
	files: list[str] = Field(default_factory=list)
	reason: str


class ArchitectureDesign(BaseModel):
	components: list[str] = Field(default_factory=list)
	data_model: str
	api_contract_yaml: str
	tradeoffs: list[str] = Field(default_factory=list)


class Task(BaseModel):
	id: str
	title: str
	description: str
	depends_on: list[str] = Field(default_factory=list)
	status: TaskStatus = TaskStatus.PENDING
	owned_files: list[str] = Field(default_factory=list)
	output_summary: Optional[str] = None
	retry_count: int = 0


class TaskDAG(BaseModel):
	tasks: list[Task] = Field(default_factory=list)

	def next_runnable_tasks(self) -> list[Task]:
		status_by_id = {task.id: task.status for task in self.tasks}
		runnable: list[Task] = []
		for task in self.tasks:
			if task.status != TaskStatus.PENDING:
				continue
			if all(status_by_id.get(dep) == TaskStatus.DONE for dep in task.depends_on):
				runnable.append(task)
		return runnable

	def topological_batches(self) -> list[list[Task]]:
		task_by_id = {task.id: task for task in self.tasks}
		in_degree = {task.id: 0 for task in self.tasks}
		children: dict[str, list[str]] = {task.id: [] for task in self.tasks}

		for task in self.tasks:
			for dep in task.depends_on:
				if dep not in task_by_id:
					raise ValueError(f"Task '{task.id}' depends on unknown task '{dep}'")
				in_degree[task.id] += 1
				children[dep].append(task.id)

		ready = sorted(task_id for task_id, degree in in_degree.items() if degree == 0)
		batches: list[list[Task]] = []
		visited_count = 0

		while ready:
			batch_ids = ready
			batch = [task_by_id[task_id] for task_id in batch_ids]
			batches.append(batch)
			visited_count += len(batch_ids)

			next_ready: list[str] = []
			for task_id in batch_ids:
				for child_id in children[task_id]:
					in_degree[child_id] -= 1
					if in_degree[child_id] == 0:
						next_ready.append(child_id)
			ready = sorted(next_ready)

		if visited_count != len(self.tasks):
			raise ValueError("Circular dependency detected in TaskDAG")

		return batches


class ValidationResult(BaseModel):
	task_id: str
	passed: bool
	logs: str
	issues: list[str] = Field(default_factory=list)


class RunState(BaseModel):
	model_config = ConfigDict(use_enum_values=True)

	run_id: str
	requirement: RequirementSpec
	impacted_areas: list[ImpactedArea] = Field(default_factory=list)
	design: Optional[ArchitectureDesign] = None
	dag: Optional[TaskDAG] = None
	validations: list[ValidationResult] = Field(default_factory=list)
	risks: list[str] = Field(default_factory=list)
	final_summary: Optional[str] = None
	current_phase: str
	status: str = "running"
	awaiting_human: bool = False
	human_feedback: Optional[str] = None
	review_payload: Optional[str] = None
	rejection_reason: Optional[str] = None


Base = declarative_base()


class _RunStateRow(Base):
	__tablename__ = "run_states"

	run_id = Column(String(255), primary_key=True)
	state_json = Column(Text, nullable=False)


class RunStateStore:
	def __init__(self, sqlite_path: str = "orchestrator_runs.db") -> None:
		self._engine = create_engine(f"sqlite:///{sqlite_path}", future=True)
		self._session_factory = sessionmaker(bind=self._engine, future=True)
		Base.metadata.create_all(self._engine)

	def save(self, state: RunState) -> None:
		payload = state.model_dump_json()
		with self._session_factory() as session:
			row = session.get(_RunStateRow, state.run_id)
			if row is None:
				row = _RunStateRow(run_id=state.run_id, state_json=payload)
				session.add(row)
			else:
				row.state_json = payload
			session.commit()

	def load(self, run_id: str) -> Optional[RunState]:
		with self._session_factory() as session:
			row = session.get(_RunStateRow, run_id)
			if row is None:
				return None
			return RunState.model_validate_json(row.state_json)
