"""Contract tests for the command line: outputs, streams and exit codes."""

import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from habits.cli import main
from habits.core import Habit
from habits.storage import load, save

MONDAY = date(2026, 11, 9)
TUESDAY = date(2026, 11, 10)
WEDNESDAY = date(2026, 11, 11)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORRUPT_PREFIX = "Error: no se puede leer el archivo de hábitos ("
ENGLISH_ARGPARSE_WORDS = ("usage", "error: ", "invalid choice", "required", "unrecognized", "arguments")


class CliTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.path = self.dir / "habits.json"

    def run_cli(self, *argv: str, today: date | None = WEDNESDAY) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv), today=today, data_path=self.path)
        return code, out.getvalue(), err.getvalue()

    def assert_ok(self, argv: tuple[str, ...], stdout: str, today: date = WEDNESDAY) -> None:
        self.assertEqual(self.run_cli(*argv, today=today), (0, stdout, ""))

    def assert_fails(self, argv: tuple[str, ...], stderr: str) -> None:
        before = self.path.read_bytes() if self.path.exists() else None
        self.assertEqual(self.run_cli(*argv), (1, "", stderr))
        after = self.path.read_bytes() if self.path.exists() else None
        self.assertEqual(after, before, "el archivo de datos no debe cambiar")


class UsageErrorsTest(CliTestCase):
    def assert_usage_error(self, *argv: str) -> str:
        code, out, err = self.run_cli(*argv)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("uso: python -m habits {crear,hecho,renombrar,listar} ...\n"), err)
        self.assertIn("\nError: ", err)
        self.assertFalse(self.path.exists())
        return err

    def test_unknown_command_shows_spanish_usage_ca_7_2(self) -> None:
        err = self.assert_usage_error("volar")
        self.assertIn("comando desconocido «volar»", err)

    def test_missing_command_shows_spanish_usage_ca_7_2(self) -> None:
        self.assertIn("falta el comando", self.assert_usage_error())

    def test_missing_argument_shows_spanish_usage_ca_7_2(self) -> None:
        self.assertIn("«crear» necesita: <nombre>", self.assert_usage_error("crear"))
        self.assertIn("«renombrar» necesita: <actual> <nuevo>", self.assert_usage_error("renombrar", "Leer"))

    def test_extra_argument_shows_spanish_usage_ca_7_2(self) -> None:
        self.assertIn("«listar» no admite argumentos", self.assert_usage_error("listar", "Leer"))

    def test_marking_another_date_is_not_allowed_ca_3_4(self) -> None:
        self.assert_usage_error("hecho", "Leer", "2026-11-01")

    def test_usage_errors_have_no_english_text_ca_7_1(self) -> None:
        for argv in ((), ("volar",), ("crear",), ("listar", "x"), ("crear", "-x"), ("-h",)):
            with self.subTest(argv=argv):
                err = self.assert_usage_error(*argv).lower()
                for word in ENGLISH_ARGPARSE_WORDS:
                    self.assertNotIn(word, err.replace("\nerror: ", "\n"))


class CrearTest(CliTestCase):
    def test_crear_creates_habit_ca_2_1(self) -> None:
        self.assert_ok(("crear", "Leer"), "Hábito «Leer» creado.\n")
        self.assertEqual(load(self.path), [Habit("Leer")])

    def test_crear_trims_name_and_keeps_case_ca_1_1_ca_1_3_cl_7(self) -> None:
        self.assert_ok(("crear", "  Repasar Inglés "), "Hábito «Repasar Inglés» creado.\n")
        self.assertEqual(load(self.path), [Habit("Repasar Inglés")])

    def test_crear_duplicate_is_rejected_ca_2_2_cl_5(self) -> None:
        self.run_cli("crear", "Leer")
        self.assert_fails(("crear", "leer"), "Error: ya existe el hábito «Leer».\n")

    def test_crear_blank_name_is_rejected_ca_1_4_cl_6(self) -> None:
        self.assert_fails(("crear", "   "), "Error: el nombre del hábito no puede estar vacío.\n")
        self.assertFalse(self.path.exists())


