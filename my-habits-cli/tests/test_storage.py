"""Tests for persistence: first use, round trip, corrupt data and atomic writes."""

import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from habits.core import Habit
from habits.storage import CorruptDataError, default_path, load, save

MONDAY = date(2026, 11, 9)
TUESDAY = date(2026, 11, 10)
WEDNESDAY = date(2026, 11, 11)


class StorageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.path = self.dir / "habits.json"

    def write_raw(self, content: str | bytes) -> None:
        if isinstance(content, bytes):
            self.path.write_bytes(content)
        else:
            self.path.write_text(content, encoding="utf-8")


class DefaultPathTest(unittest.TestCase):
    def test_default_path_uses_habits_file_env_rnf_1(self) -> None:
        with mock.patch.dict(os.environ, {"HABITS_FILE": "/tmp/otro/habits.json"}):
            self.assertEqual(default_path(), Path("/tmp/otro/habits.json"))

    def test_default_path_defaults_to_home_rnf_1(self) -> None:
        with mock.patch.dict(os.environ):
            os.environ.pop("HABITS_FILE", None)
            self.assertEqual(default_path(), Path.home() / "habits.json")


class LoadSaveTest(StorageTestCase):
    def test_load_missing_file_returns_no_habits_rnf_3(self) -> None:
        self.assertEqual(load(self.path), [])
        self.assertFalse(self.path.exists())

    def test_save_then_load_round_trip_rnf_1(self) -> None:
        habits = [Habit("Leer", {MONDAY, TUESDAY}), Habit("Repasar inglés")]
        save(self.path, habits)
        self.assertEqual(load(self.path), habits)

    def test_saved_file_has_documented_format_rnf_2(self) -> None:
        save(self.path, [Habit("Leer", {WEDNESDAY, MONDAY, TUESDAY}), Habit("Yoga")])
        self.assertEqual(
            json.loads(self.path.read_text(encoding="utf-8")),
            {
                "version": 1,
                "habits": [
                    {"name": "Leer", "done": ["2026-11-09", "2026-11-10", "2026-11-11"]},
                    {"name": "Yoga", "done": []},
                ],
            },
        )

    def test_saved_file_is_human_readable_rnf_2(self) -> None:
        save(self.path, [Habit("Repasar inglés", {TUESDAY})])
        text = self.path.read_text(encoding="utf-8")
        self.assertIn('"Repasar inglés"', text)
        self.assertNotIn("\\u00e9", text)
        self.assertIn("\n  ", text)

    def test_load_keeps_original_case_ca_1_3(self) -> None:
        save(self.path, [Habit("Repasar Inglés")])
        self.assertEqual(load(self.path)[0].name, "Repasar Inglés")

    def test_load_tolerates_duplicate_dates_ca_6_4_cl_12(self) -> None:
        self.write_raw(
            '{"version": 1, "habits": [{"name": "Leer", "done": '
            '["2026-11-10", "2026-11-10", "2026-11-09"]}]}'
        )
        habits = load(self.path)
        self.assertEqual(habits[0].done_dates, {MONDAY, TUESDAY})
        save(self.path, habits)
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved["habits"][0]["done"], ["2026-11-09", "2026-11-10"])

    def test_load_keeps_future_dates_cl_15(self) -> None:
        self.write_raw('{"version": 1, "habits": [{"name": "Leer", "done": ["2030-01-01"]}]}')
        self.assertEqual(load(self.path)[0].done_dates, {date(2030, 1, 1)})

    def test_save_creates_missing_parent_directory(self) -> None:
        path = self.dir / "nuevo" / "habits.json"
        save(path, [Habit("Leer")])
        self.assertEqual(load(path), [Habit("Leer")])


class CorruptDataTest(StorageTestCase):
    CASES: dict[str, str | bytes] = {
        "invalid json": "{",
        "invalid utf-8": b'{"version": 1, "habits": [{"name": "\xff", "done": []}]}',
        "root is not an object": "[]",
        "missing habits": '{"version": 1}',
        "habits is not a list": '{"version": 1, "habits": {}}',
        "missing version": '{"habits": []}',
        "unsupported version": '{"version": 2, "habits": []}',
        "boolean version": '{"version": true, "habits": []}',
        "habit is not an object": '{"version": 1, "habits": ["Leer"]}',
        "missing name": '{"version": 1, "habits": [{"done": []}]}',
        "name is not text": '{"version": 1, "habits": [{"name": 5, "done": []}]}',
        "blank name": '{"version": 1, "habits": [{"name": "  ", "done": []}]}',
        "missing done": '{"version": 1, "habits": [{"name": "Leer"}]}',
        "done is not a list": '{"version": 1, "habits": [{"name": "Leer", "done": "2026-11-10"}]}',
        "date is not text": '{"version": 1, "habits": [{"name": "Leer", "done": [20261110]}]}',
        "impossible date": '{"version": 1, "habits": [{"name": "Leer", "done": ["2026-02-30"]}]}',
        "slash date": '{"version": 1, "habits": [{"name": "Leer", "done": ["2026/11/10"]}]}',
        "compact date": '{"version": 1, "habits": [{"name": "Leer", "done": ["20261110"]}]}',
        "date with time": '{"version": 1, "habits": [{"name": "Leer", "done": ["2026-11-10T08:00"]}]}',
        "duplicate names": (
            '{"version": 1, "habits": [{"name": "Leer", "done": []}, '
            '{"name": " leer ", "done": []}]}'
        ),
    }

    def test_load_rejects_corrupt_data_without_touching_it_rnf_4_cl_13(self) -> None:
        for case, content in self.CASES.items():
            with self.subTest(case=case):
                self.write_raw(content)
                before = self.path.read_bytes()
                with self.assertRaises(CorruptDataError) as ctx:
                    load(self.path)
                self.assertEqual(ctx.exception.path, self.path)
                self.assertTrue(ctx.exception.reason)
                self.assertEqual(self.path.read_bytes(), before)


class AtomicSaveTest(StorageTestCase):
    def test_failed_save_keeps_previous_file_rnf_5(self) -> None:
        save(self.path, [Habit("Leer", {MONDAY})])
        before = self.path.read_bytes()
        with mock.patch("habits.storage.os.replace", side_effect=OSError("disco lleno")):
            with self.assertRaises(OSError):
                save(self.path, [Habit("Leer", {MONDAY, TUESDAY}), Habit("Yoga")])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["habits.json"])


if __name__ == "__main__":
    unittest.main()
