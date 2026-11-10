"""Tests for the pure domain rules: names, registration, renaming and streaks."""

import copy
import time
import unittest
from datetime import date, timedelta

from habits.core import (
    DuplicateHabitError,
    EmptyNameError,
    Habit,
    HabitError,
    HabitNotFoundError,
    add_habit,
    current_streak,
    find_habit,
    is_done_on,
    mark_done,
    name_key,
    normalize_name,
    rename_habit,
    sorted_habits,
)

MONDAY = date(2026, 11, 9)
TUESDAY = date(2026, 11, 10)
WEDNESDAY = date(2026, 11, 11)
ONE_DAY = timedelta(days=1)


class HabitModelTest(unittest.TestCase):
    def test_new_habit_has_no_done_dates(self) -> None:
        self.assertEqual(Habit("Leer").done_dates, set())

    def test_domain_errors_inherit_from_habit_error(self) -> None:
        for error in (EmptyNameError, DuplicateHabitError, HabitNotFoundError):
            with self.subTest(error=error.__name__):
                self.assertTrue(issubclass(error, HabitError))

    def test_errors_keep_the_affected_name(self) -> None:
        self.assertEqual(HabitNotFoundError("Leer").name, "Leer")
        self.assertEqual(DuplicateHabitError("Leer").name, "Leer")


class NameRulesTest(unittest.TestCase):
    def test_normalize_name_strips_surrounding_spaces_ca_1_1_cl_7(self) -> None:
        self.assertEqual(normalize_name("  Leer "), "Leer")
        self.assertEqual(normalize_name("\tRepasar inglés\n"), "Repasar inglés")

    def test_normalize_name_rejects_blank_name_ca_1_4_cl_6(self) -> None:
        for raw in ("", "   ", "\t\n"):
            with self.subTest(raw=raw):
                with self.assertRaises(EmptyNameError):
                    normalize_name(raw)

    def test_name_key_ignores_case_ca_1_2(self) -> None:
        self.assertEqual(name_key("Leer"), name_key("LEER"))
        self.assertEqual(name_key("Leer"), name_key("  leer "))

    def test_name_key_uses_unicode_casefold(self) -> None:
        self.assertEqual(name_key("Straße"), name_key("STRASSE"))


class AddHabitTest(unittest.TestCase):
    def test_add_habit_creates_habit_without_dates_ca_2_1(self) -> None:
        habits: list[Habit] = []
        habit = add_habit(habits, "Leer")
        self.assertEqual(habits, [Habit("Leer")])
        self.assertIs(habit, habits[0])

    def test_add_habit_keeps_original_case_ca_1_3(self) -> None:
        habits: list[Habit] = []
        add_habit(habits, "Repasar Inglés")
        self.assertEqual(habits[0].name, "Repasar Inglés")

    def test_add_habit_stores_trimmed_name_cl_7(self) -> None:
        habits: list[Habit] = []
        add_habit(habits, "  Leer  ")
        self.assertEqual(habits[0].name, "Leer")

    def test_add_habit_rejects_duplicate_ignoring_case_ca_2_2_cl_5(self) -> None:
        habits = [Habit("Leer")]
        with self.assertRaises(DuplicateHabitError) as ctx:
            add_habit(habits, " leer ")
        self.assertEqual(ctx.exception.name, "Leer")
        self.assertEqual(habits, [Habit("Leer")])

    def test_add_habit_rejects_blank_name_ca_1_4(self) -> None:
        habits: list[Habit] = []
        with self.assertRaises(EmptyNameError):
            add_habit(habits, "   ")
        self.assertEqual(habits, [])


class FindHabitTest(unittest.TestCase):
    def test_find_habit_ignores_case_and_spaces_ca_1_2(self) -> None:
        habits = [Habit("Leer"), Habit("Yoga")]
        self.assertIs(find_habit(habits, "  YOGA "), habits[1])

    def test_find_habit_unknown_raises_not_found(self) -> None:
        with self.assertRaises(HabitNotFoundError) as ctx:
            find_habit([Habit("Leer")], " Leeer ")
        self.assertEqual(ctx.exception.name, "Leeer")


class MarkDoneTest(unittest.TestCase):
    def test_mark_done_records_today_ca_3_1(self) -> None:
        habits = [Habit("Leer")]
        self.assertTrue(mark_done(habits, "leer", WEDNESDAY))
        self.assertEqual(habits[0].done_dates, {WEDNESDAY})

    def test_mark_done_twice_is_noop_ca_3_2_cl_3(self) -> None:
        habits = [Habit("Leer", {WEDNESDAY})]
        self.assertFalse(mark_done(habits, "Leer", WEDNESDAY))
        self.assertEqual(habits[0].done_dates, {WEDNESDAY})

    def test_mark_done_unknown_habit_does_not_create_it_ca_3_3_cl_4(self) -> None:
        habits = [Habit("Leer")]
        with self.assertRaises(HabitNotFoundError):
            mark_done(habits, "Leeer", WEDNESDAY)
        self.assertEqual(habits, [Habit("Leer")])

    def test_mark_done_records_only_the_given_day_ca_3_4(self) -> None:
        habits = [Habit("Leer", {MONDAY})]
        mark_done(habits, "Leer", WEDNESDAY)
        self.assertEqual(habits[0].done_dates, {MONDAY, WEDNESDAY})


class RenameHabitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.habits = [Habit("Leer", {MONDAY, TUESDAY}), Habit("Repasar")]
        self.before = copy.deepcopy(self.habits)

    def test_rename_habit_keeps_history_ca_4_1_cl_9(self) -> None:
        habit = rename_habit(self.habits, "leer", "Lectura")
        self.assertEqual(habit.name, "Lectura")
        self.assertEqual(habit.done_dates, {MONDAY, TUESDAY})
        self.assertEqual(current_streak(habit, WEDNESDAY), 2)

    def test_rename_trims_new_name_ca_1_1(self) -> None:
        self.assertEqual(rename_habit(self.habits, "Leer", "  Lectura ").name, "Lectura")

    def test_rename_unknown_habit_raises_not_found_ca_4_2(self) -> None:
        with self.assertRaises(HabitNotFoundError):
            rename_habit(self.habits, "Yoga", "Pilates")
        self.assertEqual(self.habits, self.before)

    def test_rename_to_name_of_other_habit_is_rejected_ca_4_3_cl_8(self) -> None:
        with self.assertRaises(DuplicateHabitError) as ctx:
            rename_habit(self.habits, "Leer", "REPASAR")
        self.assertEqual(ctx.exception.name, "Repasar")
        self.assertEqual(self.habits, self.before)

    def test_rename_to_blank_name_is_rejected_ca_1_4(self) -> None:
        with self.assertRaises(EmptyNameError):
            rename_habit(self.habits, "Leer", "   ")
        self.assertEqual(self.habits, self.before)

    def test_rename_changing_only_case_is_allowed_ca_4_4(self) -> None:
        habit = rename_habit(self.habits, "Leer", "LEER")
        self.assertEqual(habit.name, "LEER")
        self.assertEqual(habit.done_dates, {MONDAY, TUESDAY})
        self.assertEqual(len(self.habits), 2)


class CurrentStreakTest(unittest.TestCase):
    def streak(self, *days: date, today: date = WEDNESDAY) -> int:
        return current_streak(Habit("Leer", set(days)), today)

    def test_streak_counts_up_to_today_when_marked_today_ca_6_1(self) -> None:
        self.assertEqual(self.streak(MONDAY, TUESDAY, WEDNESDAY), 3)

    def test_streak_only_today_is_one_ca_6_1(self) -> None:
        self.assertEqual(self.streak(WEDNESDAY), 1)

    def test_streak_counts_up_to_yesterday_when_today_pending_ca_6_2_cl_1(self) -> None:
        self.assertEqual(self.streak(MONDAY, TUESDAY), 2)

    def test_streak_is_zero_when_neither_today_nor_yesterday_ca_6_3(self) -> None:
        self.assertEqual(self.streak(MONDAY), 0)

    def test_streak_of_new_habit_is_zero_cl_2(self) -> None:
        self.assertEqual(self.streak(), 0)

    def test_streak_counts_only_last_continuous_run_cl_11(self) -> None:
        early = [date(2026, 11, d) for d in (1, 2, 3)]
        late = [date(2026, 11, d) for d in range(5, 12)]
        self.assertEqual(self.streak(*early, *late), 7)

    def test_streak_counts_each_day_once_ca_6_4_cl_12(self) -> None:
        self.assertEqual(current_streak(Habit("Leer", {TUESDAY, TUESDAY, MONDAY}), WEDNESDAY), 2)

    def test_streak_ignores_future_dates_cl_15(self) -> None:
        self.assertEqual(self.streak(TUESDAY, WEDNESDAY + ONE_DAY, WEDNESDAY + 2 * ONE_DAY), 1)
        self.assertEqual(self.streak(WEDNESDAY + ONE_DAY), 0)

    def test_streak_crosses_month_and_year_boundaries(self) -> None:
        days = (date(2026, 12, 30), date(2026, 12, 31), date(2027, 1, 1))
        self.assertEqual(self.streak(*days, today=date(2027, 1, 1)), 3)

    def test_streak_is_fast_with_large_history_rnf_6(self) -> None:
        history = {WEDNESDAY - n * ONE_DAY for n in range(5 * 365 + 1)}
        habits = [Habit(f"Hábito {i}", set(history)) for i in range(100)]
        start = time.perf_counter()
        streaks = [current_streak(habit, WEDNESDAY) for habit in habits]
        elapsed = time.perf_counter() - start
        self.assertEqual(streaks, [len(history)] * 100)
        self.assertLess(elapsed, 1.0)


class ListingHelpersTest(unittest.TestCase):
    def test_is_done_on_reports_marked_day_ca_5_1(self) -> None:
        habit = Habit("Leer", {TUESDAY})
        self.assertTrue(is_done_on(habit, TUESDAY))
        self.assertFalse(is_done_on(habit, WEDNESDAY))

    def test_sorted_habits_orders_alphabetically_ignoring_case_ca_5_2(self) -> None:
        habits = [Habit("yoga"), Habit("Leer"), Habit("árbol"), Habit("Bici")]
        names = [habit.name for habit in sorted_habits(habits)]
        self.assertEqual(names, ["árbol", "Bici", "Leer", "yoga"])

    def test_sorted_habits_does_not_mutate_input(self) -> None:
        habits = [Habit("yoga"), Habit("Leer")]
        sorted_habits(habits)
        self.assertEqual([habit.name for habit in habits], ["yoga", "Leer"])


if __name__ == "__main__":
    unittest.main()
