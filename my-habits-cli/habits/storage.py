"""Local JSON persistence for habits (constitution §5)."""

import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Callable

from habits.core import EmptyNameError, Habit, name_key, normalize_name

FORMAT_VERSION = 1
HABITS_FILE_ENV = "HABITS_FILE"
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


class CorruptDataError(Exception):
    """The data file exists but cannot be interpreted (RNF-4).

    `reason` is a short Spanish description shown to the user.
    """

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"{path}: {reason}")
        self.path = path
        self.reason = reason


def default_path() -> Path:
    """`HABITS_FILE` if set, otherwise `~/habits.json` (RNF-1)."""
    override = os.environ.get(HABITS_FILE_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / "habits.json"


def load(path: Path) -> list[Habit]:
    """Read and validate the data file. A missing file means no habits (RNF-3)."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except UnicodeDecodeError:
        raise CorruptDataError(path, "el archivo no está en UTF-8") from None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise CorruptDataError(path, f"JSON inválido en la línea {error.lineno}") from None
    return _parse(path, data)


def _parse(path: Path, data: Any) -> list[Habit]:
    def corrupt(reason: str) -> CorruptDataError:
        return CorruptDataError(path, reason)

    if not isinstance(data, dict):
        raise corrupt("la raíz debe ser un objeto")
    version = data.get("version")
    if isinstance(version, bool) or version != FORMAT_VERSION:
        raise corrupt(f"versión de formato no soportada ({version!r})")
    entries = data.get("habits")
    if not isinstance(entries, list):
        raise corrupt("falta la lista «habits»")

    habits: list[Habit] = []
    seen: set[str] = set()
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise corrupt(f"el hábito n.º {position} debe ser un objeto")
        raw_name = entry.get("name")
        if not isinstance(raw_name, str):
            raise corrupt(f"el hábito n.º {position} no tiene un nombre de texto")
        try:
            name = normalize_name(raw_name)
        except EmptyNameError:
            raise corrupt(f"el hábito n.º {position} tiene el nombre vacío") from None
        if name_key(name) in seen:
            raise corrupt(f"el hábito «{name}» está repetido")
        seen.add(name_key(name))
        habits.append(Habit(name, _parse_dates(entry.get("done"), name, corrupt)))
    return habits


def _parse_dates(raw: Any, name: str, corrupt: Callable[[str], CorruptDataError]) -> set[date]:
    if not isinstance(raw, list):
        raise corrupt(f"el hábito «{name}» no tiene una lista «done»")
    dates: set[date] = set()
    for value in raw:
        # fromisoformat also accepts forms like "20261110"; RNF-2 requires AAAA-MM-DD.
        if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
            raise corrupt(f"el hábito «{name}» tiene una fecha que no es AAAA-MM-DD ({value!r})")
        try:
            dates.add(date.fromisoformat(value))
        except ValueError:
            raise corrupt(f"el hábito «{name}» tiene una fecha imposible ({value})") from None
    return dates


def save(path: Path, habits: list[Habit]) -> None:
    """Write atomically: temporary file in the same directory, then os.replace (RNF-5)."""
    data = {
        "version": FORMAT_VERSION,
        "habits": [
            {"name": habit.name, "done": [day.isoformat() for day in sorted(habit.done_dates)]}
            for habit in habits
        ],
    }
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
