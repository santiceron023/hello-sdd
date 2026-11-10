"""Pure domain rules for habits and streaks.

This module never reads argv, prints or knows about argparse: it only works
on in-memory data and reports problems through exceptions (constitution §3).
"""

import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

ONE_DAY = timedelta(days=1)


class HabitError(Exception):
    """Base class for domain errors. Carries the affected habit name."""

    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self.name = name


class EmptyNameError(HabitError):
    """The habit name is empty after trimming spaces (CA-1.4)."""


class DuplicateHabitError(HabitError):
    """Another habit already uses that name; `name` is the stored one (CA-2.2, CA-4.3)."""


class HabitNotFoundError(HabitError):
    """No habit matches the given name; `name` is the normalized input (CA-3.3, CA-4.2)."""


@dataclass
class Habit:
    name: str
    done_dates: set[date] = field(default_factory=set)


def normalize_name(raw: str) -> str:
    """Trim surrounding whitespace and reject empty names (CA-1.1, CA-1.4)."""
    name = raw.strip()
    if not name:
        raise EmptyNameError()
    return name


def name_key(name: str) -> str:
    """Comparison key that ignores case and surrounding spaces (CA-1.2)."""
    return name.strip().casefold()


def _find(habits: list[Habit], name: str) -> Habit | None:
    key = name_key(name)
    return next((habit for habit in habits if name_key(habit.name) == key), None)


def find_habit(habits: list[Habit], raw_name: str) -> Habit:
    name = normalize_name(raw_name)
    habit = _find(habits, name)
    if habit is None:
        raise HabitNotFoundError(name)
    return habit


def add_habit(habits: list[Habit], raw_name: str) -> Habit:
    """Create a habit with no done dates (RF-2)."""
    name = normalize_name(raw_name)
    existing = _find(habits, name)
    if existing is not None:
        raise DuplicateHabitError(existing.name)
    habit = Habit(name)
    habits.append(habit)
    return habit


def mark_done(habits: list[Habit], raw_name: str, today: date) -> bool:
    """Record `today` for the habit. Returns False if it was already recorded (RF-3)."""
    habit = find_habit(habits, raw_name)
    if today in habit.done_dates:
        return False
    habit.done_dates.add(today)
    return True


def rename_habit(habits: list[Habit], old_raw_name: str, new_raw_name: str) -> Habit:
    """Rename a habit keeping its history. Validates everything before mutating (RF-4)."""
    habit = find_habit(habits, old_raw_name)
    new_name = normalize_name(new_raw_name)
    other = _find(habits, new_name)
    if other is not None and other is not habit:
        raise DuplicateHabitError(other.name)
    habit.name = new_name
    return habit


def current_streak(habit: Habit, today: date) -> int:
    """Consecutive done days ending today, or yesterday if today is still pending (RF-6).

    Future dates are never reached because the walk starts at today or
    yesterday and goes backwards (CL-15).
    """
    days = habit.done_dates
    if today in days:
        cursor = today
    elif today - ONE_DAY in days:
        cursor = today - ONE_DAY
    else:
        return 0
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= ONE_DAY
    return streak


def is_done_on(habit: Habit, day: date) -> bool:
    return day in habit.done_dates


def _sort_key(habit: Habit) -> tuple[str, str]:
    folded = name_key(habit.name)
    without_accents = "".join(
        char for char in unicodedata.normalize("NFD", folded) if not unicodedata.combining(char)
    )
    return without_accents, folded


def sorted_habits(habits: list[Habit]) -> list[Habit]:
    """Alphabetical order ignoring case and accents, so «árbol» goes before «Bici» (CA-5.2)."""
    return sorted(habits, key=_sort_key)
