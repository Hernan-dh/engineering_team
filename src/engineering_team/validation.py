"""Deterministic acceptance checks for generated programs."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from engineering_team.tools.sandbox_tools import (
    SANDBOX_DIR,
    SandboxExecution,
    execute_sandbox_python,
)


class GeneratedProgramValidationError(RuntimeError):
    def __init__(self, stage_index: int, message: str) -> None:
        super().__init__(message)
        self.stage_index = stage_index


def _failure_details(result: SandboxExecution) -> str:
    details = (result.stderr or result.stdout or "No diagnostic output.").strip()
    return details[-4000:]


def validate_generated_program(
    sandbox: Path = SANDBOX_DIR,
    executor: Callable[[list[str]], SandboxExecution] = execute_sandbox_python,
) -> None:
    """Require a constructible Gradio UI and a passing unittest suite."""
    validator = sandbox / "_validate.py"
    if not validator.is_file():
        raise GeneratedProgramValidationError(2, "Frontend validation script is missing.")
    frontend = executor(["_validate.py"])
    if frontend.returncode:
        raise GeneratedProgramValidationError(
            2, "Frontend validation failed:\n" + _failure_details(frontend)
        )

    tests = list(sandbox.glob("test*.py")) + list((sandbox / "tests").glob("test*.py"))
    if not tests:
        raise GeneratedProgramValidationError(3, "No backend unit tests were generated.")
    backend = executor(["-m", "unittest", "discover", "-v", "-s", ".", "-p", "test*.py"])
    if backend.returncode:
        raise GeneratedProgramValidationError(
            3, "Backend tests failed:\n" + _failure_details(backend)
        )

    summary = (
        "# Acceptance validation\n\n"
        "- Gradio UI construction: passed\n"
        "- Backend unittest suite: passed\n"
    )
    (sandbox / "test_summary.md").write_text(summary, encoding="utf-8")
