"""Interactive program selection for local engineering-team runs."""

from __future__ import annotations

from collections.abc import Callable


PROGRAM_OPTIONS = (
    (
        "Simulador de inversiones",
        """Build an account management system for a trading simulation platform. Users can create an account, deposit and withdraw funds, buy and sell shares, inspect holdings and transactions, and calculate portfolio value and profit or loss. Prevent overdrafts, unaffordable purchases, and sales of shares the user does not own. Include fixed test prices for AAPL, TSLA, and GOOGL.""",
    ),
    (
        "Gestor de gastos personales",
        """Build a personal expense manager. Users can record income and expenses with categories and dates, edit or delete entries, set monthly category budgets, filter transactions, and view balance and monthly summaries. Persist data locally and provide useful validation and unit tests.""",
    ),
    (
        "Sistema de inventario y ventas",
        """Build an inventory and sales manager for a small business. Users can create products, adjust stock, register sales, prevent sales without sufficient inventory, search products, and view low-stock and revenue reports. Persist data locally and include comprehensive unit tests.""",
    ),
    (
        "Agenda de turnos",
        """Build an appointment scheduling system. Users can manage clients and services, create, reschedule, cancel, and list appointments, prevent overlapping bookings, and filter the calendar by date or status. Persist data locally and include comprehensive unit tests.""",
    ),
    (
        "Tablero de tareas Kanban",
        """Build a personal Kanban task manager. Users can create projects and tasks, assign priorities and due dates, move tasks between pending, in-progress, and completed states, search and filter tasks, and view progress summaries. Persist data locally and include comprehensive unit tests.""",
    ),
)


def choose_requirements(
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> str:
    """Ask the user to select a preset or enter custom requirements."""
    output_fn("\n¿Qué programa querés que genere el equipo?\n")
    output_fn("0. Escribir requisitos personalizados")
    for number, (name, _) in enumerate(PROGRAM_OPTIONS, start=1):
        output_fn(f"{number}. {name}")

    while True:
        selection = input_fn("\nElegí una opción (0-5): ").strip()
        if selection == "0":
            custom = input_fn("Describí el programa que querés generar: ").strip()
            if custom:
                return custom
            output_fn("La descripción no puede estar vacía.")
            continue
        if selection.isdigit() and 1 <= int(selection) <= len(PROGRAM_OPTIONS):
            name, requirements = PROGRAM_OPTIONS[int(selection) - 1]
            output_fn(f"Seleccionado: {name}\n")
            return requirements
        output_fn("Opción inválida. Ingresá un número entre 0 y 5.")
