"""
Main CLI entrypoint for Gemini Code (Claude Code experience).
Handles onboarding, workspace security trust, interactive REPL, direct shell commands (!),
proxy/mirror management for Russia, and multi-step agent dispatch.
"""

import sys
import os
import json
import asyncio
import argparse
import subprocess
import webbrowser
from typing import Dict, List, Optional
from pathlib import Path
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

from . import __version__
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
    print_diff,
)
from .ui.banner import print_banner, print_status_bar
from .ui.prompter import prompter
from .network.connectivity import diagnose_connection, test_endpoint, scan_local_proxies
from .network.proxies import OFFICIAL_ENDPOINT, LOCAL_PROXY_CANDIDATES, CLOUDFLARE_WORKER_SCRIPT
from .network.client import GeminiClient, GeoBlockedException
from .quota.tracker import quota_tracker
from .quota.models import (
    AVAILABLE_MODELS,
    list_model_choices,
    get_model_info,
    resolve_model_id,
    register_dynamic_models,
)
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

def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser matching Claude Code flags."""
    parser = argparse.ArgumentParser(
        prog="geminicode",
        description="Free, open-source terminal coding assistant inspired by Claude Code, powered by Google Gemini.",
        add_help=False,
    )
    parser.add_argument(
        "-h", "--help",
        action="help",
        help="Show this help message and exit.",
    )
    parser.add_argument(
        "-v", "-V", "--version",
        action="version",
        version=f"Gemini Code v{__version__}",
        help="Show version number and exit.",
    )
    parser.add_argument(
        "-p", "--print",
        dest="print_mode",
        nargs="?",
        const=True,
        default=False,
        help="Print response and exit (non-interactive mode).",
    )
    parser.add_argument(
        "-m", "--model",
        dest="model",
        type=str,
        default=None,
        help="Gemini model to use (e.g. gemini-2.0-flash, gemini-2.0-pro-exp-02-05, flash, pro, thinking).",
    )
    parser.add_argument(
        "--subagent",
        dest="subagent",
        type=str,
        choices=["planner", "coder", "reviewer", "tester"],
        default=None,
        help="Initial subagent role (planner, coder, reviewer, tester).",
    )
    parser.add_argument(
        "-y", "--dangerously-skip-permissions", "--trust",
        dest="skip_permissions",
        action="store_true",
        help="Bypass workspace trust and tool confirmation prompts.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Initial prompt or instruction to execute.",
    )
    return parser

def verify_workspace_trust(auto_trust: bool = False) -> bool:
    """Ensure user trusts the current working directory before executing tools."""
    cwd = os.path.normcase(os.path.realpath(os.getcwd()))
    trusted_file = CONFIG_DIR / "trusted_workspaces.json"
    trusted_dirs = []

    if trusted_file.exists():
        try:
            with open(trusted_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                trusted_dirs = [os.path.normcase(os.path.realpath(d)) for d in loaded if isinstance(d, str)]
        except Exception:
            trusted_dirs = []

    if cwd in trusted_dirs or auto_trust:
        if auto_trust and cwd not in trusted_dirs:
            trusted_dirs.append(cwd)
            try:
                with open(trusted_file, "w", encoding="utf-8") as f:
                    json.dump(trusted_dirs, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        return True

    # If stdin is not a tty (piped/CI) and not auto-trusted, do not block on input()
    if not sys.stdin.isatty():
        if config.language == "ru":
            console.print("\n[red]Запуск отменен: рабочая область не подтверждена. Используйте флаг --dangerously-skip-permissions для неинтерактивного запуска.[/red]")
        else:
            console.print("\n[red]Execution cancelled: workspace is not trusted. Use --dangerously-skip-permissions for non-interactive execution.[/red]")
        sys.exit(1)

    console.print()
    raw_cwd = os.getcwd()
    if config.language == "ru":
        console.print(f"  [bold yellow][!] Проверка безопасности рабочей области[/bold yellow]")
        console.print(f"  Папка проекта: [bold cyan]{raw_cwd}[/bold cyan]")
        console.print(f"  [dim]ИИ-ассистент сможет читать и изменять файлы в этой папке.[/dim]")
        prompt = "\n  Доверять этой папке? [y/n] (Enter = да): "
    else:
        console.print(f"  [bold yellow][!] Workspace Security Trust Check[/bold yellow]")
        console.print(f"  Workspace: [bold cyan]{raw_cwd}[/bold cyan]")
        console.print(f"  [dim]The AI assistant can read and modify files in this directory.[/dim]")
        prompt = "\n  Trust this directory? [y/n] (Enter = yes): "

    try:
        ans = input(prompt).strip().lower()
    except (KeyboardInterrupt, EOFError):
        ans = "n"

    if ans in ("n", "no", "нет", "н"):
        if config.language == "ru":
            console.print("\n[red]Запуск отменен: рабочая область не подтверждена.[/red]")
        else:
            console.print("\n[red]Execution cancelled: workspace is not trusted.[/red]")
        sys.exit(1)

    trusted_dirs.append(cwd)
    try:
        with open(trusted_file, "w", encoding="utf-8") as f:
            json.dump(trusted_dirs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return True

async def run_onboarding():
    """First-run setup wizard: language selection and fast API key save."""
    setup_windows_console()
    set_terminal_title("Gemini Code - Setup")
    clear_screen()

    console.print()
    console.print(f"  [bold cyan]✦ Gemini Code[/bold cyan] [dim](v{__version__})[/dim]")
    console.print("  [dim]Терминальный ИИ-ассистент разработчика на базе Google Gemini[/dim]\n")
    console.print("  Выберите язык / Select language:")
    console.print("    [1] Русский (по умолчанию)")
    console.print("    [2] English")

    try:
        lang_choice = input("\n  Выбор / Select [1/2] (1): ").strip()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)

    if lang_choice == "2":
        config.set("language", "en")
        i18n.set_lang("en")
    else:
        config.set("language", "ru")
        i18n.set_lang("ru")

    clear_screen()

    try:
        webbrowser.open("https://aistudio.google.com/app/apikey")
    except Exception:
        pass

    console.print()
    if config.language == "ru":
        console.print("  [bold cyan]Авторизация Google Gemini (AI Studio)[/bold cyan]")
        console.print("  Страница получения бесплатного ключа открыта в вашем браузере:")
        console.print("  [underline cyan]https://aistudio.google.com/app/apikey[/underline cyan]\n")
        console.print("  1. Войдите под своим Google-аккаунтом")
        console.print("  2. Нажмите синюю кнопку [bold yellow]Create API key[/bold yellow]")
        console.print("  3. Скопируйте ключ и вставьте ниже (он 100% бесплатный, карты не нужны)")
        prompt_label = "\n  Введите ваш API-ключ: "
    else:
        console.print("  [bold cyan]Google Gemini (AI Studio) Authorization[/bold cyan]")
        console.print("  The API key generation page has been opened in your browser:")
        console.print("  [underline cyan]https://aistudio.google.com/app/apikey[/underline cyan]\n")
        console.print("  1. Sign in with your Google account")
        console.print("  2. Click the blue button [bold yellow]Create API key[/bold yellow]")
        console.print("  3. Copy the key and paste below (100% free, no credit card required)")
        prompt_label = "\n  Enter your API key: "

    while not config.api_key:
        try:
            api_key = input(prompt_label).strip().strip('"').strip("'")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Отменено пользователем.[/dim]")
            sys.exit(0)

        if not api_key:
            continue

        config.set("api_key", api_key)
        console.print("  [green][OK] API-ключ сохранен![/green]\n")
        break

def show_help():
    """Display table of all Claude Code style commands."""
    table = Table(title=f"{sym.GEMINI} Gemini Code Commands", border_style="cyan", box=get_box())
    table.add_column("Command", style="bold cyan", no_wrap=True)
    table.add_column("Description", style="white")

    commands = [
        ("/help", t("cmd_help")),
        ("/model", "Выбрать или сменить модель Gemini (2.0 Flash, Flash-Lite, Pro Exp, Thinking, 1.5 Pro...)"),
        ("/models", "Список всех моделей + обновление из Google AI Studio"),
        ("/proxy", "Управление прокси и обходом блокировок для РФ (V2Ray, Clash, Cloudflare Worker)"),
        ("/quota, /cost", t("cmd_quota")),
        ("/config", "Просмотр и изменение настроек (модель, язык, авто-подтверждение)"),
        ("/key, /login", "Сменить или обновить API-ключ Google AI Studio"),
        ("/diff", "Посмотреть текущий git diff незакоммиченных изменений"),
        ("/review", t("cmd_review")),
        ("/commit", t("cmd_commit")),
        ("/undo", t("cmd_undo")),
        ("/doctor", t("cmd_doctor")),
        ("/init", t("cmd_init")),
        ("/subagent <role>", t("cmd_subagent")),
        ("/compact", t("cmd_compact")),
        ("/clear", t("cmd_clear")),
        ("/exit", t("cmd_exit")),
        ("!<command>", "Выполнить команду напрямую в шелле (например, !git status или !pytest)"),
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

def show_config_table():
    """Display current settings."""
    table = Table(title=f"{sym.TOOL} Gemini Code Settings", border_style="cyan", box=get_box())
    table.add_column("Setting", style="bold cyan")
    table.add_column("Value", style="white")

    masked_key = (config.api_key[:6] + "..." + config.api_key[-4:]) if len(config.api_key) > 10 else "(not set)"
    table.add_row("Google AI Studio API Key", masked_key)
    table.add_row("Active Model", config.model)
    table.add_row("Interface Language", config.language.upper())
    table.add_row("Active Subagent", config.active_subagent.capitalize())
    table.add_row("Proxy Mode", config.proxy_mode)
    table.add_row("Custom Proxy URL", config.custom_proxy_url or "(none)")
    table.add_row("Custom Base URL", config.custom_base_url or "(official endpoint)")
    table.add_row("Confirm Dangerous Actions", str(config.confirm_danger_actions))
    table.add_row("Config File Path", str(CONFIG_DIR / "config.json"))

    console.print(table)

def switch_model(client: GeminiClient):
    """Interactive model switcher with full up-to-date Google AI Studio lineup."""
    console.print(f"\n[bold cyan]{sym.GEMINI} Select Gemini Model from Google AI Studio:[/bold cyan]")
    models = list_model_choices()

    # Group models by category
    categories: Dict[str, list] = {}
    for idx, m in enumerate(models, 1):
        cat = m.get("category", "General")
        categories.setdefault(cat, []).append((idx, m))

    for cat_name, cat_models in categories.items():
        console.print(f"\n  [bold yellow]-- {cat_name} --[/bold yellow]")
        for idx, m in cat_models:
            desc = m["desc"] if config.language == "ru" else m["desc_en"]
            is_active = (m["id"] == config.model)
            mark = f"[bold green]{sym.CHECK}[/bold green]" if is_active else "   "
            console.print(f"  {mark} [{idx:2d}] [bold]{m['name']}[/bold] [dim]({m['id']})[/dim]")
            console.print(f"       [dim]RPM: {m['rpm']} | Day: {m['rpd']} | Context: {m['context']} | {desc}[/dim]")

    console.print(f"\n  [dim]Вы можете ввести номер [1-{len(models)}], имя модели, или 'refresh' для запроса из API.[/dim]")
    try:
        choice = input(f"\nChoice [1-{len(models)} / model ID] (Enter to cancel): ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if not choice:
        return

    if choice.lower() == "refresh":
        asyncio.run(refresh_models_from_api(client))
        return

    if choice.isdigit() and 1 <= int(choice) <= len(models):
        selected = models[int(choice) - 1]["id"]
    else:
        selected = resolve_model_id(choice)

    config.set("model", selected)
    print_success(f"Active model switched to: {selected}")

async def refresh_models_from_api(client: GeminiClient):
    """Fetch live models directly from Google AI Studio API."""
    console.print("\n[cyan]Запрос актуального списка моделей из Google AI Studio API...[/cyan]")
    try:
        live_models = await client.list_models()
        register_dynamic_models(live_models)
        print_success(f"Успешно загружено {len(live_models)} моделей из Google AI Studio!")
    except Exception as e:
        print_error(f"Не удалось обновить список моделей: {str(e)}")

def manage_proxy(client: GeminiClient):
    """Interactive proxy and Russia geo-bypass manager."""
    while True:
        console.print(f"\n[bold cyan]{sym.TOOL} Network & Proxy Management (Обход ограничений для РФ)[/bold cyan]")
        console.print(f"  Режим: [bold white]{config.proxy_mode.upper()}[/bold white]")
        console.print(f"  Прокси: [bold white]{config.custom_proxy_url or '(нет)'}[/bold white]")
        console.print(f"  Base URL: [bold white]{config.custom_base_url or '(официальный Google)'}[/bold white]")
        console.print()
        console.print("  [1] Автопоиск локального VPN / прокси (V2Ray / Clash / Hiddify)")
        console.print("  [2] Ввести адрес прокси вручную (например: http://127.0.0.1:10809 или socks5://127.0.0.1:10808)")
        console.print("  [3] Ввести адрес своего Cloudflare Worker / зеркала (Custom Base URL)")
        console.print("  [4] Прямое подключение (отключить прокси)")
        console.print("  [5] Проверить соединение и пинг прямо сейчас")
        console.print("  [6] Инструкция: как за 1 минуту сделать вечный бесплатный Cloudflare Worker для РФ")
        console.print("  [0] Назад в терминал")

        try:
            choice = input("\n  Выберите действие [0-6]: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice in ("0", ""):
            break

        elif choice == "1":
            console.print("\n[cyan]Сканирование стандартных портов V2Ray, Clash, Hiddify...[/cyan]")
            local_found = scan_local_proxies(api_key=config.api_key, timeout=2.5)
            if local_found:
                config.set("proxy_mode", "custom")
                config.set("custom_proxy_url", local_found["url"])
                client.reconnect()
                print_success(f"Подключено через: {local_found['name']} ({local_found['url']}) | Задержка: {local_found['latency']} ms")
            else:
                res = diagnose_connection(
                    preferred_mode="auto",
                    custom_proxy="",
                    custom_base_url=config.custom_base_url,
                    api_key=config.api_key,
                )
                if res.geo_unblocked:
                    if res.proxy_url:
                        config.set("proxy_mode", "custom")
                        config.set("custom_proxy_url", res.proxy_url)
                        print_success(f"Подключено через: {res.details} (Задержка: {res.latency_ms} ms)")
                    else:
                        config.set("proxy_mode", "direct")
                        config.set("custom_proxy_url", "")
                        print_success(f"Прямое подключение работает! (Задержка: {res.latency_ms} ms)")
                    client.reconnect()
                else:
                    print_error(f"Не удалось найти рабочий прокси: {res.details}")
                    console.print("  [dim]Убедитесь, что ваш VPN (V2RayN, Clash, Hiddify) запущен в режиме прокси.[/dim]")

        elif choice == "2":
            console.print("\n  Примеры:")
            console.print("    http://127.0.0.1:10809   (V2RayN HTTP)")
            console.print("    socks5://127.0.0.1:10808 (V2RayN SOCKS5)")
            console.print("    http://127.0.0.1:7890    (Clash HTTP)")
            try:
                p_url = input("\n  Введите URL прокси (Enter для отмены): ").strip()
            except (KeyboardInterrupt, EOFError):
                continue
            if p_url:
                if not (p_url.startswith("http://") or p_url.startswith("https://") or p_url.startswith("socks5://")):
                    p_url = f"http://{p_url}"
                console.print(f"[cyan]Проверка прокси {p_url}...[/cyan]")
                res = test_endpoint(OFFICIAL_ENDPOINT, proxy=p_url, api_key=config.api_key, timeout=5.0)
                if res and res["unblocked"] and not res.get("blocked"):
                    config.set("proxy_mode", "custom")
                    config.set("custom_proxy_url", p_url)
                    client.reconnect()
                    print_success(f"Прокси успешно подключен! (Задержка: {res['latency']} ms)")
                else:
                    reason = res.get("text", "timeout/connection refused") if res else "timeout"
                    print_error(f"Прокси не отвечает или блокируется: {reason[:120]}")
                    save_anyway = input("  Все равно сохранить этот прокси? [y/n]: ").strip().lower()
                    if save_anyway in ("y", "yes", "да"):
                        config.set("proxy_mode", "custom")
                        config.set("custom_proxy_url", p_url)
                        client.reconnect()
                        print_success("Прокси сохранен.")

        elif choice == "3":
            console.print("\n  Введите адрес Cloudflare Worker или своего реверс-прокси зеркала.")
            console.print("  Пример: https://my-gemini-proxy.workers.dev")
            try:
                b_url = input("\n  Base URL (Enter для сброса на Google): ").strip().rstrip("/")
            except (KeyboardInterrupt, EOFError):
                continue
            config.set("custom_base_url", b_url)
            client.reconnect()
            if b_url:
                console.print(f"[cyan]Проверка соединения с {b_url}...[/cyan]")
                res = test_endpoint(b_url, proxy=None, api_key=config.api_key, timeout=5.0)
                if res and res["unblocked"] and not res.get("blocked"):
                    print_success(f"Реверс-прокси активен! (Задержка: {res['latency']} ms)")
                else:
                    print_warning(f"Прокси сохранен, но тест вернул ошибку. Проверьте адрес скрипта.")
            else:
                print_success("Сброшено на официальный endpoint Google.")

        elif choice == "4":
            config.set("proxy_mode", "direct")
            config.set("custom_proxy_url", "")
            client.reconnect()
            print_success("Переключено на прямое подключение без прокси.")

        elif choice == "5":
            console.print("\n[cyan]Тестирование сетевого подключения к Gemini...[/cyan]")
            client.reconnect()
            st = client.connection_status
            if st and st.geo_unblocked:
                print_success(f"Соединение успешно! Режим: {st.mode} | Адрес: {st.endpoint} | Пинг: {st.latency_ms} ms")
            else:
                details = st.details if st else "Нет связи"
                print_error(f"Ошибка соединения: {details}")

        elif choice == "6":
            console.print()
            panel = Panel(
                Text(
                    "Cloudflare Workers дает 100 000 бесплатных запросов в сутки и полностью обходит блокировку РФ:\n\n"
                    "1. Зайдите на сайт https://workers.cloudflare.com и нажмите 'Create Worker'\n"
                    "2. Назовите его, например, 'gemini-worker'\n"
                    "3. Вставьте следующий код:\n\n"
                    "export default {\n"
                    "  async fetch(request) {\n"
                    "    const url = new URL(request.url);\n"
                    "    url.hostname = 'generativelanguage.googleapis.com';\n"
                    "    url.port = '443';\n"
                    "    url.protocol = 'https:';\n"
                    "    const newHeaders = new Headers(request.headers);\n"
                    "    newHeaders.set('host', 'generativelanguage.googleapis.com');\n"
                    "    const newRequest = new Request(url, {\n"
                    "      method: request.method,\n"
                    "      headers: newHeaders,\n"
                    "      body: request.body,\n"
                    "      redirect: 'follow',\n"
                    "    });\n"
                    "    return fetch(newRequest);\n"
                    "  }\n"
                    "};\n\n"
                    "4. Нажмите 'Deploy' и скопируйте полученную ссылку (например: https://gemini-worker.xxx.workers.dev)\n"
                    "5. Введите ее в Gemini Code через меню [3] (Custom Base URL)!\n"
                    "Готово! Работает молниеносно, без необходимости держать включенным VPN.",
                    style="white",
                ),
                title="[bold yellow]✦ 1-минутный Cloudflare Worker для РФ[/bold yellow]",
                border_style="yellow",
                box=get_box(),
            )
            console.print(panel)
            input("\nНажмите Enter, чтобы вернуться...")

def execute_direct_shell(command: str):
    """Execute shell command directly with ! prefix (Claude Code feature)."""
    console.print(f"[dim white]$ {command}[/dim white]")
    try:
        if sys.platform == "win32":
            cmd_args = ["powershell.exe", "-NoProfile", "-Command", command]
        else:
            cmd_args = ["/bin/bash", "-c", command]

        res = subprocess.run(cmd_args, text=True, capture_output=True)
        if res.stdout:
            sys.stdout.write(res.stdout)
            sys.stdout.flush()
        if res.stderr:
            sys.stderr.write(res.stderr)
            sys.stderr.flush()
        if res.returncode != 0:
            console.print(f"[dim red](Exit code: {res.returncode})[/dim red]")
    except Exception as e:
        print_error(f"Command execution error: {str(e)}")

def run_doctor(client: GeminiClient):
    """Full Claude Code style diagnostic suite."""
    console.print(f"\n[bold cyan]{sym.TOOL} Running Gemini Code Doctor...[/bold cyan]")
    
    # 1. Environment & Python
    py_ver = sys.version.split()[0]
    print_success(f"Python Runtime: {py_ver} ({sys.platform})")

    # 2. Git status
    git_res = git_status()
    if git_res.get("exit_code") == 0:
        branch = "main"
        for line in git_res.get("stdout", "").splitlines():
            if line.startswith("##"):
                branch = line.replace("##", "").strip()
        print_success(f"Git Repository: Active (Branch: {branch})")
    else:
        print_warning("Git Repository: None detected in current working directory")

    # 3. Project Guidelines
    gemini_file = Path("GEMINI.md")
    claude_file = Path("CLAUDE.md")
    if gemini_file.exists():
        print_success(f"Project Guidelines: Found GEMINI.md ({gemini_file.stat().st_size} bytes)")
    elif claude_file.exists():
        print_success(f"Project Guidelines: Found CLAUDE.md ({claude_file.stat().st_size} bytes)")
    else:
        print_info("Project Guidelines: No GEMINI.md found (run /init to generate one)")

    # 4. Network & Geo-location
    client.reconnect()
    st = client.connection_status
    if st and st.geo_unblocked:
        print_success(f"Network to Gemini: {st.details} (Latency: {st.latency_ms} ms)")
    else:
        details = st.details if st else "Offline"
        print_error(f"Network to Gemini: {details}")

    # 5. API Key & Quota
    masked_key = (config.api_key[:6] + "..." + config.api_key[-4:]) if len(config.api_key) > 10 else "(empty)"
    if config.api_key:
        print_success(f"Google AI Studio Key: Configured ({masked_key})")
    else:
        print_error("Google AI Studio Key: Missing! Run /key to configure.")

    # 6. Model
    info = get_model_info(config.model)
    print_info(f"Active Model: {config.model} ({info['name']}) | Context: {info['context_window'] // 1024}k tokens")
    console.print()

def generate_init():
    """Smart project analysis and GEMINI.md creation (Claude Code style)."""
    gemini_md = Path("GEMINI.md")
    if gemini_md.exists():
        print_warning("GEMINI.md already exists in this directory.")
        return

    cwd = Path.cwd()
    detected_tech = []
    test_cmd = "pytest"
    build_cmd = "python setup.py build"

    if (cwd / "package.json").exists():
        detected_tech.append("Node.js / JavaScript")
        test_cmd = "npm test"
        build_cmd = "npm run build"
    if (cwd / "pyproject.toml").exists() or (cwd / "requirements.txt").exists():
        detected_tech.append("Python")
        test_cmd = "pytest"
        build_cmd = "pip install -e ."
    if (cwd / "go.mod").exists():
        detected_tech.append("Go")
        test_cmd = "go test ./..."
        build_cmd = "go build ."
    if (cwd / "Cargo.toml").exists():
        detected_tech.append("Rust")
        test_cmd = "cargo test"
        build_cmd = "cargo build"

    tech_str = ", ".join(detected_tech) if detected_tech else "Polyglot"

    content = f"""# GEMINI.md - Project Guidelines for Gemini Code

