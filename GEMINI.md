# GEMINI.md - Repository Guidelines for Gemini Code

## Overview
Gemini Code is an open-source terminal coding assistant powered by Google Gemini, inspired by Claude Code.

## Architecture
- `gemini_code/cli.py`: Main interactive REPL and command dispatcher.
- `gemini_code/network/`: Direct connectivity tester, proxy scanner, and async Gemini SSE client.
- `gemini_code/quota/`: Real-time RPM/RPD tracker and HUD.
- `gemini_code/tools/`: File viewing, diff editing, shell execution, search, and git operations.
- `gemini_code/agent/`: Autonomous multi-turn agent loop with specialized subagents (Planner, Coder, Reviewer, Tester).
- `gemini_code/ui/symbols.py`: Windows CMD safe symbol abstraction (avoids broken question mark boxes).
- `web/`: Mobile Web-CLI PWA for iOS Safari and mobile browsers (hosted via GitHub Pages).

## Build & Test
- Run tests: `pytest`
- Run CLI: `python -m gemini_code.cli`
