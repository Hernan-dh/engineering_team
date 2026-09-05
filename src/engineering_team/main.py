#!/usr/bin/env python
import os
import sys
import warnings
from datetime import datetime

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from engineering_team.crew import EngineeringTeam
from engineering_team.model_provider import fallback_llm
from engineering_team.program_options import ProgramSelection, choose_requirements
from engineering_team.resume import (
    STAGE_NAMES,
    ask_to_resume,
    clear_failed_stage,
    first_incomplete_stage,
    has_previous_program,
    load_requirements,
    mark_failed_stage,
    save_requirements,
)
from engineering_team.validation import (
    GeneratedProgramValidationError,
    validate_generated_program,
)
from .tools.sandbox_tools import reset_sandbox

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def _resumed_crew():
    active_crew = EngineeringTeam(llm=fallback_llm()).crew()
    start_index = first_incomplete_stage()
    if start_index == len(STAGE_NAMES):
        return None
    active_tasks = active_crew.tasks[start_index:]
    for task in active_tasks:
        task.context = [context for context in (task.context or []) if context in active_tasks]
    active_crew.tasks = active_tasks
    print(f"Resuming from stage: {STAGE_NAMES[start_index]}\n")
    return active_crew


def run():
    """Run the crew and offer an in-process resume after failures."""
    configured = os.getenv("ENGINEERING_REQUIREMENTS", "").strip()
    selection = (
        ProgramSelection(requirements=configured)
        if configured
        else choose_requirements(can_resume=has_previous_program())
    )
    if selection.resume:
        requirements = load_requirements()
        active_crew = _resumed_crew()
        if active_crew is None:
            print("The previous program has already completed every stage.")
            return
    else:
        requirements = selection.requirements
        reset_sandbox()
        save_requirements(requirements)
        active_crew = EngineeringTeam(llm=fallback_llm()).crew()

    while True:
        try:
            active_crew.kickoff(inputs={'requirements': requirements})
            print("\nRunning deterministic acceptance checks...")
            validate_generated_program()
            clear_failed_stage()
            print("Generated program validated successfully.")
            return
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as error:
            if isinstance(error, GeneratedProgramValidationError):
                mark_failed_stage(error.stage_index)
            print(f"\nError: {error}", file=sys.stderr)
            if not ask_to_resume():
                raise Exception(f"An error occurred while running the crew: {error}") from error
            requirements = load_requirements()
            active_crew = _resumed_crew()
            if active_crew is None:
                print("Every stage was completed before the error occurred.")
                return


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        EngineeringTeam(llm=fallback_llm()).crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        EngineeringTeam(llm=fallback_llm()).crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        EngineeringTeam(llm=fallback_llm()).crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = EngineeringTeam(llm=fallback_llm()).crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
