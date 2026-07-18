from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from orchestrator.state import ArchitectureDesign, RequirementSpec, Task, ValidationResult
from orchestrator.tools.model_provider import ModelProvider


class _GeneratedFilesResponse(BaseModel):
	files: dict[str, str] = Field(default_factory=dict)


class CodeGenAgent:
	def run(
		self,
		task: Task,
		spec: RequirementSpec,
		design: ArchitectureDesign,
		context_from_dependencies: str,
		model: ModelProvider,
		project_dir: str | None = None,
	) -> dict[str, str]:
		system_prompt = (
			"You are a senior software engineer writing production-quality code. "
			"Use type hints and clear docstrings where useful. "
			"If this is an API task, follow the architecture API contract exactly. "
			"Return only file path to file content mappings for files relevant to this task."
		)

		user_prompt = (
			"Generate code for this task only.\n\n"
			f"Task JSON:\n{task.model_dump_json(indent=2)}\n\n"
			f"Requirement spec JSON:\n{spec.model_dump_json(indent=2)}\n\n"
			f"Architecture design JSON:\n{design.model_dump_json(indent=2)}\n\n"
			f"Dependency context:\n{context_from_dependencies}\n\n"
			f"You may only write these files:\n{task.owned_files}"
		)

		response = model.complete_structured(
			system_prompt=system_prompt,
			user_prompt=user_prompt,
			response_model=_GeneratedFilesResponse,
		)
		response.files = self._sanitize_files(task=task, files=response.files)

		self._ensure_owned_files_only(task=task, files=response.files)

		target_project_dir = self._resolve_project_dir(spec, project_dir)
		self._write_files(target_project_dir, response.files)
		return response.files

	def repair(
		self,
		task: Task,
		validation_result: ValidationResult,
		spec: RequirementSpec,
		design: ArchitectureDesign,
		model: ModelProvider,
	) -> dict[str, str]:
		system_prompt = (
			"You are a senior software engineer repairing failing code. "
			"Fix only what is broken according to validation logs/issues. "
			"Do not broaden scope, and do not create files outside the task owned_files list. "
			"Preserve behavior that already works. Return only updated file mappings."
		)

		user_prompt = (
			"Repair this task using the validation feedback.\n\n"
			f"Task JSON:\n{task.model_dump_json(indent=2)}\n\n"
			f"Requirement spec JSON:\n{spec.model_dump_json(indent=2)}\n\n"
			f"Architecture design JSON:\n{design.model_dump_json(indent=2)}\n\n"
			f"Validation result JSON:\n{validation_result.model_dump_json(indent=2)}\n\n"
			f"Only allowed files:\n{task.owned_files}"
		)

		response = model.complete_structured(
			system_prompt=system_prompt,
			user_prompt=user_prompt,
			response_model=_GeneratedFilesResponse,
		)
		response.files = self._sanitize_files(task=task, files=response.files)
		self._ensure_owned_files_only(task=task, files=response.files)
		return response.files

	def _sanitize_files(self, task: Task, files: dict[str, str]) -> dict[str, str]:
		sanitized: dict[str, str] = {}
		for rel_path, content in files.items():
			sanitized[rel_path] = self._sanitize_file_content(task=task, rel_path=rel_path, content=content)
		return sanitized

	def _sanitize_file_content(self, task: Task, rel_path: str, content: str) -> str:
		normalized = self._normalize_rel_path(rel_path)
		text = content or ""
		extracted = self._extract_code_block(text)
		if extracted is not None:
			text = extracted

		if normalized.endswith(".py"):
			candidate = text.strip()
			if not candidate or self._looks_like_placeholder_text(candidate):
				return (
					'"""Auto-generated placeholder module.\n\n'
					f'Task: {task.id} - {task.title}\n'
					'"""\n\n'
					"# TODO: replace placeholder with implementation details from a follow-up generation pass.\n"
				)

		return text

	def _extract_code_block(self, text: str) -> str | None:
		match = re.search(r"```(?:[a-zA-Z0-9_+-]+)?\\n([\\s\\S]*?)\\n```", text)
		if match:
			return match.group(1).strip() + "\n"
		return None

	def _looks_like_placeholder_text(self, text: str) -> bool:
		normalized = text.strip().lower()
		if normalized in {"updated", "done", "n/a", "na", "todo", "tbd", "placeholder"}:
			return True
		# Single short non-code token should not be treated as valid source.
		if "\n" not in normalized and len(normalized.split()) <= 3 and all(ch.isalnum() or ch in "-_" for ch in normalized):
			return True
		return False

	def _ensure_owned_files_only(self, task: Task, files: dict[str, str]) -> None:
		normalized_allowed = {self._normalize_rel_path(path) for path in task.owned_files}
		for file_path in files:
			normalized = self._normalize_rel_path(file_path)
			if normalized not in normalized_allowed:
				raise ValueError(
					f"CodeGenAgent attempted write outside owned_files: '{file_path}' not in {sorted(normalized_allowed)}"
				)

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
