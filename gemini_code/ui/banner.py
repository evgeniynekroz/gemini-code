"""
ASCII banner and status bar renderer for Gemini Code.
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from .renderer import console
from .symbols import sym
from ..config import config
from ..quota.tracker import quota_tracker
from ..i18n import t

ASCII_LOGO = r"""
  ____ _____ __  __ ___ _   _ ___   ____ ___  ____  _____ 
 / ___| ____|  \/  |_ _| \ | |_ _| / ___/ _ \|  _ \| ____|
| |  _|  _| | |\/| || ||  \| || | | |  | | | | | | |  _|  
| |_| | |___| |  | || || |\  || | | |__| |_| | |_| | |___ 
 \____|_____|_|  |_|___|_| \_|___| \____\___/|____/|_____|
"""

def print_banner():
    """Display startup ASCII banner and version info."""
    logo_text = Text(ASCII_LOGO, style="bold cyan")
    subtitle = Text(f"{sym.GEMINI} {t('app_subtitle')}", style="bold green")
    
    panel = Panel(
        Text.assemble(logo_text, "\n", subtitle),
        border_style="cyan",
        subtitle=f"[dim]v1.0.0 | Open-Source (evgeniynekroz/gemini-code)[/dim]",
    )
    console.print(panel)

def print_status_bar(model_id: str = ""):
    """Display active status bar with quota, subagent, network mode, and language."""
    status = quota_tracker.get_status(model_id)
    
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column(style="green")
    table.add_column(style="yellow")
    table.add_column(style="magenta")

    table.add_row(
        f"[bold]{sym.GEMINI} Model:[/bold] {status['model']}",
        f"[bold]{sym.TOOL} Agent:[/bold] {config.active_subagent.capitalize()}",
        f"[bold]Quota:[/bold] RPM: {status['rpm']}/{status['max_rpm']} | Day: {status['rpd']}/{status['max_rpd']}",
        f"[bold]Net:[/bold] {config.proxy_mode.upper()}",
    )
    
    panel = Panel(table, border_style="dim", padding=(0, 1))
    console.print(panel)
