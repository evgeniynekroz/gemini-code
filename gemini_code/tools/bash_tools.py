"""
Terminal command execution tool with cross-platform shell support.
"""

import sys
import asyncio
import subprocess
import time
from typing import Dict, Any

async def run_command(command: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Execute a terminal command using PowerShell (Windows) or Bash (Unix).
    """
    start_time = time.time()
    try:
        if sys.platform == "win32":
            shell_cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command]
        else:
            shell_cmd = ["/bin/bash", "-c", command]

        proc = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=float(timeout))
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds.",
                "duration_s": timeout,
            }

        duration = round(time.time() - start_time, 2)
        return {
            "exit_code": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "duration_s": duration,
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "duration_s": round(time.time() - start_time, 2),
        }
