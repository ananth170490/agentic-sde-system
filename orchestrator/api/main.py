from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from orchestrator.graph import OrchestrationGraph
from orchestrator.state import RequirementCategory, RequirementSpec, RunState, RunStateStore
from orchestrator.tools.model_provider import ModelProvider, build_model_provider_from_env


_DEMO_PROMPTS = {
	"url_shortener": "Build a scalable URL shortener service with APIs, persistence, and analytics.",
	"task_manager": "Create a task management REST API with authentication, PostgreSQL persistence, and activity audit logs.",
	"inventory": "Build an inventory service with CRUD APIs, low-stock alerts, and daily summary analytics.",
}


def _is_demo_mode_enabled() -> bool:
	return os.getenv("DEMO_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}


def _pick_demo_profile(raw_text: str) -> str:
	normalized = raw_text.strip().lower()
	for profile, prompt in _DEMO_PROMPTS.items():
		if normalized == prompt.lower():
			return profile
	if "url shortener" in normalized:
		return "url_shortener"
	if "inventory" in normalized:
		return "inventory"
	if "task" in normalized and "api" in normalized:
		return "task_manager"
	return "url_shortener"


def _demo_requirement_for(profile: str, raw_text: str) -> RequirementSpec:
	if profile == "task_manager":
		return RequirementSpec(
			raw_text=raw_text,
			category=RequirementCategory.GREENFIELD,
			explicit_requirements=[
				"Task CRUD APIs",
				"Authentication",
				"PostgreSQL persistence",
				"Audit activity logs",
			],
			implicit_requirements=[
				"Role-based access",
				"Pagination and filtering",
				"Structured error responses",
			],
		)
	if profile == "inventory":
		return RequirementSpec(
			raw_text=raw_text,
			category=RequirementCategory.GREENFIELD,
			explicit_requirements=[
				"Inventory CRUD APIs",
				"Low-stock alerts",
				"Daily summary analytics",
			],
			implicit_requirements=[
				"Threshold-based alert policy",
				"Idempotent updates",
				"Operational metrics",
			],
		)
	return RequirementSpec(
		raw_text=raw_text,
		category=RequirementCategory.GREENFIELD,
		explicit_requirements=[
			"URL shortening API",
			"Persistence layer",
			"Click analytics",
		],
		implicit_requirements=[
			"Scalable API nodes",
			"Collision-safe short codes",
			"Track redirect counters",
		],
	)


def _demo_plan_review_payload(profile: str, requirement: RequirementSpec) -> str:
	if profile == "task_manager":
		design = {
			"components": ["fastapi-service", "postgres-db", "audit-worker"],
			"data_model": "users, tasks, task_events, audit_log",
			"api_contract_yaml": "openapi: 3.0.3\\npaths:\\n  /api/v1/tasks: {}",
			"tradeoffs": [
				"JWT vs session cookies: choose JWT for API-first integrations.",
				"Sync vs async audit writes: choose async worker for lower request latency.",
			],
		}
		tasks = [
			{"id": "T1", "title": "Auth + DB schema"},
			{"id": "T2", "title": "Task CRUD endpoints"},
			{"id": "T3", "title": "Audit logging + tests"},
		]
	elif profile == "inventory":
		design = {
			"components": ["inventory-api", "postgres-db", "alert-scheduler"],
			"data_model": "items, stock_movements, alert_rules, daily_rollups",
			"api_contract_yaml": "openapi: 3.0.3\\npaths:\\n  /api/v1/items: {}",
			"tradeoffs": [
				"Cron alerts vs stream processing: choose cron for MVP simplicity.",
				"Strict transactions vs eventual consistency: choose strict updates for inventory integrity.",
			],
		}
		tasks = [
			{"id": "T1", "title": "Inventory schema + repository"},
			{"id": "T2", "title": "CRUD + stock mutation APIs"},
			{"id": "T3", "title": "Low-stock alerts + analytics endpoint"},
		]
	else:
		design = {
			"components": ["fastapi-api", "sqlite-or-postgres-store", "analytics-service"],
			"data_model": "url_mappings, click_events",
			"api_contract_yaml": "openapi: 3.0.3\\npaths:\\n  /api/v1/shorten: {}",
			"tradeoffs": [
				"Random code vs counter: choose random code for stateless scaling.",
				"Sync analytics writes vs async queue: choose sync for demo simplicity.",
			],
		}
		tasks = [
			{"id": "T1", "title": "Core shorten + resolve APIs"},
			{"id": "T2", "title": "Persistence + analytics endpoint"},
			{"id": "T3", "title": "Tests + docs"},
		]

	payload = {
		"phase": "plan_review",
		"requirement": requirement.model_dump(),
		"design": design,
		"dag": {"tasks": tasks},
	}
	return json.dumps(payload, indent=2)


def _demo_merge_review_payload(profile: str, requirement: RequirementSpec) -> str:
	payload = {
		"phase": "merge_review",
		"summary": f"Demo mode completed deterministic execution path for profile '{profile}'.",
		"artifacts": [
			"generated_projects/url-shortener/app/main.py",
			"generated_projects/url-shortener/app/store.py",
			"generated_projects/url-shortener/tests/test_api_core.py",
		],
		"risks": [
			"Demo output is deterministic and not model-generated.",
			"No live code synthesis in DEMO_MODE.",
		],
		"requirement": requirement.model_dump(),
	}
	return json.dumps(payload, indent=2)


def _create_demo_state(run_id: str, req_text: str) -> RunState:
	profile = _pick_demo_profile(req_text)
	requirement = _demo_requirement_for(profile, req_text)
	state = RunState(
		run_id=run_id,
		requirement=requirement,
		current_phase="plan_review",
		status="awaiting_human",
		awaiting_human=True,
		review_payload=_demo_plan_review_payload(profile, requirement),
	)
	return state


def _demo_advance_state(state: RunState, feedback: str | None) -> RunState:
	profile = _pick_demo_profile(state.requirement.raw_text)
	state.human_feedback = feedback or "approved"
	if state.current_phase == "plan_review":
		state.current_phase = "merge_approval_gate"
		state.status = "awaiting_human"
		state.awaiting_human = True
		state.review_payload = _demo_merge_review_payload(profile, state.requirement)
		return state

	if state.current_phase == "merge_approval_gate":
		state.current_phase = "completed"
		state.status = "completed"
		state.awaiting_human = False
		state.review_payload = None
		state.final_summary = (
			"Demo mode run completed successfully. "
			"For production behavior, disable DEMO_MODE and configure a real model provider."
		)
		return state

	state.status = "completed"
	state.awaiting_human = False
	state.current_phase = "completed"
	state.review_payload = None
	return state


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

_LIVE_DEMO_UI_PATH = (Path(__file__).resolve().parents[2] / "docs" / "live_demo_ui.html").resolve()
_LIVE_DEMO_UI_FALLBACK = """<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<title>Agentic SDE Live Demo Runner</title>
</head>
<body>
	<main>
		<h1>Agentic SDE Live Demo Runner</h1>
		<p>The live demo UI asset could not be loaded from disk, but the backend is reachable.</p>
	</main>
</body>
</html>
"""


@app.post("/requirements")
def create_requirement(
	req: RequirementRequest,
	graph: OrchestrationGraph = Depends(get_orchestration_graph),
):
	if _is_demo_mode_enabled():
		run_id = str(uuid4())
		state = _create_demo_state(run_id=run_id, req_text=req.text)
		graph.store.save(state)
		response = {"run_id": state.run_id, "status": state.status}
		if state.review_payload:
			response["review_payload"] = state.review_payload
		return response

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

	if _is_demo_mode_enabled():
		state = _demo_advance_state(state=state, feedback=req.feedback)
		graph.store.save(state)
		response = {"run_id": state.run_id, "status": state.status}
		if state.review_payload:
			response["review_payload"] = state.review_payload
		return response

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


@app.get("/live-demo", include_in_schema=False)
def live_demo_ui() -> HTMLResponse:
	if _LIVE_DEMO_UI_PATH.exists():
		return HTMLResponse(_LIVE_DEMO_UI_PATH.read_text(encoding="utf-8"))
	return HTMLResponse(_LIVE_DEMO_UI_FALLBACK)
