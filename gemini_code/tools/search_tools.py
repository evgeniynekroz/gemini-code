"""
Codebase search tools: Glob, Grep, and Directory Tree listing.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List

IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode", "dist", "build"}

def glob_files(pattern: str, directory: str = ".") -> Dict[str, Any]:
    """Find files matching a glob pattern."""
    base = Path(directory).resolve()
    if not base.exists():
        return {"error": f"Directory does not exist: {directory}"}

    matches: List[str] = []
    try:
        for p in base.glob(pattern):
            # Skip ignored directories
            if any(part in IGNORED_DIRS for part in p.parts):
                continue
            if p.is_file():
                matches.append(str(p.relative_to(base)))
                if len(matches) >= 100:
                    break
        return {"directory": str(base), "matches": matches, "count": len(matches)}
    except Exception as e:
        return {"error": f"Glob error: {str(e)}"}

def grep_search(query: str, directory: str = ".", is_regex: bool = False, max_results: int = 50) -> Dict[str, Any]:
    """Search for pattern or text occurrences across project files."""
    base = Path(directory).resolve()
    if not base.exists():
        return {"error": f"Directory does not exist: {directory}"}

    results: List[Dict[str, Any]] = []
    flags = re.IGNORECASE
    try:
        matcher = re.compile(query if is_regex else re.escape(query), flags)
    except re.error as e:
        return {"error": f"Invalid regex pattern: {str(e)}"}

    for root, dirs, files in os.walk(base):
        # Filter ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            file_path = Path(root) / file
            # Only inspect text files under 2MB
            if file_path.stat().st_size > 2 * 1024 * 1024:
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        if matcher.search(line):
                            results.append({
                                "file": str(file_path.relative_to(base)),
                                "line": line_no,
                                "text": line.strip()[:200],
                            })
                            if len(results) >= max_results:
                                return {"results": results, "capped": True}
            except Exception:
                continue

    return {"results": results, "capped": False, "count": len(results)}

def list_dir(directory: str = ".", max_depth: int = 2) -> Dict[str, Any]:
    """List directory contents with recursive depth and sizes."""
    base = Path(directory).resolve()
    if not base.exists():
        return {"error": f"Directory does not exist: {directory}"}

    items: List[Dict[str, Any]] = []
    base_depth = len(base.parts)

    for root, dirs, files in os.walk(base):
        curr_depth = len(Path(root).parts) - base_depth
        if curr_depth > max_depth:
            dirs.clear()
            continue

        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for d in dirs:
            dir_path = Path(root) / d
            items.append({
                "path": str(dir_path.relative_to(base)),
                "type": "directory",
            })

        for f in files:
            file_path = Path(root) / f
            items.append({
                "path": str(file_path.relative_to(base)),
                "type": "file",
                "size_bytes": file_path.stat().st_size,
            })

        if len(items) >= 150:
            break

    return {"directory": str(base), "items": items, "count": len(items)}
