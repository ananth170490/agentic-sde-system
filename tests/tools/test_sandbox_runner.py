import subprocess
import sys
from pathlib import Path

import pytest

from orchestrator.tools.sandbox_runner import SandboxRunner, SandboxRunnerTimeoutError


def test_run_pytest_reports_failures_and_issues() -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "pytest_sample_project"
    runner = SandboxRunner(python_executable=str(Path(sys.prefix) / "bin" / "python"))

    result = runner.run_pytest(str(fixture_root), timeout_sec=30)

    assert result["passed"] is False
    assert isinstance(result["logs"], str)
    assert isinstance(result["issues"], list)
    assert any("test_fail.py::test_intentional_failure" in issue for issue in result["issues"])


def test_run_pytest_timeout_raises_clear_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "pytest_sample_project"
    runner = SandboxRunner(python_executable=str(Path(sys.prefix) / "bin" / "python"))

    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["python", "-m", "pytest", "-q"], timeout=1)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)

    with pytest.raises(SandboxRunnerTimeoutError) as err:
        runner.run_pytest(str(fixture_root), timeout_sec=1)

    assert "SandboxRunner timed out" in str(err.value)
