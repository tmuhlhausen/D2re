"""Smoke tests for the local browser GUI command center."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from d2re import cli, gui


class GuiWorkbenchTests(unittest.TestCase):
    def test_render_workbench_contains_accessibility_tokens_and_command_center(self) -> None:
        html = gui.render_workbench()

        self.assertIn("D2RE Command Center", html)
        self.assertIn("Skip to command center", html)
        self.assertIn("--surface-panel", html)
        self.assertIn("prefers-reduced-motion", html)
        self.assertIn("aria-live", html)
        self.assertIn("Treasure Labyrinth", html)
        self.assertIn("Command builders", html)
        self.assertIn("Workflow recipes", html)
        self.assertIn("d2re parse", html)
        self.assertIn("d2re gui", html)

    def test_model_contains_all_public_command_specs(self) -> None:
        model = gui.build_model()
        spec_ids = {spec.id for spec in model.command_specs}

        self.assertEqual(
            spec_ids,
            {"parse", "roll", "extract", "sniff", "map", "tc", "drops", "gui", "doctor"},
        )

    def test_write_workbench_creates_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workbench.html"
            written = gui.write_workbench(output)

            self.assertEqual(written, output.resolve())
            self.assertTrue(written.exists())
            self.assertIn("Command Center", written.read_text(encoding="utf-8"))

    def test_gui_main_writes_without_opening_browser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workbench.html"
            buffer = io.StringIO()
            with redirect_stdout(buffer), patch("webbrowser.open") as mocked_open:
                code = gui.main(["--out", str(output), "--no-open"])

            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            mocked_open.assert_not_called()
            self.assertIn("Command Center written", buffer.getvalue())

    def test_unified_cli_gui_dispatches_to_workbench(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workbench.html"
            buffer = io.StringIO()
            with redirect_stdout(buffer), patch("webbrowser.open") as mocked_open:
                code = cli.main(["gui", "--out", str(output), "--no-open"])

            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            mocked_open.assert_not_called()
            self.assertIn("Command Center written", buffer.getvalue())

    def test_plain_d2re_opens_gui_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "startup.html"
            # The default entry point does not accept --out, so patch the writer to
            # prove that plain d2re dispatches into d2re.gui without opening a browser.
            with patch("d2re.gui.write_workbench", return_value=output.resolve()) as mocked_write:
                with patch("webbrowser.open") as mocked_open:
                    code = cli.main([])

            self.assertEqual(code, 0)
            mocked_write.assert_called_once()
            mocked_open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
