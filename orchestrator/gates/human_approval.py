from __future__ import annotations

import json

from orchestrator.state import RunState


def plan_approval_gate_node(state: RunState) -> RunState:
	state.current_phase = "plan_review"
	state.awaiting_human = True
	state.status = "awaiting_human"
	state.review_payload = _build_review_payload(state, phase="plan_review")
	return state


def merge_approval_gate_node(state: RunState) -> RunState:
	state.current_phase = "merge_approval_gate"
	state.awaiting_human = True
	state.status = "awaiting_human"
	state.review_payload = _build_review_payload(state, phase="merge_review")
	return state


def clarify_gate_payload(state: RunState) -> str:
	questions = state.requirement.ambiguities or [
		"What endpoint(s) or workflows must be optimized first?",
		"What measurable latency/SLO target should define success?",
		"What current baseline and traffic profile should we optimize for?",
	]
	return json.dumps(
		{
			"phase": "clarify_gate",
			"requirement": state.requirement.raw_text,
			"clarifying_questions": questions,
		},
		indent=2,
	)


def _build_review_payload(state: RunState, phase: str) -> str:
	if phase == "plan_review":
		dag_payload = state.dag.model_dump() if state.dag is not None else {"tasks": []}
		return json.dumps(
			{
				"phase": phase,
				"requirement": state.requirement.model_dump(),
				"design": state.design.model_dump() if state.design else None,
				"dag": dag_payload,
			},
			indent=2,
		)

	return json.dumps(
		{
			"phase": phase,
			"design": state.design.model_dump() if state.design else None,
			"risks": state.risks,
			"final_summary": state.final_summary,
		},
		indent=2,
	)
