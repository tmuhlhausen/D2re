"""Smoke tests for intentionally disabled command surfaces.

These tests protect the cleanup contract: planned commands can remain visible,
but they must fail clearly instead of crashing with missing imports or silently
pretending to work.
"""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from typing import Callable

from d2re import cli
from tools import item_roller_impl


class DisabledCommandTests(unittest.TestCase):
    def capture_return(self, func: Callable[[], int]) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = func()
        return code, buffer.getvalue()

    def test_doctor_command_is_registered_but_disabled(self) -> None:
        code, output = self.capture_return(lambda: cli.main(["doctor"]))

        self.assertEqual(code, 2)
        self.assertIn("temporarily disabled", output)
        self.assertIn("doctor", output)

    def test_doctor_console_entrypoint_is_disabled(self) -> None:
        code, output = self.capture_return(cli.doctor_main)

        self.assertEqual(code, 2)
        self.assertIn("temporarily disabled", output)
        self.assertIn("doctor", output)

    def test_item_roller_brute_force_flags_are_disabled(self) -> None:
        old_argv = sys.argv[:]
        sys.argv = ["item_roller.py", "--brute", "--target", "Stone of Jordan"]
        try:
            code, output = self.capture_return(item_roller_impl.main)
        finally:
            sys.argv = old_argv

        self.assertEqual(code, 2)
        self.assertIn("brute-force seed search is temporarily disabled", output)
        self.assertIn("implemented incrementally", output)


if __name__ == "__main__":
    unittest.main()
