from pathlib import Path
import shutil
import subprocess
from dataclasses import dataclass

from crewai.tools import tool


PROJECT_DIR = Path(__file__).parents[3]
SANDBOX_DIR = PROJECT_DIR / "sandbox"
DOCKERFILE = PROJECT_DIR / "docker" / "sandbox.Dockerfile"
DOCKER_IMAGE = "engineering-team-sandbox:local"
EXECUTION_TIMEOUT_SECONDS = 300
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class SandboxExecution:
    returncode: int
    stdout: str
    stderr: str


def _sandbox_path(filename: str) -> Path:
    """Resolve a relative path and guarantee that it stays in the sandbox."""
    if not filename or Path(filename).is_absolute():
        raise ValueError("Use a non-empty path relative to the sandbox.")
    path = (SANDBOX_DIR / filename).resolve()
    try:
        path.relative_to(SANDBOX_DIR.resolve())
    except ValueError as exc:
        raise ValueError("The path must stay inside the sandbox.") from exc
    return path


def ensure_sandbox_image() -> None:
    """Build the pinned Python/Gradio runtime when it is not available."""
    inspected = subprocess.run(
        ["docker", "image", "inspect", DOCKER_IMAGE], capture_output=True, text=True
    )
    if inspected.returncode == 0:
        return
    subprocess.run(
        [
            "docker", "build", "--tag", DOCKER_IMAGE,
            "--file", str(DOCKERFILE), str(DOCKERFILE.parent),
        ],
        check=True,
    )


def reset_sandbox() -> None:
    """Create a clean workspace and ensure its isolated runtime exists."""
    ensure_sandbox_image()
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)
    SANDBOX_DIR.mkdir(parents=True)


def execute_sandbox_python(arguments: list[str]) -> SandboxExecution:
    """Execute Python arguments in the same constrained runtime used by tools."""
    command = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "1g",
        "--cpus", "1",
        "--pids-limit", "128",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=128m",
        "--volume", f"{SANDBOX_DIR}:/workspace:rw",
        "--workdir", "/workspace",
        DOCKER_IMAGE,
        "python", *arguments,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=EXECUTION_TIMEOUT_SECONDS,
        )
        return SandboxExecution(result.returncode, result.stdout, result.stderr)
    except FileNotFoundError:
        return SandboxExecution(127, "", "Docker is not installed or is not available on PATH.")
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
        return SandboxExecution(
            124,
            stdout,
            f"Execution stopped after {EXECUTION_TIMEOUT_SECONDS} seconds.\n{stderr}",
        )


@tool("List Sandbox Files")
def list_sandbox_files(directory: str = ".") -> str:
    """List files in a directory relative to the sandbox root."""
    try:
        root = _sandbox_path(directory)
    except ValueError as exc:
        return str(exc)
    if not root.is_dir():
        return f"No such directory in the sandbox: {directory}"
    names = sorted(str(path.relative_to(SANDBOX_DIR)) for path in root.iterdir())
    return "\n".join(names) if names else "The sandbox is empty."


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """Read a UTF-8 text file contained by the sandbox."""
    try:
        path = _sandbox_path(filename)
    except ValueError as exc:
        return str(exc)
    if not path.is_file():
        return f"No such file in the sandbox: {filename}"
    return path.read_text(encoding="utf-8")


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """Write a UTF-8 text file contained by the sandbox."""
    try:
        path = _sandbox_path(filename)
    except ValueError as exc:
        return str(exc)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """Run a sandbox Python file in the constrained Docker runtime."""
    try:
        path = _sandbox_path(filename)
    except ValueError as exc:
        return str(exc)
    if not path.is_file() or path.suffix.lower() != ".py":
        return f"No such Python file in the sandbox: {filename}"

    relative_filename = path.relative_to(SANDBOX_DIR).as_posix()
    result = execute_sandbox_python([relative_filename])
    return (
        f"Exit code: {result.returncode}\n\n"
        f"--- stdout ---\n{result.stdout or '(empty)'}\n\n"
        f"--- stderr ---\n{result.stderr or '(empty)'}"
    )


sandbox_tools = [list_sandbox_files, read_sandbox_file, write_sandbox_file, run_sandbox_python]


def _never_cache(*_args, **_kwargs) -> bool:
    return False


for _tool in sandbox_tools:
    _tool.cache_function = _never_cache
