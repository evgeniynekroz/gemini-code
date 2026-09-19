"""
Terminal symbols and glyphs manager with Windows CMD safe mode.
Prevents broken square-with-question-mark glyphs in legacy Windows terminals.
"""

import os
import sys
import ctypes
from rich import box

def setup_windows_console():
    """Configure Windows console for UTF-8 and ANSI colors."""
    if sys.platform == "win32":
        try:
            # Switch code page to UTF-8
            os.system("chcp 65001 >nul 2>&1")
        except Exception:
            pass

        try:
            # Reconfigure stdout/stderr with UTF-8 and safe character replacement
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

        try:
            # Enable ENABLE_VIRTUAL_TERMINAL_PROCESSING for ANSI escape sequences
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass

def is_modern_terminal() -> bool:
    """
    Detect whether the current terminal supports modern unicode/nerd fonts.
    Returns False for classic Windows CMD or PowerShell.
    """
    if sys.platform != "win32":
        return True
    
    # Windows Terminal, VS Code, Cursor, Alacritty, WezTerm, ConEmu
    modern_env_vars = ["WT_SESSION", "VSCODE_PID", "TERM_PROGRAM", "ALACRITTY_LOG", "ConEmuPID"]
    if any(var in os.environ for var in modern_env_vars):
        return True
    
    # Standard cmd.exe or legacy PowerShell
    return False

class Symbols:
    """Symbol repository with Safe (CMD-proof) and Modern Unicode modes."""

    def __init__(self, mode: str = "auto"):
        setup_windows_console()
        if mode == "auto":
            # On Windows, always default to safe mode unless explicitly overridden
            self.mode = "safe" if sys.platform == "win32" else "unicode"
        else:
            self.mode = mode
        self._load_symbols()

    def set_mode(self, mode: str):
        self.mode = mode
        self._load_symbols()

    def _load_symbols(self):
        if self.mode == "safe":
            # 100% safe ASCII and CP65001 compatible symbols for legacy Windows CMD
            self.SUCCESS = "[OK]"
            self.ERROR = "[FAIL]"
            self.WARNING = "[!]"
            self.INFO = "[*]"
            self.GEMINI = "[Gemini]"
            self.USER = "> "
            self.THINK = "[Думаю...]"
            self.TOOL = "[Инструмент]"
            self.CHECK = "[v]"
            self.CROSS = "[x]"
            self.ARROW = "->"
            self.BULLET = "*"
            self.QUESTION = "?"
            self.DOT = "."
            self.SPINNER = ["-", "\\", "|", "/"]
            self.BOX_TOP_LEFT = "+"
            self.BOX_TOP_RIGHT = "+"
            self.BOX_BOTTOM_LEFT = "+"
            self.BOX_BOTTOM_RIGHT = "+"
            self.BOX_HORIZONTAL = "-"
            self.BOX_VERTICAL = "|"
        else:
            # Modern, stylish Unicode symbols for Windows Terminal, VS Code, macOS, Linux
            self.SUCCESS = "[OK]"
            self.ERROR = "[FAIL]"
            self.WARNING = "[!]"
            self.INFO = "[*]"
            self.GEMINI = "✦"
            self.USER = "> "
            self.THINK = "◆"
            self.TOOL = "⚙"
            self.CHECK = "✔"
            self.CROSS = "✖"
            self.ARROW = "→"
            self.BULLET = "*"
            self.QUESTION = "?"
            self.DOT = "·"
            self.SPINNER = ["-", "\\", "|", "/"]
            self.BOX_TOP_LEFT = "+"
            self.BOX_TOP_RIGHT = "+"
            self.BOX_BOTTOM_LEFT = "+"
            self.BOX_BOTTOM_RIGHT = "+"
            self.BOX_HORIZONTAL = "-"
            self.BOX_VERTICAL = "|"

def get_box():
    """Return safe box style for Rich panels."""
    return box.ASCII if sym.mode == "safe" else box.SQUARE

# Global singleton instance
sym = Symbols()
