from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from orchestrator.state import RequirementSpec, Task
from orchestrator.tools.model_provider import ModelProvider


class _GeneratedTestsResponse(BaseModel):
	files: dict[str, str] = Field(default_factory=dict)


class TestGenAgent:
	def run(
		self,
		task: Task,
		generated_files: dict[str, str],
		spec: RequirementSpec,
		model: ModelProvider,
		project_dir: str | None = None,
	) -> dict[str, str]:
		system_prompt = (
			"You are a senior test engineer. Generate pytest-based tests that cover both unit and integration-level "
			"behavior described in the task. Keep tests deterministic and implementation-aware."
		)

		user_prompt = (
			"Generate pytest test files for this task.\n\n"
			f"Task JSON:\n{task.model_dump_json(indent=2)}\n\n"
			f"Requirement spec JSON:\n{spec.model_dump_json(indent=2)}\n\n"
			f"Generated source files JSON:\n{generated_files}\n\n"
			f"You may only write these files:\n{task.owned_files}"
		)

		try:
			response = model.complete_structured(
				system_prompt=system_prompt,
				user_prompt=user_prompt,
				response_model=_GeneratedTestsResponse,
			)
		except Exception:
			response = _GeneratedTestsResponse(files={})

		normalized_allowed = {self._normalize_rel_path(path) for path in task.owned_files}
		for file_path in response.files:
			normalized = self._normalize_rel_path(file_path)
			if normalized not in normalized_allowed and not self._is_allowed_test_file(normalized):
				raise ValueError(
					f"TestGenAgent attempted write outside owned_files: '{file_path}' not in {sorted(normalized_allowed)}"
				)

		target_project_dir = self._resolve_project_dir(spec, project_dir)
		self._write_files(target_project_dir, response.files)
		return response.files

	def _resolve_project_dir(self, spec: RequirementSpec, project_dir: str | None) -> Path:
		if project_dir:
			return Path(project_dir).resolve()
		slug = self._slugify(spec.raw_text)
		return (Path.cwd() / "generated_projects" / slug).resolve()

	def _write_files(self, project_dir: Path, files: dict[str, str]) -> None:
		project_dir.mkdir(parents=True, exist_ok=True)
		for rel_path, content in files.items():
			normalized = self._normalize_rel_path(rel_path)
			target = project_dir / normalized
			target.parent.mkdir(parents=True, exist_ok=True)
			target.write_text(content, encoding="utf-8")

	def _normalize_rel_path(self, file_path: str) -> str:
		path = Path(file_path)
		if path.is_absolute():
			raise ValueError(f"Absolute paths are not allowed: {file_path}")
		normalized = str(path).replace("\\", "/")
		parts = [part for part in normalized.split("/") if part not in ("", ".")]
		if any(part == ".." for part in parts):
			raise ValueError(f"Path traversal is not allowed: {file_path}")
		if not parts:
			raise ValueError("File path cannot be empty")
		return "/".join(parts)

	def _slugify(self, text: str) -> str:
		slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
		return slug[:80] or "generated-project"

	def _is_allowed_test_file(self, normalized_path: str) -> bool:
		return (
			normalized_path.startswith("tests/")
			or normalized_path.startswith("test_")
			or "/test_" in normalized_path
		)
