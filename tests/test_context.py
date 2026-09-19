"""
Tests for conversation context manager and compaction.
"""

import unittest
from gemini_code.agent.context import ContextManager

class TestContext(unittest.TestCase):
    def test_context_operations(self):
        cm = ContextManager()
        self.assertEqual(len(cm.get_contents()), 0)

        cm.add_user_message("Hello, please help with my code")
        cm.add_model_message([{"text": "Sure, let's look at it."}])
        cm.add_tool_response("view_file", {"total_lines": 50})

        contents = cm.get_contents()
        self.assertEqual(len(contents), 3)
        self.assertGreater(cm.estimate_tokens(), 0)

    def test_multiple_tool_responses_merged(self):
        """Verify multiple consecutive tool responses merge into a single turn to comply with Gemini API."""
        cm = ContextManager()
        cm.add_user_message("Run commands")
        cm.add_model_message([
            {"functionCall": {"name": "tool_a", "args": {}}},
            {"functionCall": {"name": "tool_b", "args": {}}},
        ])
        cm.add_tool_response("tool_a", {"result": "A"})
        cm.add_tool_response("tool_b", {"result": "B"})

        contents = cm.get_contents()
        # Should be user, model, function (3 messages total, NOT 4)
        self.assertEqual(len(contents), 3)
        self.assertEqual(contents[2]["role"], "function")
        self.assertEqual(len(contents[2]["parts"]), 2)
        self.assertEqual(contents[2]["parts"][0]["functionResponse"]["name"], "tool_a")
        self.assertEqual(contents[2]["parts"][1]["functionResponse"]["name"], "tool_b")

    def test_compaction(self):
        cm = ContextManager()
        for i in range(15):
            cm.add_user_message(f"Step {i}")
            cm.add_model_message([{"text": f"Response {i}"}])

        initial_len = len(cm.get_contents())
        self.assertEqual(initial_len, 30)

        cm.compact(keep_last=4)
        compacted = cm.get_contents()
        # Should keep initial 2 + summary + last 4
        self.assertLess(len(compacted), initial_len)
        self.assertIn("Previous conversation history compressed", str(compacted))

if __name__ == "__main__":
    unittest.main()
