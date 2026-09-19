"""
File system manipulation tools: View, Create, Edit (diff-based), and Delete.
"""

import os
import difflib
from pathlib import Path
from typing import Dict, Any, Optional

def view_file(path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
    """Read file content with 1-indexed line numbers."""
    target = Path(path)
    if not target.exists():
        return {"error": f"File not found: {path}"}
    if not target.is_file():
        return {"error": f"Path is not a file: {path}"}

    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        s_line = max(1, start_line) if start_line else 1
        e_line = min(total_lines, end_line) if end_line else total_lines

        numbered_lines = []
        for idx in range(s_line - 1, e_line):
            numbered_lines.append(f"{idx + 1:5d} | {lines[idx]}")

        return {
            "path": str(target),
            "total_lines": total_lines,
            "start_line": s_line,
            "end_line": e_line,
            "content": "".join(numbered_lines),
        }
    except Exception as e:
        return {"error": f"Failed to read file {path}: {str(e)}"}

def create_file(path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    """Create a new file or overwrite existing with safety flag."""
    target = Path(path)
    if target.exists() and not overwrite:
        return {"error": f"File already exists: {path}. Set overwrite=True to replace."}

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": str(target), "bytes_written": len(content.encode("utf-8"))}
    except Exception as e:
        return {"error": f"Failed to create file {path}: {str(e)}"}

def compute_diff(original: str, modified: str, filename: str) -> str:
    """Generate unified diff between original and modified text."""
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    return "".join(diff)

def edit_file(path: str, old_text: str, new_text: str) -> Dict[str, Any]:
    """
    Replace unique occurrence of old_text with new_text and calculate unified diff.
    Handles Windows CRLF vs Unix LF normalization seamlessly.
    """
    target = Path(path)
    if not target.exists():
        return {"error": f"File not found: {path}"}

    try:
        with open(target, "r", encoding="utf-8", errors="replace", newline="") as f:
            raw_content = f.read()

        is_crlf = "\r\n" in raw_content
        content = raw_content.replace("\r\n", "\n")
        normalized_old = old_text.replace("\r\n", "\n")
        normalized_new = new_text.replace("\r\n", "\n")

        if normalized_old not in content:
            # Try strip trailing whitespace on each line as fallback
            stripped_content = "\n".join(l.rstrip() for l in content.split("\n"))
            stripped_old = "\n".join(l.rstrip() for l in normalized_old.split("\n"))
            if stripped_old in stripped_content:
                # Found with stripped lines! Replace using stripped mapping
                count = stripped_content.count(stripped_old)
                if count > 1:
                    return {"error": f"Target content is ambiguous ({count} occurrences found in {path}). Provide more surrounding context."}
                
                # Locate and replace
                idx = stripped_content.find(stripped_old)
                prefix_lines = stripped_content[:idx].count("\n")
                old_line_count = stripped_old.count("\n") + 1
                all_orig_lines = content.split("\n")
                new_content_lines = all_orig_lines[:prefix_lines] + normalized_new.split("\n") + all_orig_lines[prefix_lines + old_line_count:]
                new_content = "\n".join(new_content_lines)
            else:
                return {"error": f"Target content not found in file: {path}"}
        else:
            count = content.count(normalized_old)
            if count > 1:
                return {"error": f"Target content is ambiguous (found {count} occurrences in {path}). Provide more surrounding context."}
            new_content = content.replace(normalized_old, normalized_new, 1)

        diff = compute_diff(content, new_content, target.name)

        # Restore CRLF if file was CRLF originally
        final_write = new_content.replace("\n", "\r\n") if is_crlf else new_content
        with open(target, "w", encoding="utf-8", newline="") as f:
            f.write(final_write)

        return {
            "success": True,
            "path": str(target),
            "diff": diff,
            "message": f"Successfully updated {path}",
        }
    except Exception as e:
        return {"error": f"Failed to edit file {path}: {str(e)}"}

def delete_file(path: str) -> Dict[str, Any]:
    """Delete a file with safety check."""
    target = Path(path)
    if not target.exists():
        return {"error": f"File not found: {path}"}
    try:
        target.unlink()
        return {"success": True, "path": str(target)}
    except Exception as e:
        return {"error": f"Failed to delete {path}: {str(e)}"}
