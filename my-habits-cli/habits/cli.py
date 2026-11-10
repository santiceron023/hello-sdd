"""Command line layer: turns argv into domain calls and results into Spanish text."""

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import NoReturn

from habits import core, storage

USAGE = "uso: python -m habits {crear,hecho,renombrar,listar} ..."

# Command -> positional arguments as (attribute, label shown to the user).
COMMANDS: dict[str, tuple[tuple[str, str], ...]] = {
    "crear": (("name", "nombre"),),
    "hecho": (("name", "nombre"),),
    "renombrar": (("old_name", "actual"), ("new_name", "nuevo")),
    "listar": (),
}


class _UsageError(Exception):
    pass


class _SpanishArgumentParser(argparse.ArgumentParser):
    """argparse reports errors in English; we replace them with our own text (CA-7.2)."""

    def error(self, message: str) -> NoReturn:
        raise _UsageError(message)


def _build_parser() -> argparse.ArgumentParser:
    # Help is disabled because argparse would print it in English (CA-7.1).
    parser = _SpanishArgumentParser(prog="python -m habits", add_help=False)
    commands = parser.add_subparsers(dest="command", required=True)
    for command, arguments in COMMANDS.items():
        subparser = commands.add_parser(command, add_help=False)
        for attribute, label in arguments:
            subparser.add_argument(attribute, metavar=label)
    return parser


def _usage_problem(argv: list[str]) -> str:
    if not argv:
        return "falta el comando."
    command, given = argv[0], argv[1:]
    if command not in COMMANDS:
        return f"comando desconocido «{command}»."
    expected = COMMANDS[command]
    if not expected:
        return f"«{command}» no admite argumentos."
    if len(given) != len(expected):
        labels = " ".join(f"<{label}>" for _, label in expected)
        return f"«{command}» necesita: {labels}."
    return f"argumentos no válidos para «{command}». Si un nombre empieza por «-», escribe «--» antes."


def _format_listing(habits: list[core.Habit], today: date) -> list[str]:
    if not habits:
        return ["No existen hábitos"]
    ordered = core.sorted_habits(habits)
    width = max(len(habit.name) for habit in ordered)
    lines = []
    for habit in ordered:
        mark = "✓" if core.is_done_on(habit, today) else "✗"
        streak = core.current_streak(habit, today)
        unit = "día" if streak == 1 else "días"
        lines.append(f"{mark} {habit.name.ljust(width)}  racha: {streak} {unit}")
    return lines


def _run(args: argparse.Namespace, habits: list[core.Habit], today: date, path: Path) -> list[str]:
    if args.command == "crear":
        habit = core.add_habit(habits, args.name)
        storage.save(path, habits)
        return [f"Hábito «{habit.name}» creado."]
    if args.command == "hecho":
        habit = core.find_habit(habits, args.name)
        if not core.mark_done(habits, habit.name, today):
            return [f"El hábito «{habit.name}» ya estaba marcado hoy."]
        storage.save(path, habits)
        return [f"Hábito «{habit.name}» marcado como hecho hoy."]
    if args.command == "renombrar":
        old_name = core.find_habit(habits, args.old_name).name
        habit = core.rename_habit(habits, args.old_name, args.new_name)
        storage.save(path, habits)
        return [f"Hábito «{old_name}» renombrado a «{habit.name}»."]
    return _format_listing(habits, today)


def _error_message(error: Exception) -> str:
    if isinstance(error, core.EmptyNameError):
        return "el nombre del hábito no puede estar vacío."
    if isinstance(error, core.DuplicateHabitError):
        return f"ya existe el hábito «{error.name}»."
    if isinstance(error, core.HabitNotFoundError):
        return f"no existe el hábito «{error.name}»."
    if isinstance(error, storage.CorruptDataError):
        return f"no se puede leer el archivo de hábitos ({error.path}): {error.reason}."
    raise error


def main(
    argv: list[str] | None = None,
    *,
    today: date | None = None,
    data_path: Path | None = None,
) -> int:
    """Run one command and return its exit code: 0 ok, 1 domain/data error, 2 usage error."""
    if today is None:
        today = date.today()  # Read once at start so the whole command sees one day (CL-14).
    argv = sys.argv[1:] if argv is None else argv
    path = data_path if data_path is not None else storage.default_path()

    try:
        args = _build_parser().parse_args(argv)
    except _UsageError:
        print(USAGE, file=sys.stderr)
        print(f"Error: {_usage_problem(argv)}", file=sys.stderr)
        return 2

    try:
        habits = storage.load(path)
        lines = _run(args, habits, today, path)
    except (core.HabitError, storage.CorruptDataError) as error:
        print(f"Error: {_error_message(error)}", file=sys.stderr)
        return 1

    for line in lines:
        print(line)
    return 0
