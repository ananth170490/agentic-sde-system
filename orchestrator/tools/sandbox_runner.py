from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


class SandboxRunnerTimeoutError(subprocess.TimeoutExpired):
	"""Raised when sandboxed pytest execution exceeds configured timeout."""

	def __init__(
		self,
		cmd: object,
		timeout: float,
		output: str | bytes | None = None,
		stderr: str | bytes | None = None,
		message: str | None = None,
	) -> None:
		super().__init__(cmd=cmd, timeout=timeout, output=output, stderr=stderr)
		self._message = message

	def __str__(self) -> str:
		if self._message:
			return self._message
		return super().__str__()


class SandboxRunner:
	def __init__(self, python_executable: str = "python") -> None:
		self._python_executable = self._normalize_python_executable(python_executable)

	def run_pytest(
		self,
		project_dir: str,
		timeout_sec: int = 60,
		test_paths: list[str] | None = None,
	) -> dict[str, object]:
		source_dir = Path(project_dir).resolve()
		if not source_dir.exists() or not source_dir.is_dir():
			raise ValueError(f"Invalid project_dir: {project_dir}")

		# Prototype limitation: this executes tests locally and does not enforce true network isolation.
		if self._is_isolated_dir(source_dir):
			target_dir = source_dir
			cleanup_dir = None
		else:
			cleanup_dir = Path(tempfile.mkdtemp(prefix="sandbox_runner_"))
			target_dir = cleanup_dir / source_dir.name
			shutil.copytree(source_dir, target_dir)

		try:
			normalized_test_paths = self._normalize_test_paths(
				target_dir=target_dir,
				test_paths=test_paths,
			)
			if test_paths is not None and not normalized_test_paths:
				return {
					"passed": True,
					"logs": "No scoped pytest files found for this task; skipping pytest.",
					"issues": [],
				}

			completed = self._run_pytest_subprocess(target_dir, timeout_sec, normalized_test_paths)
			logs = self._combine_streams(completed.stdout, completed.stderr)
			issues = self._extract_failed_tests(logs)
			passed = completed.returncode == 0
			return {
				"passed": passed,
				"logs": logs,
				"issues": issues,
			}
		finally:
			if cleanup_dir is not None:
				shutil.rmtree(cleanup_dir, ignore_errors=True)

	def _run_pytest_subprocess(
		self,
		run_dir: Path,
		timeout_sec: int,
		test_paths: list[str],
	) -> subprocess.CompletedProcess[str]:
		cmd = [self._python_executable, "-m", "pytest", "-q", *test_paths]
		try:
			return subprocess.run(
				cmd,
				cwd=str(run_dir),
				capture_output=True,
				text=True,
				timeout=timeout_sec,
				check=False,
			)
		except subprocess.TimeoutExpired as err:
			message = (
				f"SandboxRunner timed out after {timeout_sec}s while running pytest in {run_dir}"
			)
			raise SandboxRunnerTimeoutError(
				cmd=err.cmd or cmd,
				timeout=err.timeout,
				output=err.output,
				stderr=f"{err.stderr or ''}\n{message}".strip(),
				message=message,
			) from err

	def _normalize_test_paths(self, target_dir: Path, test_paths: list[str] | None) -> list[str]:
		if test_paths is None:
			return []

		normalized: list[str] = []
		for rel_path in test_paths:
			path = Path(rel_path)
			if path.is_absolute():
				continue
			candidate = (target_dir / path).resolve()
			if not candidate.exists() or not candidate.is_file():
				continue
			try:
				normalized.append(str(candidate.relative_to(target_dir)))
			except ValueError:
				continue
		return sorted(set(normalized))

	def _extract_failed_tests(self, logs: str) -> list[str]:
		summary_lines = [line for line in logs.splitlines() if " failed" in line and " in " in line]
		if not summary_lines:
			return []

		issues: list[str] = []
		for line in logs.splitlines():
			match = re.match(r"^FAILED\s+([^\s]+)\s+-\s+", line)
			if match:
				issues.append(match.group(1))

		# Some pytest outputs may include short test summary without error details.
		if issues:
			return sorted(set(issues))

		fallback = re.findall(r"([^\s]+::[^\s]+)\s+FAILED", logs)
		return sorted(set(fallback))

	def _combine_streams(self, stdout: str | None, stderr: str | None) -> str:
		out = stdout or ""
		err = stderr or ""
		if out and err:
			return f"{out}\n\n[stderr]\n{err}"
		return out or err

	def _is_isolated_dir(self, path: Path) -> bool:
		parts = {part.lower() for part in path.parts}
		return ".venv" in parts or "tmp" in parts or "private" in parts

	def _normalize_python_executable(self, python_executable: str) -> str:
		if "/" not in python_executable and "\\" not in python_executable:
			return python_executable
		path = Path(python_executable).expanduser()
		if path.is_absolute():
			return str(path)
		return str((Path.cwd() / path).resolve())
