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
    if not (sandbox / "design.md").is_file():
        return 0
    managed_run = (sandbox / STATE_FILE).is_file()
    backend_files = list((sandbox / "backend").glob("*.py"))
    backend_complete = (sandbox / "backend_summary.md").is_file() or (
        not managed_run and bool(backend_files)
    )
    if not backend_complete:
        return 1
    if not (sandbox / "frontend" / "app.py").is_file() or not (
        (sandbox / "_validate.py").is_file()
        or (sandbox / "frontend_summary.md").is_file()
    ):
        return 2
    if not (sandbox / "test_summary.md").is_file():
        return 3
    return len(STAGE_NAMES)


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
