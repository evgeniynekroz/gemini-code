"""
Autonomous agentic execution loop with tool calling and user confirmations (Claude Code style).
"""

import sys
import os
import difflib
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..network.client import GeminiClient, GeoBlockedException
from ..quota.tracker import quota_tracker
from ..tools import registry
from ..ui.renderer import (
    console,
    print_markdown,
    print_tool_call,
    print_tool_result,
    print_diff,
    print_thinking,
    print_error,
    print_warning,
    print_info,
)
from ..ui.symbols import sym
from ..config import config
from ..i18n import t
from .prompts import get_system_prompt
from .context import ContextManager

def load_project_guidelines() -> str:
    """Load GEMINI.md or CLAUDE.md project guidelines if present in current directory."""
    cwd = Path.cwd()
    for filename in ("GEMINI.md", "CLAUDE.md", "AGENTS.md"):
        guideline_file = cwd / filename
        if guideline_file.is_file():
            try:
                with open(guideline_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read().strip()
                if content:
                    return f"\n\n[Project Guidelines from {filename}]:\n{content}"
            except Exception:
                pass
    return ""

class Agent:
    def __init__(self, client: GeminiClient):
        self.client = client
        self.context = ContextManager()
        self.always_allow_commands = False
        self.always_allow_edits = False

    async def run_turn(self, user_input: str):
        """Execute a full multi-step agent turn with autonomous tool execution."""
        self.context.add_user_message(user_input)

        max_steps = 20
        step = 0

        while step < max_steps:
            step += 1
            system_prompt = get_system_prompt(config.active_subagent)
            guidelines = load_project_guidelines()
            if guidelines:
                system_prompt += guidelines

            gemini_tools = registry.to_gemini_tools()

            model_parts: List[Dict[str, Any]] = []
            current_text = ""
            current_thought = ""
            function_calls: List[Dict[str, Any]] = []

            quota_tracker.record_request()

            try:
                stream = self.client.stream_generate_content(
                    model=config.model,
                    contents=self.context.get_contents(),
                    system_instruction=system_prompt,
                    tools=gemini_tools,
                )

                async for part in stream:
                    # Thinking part (Gemini 2.0 / 2.5 thinking models)
                    if part.get("thought"):
                        thought_chunk = part.get("text", "")
                        current_thought += thought_chunk
                        continue

                    # Regular text streaming
                    if "text" in part:
                        # If we just finished a thinking block, print it first!
                        if current_thought:
                            print_thinking(current_thought)
                            current_thought = ""

                        text_chunk = part["text"]
                        current_text += text_chunk
                        console.print(text_chunk, end="", markup=False, style="white")

                    # Function call
                    if "functionCall" in part:
                        if current_thought:
                            print_thinking(current_thought)
                            current_thought = ""
                        function_calls.append(part["functionCall"])

                if current_thought:
                    print_thinking(current_thought)
                    current_thought = ""

                if current_text:
                    console.print()  # Final newline
                    model_parts.append({"text": current_text})

            except GeoBlockedException as ge:
                print_error(str(ge))
                console.print(
                    "\n  [cyan]Совет:[/cyan] Введите [bold yellow]/proxy[/bold yellow] для авто-поиска локального VPN "
                    "или настройки Cloudflare Worker, чтобы обходить блокировку без ограничений.\n"
                )
                return False
            except Exception as e:
                print_error(f"Error during generation: {str(e)}")
                return False

            for fc in function_calls:
                model_parts.append({"functionCall": fc})

            if model_parts:
                self.context.add_model_message(model_parts)

            # If model didn't call any tools, turn is complete!
            if not function_calls:
                break

            # Execute function calls
            for fc in function_calls:
                tool_name = fc.get("name", "")
                args = fc.get("args") or {}
                if isinstance(args, dict) and "path" in args:
                    args["path"] = str(args["path"]).strip().strip('"').strip("'")

                print_tool_call(tool_name, args)

                tool = registry.get(tool_name)
                if not tool:
                    err_msg = f"Unknown tool: {tool_name}"
                    print_error(err_msg)
                    self.context.add_tool_response(tool_name, {"error": err_msg})
                    continue

                # Handle confirmations for dangerous actions
                if tool.is_dangerous and config.confirm_danger_actions:
                    # Check if allowed by session switches
                    if tool_name in ("edit_file", "create_file", "delete_file") and self.always_allow_edits:
                        pass
                    elif tool_name == "run_command" and self.always_allow_commands:
                        pass
                    else:
                        # Show prompt
                        if tool_name == "edit_file":
                            file_path = args.get("path", "")
                            old_text = args.get("old_text", "")
                            new_text = args.get("new_text", "")
                            diff = "".join(difflib.unified_diff(
                                old_text.splitlines(keepends=True),
                                new_text.splitlines(keepends=True),
                                fromfile=f"a/{Path(file_path).name}",
                                tofile=f"b/{Path(file_path).name}",
                            ))
                            if diff:
                                print_diff(diff, file_path)

                            console.print(f"\n  [bold yellow]{sym.QUESTION} Apply changes to `{file_path}`?[/bold yellow]")
                            console.print("  [bold green][y][/bold green] Yes, apply  |  [bold yellow][a][/bold yellow] Always allow edits  |  [bold red][n][/bold red] Reject")
                            prompt_msg = "  Choice [y/a/n] (y): "
                        elif tool_name == "run_command":
                            cmd = args.get("command", "")
                            console.print(f"\n  [bold yellow]{sym.QUESTION} Run terminal command:[/bold yellow] [bold cyan]{cmd}[/bold cyan]")
                            console.print("  [bold green][y][/bold green] Yes, run once  |  [bold yellow][a][/bold yellow] Always allow commands  |  [bold red][n][/bold red] Reject")
                            prompt_msg = "  Choice [y/a/n] (y): "
                        else:
                            console.print(f"\n  [bold yellow]{sym.QUESTION} Execute `{tool_name}`?[/bold yellow]")
                            console.print("  [bold green][y][/bold green] Yes  |  [bold red][n][/bold red] Reject")
                            prompt_msg = "  Choice [y/n] (y): "

                        try:
                            choice = input(prompt_msg).strip().lower()
                        except (KeyboardInterrupt, EOFError):
                            choice = "n"

                        if choice == "a":
                            if tool_name == "run_command":
                                self.always_allow_commands = True
                            else:
                                self.always_allow_edits = True
                        elif choice in ("n", "no", "н", "нет"):
                            print_warning(t("command_rejected"))
                            self.context.add_tool_response(tool_name, {"rejected": True, "error": "User rejected this tool execution."})
                            continue

                # Execute tool
                try:
                    result = await tool.execute(**args)
                    
                    # If tool returned diff, render it nicely
                    if isinstance(result, dict) and "diff" in result and result["diff"]:
                        print_diff(result["diff"], args.get("path", ""))

                    is_error = isinstance(result, dict) and "error" in result
                    print_tool_result(tool_name, result, is_error=is_error)
                    self.context.add_tool_response(tool_name, result)
                except Exception as e:
                    err_msg = f"Tool execution failed: {str(e)}"
                    print_error(err_msg)
                    self.context.add_tool_response(tool_name, {"error": err_msg})

        # Suggest compaction if token count is high
        if self.context.estimate_tokens() > 80_000:
            self.context.compact()

        return True
