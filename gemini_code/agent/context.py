"""
Conversation context manager and token compaction engine.
"""

from typing import List, Dict, Any

class ContextManager:
    def __init__(self, max_tokens: int = 100_000):
        self.max_tokens = max_tokens
        self.messages: List[Dict[str, Any]] = []

    def add_user_message(self, text: str):
        self.messages.append({
            "role": "user",
            "parts": [{"text": text}],
        })

    def add_model_message(self, parts: List[Dict[str, Any]]):
        self.messages.append({
            "role": "model",
            "parts": parts,
        })

    def add_tool_response(self, tool_name: str, response_data: Any):
        """Append a function response part. If previous message is function, merge part to avoid consecutive function turns."""
        part = {
            "functionResponse": {
                "name": tool_name,
                "response": {"output": response_data},
            }
        }
        if self.messages and self.messages[-1].get("role") == "function":
            self.messages[-1]["parts"].append(part)
        else:
            self.messages.append({
                "role": "function",
                "parts": [part],
            })

    def add_tool_responses(self, responses: List[Dict[str, Any]]):
        """Add multiple function responses in a single turn."""
        for r in responses:
            self.add_tool_response(r["name"], r.get("output", r.get("response", {})))

    def estimate_tokens(self) -> int:
        total_chars = 0
        for msg in self.messages:
            for part in msg.get("parts", []):
                if "text" in part:
                    total_chars += len(part["text"])
                elif "functionCall" in part:
                    total_chars += len(str(part["functionCall"]))
                elif "functionResponse" in part:
                    total_chars += len(str(part["functionResponse"]))
        return total_chars // 4

    def clear(self):
        self.messages.clear()

    def compact(self, keep_last: int = 6):
        """Keep the initial task context and the last few turns, dropping middle ones."""
        if len(self.messages) <= keep_last + 2:
            return

        initial = self.messages[:2]
        recent = self.messages[-keep_last:]
        summary_note = {
            "role": "user",
            "parts": [{"text": "[Previous conversation history compressed to conserve context]"}]
        }
        self.messages = initial + [summary_note] + recent

    def get_contents(self) -> List[Dict[str, Any]]:
        return self.messages
