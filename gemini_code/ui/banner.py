"""
Clean, modern header and status renderer for Gemini Code (Claude Code style).
"""

import os
import sys
from rich.text import Text
from .renderer import console
from .symbols import sym
from ..config import config
from ..quota.tracker import quota_tracker
from ..i18n import t

def print_banner(cwd: str = ""):
    """Display clean, compact Claude Code style header."""
    cwd = cwd or os.getcwd()
    status = quota_tracker.get_status()

    console.print()
    console.print("  [bold cyan]Gemini Code[/bold cyan] [dim](v1.0.0)[/dim]")
    console.print(f"  [dim]Рабочая область:[/dim] [white]{cwd}[/white]")
    console.print(
        f"  [dim]Модель:[/dim] [cyan]{status['model']}[/cyan]  "
        f"[dim]| Агент:[/dim] [green]{config.active_subagent.capitalize()}[/green]  "
        f"[dim]| Квота:[/dim] [yellow]{status['rpm']}/{status['max_rpm']} RPM[/yellow]  "
        f"[dim]| Сеть:[/dim] [magenta]{config.proxy_mode.upper()}[/magenta]"
    )
    console.print()
    console.print("  [dim]Опишите задачу своими словами или введите [cyan]/help[/cyan] (выход: [cyan]/exit[/cyan])[/dim]")
    console.print("[dim]--------------------------------------------------------------------------------[/dim]")

def print_status_bar(model_id: str = ""):
    """Minimal inline status update."""
    status = quota_tracker.get_status(model_id)
    console.print(
        f"[dim][{status['model']} | {config.active_subagent.capitalize()} | "
        f"RPM: {status['rpm']}/{status['max_rpm']} | {config.proxy_mode.upper()}][/dim]"
    )
