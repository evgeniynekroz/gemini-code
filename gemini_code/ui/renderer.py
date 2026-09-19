"""
Rich terminal UI renderer with safe symbol fallback for classic Windows CMD.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .symbols import sym, get_box

console = Console(highlight=False)

def print_markdown(content: str):
    """Render markdown with syntax highlighting."""
    md = Markdown(content)
    console.print(md)

def print_diff(diff_text: str, filename: str = ""):
    """Render unified diff with colored additions, deletions, and line markers."""
    title = f"{sym.TOOL} Diff: {filename}" if filename else f"{sym.TOOL} Diff"
    table = Table.grid(padding=(0, 1))
    table.add_column("Line", style="dim")
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
        subtitle=f"[green]+ addition[/green] | [red]- deletion[/red]",
    )
    console.print(panel)

def print_tool_call(tool_name: str, args: dict):
    """Display clean badge for tool invocation."""
    args_str = ", ".join(f"[bold]{k}[/bold]={repr(v)}" for k, v in args.items())
    console.print(f"\n[cyan]{sym.TOOL} [bold]Calling tool:[/bold] {tool_name}({args_str})[/cyan]")

def print_tool_result(tool_name: str, result: dict, is_error: bool = False):
    """Display tool output or error."""
    if is_error:
        console.print(f"[bold red]{sym.ERROR} Tool [{tool_name}] failed:[/bold red] {result.get('error', result)}")
    else:
        status_text = result.get("message", "Done")
        console.print(f"[green]{sym.SUCCESS} Tool [{tool_name}]: {status_text}[/green]")

def print_thinking(thought: str):
    """Display model's reasoning/thinking step."""
    panel = Panel(
        Text(thought, style="italic magenta"),
        title=f"[magenta]{sym.THINK} Thinking[/magenta]",
        border_style="magenta",
        box=get_box(),
    )
    console.print(panel)

def print_warning(msg: str):
    console.print(f"[yellow]{sym.WARNING} {msg}[/yellow]")

def print_error(msg: str):
    console.print(f"[bold red]{sym.ERROR} {msg}[/bold red]")

def print_success(msg: str):
    console.print(f"[bold green]{sym.SUCCESS} {msg}[/bold green]")

def print_info(msg: str):
    console.print(f"[cyan]{sym.INFO} {msg}[/cyan]")
