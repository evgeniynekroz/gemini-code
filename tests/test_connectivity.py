"""
Tests for connectivity diagnostics and geo-blocking parsing.
"""

import unittest
from unittest.mock import patch, MagicMock
from gemini_code.network.connectivity import ConnectionResult, check_port_open

class TestConnectivity(unittest.TestCase):
    def test_connection_result(self):
        """Verify ConnectionResult properties."""
        res_ok = ConnectionResult(
            mode="direct",
            endpoint="https://generativelanguage.googleapis.com",
            latency_ms=45,
            geo_unblocked=True,
            details="Direct connection",
            key_valid=True,
        )
        self.assertTrue(res_ok.is_success())
        self.assertTrue(res_ok.key_valid)

        res_blocked = ConnectionResult(
            mode="failed",
            endpoint="https://generativelanguage.googleapis.com",
            latency_ms=0,
            geo_unblocked=False,
            details="User location is not supported",
            key_valid=False,
        )
        self.assertFalse(res_blocked.is_success())

    def test_check_port_open(self):
        """Verify port check handles invalid/closed ports without crashing."""
        # Port 65530 is unlikely to be open
        is_open = check_port_open("127.0.0.1", 65530, timeout=0.05)
        self.assertIsInstance(is_open, bool)

    @patch("gemini_code.network.connectivity.httpx.Client")
    def test_geo_blocking_detected(self, mock_client_cls):
        """Verify that HTTP 400 with 'User location is not supported' is detected as GEO_BLOCKED."""
        from gemini_code.network.connectivity import test_endpoint
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.text = '{"error": {"code": 400, "message": "User location is not supported for the API use.", "status": "FAILED_PRECONDITION"}}'
        
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__enter__.return_value = mock_client

        res = test_endpoint("https://generativelanguage.googleapis.com", api_key="AIzaFakeRealKey1234567890")
        self.assertIsNotNone(res)
        self.assertTrue(res["blocked"])
        self.assertFalse(res["unblocked"])
        self.assertEqual(res["reason"], "GEO_BLOCKED")

    @patch("gemini_code.network.connectivity.httpx.Client")
    def test_proxy_scheme_normalization(self, mock_client_cls):
        """Verify that proxies without scheme (127.0.0.1:10809) are auto-prefixed with http://."""
        from gemini_code.network.connectivity import test_endpoint
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.text = '{"models": []}'
        
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__enter__.return_value = mock_client

        test_endpoint("https://generativelanguage.googleapis.com", proxy="127.0.0.1:10809", api_key="AIzaValidKey1234567890")
        # Ensure httpx.Client was called with normalized proxy='http://127.0.0.1:10809'
        mock_client_cls.assert_called_once()
        _, kwargs = mock_client_cls.call_args
        self.assertEqual(kwargs.get("proxy"), "http://127.0.0.1:10809")

    @patch("gemini_code.network.connectivity.scan_local_proxies")
    def test_diagnose_connection_prefers_local_proxy_when_found(self, mock_scan):
        """Verify auto mode selects local proxy when active on localhost."""
        from gemini_code.network.connectivity import diagnose_connection
        mock_scan.return_value = {
            "url": "http://127.0.0.1:10809",
            "name": "V2RayN (HTTP 10809)",
            "latency": 42,
            "key_valid": False,
        }
        res = diagnose_connection(preferred_mode="auto")
        self.assertEqual(res.mode, "local_proxy")
        self.assertEqual(res.proxy_url, "http://127.0.0.1:10809")
        self.assertTrue(res.geo_unblocked)

if __name__ == "__main__":
    unittest.main()
