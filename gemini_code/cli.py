"""
Main CLI entrypoint for Gemini Code.
Handles onboarding, interactive command REPL, and agent dispatch.
"""

import sys
import asyncio
from pathlib import Path
from rich.table import Table
from rich.panel import Panel

from .config import config
from .i18n import t, i18n
from .ui.symbols import sym, setup_windows_console
from .ui.renderer import (
    console,
    print_markdown,
    print_error,
    print_success,
    print_info,
    print_warning,
)
from .ui.banner import print_banner, print_status_bar
from .ui.prompter import prompter
from .network.connectivity import diagnose_connection
from .network.client import GeminiClient
from .quota.tracker import quota_tracker
from .quota.models import AVAILABLE_MODELS, list_model_choices
from .agent.agent import Agent
from .tools.git_tools import git_status, git_diff, git_undo

def run_onboarding():
    """First-run setup wizard: language, network check, API key."""
    setup_windows_console()
    console.print(f"\n[bold cyan]{sym.GEMINI} {t('onboarding_title')}[/bold cyan]\n")

    # 1. Language selection
    console.print(t("choose_lang"))
    console.print("  [bold cyan]1[/bold cyan] - Русский")
    console.print("  [bold cyan]2[/bold cyan] - English")
    lang_choice = input("Select [1/2] (default: 1): ").strip()
    if lang_choice == "2":
        config.set("language", "en")
        i18n.set_lang("en")
    else:
        config.set("language", "ru")
        i18n.set_lang("ru")

    console.print(f"[green]{sym.SUCCESS} {t('lang_selected')}[/green]\n")

    # 2. Connectivity check
    console.print(f"[cyan]{sym.INFO} {t('checking_connection')}[/cyan]")
    res = diagnose_connection()
    if res.mode == "direct":
        console.print(f"[green]{sym.SUCCESS} {t('conn_direct_ok')}[/green]")
    elif res.mode == "local_proxy":
        console.print(f"[green]{sym.SUCCESS} {t('local_proxy_found', proxy=res.proxy_url)}[/green]")
    elif res.mode == "mirror":
        console.print(f"[green]{sym.SUCCESS} {t('trying_mirror')}: {res.endpoint}[/green]")
    else:
        console.print(f"[yellow]{sym.WARNING} {t('conn_blocked')}[/yellow]")
        console.print(f"[yellow]{sym.WARNING} {res.details}[/yellow]")

    # 3. API Key prompt
    console.print()
    while not config.api_key:
        api_key = input(t("api_key_prompt")).strip()
        if not api_key:
            continue
        
        # Test key
        try:
            client = GeminiClient(api_key=api_key)
            asyncio.run(client.list_models())
            config.set("api_key", api_key)
            console.print(f"[bold green]{sym.SUCCESS} {t('api_key_saved')}[/bold green]\n")
            break
        except Exception as e:
            print_error(f"{t('api_key_invalid')} ({str(e)})")

def show_help():
    """Display table of all commands."""
    table = Table(title=f"{sym.GEMINI} Gemini Code Commands", border_style="cyan")
    table.add_column("Command", style="bold cyan")
    table.add_column("Description", style="white")

    commands = [
        ("/help", t("cmd_help")),
        ("/model", t("cmd_model")),
        ("/quota", t("cmd_quota")),
        ("/subagent <role>", t("cmd_subagent")),
        ("/doctor", t("cmd_doctor")),
        ("/init", t("cmd_init")),
        ("/review", t("cmd_review")),
        ("/commit", t("cmd_commit")),
        ("/undo", t("cmd_undo")),
        ("/compact", t("cmd_compact")),
        ("/proxy", t("cmd_proxy")),
        ("/theme", t("cmd_theme")),
        ("/lang", t("cmd_lang")),
        ("/clear", t("cmd_clear")),
        ("/exit", t("cmd_exit")),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)
    console.print(table)

def show_quota():
    """Display rich quota usage table."""
    status = quota_tracker.get_status()
    table = Table(title=f"{sym.GEMINI} Quota & Free Tier Status", border_style="cyan")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Usage", style="bold white")
    table.add_column("Limit", style="dim")
    table.add_column("Remaining", style="green")

    table.add_row("Model", status["model"], "-", "-")
    table.add_row("Requests / Min (RPM)", str(status["rpm"]), str(status["max_rpm"]), str(status["rpm_remaining"]))
    table.add_row("Requests / Day (RPD)", str(status["rpd"]), str(status["max_rpd"]), str(status["rpd_remaining"]))
    table.add_row("Session Total Requests", str(status["session_total"]), "-", "-")
    table.add_row("Context Window", f"{status['context_window'] // 1024}k tokens", "-", "-")

    console.print(table)

