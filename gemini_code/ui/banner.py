"""
Clean, modern header and status renderer for Gemini Code (Claude Code style).
"""

import os
import sys
import subprocess
from pathlib import Path
from rich.text import Text
from .renderer import console
from .symbols import sym
from ..config import config
from ..quota.tracker import quota_tracker
from ..i18n import t

def get_git_branch(cwd: str = "") -> str:
    """Safely get current git branch name without slow external calls if possible."""
    target_dir = Path(cwd or os.getcwd())
    git_head = target_dir / ".git" / "HEAD"
    if git_head.exists():
        try:
            with open(git_head, "r", encoding="utf-8") as f:
                ref = f.read().strip()
                if ref.startswith("ref: refs/heads/"):
                    return ref.replace("ref: refs/heads/", "")
                return ref[:7]
        except Exception:
            pass
    # Fallback to git command
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(target_dir),
            capture_output=True,
            text=True,
            timeout=1.0,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return ""

def get_network_badge() -> str:
    """Format short network status badge."""
    if config.custom_base_url:
        return "[cyan]BaseURL[/cyan]"
    if config.custom_proxy_url:
        p = config.custom_proxy_url.split("@")[-1].replace("http://", "").replace("socks5://", "")
        return f"[magenta]Proxy: {p}[/magenta]"
    if config.proxy_mode == "direct":
        return "[green]Direct[/green]"
    return "[yellow]Auto[/yellow]"

def print_banner(cwd: str = "", network_details: str = ""):
    """Display clean, authentic Claude Code style header."""
    cwd = cwd or os.getcwd()
    branch = get_git_branch(cwd)
    branch_str = f" [dim]({branch})[/dim]" if branch else ""
    status = quota_tracker.get_status()
    net_badge = get_network_badge()

    console.print()
    console.print(f"  [bold cyan]{sym.GEMINI} Gemini Code[/bold cyan] [dim](v1.0.0)[/dim]")
    console.print(f"  [white]{cwd}[/white]{branch_str}")
    console.print(
        f"  [dim]Model:[/dim] [bold cyan]{status['model']}[/bold cyan]  "
        f"[dim]| Context:[/dim] [white]{status['context_window'] // 1024}k[/white]  "
        f"[dim]| RPM:[/dim] [yellow]{status['rpm']}/{status['max_rpm']}[/yellow]  "
        f"[dim]| Net:[/dim] {net_badge}"
    )
    if network_details:
        console.print(f"  [dim]{network_details}[/dim]")
    console.print()
    console.print(
        "  [dim]Type your prompt, [cyan]/help[/cyan] for commands, [cyan]!<cmd>[/cyan] for shell, [cyan]/exit[/cyan] to quit[/dim]"
    )
    console.print("[dim]────────────────────────────────────────────────────────────────────────────────[/dim]")

def print_status_bar(model_id: str = ""):
    """Minimal inline status update."""
    status = quota_tracker.get_status(model_id)
    net_badge = get_network_badge()
    console.print(
        f"[dim][{status['model']} | Context: {status['context_window'] // 1024}k | "
        f"RPM: {status['rpm']}/{status['max_rpm']} | {net_badge}][/dim]"
    )
