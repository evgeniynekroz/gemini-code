"""
Git integration tools for status, diff, review, and commits.
"""

import subprocess
from typing import Dict, Any, Optional

def _run_git(*args) -> Dict[str, Any]:
    try:
        res = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
        }
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e)}

def git_status() -> Dict[str, Any]:
    """Get concise git status."""
    return _run_git("status", "--short")

def git_diff(cached: bool = False) -> Dict[str, Any]:
    """Get uncommitted or staged changes."""
    args = ["diff"]
    if cached:
        args.append("--cached")
    return _run_git(*args)

def git_commit(message: str) -> Dict[str, Any]:
    """Stage all changes and create commit with message."""
    stage_res = _run_git("add", "-A")
    if stage_res["exit_code"] != 0:
        return {"error": f"Failed to stage files: {stage_res['stderr']}"}
    return _run_git("commit", "-m", message)

def git_undo(file_path: Optional[str] = None) -> Dict[str, Any]:
    """Discard unstaged changes for a specific file or all files."""
    if file_path:
        return _run_git("checkout", "--", file_path)
    return _run_git("checkout", "--", ".")
