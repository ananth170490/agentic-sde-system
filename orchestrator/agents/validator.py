from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from orchestrator.state import Task, ValidationResult
from orchestrator.tools.sandbox_runner import SandboxRunner


class ValidationAgent:
	def run(self, task: Task, project_dir: str, sandbox: SandboxRunner) -> ValidationResult:
		pytest_result = sandbox.run_pytest(project_dir)

		issues: list[str] = list(pytest_result.get("issues", []))
		logs_parts: list[str] = []
		pytest_logs = str(pytest_result.get("logs", ""))
		if pytest_logs:
			logs_parts.append(f"[pytest]\n{pytest_logs}")

		compile_ok, compile_logs, compile_issues = self._run_py_compile(task=task, project_dir=project_dir)
		if compile_logs:
			logs_parts.append(f"[py_compile]\n{compile_logs}")
		issues.extend(compile_issues)

		pyflakes_ok, pyflakes_logs, pyflakes_issues = self._run_pyflakes(task=task, project_dir=project_dir)
		if pyflakes_logs:
			logs_parts.append(f"[pyflakes]\n{pyflakes_logs}")
		issues.extend(pyflakes_issues)

		pytest_passed = bool(pytest_result.get("passed", False))
		passed = pytest_passed and compile_ok and pyflakes_ok and not issues

		return ValidationResult(
			task_id=task.id,
			passed=passed,
			logs="\n\n".join(part for part in logs_parts if part).strip(),
			issues=sorted(set(issues)),
		)

	def _run_py_compile(self, task: Task, project_dir: str) -> tuple[bool, str, list[str]]:
		project_root = Path(project_dir).resolve()
		issues: list[str] = []
		logs: list[str] = []

		for rel_path in task.owned_files:
			target = project_root / rel_path
			if target.suffix != ".py":
				continue
			if not target.exists():
				issues.append(f"Missing owned file for compile check: {rel_path}")
				continue

			proc = subprocess.run(
				[sys.executable, "-m", "py_compile", str(target)],
				capture_output=True,
				text=True,
				check=False,
			)
			combined = self._combine_output(proc.stdout, proc.stderr)
			if combined:
				logs.append(f"{rel_path}:\n{combined}")
			if proc.returncode != 0:
				issues.append(f"py_compile failed: {rel_path}")

		return len(issues) == 0, "\n\n".join(logs).strip(), issues

	def _run_pyflakes(self, task: Task, project_dir: str) -> tuple[bool, str, list[str]]:
		project_root = Path(project_dir).resolve()
		python_files: list[str] = []
		for rel_path in task.owned_files:
			target = project_root / rel_path
			if target.suffix == ".py" and target.exists():
				python_files.append(str(target))

		if not python_files:
			return True, "", []

		proc = subprocess.run(
			[sys.executable, "-m", "pyflakes", *python_files],
			capture_output=True,
			text=True,
			check=False,
		)
		combined = self._combine_output(proc.stdout, proc.stderr)
		if proc.returncode == 0:
			return True, combined, []

		issues = [line.strip() for line in combined.splitlines() if line.strip()]
		if not issues:
			issues = ["pyflakes reported failures"]
		return False, combined, issues

	def _combine_output(self, stdout: str, stderr: str) -> str:
		out = stdout.strip()
		err = stderr.strip()
		if out and err:
			return f"{out}\n{err}"
		return out or err
