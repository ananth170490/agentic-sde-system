from __future__ import annotations

import re

from orchestrator.state import ImpactedArea, RequirementSpec
from orchestrator.tools.repo_index import RepoIndex


class CodebaseReasoningAgent:
	def run(self, spec: RequirementSpec, repo_root: str) -> list[ImpactedArea]:
		index = RepoIndex()
		index.build(repo_root)
		keywords = self._extract_keywords(spec)
		return index.find_impacted(keywords)

	def _extract_keywords(self, spec: RequirementSpec) -> list[str]:
		raw_parts = spec.explicit_requirements + spec.implicit_requirements
		if not raw_parts:
			raw_parts = [spec.raw_text]
		text = " ".join(raw_parts).lower()
		tokens = re.findall(r"[a-z]{4,}", text)
		seen: list[str] = []
		for token in tokens:
			if token not in seen:
				seen.append(token)
		return seen[:20]
