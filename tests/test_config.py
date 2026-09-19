"""
Tests for Gemini Code configuration and environment variables.
"""

import os
import unittest
from unittest.mock import patch
from gemini_code.config import Config

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.config = Config()

    def test_default_values(self):
        """Verify sensible default configuration values."""
        self.assertEqual(self.config.model, "gemini-2.0-flash")
        self.assertIn(self.config.language, ("ru", "en"))
        self.assertTrue(self.config.confirm_danger_actions)

    def test_env_var_api_key_override(self):
        """Verify GEMINI_API_KEY environment variable takes precedence."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-env-key-12345"}):
            cfg = Config()
            self.assertEqual(cfg.api_key, "test-env-key-12345")

    def test_env_var_proxy_override(self):
        """Verify GEMINI_PROXY environment variable takes precedence."""
        with patch.dict(os.environ, {"GEMINI_PROXY": "http://127.0.0.1:9999"}):
            cfg = Config()
            # Clear stored custom_proxy_url to test env fallback
            cfg._data["custom_proxy_url"] = ""
            self.assertEqual(cfg.custom_proxy_url, "http://127.0.0.1:9999")

    def test_env_var_base_url_override(self):
        """Verify GEMINI_BASE_URL environment variable takes precedence."""
        with patch.dict(os.environ, {"GEMINI_BASE_URL": "https://my-proxy.workers.dev"}):
            cfg = Config()
            self.assertEqual(cfg.custom_base_url, "https://my-proxy.workers.dev")

if __name__ == "__main__":
    unittest.main()
