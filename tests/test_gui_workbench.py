"""Smoke tests for the local browser GUI workbench."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from d2re import cli, gui


class GuiWorkbenchTests(unittest.TestCase):
    def test_render_workbench_contains_accessibility_and_design_tokens(self) -> None:
        html = gui.render_workbench()

        self.assertIn("D2RE Visual Workbench", html)
        self.assertIn("Skip to workbench modules", html)
        self.assertIn("--surface-panel", html)
        self.assertIn("prefers-reduced-motion", html)
        self.assertIn("aria-live", html)
        self.assertIn("Treasure Labyrinth", html)

    def test_write_workbench_creates_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workbench.html"
            written = gui.write_workbench(output)

            self.assertEqual(written, output.resolve())
            self.assertTrue(written.exists())
            self.assertIn("Visual Workbench", written.read_text(encoding="utf-8"))

    def test_gui_main_writes_without_opening_browser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workbench.html"
            buffer = io.StringIO()
            with redirect_stdout(buffer), patch("webbrowser.open") as mocked_open:
                code = gui.main(["--out", str(output), "--no-open"])

            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            mocked_open.assert_not_called()
            self.assertIn("Visual Workbench written", buffer.getvalue())

    def test_unified_cli_gui_dispatches_to_workbench(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workbench.html"
            buffer = io.StringIO()
            with redirect_stdout(buffer), patch("webbrowser.open") as mocked_open:
                code = cli.main(["gui", "--out", str(output), "--no-open"])

            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            mocked_open.assert_not_called()
            self.assertIn("Visual Workbench written", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
