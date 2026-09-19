"""
Interactive terminal prompter with autocompletion and command history.
"""

import sys
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from .symbols import sym
from ..config import CONFIG_DIR

HISTORY_FILE = CONFIG_DIR / "history.txt"

SLASH_COMMANDS = [
    "/help",
    "/model",
    "/quota",
    "/limits",
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
    "/exit",
    "/quit",
]

completer = WordCompleter(SLASH_COMMANDS, ignore_case=True, match_middle=False)

style = Style.from_dict({
    "prompt": "cyan bold",
})

class Prompter:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            self.session = PromptSession(
                history=FileHistory(str(HISTORY_FILE)),
                completer=completer,
                style=style,
            )
        except Exception:
            self.session = None

    def get_input(self, placeholder: str = "") -> str:
        prompt_marker = f"{sym.USER} "
        if self.session:
            try:
                return self.session.prompt(prompt_marker)
            except (KeyboardInterrupt, EOFError):
                return "/exit"
        else:
            try:
                return input(prompt_marker)
            except (KeyboardInterrupt, EOFError):
                return "/exit"

prompter = Prompter()
