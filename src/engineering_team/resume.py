"""Local checkpoints used to continue an interrupted engineering crew."""

from __future__ import annotations

import json
from pathlib import Path

from engineering_team.tools.sandbox_tools import SANDBOX_DIR


STATE_FILE = ".engineering_team_state.json"
STAGE_NAMES = ("design", "backend", "frontend", "tests")


def has_previous_program(sandbox: Path = SANDBOX_DIR) -> bool:
    return sandbox.is_dir() and any(sandbox.iterdir())


def save_requirements(requirements: str, sandbox: Path = SANDBOX_DIR) -> None:
    state = {"requirements": requirements}
    (sandbox / STATE_FILE).write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def mark_failed_stage(stage_index: int, sandbox: Path = SANDBOX_DIR) -> None:
    state_path = sandbox / STATE_FILE
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    state["resume_stage"] = stage_index
    state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def clear_failed_stage(sandbox: Path = SANDBOX_DIR) -> None:
    state_path = sandbox / STATE_FILE
    if not state_path.is_file():
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.pop("resume_stage", None)
    state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def load_requirements(sandbox: Path = SANDBOX_DIR) -> str:
    state_path = sandbox / STATE_FILE
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        requirements = state.get("requirements", "")
        if isinstance(requirements, str) and requirements.strip():
            return requirements.strip()
    design = sandbox / "design.md"
    if design.is_file():
        return (
            "Continue the program already described and implemented in the sandbox. "
            "Preserve its existing behavior and follow this design:\n\n"
            + design.read_text(encoding="utf-8")
        )
    raise RuntimeError("No requirements or design were found to resume.")


def first_incomplete_stage(sandbox: Path = SANDBOX_DIR) -> int:
    """Return the zero-based task index that should run next."""
    forced_stage = len(STAGE_NAMES)
    state: dict[str, object] = {}
    state_path = sandbox / STATE_FILE
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        saved_stage = state.get("resume_stage")
        if isinstance(saved_stage, int) and 0 <= saved_stage < len(STAGE_NAMES):
            forced_stage = saved_stage
    if not (sandbox / "design.md").is_file():
        return min(0, forced_stage)
    managed_run = isinstance(state.get("requirements"), str) and bool(
        str(state["requirements"]).strip()
    )
    backend_files = list((sandbox / "backend").glob("*.py"))
    backend_complete = (sandbox / "backend_summary.md").is_file() or (
        not managed_run and bool(backend_files)
    )
    if not backend_complete:
        return min(1, forced_stage)
    if not (sandbox / "frontend" / "app.py").is_file() or not (
        (sandbox / "_validate.py").is_file()
        or (sandbox / "frontend_summary.md").is_file()
    ):
        return min(2, forced_stage)
    if not (sandbox / "test_summary.md").is_file():
        return min(3, forced_stage)
    return forced_stage


def ask_to_resume(
    input_fn=input,
    output_fn=print,
) -> bool:
    """Offer an in-process retry after a recoverable crew failure."""
    output_fn("\nThe run ended with an error, but its work has been saved.")
    while True:
        try:
            answer = input_fn("Resume from the pending stage? [y/N]: ").strip().lower()
        except EOFError:
            return False
        if answer in {"s", "si", "sí", "y", "yes"}:
            return True
        if answer in {"", "n", "no"}:
            return False
        output_fn("Enter 'y' to resume or 'n' to exit.")
