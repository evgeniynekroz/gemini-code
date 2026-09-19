"""
Tests for Gemini Code model definitions, aliases, and dynamic registration.
"""

import unittest
from gemini_code.quota.models import (
    AVAILABLE_MODELS,
    get_model_info,
    resolve_model_id,
    register_dynamic_models,
    list_model_choices,
)

class TestModels(unittest.TestCase):
    def test_current_models_exist(self):
        """Verify all latest Google AI Studio models exist."""
        expected_models = [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.0-pro-exp-02-05",
            "gemini-2.0-flash-thinking-exp-01-21",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
        ]
        for model in expected_models:
            self.assertIn(model, AVAILABLE_MODELS, f"Missing model {model}")
            info = AVAILABLE_MODELS[model]
            self.assertGreater(info["max_rpm"], 0)
            self.assertGreater(info["max_rpd"], 0)
            self.assertGreater(info["context_window"], 0)

    def test_model_aliases(self):
        """Verify model aliases resolve to canonical model IDs."""
        self.assertEqual(resolve_model_id("flash"), "gemini-2.0-flash")
        self.assertEqual(resolve_model_id("pro"), "gemini-2.0-pro-exp-02-05")
        self.assertEqual(resolve_model_id("thinking"), "gemini-2.0-flash-thinking-exp-01-21")
        self.assertEqual(resolve_model_id("lite"), "gemini-2.0-flash-lite")
        self.assertEqual(resolve_model_id("2.0-flash"), "gemini-2.0-flash")
        self.assertEqual(resolve_model_id("2.0-pro"), "gemini-2.0-pro-exp-02-05")
        self.assertEqual(resolve_model_id("models/gemini-2.0-flash"), "gemini-2.0-flash")
        # Legacy backwards compatibility alias
        self.assertEqual(resolve_model_id("gemini-2.5-flash"), "gemini-2.0-flash")

    def test_get_model_info_custom_fallback(self):
        """Verify custom model IDs from Google AI Studio do not crash and return valid info."""
        custom_id = "gemini-custom-future-model"
        info = get_model_info(custom_id)
        self.assertEqual(info["name"], custom_id)
        self.assertEqual(info["max_rpm"], 15)
        self.assertGreaterEqual(info["context_window"], 1_000_000)

    def test_register_dynamic_models(self):
        """Verify dynamically fetched models from API can be registered."""
        dynamic_list = [
            {
                "name": "models/gemini-experimental-3.0",
                "displayName": "Gemini 3.0 Experimental",
                "description": "Next-gen test model",
                "inputTokenLimit": 2_000_000,
            }
        ]
        register_dynamic_models(dynamic_list)
        self.assertIn("gemini-experimental-3.0", AVAILABLE_MODELS)
        info = get_model_info("gemini-experimental-3.0")
        self.assertEqual(info["name"], "Gemini 3.0 Experimental")
        self.assertEqual(info["context_window"], 2_000_000)

    def test_list_model_choices(self):
        """Verify list_model_choices returns formatted choices."""
        choices = list_model_choices()
        self.assertGreater(len(choices), 5)
        for c in choices:
            self.assertIn("id", c)
            self.assertIn("name", c)
            self.assertIn("rpm", c)
            self.assertIn("rpd", c)
            self.assertIn("context", c)

if __name__ == "__main__":
    unittest.main()
