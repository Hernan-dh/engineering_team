"""Recover sandbox writes emitted as text by imperfect tool-calling models."""

from __future__ import annotations

import re
from pathlib import Path

from engineering_team.tools.sandbox_tools import SANDBOX_DIR


WRITE_CALL = re.compile(
    r"<tool_call>\s*<function=write_sandbox_file>\s*"
    r"<parameter=filename>\s*(?P<filename>.*?)\s*</parameter>\s*"
    r"<parameter=content>\s*(?P<content>.*?)\s*</parameter>\s*</function>\s*</tool_call>",
    re.DOTALL,
)


def recover_sandbox_write(text: str, sandbox: Path = SANDBOX_DIR) -> str | None:
    """Apply one explicitly serialized write call, constrained to the sandbox."""
    match = WRITE_CALL.fullmatch(text.strip())
    if not match:
        return None
    filename = match.group("filename").strip()
    if not filename or Path(filename).is_absolute():
        return None
    target = (sandbox / filename).resolve()
    try:
        target.relative_to(sandbox.resolve())
    except ValueError:
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(match.group("content").rstrip() + "\n", encoding="utf-8")
    return filename
