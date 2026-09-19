"""
Interactive terminal prompter with autocompletion, file path completion, and history (Claude Code style).
"""

import sys
import asyncio
from pathlib import Path
from ..config import CONFIG_DIR

HISTORY_FILE = CONFIG_DIR / "history.txt"

from .symbols import sym

SLASH_COMMANDS = [
    "/help",
    "/model",
    "/models",
    "/quota",
    "/limits",
    "/cost",
    "/key",
    "/login",
    "/proxy",
    "/doctor",
    "/init",
    "/review",
    "/commit",
    "/diff",
    "/undo",
    "/compact",
    "/subagent",
    "/config",
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
            from prompt_toolkit.completion import WordCompleter, PathCompleter, merge_completers
            from prompt_toolkit.styles import Style

            command_completer = WordCompleter(SLASH_COMMANDS, ignore_case=True, match_middle=False)
            path_completer = PathCompleter(expanduser=True)
            combined_completer = merge_completers([command_completer, path_completer])

            style = Style.from_dict({
                "prompt": "cyan bold",
                "prompt.symbol": "cyan bold",
            })

            self.session = PromptSession(
                history=FileHistory(str(HISTORY_FILE)),
                completer=combined_completer,
                style=style,
            )
        except Exception:
            self.session = None

    async def get_input(self, placeholder: str = "") -> str:
        # Iconic Claude Code prompt glyph ❯ or >
        prompt_char = sym.USER
        prompt_marker = [("class:prompt.symbol", prompt_char)]
        if self.session:
            try:
                text = await self.session.prompt_async(prompt_marker)
                return text.strip()
            except KeyboardInterrupt:
                # Ctrl+C cancels the current input line, does not quit the application!
                return ""
            except EOFError:
                return "/exit"
            except Exception:
                self.session = None

        # Bulletproof fallback using built-in input in thread pool
        try:
            text = await asyncio.to_thread(input, prompt_char)
            return text.strip()
        except KeyboardInterrupt:
            return ""
        except EOFError:
            return "/exit"

prompter = Prompter()
