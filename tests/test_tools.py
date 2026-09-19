"""
Tests for Gemini Code tools: file operations, CRLF handling, search, and command execution.
"""

import os
import sys
import shutil
import tempfile
import unittest
import asyncio
from pathlib import Path

from gemini_code.tools.file_tools import (
    create_file,
    view_file,
    edit_file,
    delete_file,
    compute_diff,
)
from gemini_code.tools.search_tools import glob_files, grep_search, list_dir
from gemini_code.tools.bash_tools import run_command

class TestTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="gemini_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_and_view_file(self):
        """Verify file creation and slice-based reading."""
        target = Path(self.test_dir) / "sample.py"
        content = "line 1\nline 2\nline 3\nline 4\nline 5\n"
        res = create_file(str(target), content)
        self.assertTrue(res.get("success"))

        # View full file
        v_res = view_file(str(target))
        self.assertEqual(v_res.get("total_lines"), 5)
        self.assertIn("line 1", v_res.get("content", ""))

        # View slice (lines 2 to 4)
        v_slice = view_file(str(target), start_line=2, end_line=4)
        self.assertEqual(v_slice.get("start_line"), 2)
        self.assertEqual(v_slice.get("end_line"), 4)
        self.assertIn("line 2", v_slice.get("content", ""))
        self.assertNotIn("line 1", v_slice.get("content", ""))

    def test_edit_file_unix_newlines(self):
        """Verify surgical edit with Unix LF newlines."""
        target = Path(self.test_dir) / "test_lf.py"
        create_file(str(target), "def hello():\n    return 'old'\n")
        
        edit_res = edit_file(str(target), "return 'old'", "return 'new'")
        self.assertTrue(edit_res.get("success"))
        self.assertIn("+    return 'new'", edit_res.get("diff", ""))

        with open(target, "r", encoding="utf-8") as f:
            updated = f.read()
        self.assertIn("return 'new'", updated)

    def test_edit_file_crlf_newlines(self):
        """Verify surgical edit on Windows files with CRLF newlines."""
        target = Path(self.test_dir) / "test_crlf.py"
        # Write explicit CRLF
        with open(target, "wb") as f:
            f.write(b"def foo():\r\n    x = 10\r\n    return x\r\n")

        # Edit using LF strings from LLM
        edit_res = edit_file(str(target), "    x = 10", "    x = 20")
        self.assertTrue(edit_res.get("success"), edit_res.get("error"))

        with open(target, "rb") as f:
            updated = f.read()
        self.assertIn(b"x = 20", updated)
        # Verify CRLF is preserved
        self.assertIn(b"\r\n", updated)

    def test_delete_file(self):
        """Verify safe file deletion."""
        target = Path(self.test_dir) / "to_delete.txt"
        create_file(str(target), "temp content")
        self.assertTrue(target.exists())

        del_res = delete_file(str(target))
        self.assertTrue(del_res.get("success"))
        self.assertFalse(target.exists())

    def test_search_tools(self):
        """Verify glob_files, grep_search, and list_dir."""
        sub = Path(self.test_dir) / "sub"
        sub.mkdir()
        create_file(str(sub / "a.py"), "def find_me(): pass\n")
        create_file(str(sub / "b.txt"), "hello world\n")

        # Glob
        glob_res = glob_files("*.py", directory=str(sub))
        self.assertEqual(glob_res.get("count"), 1)
        self.assertIn("a.py", glob_res.get("matches", []))

        # Grep
        grep_res = grep_search("find_me", directory=str(self.test_dir))
        self.assertEqual(grep_res.get("count"), 1)
        self.assertIn("find_me", grep_res.get("results", [])[0]["text"])

        # List dir
        list_res = list_dir(str(self.test_dir))
        self.assertGreaterEqual(list_res.get("count"), 2)

    def test_run_command(self):
        """Verify terminal command execution and cwd handling."""
        cmd = "echo hello_gemini"
        res = asyncio.run(run_command(cmd, cwd=self.test_dir))
        self.assertEqual(res.get("exit_code"), 0)
        self.assertIn("hello_gemini", res.get("stdout", ""))

    def test_edit_file_not_found(self):
        """Verify editing a non-existent file returns error."""
        res = edit_file(str(Path(self.test_dir) / "does_not_exist.py"), "a", "b")
        self.assertIn("error", res)

    def test_edit_file_target_content_missing(self):
        """Verify editing when old_text is missing returns error."""
        target = Path(self.test_dir) / "test_missing.py"
        create_file(str(target), "foo = 1\nbar = 2\n")
        res = edit_file(str(target), "baz = 3", "baz = 4")
        self.assertIn("error", res)
        self.assertIn("Target content not found", res["error"])

    def test_edit_file_ambiguous_content(self):
        """Verify editing when old_text matches multiple times returns error."""
        target = Path(self.test_dir) / "test_ambiguous.py"
        create_file(str(target), "x = 1\nx = 1\n")
        res = edit_file(str(target), "x = 1", "x = 2")
        self.assertIn("error", res)
        self.assertIn("ambiguous", res["error"])

    def test_view_file_non_existent(self):
        """Verify viewing a non-existent file returns error."""
        res = view_file(str(Path(self.test_dir) / "no_such_file.txt"))
        self.assertIn("error", res)

    def test_delete_file_non_existent(self):
        """Verify deleting a non-existent file returns error."""
        res = delete_file(str(Path(self.test_dir) / "no_such_file.txt"))
        self.assertIn("error", res)

    def test_run_command_error(self):
        """Verify running a failing command captures non-zero exit code."""
        # Run command with non-zero exit
        cmd = "exit 42" if sys.platform == "win32" else "exit 42"
        res = asyncio.run(run_command(cmd, cwd=self.test_dir))
        self.assertEqual(res.get("exit_code"), 42)

if __name__ == "__main__":
    unittest.main()
