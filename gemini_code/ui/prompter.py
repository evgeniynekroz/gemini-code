"""
Interactive terminal prompter with autocompletion, command history, and async execution.
"""

import sys
import asyncio
from pathlib import Path
from ..config import CONFIG_DIR

HISTORY_FILE = CONFIG_DIR / "history.txt"

SLASH_COMMANDS = [
    "/help",
    "/model",
    "/quota",
    "/limits",
    "/key",
    "/subagent",
    "/doctor",
    "/init",
    "/review",
    "/commit",
    "/undo",
    "/compact",
    "/proxy",
    "/theme",
    "/lang",
    "/clear",
    "/cls",
    "/exit",
    "/quit",
]

class Prompter:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.session = None
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.completion import WordCompleter
            from prompt_toolkit.styles import Style

            completer = WordCompleter(SLASH_COMMANDS, ignore_case=True, match_middle=False)
            style = Style.from_dict({"prompt": "cyan bold"})

            self.session = PromptSession(
                history=FileHistory(str(HISTORY_FILE)),
                completer=completer,
                style=style,
            )
        except Exception:
            self.session = None

    async def get_input(self, placeholder: str = "") -> str:
        prompt_marker = "> "
        if self.session:
            try:
                # MUST USE prompt_async inside active asyncio loop!
                return await self.session.prompt_async(prompt_marker)
            except (KeyboardInterrupt, EOFError):
                return "/exit"
            except Exception:
                # If prompt_toolkit fails, disable and fallback
                self.session = None

        # Bulletproof fallback using built-in input in thread pool
        try:
            return await asyncio.to_thread(input, prompt_marker)
        except (KeyboardInterrupt, EOFError):
            return "/exit"

prompter = Prompter()
