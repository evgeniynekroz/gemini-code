"""
Rich terminal UI renderer inspired by Claude Code.
Provides clean collapsible-style tool execution badges, unified diffs, thinking panels, and streaming markdown.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .symbols import sym, get_box

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(highlight=False, legacy_windows=False)

TOOL_DISPLAY_NAMES = {
    "view_file": "ViewFile",
    "edit_file": "EditFile",
    "create_file": "CreateFile",
    "delete_file": "DeleteFile",
    "run_command": "RunCommand",
    "glob_files": "Glob",
    "grep_search": "Grep",
    "list_dir": "ListDir",
    "git_status": "GitStatus",
    "git_diff": "GitDiff",
    "git_commit": "GitCommit",
    "git_undo": "GitUndo",
}

def print_markdown(content: str):
    """Render markdown with syntax highlighting."""
    if not content or not content.strip():
        return
    md = Markdown(content.strip())
    console.print(md)

def print_diff(diff_text: str, filename: str = ""):
    """Render unified diff with colored additions, deletions, and line markers."""
    if not diff_text.strip():
        return

    title = f"{sym.TOOL} Diff: {filename}" if filename else f"{sym.TOOL} Unified Diff"
    table = Table.grid(padding=(0, 1))
    table.add_column("Line", style="dim", justify="right")
    table.add_column("Content")

    lines = diff_text.splitlines()
    for idx, line in enumerate(lines, 1):
        if line.startswith("+") and not line.startswith("+++"):
            table.add_row(str(idx), Text(line, style="bold green"))
        elif line.startswith("-") and not line.startswith("---"):
            table.add_row(str(idx), Text(line, style="bold red"))
        elif line.startswith("@@"):
            table.add_row(str(idx), Text(line, style="bold cyan"))
        else:
            table.add_row(str(idx), Text(line, style="dim white"))

    panel = Panel(
        table,
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        box=get_box(),
        subtitle="[green]+ addition[/green] | [red]- deletion[/red]",
    )
    console.print(panel)

def print_tool_call(tool_name: str, args: dict):
    """Display clean Claude Code style badge for tool invocation."""
    display_name = TOOL_DISPLAY_NAMES.get(tool_name, tool_name)
    
    # Format primary argument compactly
    arg_summary = []
    for k, v in args.items():
        if k in ("content", "old_text", "new_text"):
            # Truncate long content previews
            lines = str(v).count("\n") + 1
            arg_summary.append(f"{k}=[dim]<{lines} lines>[/dim]")
        elif isinstance(v, str) and len(v) > 60:
            arg_summary.append(f'{k}="{v[:57]}..."')
        else:
            arg_summary.append(f"{k}={repr(v)}")
    
    summary_str = ", ".join(arg_summary)
    console.print(f"\n[bold cyan]{sym.TOOL} {display_name}[/bold cyan][dim]({summary_str})[/dim]")

def print_tool_result(tool_name: str, result: dict, is_error: bool = False):
    """Display tool output summary in Claude Code tree format."""
    if is_error:
        err = result.get("error", str(result))
        console.print(f"  [bold red]└ {sym.ERROR} {err}[/bold red]")
        return

    # Custom concise summaries for each tool
    if tool_name == "view_file":
        lines = result.get("total_lines", 0)
        s = result.get("start_line", 1)
        e = result.get("end_line", lines)
        msg = f"Read lines {s}-{e} of {lines}"
    elif tool_name == "create_file":
        bytes_w = result.get("bytes_written", 0)
        msg = f"Created file ({bytes_w} bytes written)"
    elif tool_name == "edit_file":
        msg = result.get("message", "File updated successfully")
    elif tool_name == "delete_file":
        msg = "File deleted successfully"
    elif tool_name == "run_command":
        code = result.get("exit_code", 0)
        dur = result.get("duration_s", 0)
        status_str = f"[green]Exited with code {code}[/green]" if code == 0 else f"[red]Exited with code {code}[/red]"
        msg = f"{status_str} [dim]({dur}s)[/dim]"
    elif tool_name == "glob_files":
        count = result.get("count", 0)
        msg = f"Found {count} matching file{'s' if count != 1 else ''}"
    elif tool_name == "grep_search":
        count = result.get("count", 0)
        capped = " (capped)" if result.get("capped") else ""
        msg = f"Found {count} occurrence{'s' if count != 1 else ''}{capped}"
    elif tool_name == "list_dir":
        count = result.get("count", 0)
        msg = f"Listed {count} entries"
    else:
        msg = result.get("message", "Completed")

    console.print(f"  [dim green]└ {sym.CHECK} {msg}[/dim green]")

def print_thinking(thought: str):
    """Display model's reasoning/thinking step in Claude Code style."""
    if not thought or not thought.strip():
        return
    text = Text(thought.strip(), style="italic dim magenta")
    panel = Panel(
        text,
        title=f"[magenta]{sym.THINK} Thinking...[/magenta]",
        border_style="magenta",
        box=get_box(),
    )
    console.print(panel)

def print_warning(msg: str):
    console.print(f"  [yellow]{sym.WARNING} {msg}[/yellow]")

def print_error(msg: str):
    console.print(f"  [bold red]{sym.ERROR} {msg}[/bold red]")

def print_success(msg: str):
    console.print(f"  [bold green]{sym.SUCCESS} {msg}[/bold green]")

def print_info(msg: str):
    console.print(f"  [cyan]{sym.INFO} {msg}[/cyan]")