def switch_model():
    """Interactive model switcher."""
    console.print(f"\n[bold cyan]{sym.GEMINI} Select Gemini Model:[/bold cyan]")
    models = list_model_choices()
    for idx, m in enumerate(models, 1):
        desc = m["desc"] if config.language == "ru" else m["desc_en"]
        mark = f"[bold green]{sym.CHECK}[/bold green]" if m["id"] == config.model else " "
        console.print(f"  {mark} [{idx}] [bold]{m['name']}[/bold] (RPM: {m['rpm']}, Day: {m['rpd']})")
        console.print(f"      [dim]{desc}[/dim]")

    choice = input(f"\nSelect [1-{len(models)}] (Enter to cancel): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(models):
        selected = models[int(choice) - 1]["id"]
        config.set("model", selected)
        print_success(f"Model switched to: {selected}")

def run_doctor():
    """Diagnostic suite."""
    console.print(f"\n[bold cyan]{sym.TOOL} Running Gemini Code Doctor...[/bold cyan]")
    
    # 1. Network test
    res = diagnose_connection()
    if res.is_success():
        print_success(f"Network: {res.details} (Latency: {res.latency_ms} ms)")
    else:
        print_error(f"Network: {res.details}")

    # 2. Git test
    git_res = git_status()
    if git_res.get("exit_code") == 0:
        print_success("Git repository detected")
    else:
        print_warning("No git repository detected in current directory")

    # 3. Python version
    print_info(f"Python: {sys.version.split()[0]} ({sys.platform})")
    print_info(f"Terminal mode: {sym.mode.upper()}")
    print_info(f"Active model: {config.model}")
    print_info(f"Subagent: {config.active_subagent}")
    console.print()

def generate_init():
    """Create GEMINI.md instructions for project."""
    gemini_md = Path("GEMINI.md")
    if gemini_md.exists():
        print_warning("GEMINI.md already exists in this directory.")
        return

    content = f"""# GEMINI.md - Project Guidelines for Gemini Code

## Project Overview
This repository uses Gemini Code as a terminal AI coding assistant.

## Tech Stack & Conventions
- Add language, framework, and linting guidelines here.

## Build & Test Commands
- Test: `pytest` or `npm test`
- Build: `python setup.py build` or `npm run build`
"""
    with open(gemini_md, "w", encoding="utf-8") as f:
        f.write(content)
    print_success("Created GEMINI.md with base project rules.")

async def main_loop():
    setup_windows_console()
    i18n.set_lang(config.language)
    sym.set_mode(config.theme if config.theme != "auto" else ("unicode" if sys.platform != "win32" else "safe"))

    if config.is_first_run():
        run_onboarding()

    print_banner()
    print_status_bar()

    client = GeminiClient()
    agent = Agent(client)

    while True:
        try:
            user_input = prompter.get_input()
            if not user_input:
                continue

            cmd = user_input.strip()

            if cmd in ("/exit", "/quit", "exit", "quit"):
                console.print(f"[bold cyan]{t('goodbye')}[/bold cyan]")
                break

            elif cmd == "/help":
                show_help()

            elif cmd in ("/quota", "/limits"):
                show_quota()

            elif cmd == "/model":
                switch_model()
                print_status_bar()

            elif cmd.startswith("/subagent"):
                parts = cmd.split()
                if len(parts) > 1 and parts[1] in ("planner", "coder", "reviewer", "tester"):
                    config.set("active_subagent", parts[1])
                    print_success(t("subagent_active", role=parts[1].capitalize()))
                else:
                    console.print("\nAvailable subagents:")
                    console.print(f"  • [bold]planner[/bold]  - {t('subagent_planner_desc')}")
                    console.print(f"  • [bold]coder[/bold]    - {t('subagent_coder_desc')}")
                    console.print(f"  • [bold]reviewer[/bold] - {t('subagent_reviewer_desc')}")
                    console.print(f"  • [bold]tester[/bold]   - {t('subagent_tester_desc')}")
                    sub_choice = input("\nSwitch to [planner/coder/reviewer/tester]: ").strip().lower()
                    if sub_choice in ("planner", "coder", "reviewer", "tester"):
                        config.set("active_subagent", sub_choice)
                        print_success(t("subagent_active", role=sub_choice.capitalize()))
                print_status_bar()

            elif cmd == "/doctor":
                run_doctor()

            elif cmd == "/init":
                generate_init()

            elif cmd == "/review":
                diff_data = git_diff()
                if diff_data.get("stdout"):
                    console.print(f"[cyan]{sym.INFO} Reviewing uncommitted changes...[/cyan]")
                    await agent.run_turn(f"Please review the following git diff for bugs and improvements:\n```diff\n{diff_data['stdout']}\n```")
                else:
                    print_info("No uncommitted changes detected to review.")

            elif cmd == "/commit":
                diff_data = git_diff()
                if diff_data.get("stdout"):
                    await agent.run_turn(f"Analyze this git diff and suggest a concise conventional commit message, then run `git_commit`:\n```diff\n{diff_data['stdout']}\n```")
                else:
                    print_info("No uncommitted changes to commit.")

            elif cmd == "/undo":
                res = git_undo()
                if res.get("exit_code") == 0:
                    print_success("Last changes successfully discarded.")
                else:
                    print_error(f"Failed to undo: {res.get('stderr')}")

            elif cmd == "/compact":
                agent.context.compact()
                print_success("Conversation context compacted.")

            elif cmd == "/theme":
                new_theme = "safe" if sym.mode == "unicode" else "unicode"
                sym.set_mode(new_theme)
                config.set("theme", new_theme)
                print_success(f"Symbol theme switched to: {new_theme.upper()}")

            elif cmd == "/lang":
                new_lang = "en" if config.language == "ru" else "ru"
                config.set("language", new_lang)
                i18n.set_lang(new_lang)
                print_success(t("lang_selected"))

            elif cmd == "/clear":
                agent.context.clear()
                print_info(t("context_cleared"))

            else:
                # Regular task prompt to agent
                await agent.run_turn(user_input)

        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[bold cyan]{t('goodbye')}[/bold cyan]")
            break
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")

def main():
    asyncio.run(main_loop())

if __name__ == "__main__":
    main()
