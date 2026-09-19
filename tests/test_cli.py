"""
Unit tests for Gemini Code CLI argument handling, flags, and modes.
"""

import sys
import os
import io
import json
import subprocess
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from gemini_code import __version__
from gemini_code.cli import (
    build_parser,
    parse_cli_args,
    main,
    run_print_mode,
    verify_workspace_trust,
)
from gemini_code.config import config, CONFIG_DIR

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.original_model = config.model
        self.original_subagent = config.active_subagent
        self.original_confirm = config.confirm_danger_actions

    def tearDown(self):
        config.reset_overrides()

    def test_help_flag_exits_cleanly(self):
        """Verify -h and --help print usage and exit immediately with code 0 without blocking."""
        parser = build_parser()
        for flag in ["-h", "--help"]:
            with patch("sys.stdout", new=io.StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    parser.parse_args([flag])
                self.assertEqual(cm.exception.code, 0)
                output = fake_out.getvalue()
                self.assertIn("geminicode", output)
                self.assertIn("--print", output)
                self.assertIn("--version", output)

    def test_version_flag_exits_cleanly(self):
        """Verify -v, -V, and --version print version and exit immediately with code 0."""
        parser = build_parser()
        for flag in ["-v", "-V", "--version"]:
            with patch("sys.stdout", new=io.StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    parser.parse_args([flag])
                self.assertEqual(cm.exception.code, 0)
                output = fake_out.getvalue()
                self.assertIn(__version__, output)
                self.assertIn("Gemini Code", output)

    def test_main_help_does_not_call_trust_or_onboarding(self):
        """Verify calling main(['--help']) exits 0 without calling verify_workspace_trust or run_onboarding."""
        with patch("gemini_code.cli.verify_workspace_trust") as mock_trust, \
             patch("gemini_code.cli.run_onboarding") as mock_onboard, \
             patch("sys.stdout", new=io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                main(["--help"])
            self.assertEqual(cm.exception.code, 0)
            mock_trust.assert_not_called()
            mock_onboard.assert_not_called()

    def test_main_version_does_not_call_trust_or_onboarding(self):
        """Verify calling main(['-v']) exits 0 without calling verify_workspace_trust or run_onboarding."""
        with patch("gemini_code.cli.verify_workspace_trust") as mock_trust, \
             patch("gemini_code.cli.run_onboarding") as mock_onboard, \
             patch("sys.stdout", new=io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                main(["-v"])
            self.assertEqual(cm.exception.code, 0)
            mock_trust.assert_not_called()
            mock_onboard.assert_not_called()

    def test_parse_print_mode_flag_with_prompt(self):
        """Verify -p and --print with prompt string."""
        args1 = parse_cli_args(["-p", "write tests for cli"])
        self.assertEqual(args1.print_mode, "write tests for cli")

        args2 = parse_cli_args(["--print", "analyze diff"])
        self.assertEqual(args2.print_mode, "analyze diff")

        args3 = parse_cli_args(["-p"])
        self.assertTrue(args3.print_mode)

    def test_parse_positional_prompt(self):
        """Verify passing initial prompt as positional arguments."""
        args = parse_cli_args(["Explain", "this", "repository"])
        self.assertFalse(args.print_mode)
        self.assertEqual(args.prompt, ["Explain", "this", "repository"])

    def test_parse_model_override(self):
        """Verify model flag parsing and alias resolution."""
        args = parse_cli_args(["-m", "gemini-2.0-pro-exp-02-05", "prompt"])
        self.assertEqual(args.model, "gemini-2.0-pro-exp-02-05")

        with patch("gemini_code.cli.run_print_mode", new_callable=AsyncMock):
            with patch("sys.stdin.isatty", return_value=True):
                main(["-m", "pro", "-p", "hello"])
                self.assertEqual(config.model, "gemini-2.0-pro-exp-02-05")

    def test_parse_subagent_flag(self):
        """Verify subagent flag parsing."""
        args = parse_cli_args(["--subagent", "tester"])
        self.assertEqual(args.subagent, "tester")

        with patch("gemini_code.cli.run_print_mode", new_callable=AsyncMock):
            with patch("sys.stdin.isatty", return_value=True):
                main(["--subagent", "reviewer", "-p", "test"])
                self.assertEqual(config.active_subagent, "reviewer")

    def test_parse_skip_permissions_flags(self):
        """Verify -y, --dangerously-skip-permissions, and --trust."""
        for flag in ["-y", "--dangerously-skip-permissions", "--trust"]:
            args = parse_cli_args([flag, "prompt"])
            self.assertTrue(args.skip_permissions, f"Failed for {flag}")

    def test_main_dispatches_print_mode(self):
        """Verify main() dispatches to run_print_mode when -p is specified."""
        with patch("gemini_code.cli.run_print_mode", new_callable=AsyncMock) as mock_print:
            with patch("sys.stdin.isatty", return_value=True):
                main(["-p", "explain this file"])
                mock_print.assert_called_once_with("explain this file", skip_permissions=False)

    def test_main_dispatches_interactive_with_initial_prompt(self):
        """Verify main() dispatches to main_loop with initial_prompt when prompt passed without -p."""
        with patch("gemini_code.cli.main_loop", new_callable=AsyncMock) as mock_loop:
            with patch("sys.stdin.isatty", return_value=True):
                main(["Refactor", "utils.py"])
                mock_loop.assert_called_once_with(initial_prompt="Refactor utils.py", skip_permissions=False)

    def test_main_print_mode_missing_prompt_exits(self):
        """Verify main() exits with 1 when -p passed with no prompt and stdin is tty."""
        with patch("sys.stdin.isatty", return_value=True), \
             patch("gemini_code.cli.print_error") as mock_err, \
             self.assertRaises(SystemExit) as cm:
            main(["-p"])
        self.assertEqual(cm.exception.code, 1)
        mock_err.assert_called_once()

    def test_piped_stdin_in_print_mode(self):
        """Verify -p with piped stdin reads stdin and dispatches to run_print_mode."""
        with patch("sys.stdin.isatty", return_value=False), \
             patch("sys.stdin.read", return_value="print('hello from pipe')"), \
             patch("gemini_code.cli.run_print_mode", new_callable=AsyncMock) as mock_print:
            main(["-p"])
            mock_print.assert_called_once_with("print('hello from pipe')", skip_permissions=False)

    def test_piped_stdin_with_cli_prompt(self):
        """Verify prompt argument + piped stdin are concatenated."""
        with patch("sys.stdin.isatty", return_value=False), \
             patch("sys.stdin.read", return_value="def add(a, b): return a + b"), \
             patch("gemini_code.cli.run_print_mode", new_callable=AsyncMock) as mock_print:
            main(["-p", "Review this function:"])
            expected = "Review this function:\n\ndef add(a, b): return a + b"
            mock_print.assert_called_once_with(expected, skip_permissions=False)

    def test_piped_stdin_without_p_flag_auto_dispatches_print_mode(self):
        """Verify piped stdin without -p automatically runs print mode rather than attempting REPL."""
        with patch("sys.stdin.isatty", return_value=False), \
             patch("sys.stdin.read", return_value="Explain this repository"), \
             patch("gemini_code.cli.run_print_mode", new_callable=AsyncMock) as mock_print, \
             patch("gemini_code.cli.main_loop", new_callable=AsyncMock) as mock_loop:
            main([])
            mock_print.assert_called_once_with("Explain this repository", skip_permissions=False)
            mock_loop.assert_not_called()

    def test_piped_stdin_strips_bom_and_cp1251(self):
        """Verify PowerShell UTF-8 and CP1251 BOM artifacts are cleaned up."""
        # Unicode BOM
        with patch("sys.stdin.isatty", return_value=False), \
             patch("sys.stdin.read", return_value="\ufeffclean prompt"), \
             patch("gemini_code.cli.run_print_mode", new_callable=AsyncMock) as mock_print:
            main(["-p"])
            mock_print.assert_called_once_with("clean prompt", skip_permissions=False)

        # CP1251 decoded BOM
        with patch("sys.stdin.isatty", return_value=False), \
             patch("sys.stdin.read", return_value="п»їclean prompt 2"), \
             patch("gemini_code.cli.run_print_mode", new_callable=AsyncMock) as mock_print:
            main(["-p"])
            mock_print.assert_called_once_with("clean prompt 2", skip_permissions=False)

    def test_run_print_mode_failure_exits_1(self):
        """Verify run_print_mode exits with code 1 if agent.run_turn fails."""
        with patch("gemini_code.cli.config") as mock_cfg, \
             patch("gemini_code.cli.GeminiClient"), \
             patch("gemini_code.cli.Agent") as mock_agent_cls, \
             patch("gemini_code.cli.verify_workspace_trust", return_value=True):
            mock_cfg.api_key = "test-key"
            mock_cfg.language = "en"
            mock_cfg.theme = "safe"
            mock_agent = MagicMock()
            mock_agent.run_turn = AsyncMock(return_value=False)
            mock_agent_cls.return_value = mock_agent

            import asyncio
            with self.assertRaises(SystemExit) as cm:
                asyncio.run(run_print_mode("failing prompt"))
            self.assertEqual(cm.exception.code, 1)

    def test_verify_workspace_trust_auto_trust(self):
        """Verify auto_trust=True returns True without calling input()."""
        with patch("builtins.input", side_effect=AssertionError("Should not prompt")):
            self.assertTrue(verify_workspace_trust(auto_trust=True))

    def test_verify_workspace_trust_casing_normalization(self):
        """Verify workspace trust succeeds even with drive casing differences on Windows."""
        cwd = os.getcwd()
        # Toggle drive letter case
        if len(cwd) >= 2 and cwd[1] == ":":
            swapped = (cwd[0].lower() if cwd[0].isupper() else cwd[0].upper()) + cwd[1:]
        else:
            swapped = cwd

        mock_trusted = [swapped]
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_trusted))), \
             patch("builtins.input", side_effect=AssertionError("Should match trusted cache without prompting")):
            self.assertTrue(verify_workspace_trust(auto_trust=False))

    def test_verify_workspace_trust_rejection_exits_1(self):
        """Verify rejecting workspace trust exits with code 1."""
        with patch("pathlib.Path.exists", return_value=False), \
             patch("builtins.input", return_value="n"), \
             patch("sys.stdin.isatty", return_value=True), \
             self.assertRaises(SystemExit) as cm:
            verify_workspace_trust(auto_trust=False)
        self.assertEqual(cm.exception.code, 1)

    def test_verify_workspace_trust_non_interactive_exits_1(self):
        """Verify untrusted workspace in non-interactive stdin exits with code 1."""
        with patch("pathlib.Path.exists", return_value=False), \
             patch("sys.stdin.isatty", return_value=False), \
             self.assertRaises(SystemExit) as cm:
            verify_workspace_trust(auto_trust=False)
        self.assertEqual(cm.exception.code, 1)

    def test_config_reset_overrides(self):
        """Verify config.reset_overrides() clears session overrides."""
        config.model = "custom-test-model"
        config.active_subagent = "tester"
        config.confirm_danger_actions = False

        self.assertEqual(config.model, "custom-test-model")
        self.assertEqual(config.active_subagent, "tester")
        self.assertFalse(config.confirm_danger_actions)

        config.reset_overrides()
        self.assertEqual(config.active_subagent, "coder")
        self.assertTrue(config.confirm_danger_actions)

    def test_subprocess_help_and_version(self):
        """Real subprocess test to guarantee python -m gemini_code.cli exits immediately without hanging."""
        # Test help
        res_help = subprocess.run(
            [sys.executable, "-m", "gemini_code.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(res_help.returncode, 0)
        self.assertIn("geminicode", res_help.stdout)

        # Test version
        res_ver = subprocess.run(
            [sys.executable, "-m", "gemini_code.cli", "-v"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(res_ver.returncode, 0)
        self.assertIn(f"Gemini Code v{__version__}", res_ver.stdout)

    def test_subprocess_piped_help(self):
        """Real subprocess test piping into python -m gemini_code.cli."""
        proc = subprocess.run(
            [sys.executable, "-m", "gemini_code.cli", "--version"],
            input="ignored input",
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn(__version__, proc.stdout)

if __name__ == "__main__":
    unittest.main()
