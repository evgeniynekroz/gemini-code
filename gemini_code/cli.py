"""
Main CLI entrypoint for Gemini Code.
Handles onboarding, workspace trust, interactive command REPL, and agent dispatch.
"""

import sys
import os
import json
import asyncio
import webbrowser
from pathlib import Path
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .config import config, CONFIG_DIR
from .i18n import t, i18n
from .ui.symbols import sym, get_box, setup_windows_console
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

def clear_screen():
    """Wipe terminal screen completely across Windows and POSIX."""
    if sys.platform == "win32":
        os.system("cls")
    else:
        os.system("clear")
    console.clear()

def set_terminal_title(title: str = "Gemini Code"):
    """Set window title in console."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception:
            pass
    else:
        sys.stdout.write(f"\x1b]0;{title}\x07")
        sys.stdout.flush()

def verify_workspace_trust() -> bool:
    """
    Ensure user trusts the current working directory.
    Claude Code style workspace security check.
    """
    cwd = os.getcwd()
    trusted_file = CONFIG_DIR / "trusted_workspaces.json"
    trusted_dirs = []

    if trusted_file.exists():
        try:
            with open(trusted_file, "r", encoding="utf-8") as f:
                trusted_dirs = json.load(f)
        except Exception:
            trusted_dirs = []

    if cwd in trusted_dirs:
        return True

    if config.language == "ru":
        title = "[!] ПРОВЕРКА БЕЗОПАСНОСТИ РАБОЧЕЙ ОБЛАСТИ"
        content = (
            f"Текущая папка: [bold cyan]{cwd}[/bold cyan]\n\n"
            f"Вы уверены, что доверяете эту рабочую область для Gemini Code?\n"
            f"ИИ-ассистент имеет доступ к чтению, созданию, изменению файлов\n"
            f"и выполнению консольных команд в этой папке.\n"
            f"[bold yellow]Внимание:[/bold yellow] Он может ошибаться и что-то сломать.\n\n"
            f"Доверять этой рабочей области? [y/n] (по умолчанию: y): "
        )
    else:
        title = "[!] WORKSPACE TRUST SECURITY CHECK"
        content = (
            f"Current directory: [bold cyan]{cwd}[/bold cyan]\n\n"
            f"Do you trust this workspace for Gemini Code?\n"
            f"The AI assistant can read, modify, create files and execute\n"
            f"terminal commands in this directory.\n"
            f"[bold yellow]Warning:[/bold yellow] It can make mistakes and alter files.\n\n"
            f"Trust this workspace? [y/n] (default: y): "
        )

    panel = Panel(
        content,
        title=title,
        border_style="yellow",
        box=get_box(),
        padding=(1, 2),
    )
    console.print(panel)

    try:
        ans = input("> ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        ans = "n"

    if ans in ("n", "no", "нет", "н"):
        if config.language == "ru":
            console.print("\n[red][X] Запуск отменен: рабочая область не подтверждена пользователем.[/red]")
        else:
            console.print("\n[red][X] Launch aborted: workspace not trusted by user.[/red]")
        sys.exit(0)

    # Save to trusted list
    trusted_dirs.append(cwd)
    try:
        with open(trusted_file, "w", encoding="utf-8") as f:
            json.dump(trusted_dirs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return True

async def run_onboarding():
    """First-run setup wizard: language selection and fast API key save without network probing."""
    setup_windows_console()
    set_terminal_title("Gemini Code - Setup")
    clear_screen()

    # 1. Language selection panel (pure text, no emojis)
    welcome_panel = Panel(
        Text.assemble(
            ("GEMINI CODE\n", "bold cyan"),
            ("Терминальный ИИ-ассистент разработчика (v1.0.0)\n\n", "bold green"),
            ("Выберите язык интерфейса / Select language:\n", "bold white"),
            ("  [1] Русский (по умолчанию)\n", "cyan"),
            ("  [2] English", "cyan"),
        ),
        border_style="cyan",
        box=get_box(),
        title="[bold cyan]Добро пожаловать / Welcome[/bold cyan]",
        padding=(1, 2),
    )
    console.print(welcome_panel)

    try:
        lang_choice = input("\nВыбор / Select [1/2] (1): ").strip()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)

    if lang_choice == "2":
        config.set("language", "en")
        i18n.set_lang("en")
    else:
        config.set("language", "ru")
        i18n.set_lang("ru")

    # Wipe screen immediately after language selection
    clear_screen()

    # Open Google AI Studio page automatically in browser
    try:
        webbrowser.open("https://aistudio.google.com/app/apikey")
    except Exception:
        pass

    # 2. Clean authorization panel
    if config.language == "ru":
        auth_text = Text.assemble(
            ("Авторизация Google Gemini (AI Studio)\n\n", "bold cyan"),
            ("Страница получения бесплатного ключа открыта в вашем браузере:\n", "white"),
            ("-> https://aistudio.google.com/app/apikey\n\n", "bold underline cyan"),
            ("1. Войдите с вашим Google-аккаунтом\n", "dim white"),
            ("2. Нажмите кнопку ", "dim white"),
            ("«Create API key»\n", "bold yellow"),
            ("3. Скопируйте созданный ключ (он 100% бесплатный, карты не нужны)\n", "dim white"),
            ("4. Вставьте ключ в строку ниже и нажмите Enter\n", "dim white"),
        )
        auth_title = "[bold cyan]Первоначальная настройка Gemini Code[/bold cyan]"
        prompt_label = "\nВведите ваш API-ключ Google AI Studio: "
    else:
        auth_text = Text.assemble(
            ("Google Gemini (AI Studio) Authorization\n\n", "bold cyan"),
            ("The API key generation page has been opened in your browser:\n", "white"),
            ("-> https://aistudio.google.com/app/apikey\n\n", "bold underline cyan"),
            ("1. Sign in with your Google account\n", "dim white"),
            ("2. Click the button ", "dim white"),
            ("«Create API key»\n", "bold yellow"),
            ("3. Copy the generated key (100% free tier, no credit card required)\n", "dim white"),
            ("4. Paste the key in the prompt below and press Enter\n", "dim white"),
        )
        auth_title = "[bold cyan]Initial Setup for Gemini Code[/bold cyan]"
        prompt_label = "\nEnter your Google AI Studio API key: "

    auth_panel = Panel(
        auth_text,
        border_style="cyan",
        box=get_box(),
        title=auth_title,
        padding=(1, 2),
    )
    console.print(auth_panel)

    # 3. Prompt for key (Save immediately, ZERO network probing during setup!)
    while not config.api_key:
        try:
            api_key = input(prompt_label).strip().strip('"').strip("'")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Отменено пользователем.[/dim]")
            sys.exit(0)

        if not api_key:
            continue

        config.set("api_key", api_key)
        console.print(f"[bold green]{sym.SUCCESS} {t('api_key_saved')}[/bold green]\n")
        break

def show_help():
    """Display table of all commands."""
    table = Table(title=f"{sym.GEMINI} Gemini Code Commands", border_style="cyan", box=get_box())
    table.add_column("Command", style="bold cyan")
    table.add_column("Description", style="white")

    commands = [
        ("/help", t("cmd_help")),
        ("/model", t("cmd_model")),
        ("/quota", t("cmd_quota")),
        ("/key", "Сменить API-ключ Google AI Studio"),
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
    table = Table(title=f"{sym.GEMINI} Quota & Free Tier Status", border_style="cyan", box=get_box())
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
        mark = f"[bold green]{sym.CHECK}[/bold green]" if m["id"] == config.model else "   "
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
    set_terminal_title("Gemini Code")
    i18n.set_lang(config.language)
    sym.set_mode(config.theme if config.theme != "auto" else ("safe" if sys.platform == "win32" else "unicode"))

    if config.is_first_run() or not config.api_key:
        await run_onboarding()

    # Verify workspace trust before entering REPL
    verify_workspace_trust()

    clear_screen()
    cwd = os.getcwd()
    set_terminal_title(f"Gemini Code - {os.path.basename(cwd)}")
    print_banner()
    print_status_bar()

    console.print(f"[dim white][Папка проекта]: [bold cyan]{cwd}[/bold cyan][/dim white]")
    console.print(f"[dim][Инфо]: Введите задачу своими словами или [cyan]/help[/cyan] для списка команд (выход: [cyan]/exit[/cyan])[/dim]\n")

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

            elif cmd == "/key":
                new_key = input("Введите новый Google AI Studio API-ключ: ").strip().strip('"').strip("'")
                if new_key:
                    config.set("api_key", new_key)
                    client.api_key = new_key
                    print_success("API-ключ успешно обновлен!")

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
                    console.print(f"  * [bold]planner[/bold]  - {t('subagent_planner_desc')}")
                    console.print(f"  * [bold]coder[/bold]    - {t('subagent_coder_desc')}")
                    console.print(f"  * [bold]reviewer[/bold] - {t('subagent_reviewer_desc')}")
                    console.print(f"  * [bold]tester[/bold]   - {t('subagent_tester_desc')}")
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

            elif cmd in ("/clear", "/cls"):
                agent.context.clear()
                clear_screen()
                print_banner()
                print_status_bar()
                console.print(f"[dim white][Папка проекта]: [bold cyan]{os.getcwd()}[/bold cyan][/dim white]")
                console.print(f"[dim][Инфо]: Введите запрос или [cyan]/help[/cyan] для списка команд[/dim]\n")
                print_info(t("context_cleared"))

            else:
                # Regular task prompt to agent
                await agent.run_turn(user_input)

        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[bold cyan]{t('goodbye')}[/bold cyan]")
            break
        except Exception as e:
            err_str = str(e)
            if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                print_error("Ошибка API: Неверный API-ключ Google AI Studio. Введите правильный ключ через команду /key.")
            elif "User location is not supported" in err_str or "FAILED_PRECONDITION" in err_str:
                print_error("Ошибка сети: Google блокирует запросы из вашего региона. Включите VPN или настройте прокси через команду /proxy.")
            else:
                print_error(f"Ошибка выполнения: {err_str}")

def main():
    asyncio.run(main_loop())

if __name__ == "__main__":
    main()