## Project Overview
- **Project Name**: {cwd.name}
- **Detected Stack**: {tech_str}
- **Primary Assistant**: Gemini Code

## Build & Test Commands
- Run Tests: `{test_cmd}`
- Build / Install: `{build_cmd}`

## Code Conventions
- Keep changes surgical and avoid rewriting entire files.
- Verify changes by running unit tests.
- Match existing naming, indentation, and typing conventions.
"""
    with open(gemini_md, "w", encoding="utf-8") as f:
        f.write(content)
    print_success("Created GEMINI.md with customized project rules!")

async def main_loop(initial_prompt: str = "", skip_permissions: bool = False):
    setup_windows_console()
    set_terminal_title("Gemini Code")
    i18n.set_lang(config.language)
    sym.set_mode(config.theme if config.theme != "auto" else ("safe" if sys.platform == "win32" else "unicode"))

    if config.is_first_run() or not config.api_key:
        await run_onboarding()

    # Verify workspace trust before entering REPL
    verify_workspace_trust(auto_trust=skip_permissions)

    clear_screen()
    cwd = os.getcwd()
    set_terminal_title(f"Gemini Code - {os.path.basename(cwd)}")

    client = GeminiClient()
    agent = Agent(client)
    if skip_permissions:
        agent.always_allow_commands = True
        agent.always_allow_edits = True
        config.confirm_danger_actions = False

    # Initial banner
    net_status = client.connection_status
    net_details = f"Route: {net_status.details}" if net_status and net_status.is_success() else ""
    print_banner(cwd, network_details=net_details)

    # If geo-blocked on startup, warn user gently
    if net_status and not net_status.geo_unblocked:
        console.print(
            "  [bold yellow][!] Внимание: Прямое подключение к Google заблокировано в вашем регионе.[/bold yellow]\n"
            "  [dim]Введите [bold cyan]/proxy[/bold cyan] для автоматического поиска V2Ray/Clash или настройки Cloudflare Worker.[/dim]\n"
        )

    # If initial prompt was passed from CLI, execute it immediately!
    if initial_prompt:
        console.print(f"[bold cyan]> {initial_prompt}[/bold cyan]\n")
        try:
            await agent.run_turn(initial_prompt)
        except GeoBlockedException as ge:
            print_error(str(ge))
            console.print("  [cyan]Используйте команду [bold yellow]/proxy[/bold yellow] для настройки обхода блокировки.[/cyan]\n")
        except Exception as e:
            print_error(f"Ошибка выполнения: {str(e)}")

    while True:
        try:
            user_input = await prompter.get_input()
            if not user_input:
                continue

            cmd = user_input.strip()

            # Direct shell execution with ! prefix (Claude Code feature)
            if cmd.startswith("!"):
                shell_command = cmd[1:].strip()
                if shell_command:
                    execute_direct_shell(shell_command)
                continue

            # Slash commands
            if cmd in ("/exit", "/quit", "exit", "quit"):
                console.print(f"[bold cyan]{t('goodbye')}[/bold cyan]")
                break

            elif cmd == "/help":
                show_help()

            elif cmd in ("/quota", "/limits", "/cost"):
                show_quota()

            elif cmd == "/config":
                show_config_table()

            elif cmd in ("/model", "/models"):
                switch_model(client)
                print_status_bar()

            elif cmd == "/proxy":
                manage_proxy(client)
                print_status_bar()

            elif cmd == "/diff":
                diff_data = git_diff()
                if diff_data.get("stdout"):
                    print_diff(diff_data["stdout"], "Uncommitted changes")
                else:
                    print_info("No uncommitted changes in git repository.")

            elif cmd in ("/key", "/login"):
                console.print("\nПолучить бесплатный ключ: https://aistudio.google.com/app/apikey")
                new_key = input("Введите новый Google AI Studio API-ключ: ").strip().strip('"').strip("'")
                if new_key:
                    config.set("api_key", new_key)
                    client.api_key = new_key
                    client.reconnect()
                    print_success("API-ключ успешно обновлен!")

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
                run_doctor(client)

            elif cmd == "/init":
                generate_init()

            elif cmd == "/review":
                diff_data = git_diff()
                if diff_data.get("stdout"):
                    console.print(f"[cyan]{sym.INFO} Reviewing uncommitted changes...[/cyan]")
                    await agent.run_turn(f"Please review the following git diff for bugs, edge cases, and improvements:\n```diff\n{diff_data['stdout']}\n```")
                else:
                    print_info("No uncommitted changes detected to review.")

            elif cmd == "/commit":
                diff_data = git_diff()
                if diff_data.get("stdout"):
                    await agent.run_turn(f"Analyze this git diff and create a conventional git commit using `git_commit`:\n```diff\n{diff_data['stdout']}\n```")
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
                print_banner(os.getcwd())
                print_info(t("context_cleared"))

            else:
                # Regular task prompt to agent
                await agent.run_turn(user_input)

        except KeyboardInterrupt:
            console.print("\n[dim](Действие прервано пользователем)[/dim]")
        except EOFError:
            console.print(f"\n[bold cyan]{t('goodbye')}[/bold cyan]")
            break
        except GeoBlockedException as ge:
            print_error(str(ge))
            console.print("  [cyan]Используйте команду [bold yellow]/proxy[/bold yellow] для настройки обхода блокировки.[/cyan]\n")
        except Exception as e:
            err_str = str(e)
            if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                print_error("Ошибка API: Неверный API-ключ Google AI Studio. Введите правильный ключ через команду /key.")
            elif "User location is not supported" in err_str or "FAILED_PRECONDITION" in err_str:
                print_error("Ошибка сети: Google блокирует запросы из вашего региона. Настройте прокси через команду /proxy.")
            else:
                print_error(f"Ошибка выполнения: {err_str}")
            await asyncio.sleep(0.3)

async def run_print_mode(prompt: str, skip_permissions: bool = False):
    """Execute a single prompt non-interactively, print output, and exit (Claude Code -p style)."""
    setup_windows_console()
    i18n.set_lang(config.language)
    sym.set_mode(config.theme if config.theme != "auto" else ("safe" if sys.platform == "win32" else "unicode"))

    if not config.api_key:
        if sys.stdin.isatty():
            await run_onboarding()
        else:
            print_error("Error: Google AI Studio API key is not configured. Set GEMINI_API_KEY environment variable or run 'geminicode' interactively.")
            sys.exit(1)

    verify_workspace_trust(auto_trust=skip_permissions)

    client = GeminiClient()
    agent = Agent(client)
    if skip_permissions:
        agent.always_allow_commands = True
        agent.always_allow_edits = True
        config.confirm_danger_actions = False

    try:
        success = await agent.run_turn(prompt)
        if not success:
            sys.exit(1)
    except GeoBlockedException as ge:
        print_error(str(ge))
        sys.exit(1)
    except Exception as e:
        print_error(f"Execution error: {str(e)}")
        sys.exit(1)

def parse_cli_args(argv=None):
    """Parse command line arguments."""
    parser = build_parser()
    return parser.parse_args(argv)

def main(argv=None):
    """Main CLI entrypoint for Gemini Code with Claude Code CLI arguments."""
    args = parse_cli_args(argv)

    # Apply model override if specified
    if args.model:
        resolved = resolve_model_id(args.model)
        config.model = resolved

    # Apply subagent override if specified
    if args.subagent:
        config.active_subagent = args.subagent

    # Determine prompt and print mode
    is_print_mode = bool(args.print_mode)
    prompt_parts = []
    if isinstance(args.print_mode, str) and args.print_mode:
        prompt_parts.append(args.print_mode)
    if args.prompt:
        prompt_parts.extend(args.prompt)

    prompt = " ".join(prompt_parts).strip()

    # Check for piped / redirected stdin input across all platforms
    piped_input = ""
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw:
                piped_input = raw.lstrip("\ufeff").lstrip("п»ї").strip()
        except Exception:
            piped_input = ""

    if piped_input:
        if prompt:
            prompt = f"{prompt}\n\n{piped_input}"
        else:
            prompt = piped_input

    # If stdin is not a tty and a prompt / piped input exists, run in print mode
    # because interactive terminal REPL requires an interactive tty.
    if not sys.stdin.isatty() and prompt:
        is_print_mode = True

    # If stdin is not a tty and no prompt was provided
    if not sys.stdin.isatty() and not prompt:
        if is_print_mode:
            print_error("Error: -p/--print requires a prompt or piped input (e.g. geminicode -p \"Explain this project\" or cat file | geminicode -p).")
        else:
            print_error("Error: geminicode requires an interactive terminal (TTY) or a prompt/piped input.")
        sys.exit(1)

    if is_print_mode:
        if not prompt:
            print_error("Error: -p/--print requires a prompt or piped input (e.g. geminicode -p \"Explain this project\" or cat file | geminicode -p).")
            sys.exit(1)
        asyncio.run(run_print_mode(prompt, skip_permissions=args.skip_permissions))
    else:
        asyncio.run(main_loop(initial_prompt=prompt, skip_permissions=args.skip_permissions))

if __name__ == "__main__":
    main()
