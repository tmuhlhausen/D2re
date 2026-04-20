"""Smoke tests for the local browser GUI workbench."""

from __future__ import annotations

import http.client
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from d2re import cli, gui


class GuiWorkbenchTests(unittest.TestCase):
    def test_render_workbench_contains_accessibility_and_design_tokens(self) -> None:
        html = gui.render_workbench(server_mode=True, csrf_token="test-token")

        self.assertIn("D2RE Visual Workbench", html)
        self.assertIn("Skip to workbench modules", html)
        self.assertIn("--panel", html)
        self.assertIn("prefers-reduced-motion", html)
        self.assertIn("aria-live", html)
        self.assertIn("Treasure Labyrinth", html)
        self.assertIn("/api/run", html)
        self.assertIn("test-token", html)

    def test_render_workbench_contains_beautified_ide_features(self) -> None:
        html = gui.render_workbench(server_mode=True, csrf_token="test-token")

        self.assertIn("Runic Workbench", html)
        self.assertIn("Command palette", html)
        self.assertIn("Run History", html)
        self.assertIn("Favorites", html)
        self.assertIn("Pretty JSON", html)
        self.assertIn("d2re.favorites", html)
        self.assertIn("data-theme=", html)
        self.assertIn("packet-demo", html)

    def test_write_workbench_creates_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workbench.html"
            written = gui.write_workbench(output)

            self.assertEqual(written, output.resolve())
            self.assertTrue(written.exists())
            self.assertIn("Runic Workbench", written.read_text(encoding="utf-8"))

    def test_gui_main_writes_static_file_without_opening_browser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workbench.html"
            buffer = io.StringIO()
            with redirect_stdout(buffer), patch("webbrowser.open") as mocked_open:
                code = gui.main(["--out", str(output), "--no-open"])

            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            mocked_open.assert_not_called()
            self.assertIn("Visual Workbench written", buffer.getvalue())

    def test_unified_cli_gui_dispatches_to_workbench_static_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workbench.html"
            buffer = io.StringIO()
            with redirect_stdout(buffer), patch("webbrowser.open") as mocked_open:
                code = cli.main(["gui", "--out", str(output), "--no-open"])

            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            mocked_open.assert_not_called()
            self.assertIn("Visual Workbench written", buffer.getvalue())

    def test_bare_cli_launches_gui_by_default(self) -> None:
        with patch("d2re.cli._dispatch", return_value=0) as dispatch:
            code = cli.main([])

        self.assertEqual(code, 0)
        dispatch.assert_called_once_with("d2re.gui", [], "d2re-gui")

    def test_no_gui_flag_prints_help_instead_of_launching_gui(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer), patch("d2re.cli._dispatch") as dispatch:
            code = cli.main(["--no-gui"])

        self.assertEqual(code, 0)
        self.assertIn("Unified CLI", buffer.getvalue())
        dispatch.assert_not_called()

    def test_build_command_for_treasure_class_action(self) -> None:
        action = gui.action_by_key("treasure-class")
        self.assertIsNotNone(action)
        assert action is not None

        argv = gui.build_command(
            action,
            {"tc": "Act 5 Super C", "top": "10", "resolve": True, "json": False},
        )

        self.assertEqual(argv, ["--tc", "Act 5 Super C", "--top", "10", "--resolve"])
        self.assertIn("'Act 5 Super C'", gui.format_command(action, argv))

    def test_run_action_uses_predefined_module_not_shell(self) -> None:
        completed = Mock(returncode=0, stdout="ok", stderr="")
        with patch("subprocess.run", return_value=completed) as run:
            result = gui.run_action("packet-timeline", {"demo": True, "verbose": True})

        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout"], "ok")
        command = run.call_args.args[0]
        self.assertIn("-m", command)
        self.assertIn("scripts.packet_sniffer", command)
        self.assertIn("--demo", command)
        self.assertIn("--verbose", command)

    def test_gui_server_no_wait_prints_url_and_shuts_down(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer), patch("webbrowser.open") as mocked_open:
            code = gui.main(["--no-open", "--print-path", "--no-wait"])

        self.assertEqual(code, 0)
        self.assertIn("http://127.0.0.1:", buffer.getvalue())
        mocked_open.assert_not_called()

    def test_loopback_server_rejects_missing_token(self) -> None:
        server, url = gui.serve_workbench(open_browser=False)
        try:
            port = int(url.rsplit(":", 1)[1].rstrip("/"))
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            body = json.dumps({"action": "packet-timeline", "values": {"demo": True}})
            conn.request("POST", "/api/run", body=body, headers={"Content-Type": "application/json"})
            response = conn.getresponse()
            self.assertEqual(response.status, 403)
            self.assertIn("Invalid workbench token", response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
