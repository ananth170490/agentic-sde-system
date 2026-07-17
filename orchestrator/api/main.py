from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator.graph import OrchestrationGraph
from orchestrator.state import RequirementCategory, RequirementSpec, RunState, RunStateStore
from orchestrator.tools.model_provider import ModelProvider, build_model_provider_from_env


class RequirementRequest(BaseModel):
	text: str


class ApproveRequest(BaseModel):
	feedback: str | None = None


class RejectRequest(BaseModel):
	reason: str


def get_store() -> RunStateStore:
	return RunStateStore(sqlite_path=str((Path.cwd() / "orchestrator_runs.db").resolve()))


def get_model_provider() -> ModelProvider:
	return build_model_provider_from_env()


@lru_cache(maxsize=1)
def get_orchestration_graph() -> OrchestrationGraph:
	return OrchestrationGraph(
		model_provider=get_model_provider(),
		store=get_store(),
		repo_root=str(Path.cwd()),
		generated_root=str((Path.cwd() / "generated_projects").resolve()),
	)


app = FastAPI(title="Agentic SDE Orchestrator API")


@app.post("/requirements")
def create_requirement(
	req: RequirementRequest,
	graph: OrchestrationGraph = Depends(get_orchestration_graph),
):
	run_id = str(uuid4())
	initial_state = RunState(
		run_id=run_id,
		requirement=RequirementSpec(
			raw_text=req.text,
			category=RequirementCategory.AMBIGUOUS,
			explicit_requirements=[],
			implicit_requirements=[],
			ambiguities=[],
			ambiguity_score=1.0,
		),
		current_phase="intake",
		status="running",
	)

	state = graph.invoke(initial_state)
	response = {"run_id": state.run_id, "status": state.status}
	if state.review_payload:
		response["review_payload"] = state.review_payload
	return response


@app.get("/runs/{run_id}")
def get_run(
	run_id: str,
	graph: OrchestrationGraph = Depends(get_orchestration_graph),
):
	state = graph.store.load(run_id)
	if state is None:
		raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
	return state.model_dump()


@app.post("/runs/{run_id}/approve")
def approve_run(
	run_id: str,
	req: ApproveRequest,
	graph: OrchestrationGraph = Depends(get_orchestration_graph),
):
	state = graph.store.load(run_id)
	if state is None:
		raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
	if state.status == "rejected":
		raise HTTPException(status_code=400, detail="Cannot approve a rejected run")

	state.human_feedback = req.feedback or "approved"
	state.awaiting_human = False
	state.status = "running"

	if state.current_phase == "plan_review":
		state.current_phase = "execute_dag"
	elif state.current_phase == "merge_approval_gate":
		state.current_phase = "finalize"

	updated = graph.invoke(state)
	response = {"run_id": updated.run_id, "status": updated.status}
	if updated.review_payload:
		response["review_payload"] = updated.review_payload
	return response


@app.post("/runs/{run_id}/reject")
def reject_run(
	run_id: str,
	req: RejectRequest,
	graph: OrchestrationGraph = Depends(get_orchestration_graph),
):
	state = graph.store.load(run_id)
	if state is None:
		raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

	state.status = "rejected"
	state.rejection_reason = req.reason
	state.awaiting_human = False
	state.review_payload = None
	graph.store.save(state)
	return {"run_id": state.run_id, "status": state.status, "reason": state.rejection_reason}
