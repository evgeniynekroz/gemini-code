"""
Autonomous agentic execution loop with tool calling and user confirmations.
"""

import sys
import difflib
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..network.client import GeminiClient
from ..quota.tracker import quota_tracker
from ..tools import registry
from ..ui.renderer import (
    console,
    print_tool_call,
    print_tool_result,
    print_diff,
    print_thinking,
    print_error,
    print_warning,
)
from ..ui.symbols import sym
from ..config import config
from ..i18n import t
from .prompts import get_system_prompt
from .context import ContextManager

class Agent:
    def __init__(self, client: GeminiClient):
        self.client = client
        self.context = ContextManager()
        self.always_allow_commands = False

    async def run_turn(self, user_input: str):
        """Execute a full multi-step agent turn with autonomous tool execution."""
        self.context.add_user_message(user_input)

        max_steps = 15
        step = 0

        while step < max_steps:
            step += 1
            system_prompt = get_system_prompt(config.active_subagent)
            gemini_tools = registry.to_gemini_tools()

            model_parts: List[Dict[str, Any]] = []
            current_text = ""
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
                    # 1. Text token streaming
                    if "text" in part:
                        text_chunk = part["text"]
                        current_text += text_chunk
                        console.print(text_chunk, end="", style="white")

                    # 2. Function call
                    if "functionCall" in part:
                        function_calls.append(part["functionCall"])

                if current_text:
                    console.print()  # Newline after streaming text
                    model_parts.append({"text": current_text})

            except Exception as e:
                print_error(f"Error during generation: {str(e)}")
                break

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
                args = fc.get("args", {})

                print_tool_call(tool_name, args)

                tool = registry.get(tool_name)
                if not tool:
                    err_msg = f"Unknown tool: {tool_name}"
                    print_error(err_msg)
                    self.context.add_tool_response(tool_name, {"error": err_msg})
                    continue

                # Handle confirmations for dangerous actions
                if tool.is_dangerous and config.confirm_danger_actions and not self.always_allow_commands:
                    # If edit_file, show preview of diff before asking
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

                        prompt_msg = f"{sym.QUESTION} {t('confirm_edit', path=file_path)} [y/n/a]: "
                    elif tool_name == "run_command":
                        cmd = args.get("command", "")
                        prompt_msg = f"{sym.QUESTION} {t('confirm_command', cmd=cmd)}"
                    else:
                        prompt_msg = f"{sym.QUESTION} Execute `{tool_name}`? [y/n/a]: "

                    choice = input(prompt_msg).strip().lower()
                    if choice == "a":
                        self.always_allow_commands = True
                    elif choice not in ("y", "yes", ""):
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
        if self.context.estimate_tokens() > 60_000:
            self.context.compact()
