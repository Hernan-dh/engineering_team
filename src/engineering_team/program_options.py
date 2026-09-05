"""Interactive program selection for local engineering-team runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ProgramSelection:
    requirements: str = ""
    resume: bool = False


PROGRAM_OPTIONS = (
    (
        "Investment simulator",
        """Build an account management system for a trading simulation platform. Users can create an account, deposit and withdraw funds, buy and sell shares, inspect holdings and transactions, and calculate portfolio value and profit or loss. Prevent overdrafts, unaffordable purchases, and sales of shares the user does not own. Include fixed test prices for AAPL, TSLA, and GOOGL.""",
    ),
    (
        "Personal expense manager",
        """Build a personal expense manager. Users can record income and expenses with categories and dates, edit or delete entries, set monthly category budgets, filter transactions, and view balance and monthly summaries. Persist data locally and provide useful validation and unit tests.""",
    ),
    (
        "Inventory and sales system",
        """Build an inventory and sales manager for a small business. Users can create products, adjust stock, register sales, prevent sales without sufficient inventory, search products, and view low-stock and revenue reports. Persist data locally and include comprehensive unit tests.""",
    ),
    (
        "Appointment scheduler",
        """Build an appointment scheduling system. Users can manage clients and services, create, reschedule, cancel, and list appointments, prevent overlapping bookings, and filter the calendar by date or status. Persist data locally and include comprehensive unit tests.""",
    ),
    (
        "Kanban task board",
        """Build a personal Kanban task manager. Users can create projects and tasks, assign priorities and due dates, move tasks between pending, in-progress, and completed states, search and filter tasks, and view progress summaries. Persist data locally and include comprehensive unit tests.""",
    ),
)


def choose_requirements(
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    can_resume: bool = False,
) -> ProgramSelection:
    """Ask the user to select a preset or enter custom requirements."""
    output_fn("\nWhat program would you like the team to generate?\n")
    output_fn("0. Enter custom requirements")
    for number, (name, _) in enumerate(PROGRAM_OPTIONS, start=1):
        output_fn(f"{number}. {name}")
    if can_resume:
        output_fn("6. Continue the previous program")

    while True:
        maximum = 6 if can_resume else 5
        selection = input_fn(f"\nChoose an option (0-{maximum}): ").strip()
        if selection == "6" and can_resume:
            return ProgramSelection(resume=True)
        if selection == "0":
            custom = input_fn("Describe the program you want to generate: ").strip()
            if custom:
                return ProgramSelection(requirements=custom)
            output_fn("The description cannot be empty.")
            continue
        if selection.isdigit() and 1 <= int(selection) <= len(PROGRAM_OPTIONS):
            name, requirements = PROGRAM_OPTIONS[int(selection) - 1]
            output_fn(f"Selected: {name}\n")
            return ProgramSelection(requirements=requirements)
        output_fn(f"Invalid option. Enter a number between 0 and {maximum}.")