class HechoTest(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.run_cli("crear", "Leer")

    def test_hecho_marks_today_ca_3_1(self) -> None:
        self.assert_ok(("hecho", "Leer"), "Hábito «Leer» marcado como hecho hoy.\n")
        self.assertEqual(load(self.path)[0].done_dates, {WEDNESDAY})

    def test_hecho_shows_stored_name_ca_1_2_ca_1_3(self) -> None:
        self.assert_ok(("hecho", "  LEER "), "Hábito «Leer» marcado como hecho hoy.\n")

    def test_hecho_twice_does_not_change_data_ca_3_2_cl_3(self) -> None:
        self.run_cli("hecho", "Leer")
        before = self.path.read_bytes()
        with mock.patch("habits.storage.save") as save_mock:
            self.assert_ok(("hecho", "Leer"), "El hábito «Leer» ya estaba marcado hoy.\n")
        save_mock.assert_not_called()
        self.assertEqual(self.path.read_bytes(), before)

    def test_hecho_unknown_habit_does_not_create_it_ca_3_3_cl_4(self) -> None:
        self.assert_fails(("hecho", " Leeer "), "Error: no existe el hábito «Leeer».\n")
        self.assertEqual(load(self.path), [Habit("Leer")])

    def test_hecho_without_data_file_does_not_create_it_ca_3_3(self) -> None:
        self.path.unlink()
        self.assert_fails(("hecho", "Leer"), "Error: no existe el hábito «Leer».\n")
        self.assertFalse(self.path.exists())

    def test_hecho_uses_local_system_date_ca_3_4(self) -> None:
        before = date.today()
        code, _, _ = self.run_cli("hecho", "Leer", today=None)
        after = date.today()
        self.assertEqual(code, 0)
        (marked,) = load(self.path)[0].done_dates
        self.assertIn(marked, {before, after})

    def test_hecho_reads_the_date_once_at_start_cl_14(self) -> None:
        with mock.patch("habits.cli.date") as date_mock:
            date_mock.today.side_effect = [TUESDAY, WEDNESDAY]
            code, _, _ = self.run_cli("hecho", "Leer", today=None)
        self.assertEqual(code, 0)
        self.assertEqual(date_mock.today.call_count, 1)
        self.assertEqual(load(self.path)[0].done_dates, {TUESDAY})


class RenombrarTest(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.run_cli("crear", "Leer")
        self.run_cli("crear", "Repasar")

    def test_renombrar_keeps_history_and_streak_ca_4_1_cl_9(self) -> None:
        self.run_cli("hecho", "Leer", today=MONDAY)
        self.run_cli("hecho", "Leer", today=TUESDAY)
        self.assert_ok(("renombrar", "leer", "Lectura"), "Hábito «Leer» renombrado a «Lectura».\n")
        code, out, _ = self.run_cli("listar")
        self.assertEqual(code, 0)
        self.assertIn("✗ Lectura  racha: 2 días\n", out)
        self.assertNotIn("Leer", out)

    def test_renombrar_unknown_habit_is_rejected_ca_4_2(self) -> None:
        self.assert_fails(("renombrar", "X", "Y"), "Error: no existe el hábito «X».\n")

    def test_renombrar_to_existing_name_is_rejected_ca_4_3_cl_8(self) -> None:
        self.assert_fails(("renombrar", "Leer", "repasar"), "Error: ya existe el hábito «Repasar».\n")

    def test_renombrar_to_blank_name_is_rejected_ca_1_4(self) -> None:
        self.assert_fails(("renombrar", "Leer", "  "), "Error: el nombre del hábito no puede estar vacío.\n")

    def test_renombrar_changing_only_case_is_allowed_ca_4_4(self) -> None:
        self.assert_ok(("renombrar", "Leer", "LEER"), "Hábito «Leer» renombrado a «LEER».\n")
        self.assertEqual([h.name for h in load(self.path)], ["LEER", "Repasar"])


class ListarTest(CliTestCase):
    def test_listar_shows_mark_name_and_streak_ca_5_1_cl_1_cl_2(self) -> None:
        save(
            self.path,
            [
                Habit("Yoga"),
                Habit("Lectura", {MONDAY, TUESDAY, WEDNESDAY}),
                Habit("Repasar inglés", {TUESDAY}),
            ],
        )
        expected = (
            "✓ Lectura" + " " * 9 + "racha: 3 días\n"
            "✗ Repasar inglés" + " " * 2 + "racha: 1 día\n"
            "✗ Yoga" + " " * 12 + "racha: 0 días\n"
        )
        self.assert_ok(("listar",), expected)

    def test_listar_sorts_alphabetically_ignoring_case_ca_5_2(self) -> None:
        for name in ("yoga", "Leer", "árbol"):
            self.run_cli("crear", name)
        _, out, _ = self.run_cli("listar")
        self.assertEqual([line.split()[1] for line in out.splitlines()], ["árbol", "Leer", "yoga"])

    def test_listar_without_habits_ca_5_3_cl_10(self) -> None:
        save(self.path, [])
        self.assert_ok(("listar",), "No existen hábitos\n")

    def test_listar_on_first_use_rnf_3(self) -> None:
        self.assert_ok(("listar",), "No existen hábitos\n")
        self.assertFalse(self.path.exists())

    def test_listar_never_writes_data(self) -> None:
        save(self.path, [Habit("Leer", {TUESDAY})])
        with mock.patch("habits.storage.save") as save_mock:
            self.run_cli("listar")
        save_mock.assert_not_called()

    def test_listar_is_fast_with_large_history_rnf_6(self) -> None:
        history = {WEDNESDAY - timedelta(days=n) for n in range(5 * 365 + 1)}
        save(self.path, [Habit(f"Hábito {i:03}", set(history)) for i in range(100)])
        start = time.perf_counter()
        code, out, _ = self.run_cli("listar")
        elapsed = time.perf_counter() - start
        self.assertEqual(code, 0)
        self.assertEqual(out.count("racha: 1826 días"), 100)
        self.assertLess(elapsed, 1.0)


class CorruptDataTest(CliTestCase):
    def test_corrupt_file_is_reported_and_kept_rnf_4_cl_13(self) -> None:
        self.path.write_text("{ esto no es json", encoding="utf-8")
        for argv in (("crear", "Leer"), ("hecho", "Leer"), ("renombrar", "Leer", "Lectura"), ("listar",)):
            with self.subTest(argv=argv):
                before = self.path.read_bytes()
                code, out, err = self.run_cli(*argv)
                self.assertEqual((code, out), (1, ""))
                self.assertTrue(err.startswith(CORRUPT_PREFIX + str(self.path) + "): "), err)
                self.assertTrue(err.endswith(".\n"), err)
                self.assertEqual(self.path.read_bytes(), before)


class EntryPointTest(CliTestCase):
    def run_module(self, *argv: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "HABITS_FILE": str(self.path), "PYTHONIOENCODING": "utf-8"}
        return subprocess.run(
            [sys.executable, "-m", "habits", *argv],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_python_m_habits_runs_rnf_1(self) -> None:
        result = self.run_module("listar")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "No existen hábitos\n", ""))

    def test_python_m_habits_persists_between_runs_rnf_1(self) -> None:
        self.assertEqual(self.run_module("crear", "Leer").returncode, 0)
        self.assertEqual(self.run_module("hecho", "Leer").returncode, 0)
        result = self.run_module("listar")
        self.assertEqual(result.stdout, "✓ Leer  racha: 1 día\n")

    def test_python_m_habits_returns_usage_exit_code_ca_7_2(self) -> None:
        self.assertEqual(self.run_module("volar").returncode, 2)


if __name__ == "__main__":
    unittest.main()
