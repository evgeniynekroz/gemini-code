"""
Network connectivity checker and auto-detector for Gemini access.
Handles direct check, local proxy port scanning, and custom reverse proxies.
"""

import os
import socket
import time
from typing import Optional, Dict, Any
import httpx

from .proxies import OFFICIAL_ENDPOINT, LOCAL_PROXY_CANDIDATES

class ConnectionResult:
    def __init__(
        self,
        mode: str,
        endpoint: str,
        proxy_url: Optional[str] = None,
        latency_ms: int = 0,
        geo_unblocked: bool = False,
        details: str = "",
        key_valid: bool = False,
    ):
        self.mode = mode
        self.endpoint = endpoint
        self.proxy_url = proxy_url
        self.latency_ms = latency_ms
        self.geo_unblocked = geo_unblocked
        self.details = details
        self.key_valid = key_valid

    def is_success(self) -> bool:
        return self.geo_unblocked

def test_endpoint(
    endpoint: str,
    proxy: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: float = 4.0,
) -> Optional[Dict[str, Any]]:
    """
    Send a probe to test if the endpoint responds and if geo-blocking is bypassed.
    Correctly differentiates between geographic blocking, API key validity, and network reachability.
    """
    if proxy:
        proxy = proxy.strip()
        if not (proxy.startswith("http://") or proxy.startswith("https://") or proxy.startswith("socks5://")):
            proxy = f"http://{proxy}"

    endpoint_clean = endpoint.rstrip("/")
    if endpoint_clean.endswith("/v1beta"):
        endpoint_clean = endpoint_clean[:-7]

    has_real_key = bool(api_key and len(api_key.strip()) > 10)
    key_to_use = api_key.strip() if has_real_key else "AIzaSyTestGeoProbe12345678901234567890123"
    test_url = f"{endpoint_clean}/v1beta/models?key={key_to_use}"
    start_time = time.time()

    try:
        kwargs: Dict[str, Any] = {"timeout": timeout, "follow_redirects": True}
        if proxy:
            kwargs["proxy"] = proxy

        headers = {
            "x-goog-api-key": key_to_use,
            "User-Agent": "GeminiCode/1.0",
        }

        with httpx.Client(**kwargs) as client:
            resp = client.get(test_url, headers=headers)
            latency = int((time.time() - start_time) * 1000)
            text = resp.text
            lower_text = text.lower()
            ctype = resp.headers.get("content-type", "")

            # If response is HTML or not JSON, check if it's an error page
            if "application/json" not in ctype and not text.strip().startswith("{"):
                return None

            # Geo-blocking detection (Google AI Studio Russia/restricted region)
            if "user location is not supported" in lower_text or "failed_precondition" in lower_text:
                return {
                    "unblocked": False,
                    "blocked": True,
                    "key_valid": False,
                    "latency": latency,
                    "reason": "GEO_BLOCKED",
                    "text": text,
                }

            # 200 OK: Route is open and API key is completely valid!
            if resp.status_code == 200:
                return {
                    "unblocked": True,
                    "blocked": False,
                    "key_valid": True,
                    "latency": latency,
                    "reason": "SUCCESS",
                    "text": text,
                }

            # If real key was provided and returned 400 with API key invalid:
            if has_real_key:
                if "api_key_invalid" in lower_text or "api key not valid" in lower_text:
                    return {
                        "unblocked": True,
                        "blocked": False,
                        "key_valid": False,
                        "latency": latency,
                        "reason": "API_KEY_INVALID",
                        "text": text,
                    }

            # Dummy key response (API_KEY_INVALID): traffic reached Google endpoint
            if "api_key_invalid" in lower_text or "api key not valid" in lower_text or resp.status_code == 400:
                return {
                    "unblocked": True,
                    "blocked": False,
                    "key_valid": False,
                    "dummy_probe": not has_real_key,
                    "latency": latency,
                    "reason": "REACHABLE",
                    "text": text,
                }

            return {
                "unblocked": True,
                "blocked": False,
                "key_valid": False,
                "latency": latency,
                "reason": f"HTTP_{resp.status_code}",
                "text": text,
            }
    except Exception:
        return None

def check_port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    """Check if a local TCP port is open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def scan_local_proxies(api_key: Optional[str] = None, timeout: float = 2.5) -> Optional[Dict[str, Any]]:
    """Scan standard local proxy client ports (V2Ray, Clash, Hiddify) and return the first working one."""
    for candidate in LOCAL_PROXY_CANDIDATES:
        url = candidate["url"]
        name = candidate["name"]
        try:
            port = int(url.split(":")[-1])
            if check_port_open("127.0.0.1", port):
                res = test_endpoint(OFFICIAL_ENDPOINT, proxy=url, api_key=api_key, timeout=timeout)
                if res and res.get("unblocked") and not res.get("blocked"):
                    return {
                        "url": url,
                        "name": name,
                        "latency": res["latency"],
                        "key_valid": res.get("key_valid", False),
                    }
        except Exception:
            continue
    return None

def diagnose_connection(
    preferred_mode: str = "auto",
    custom_proxy: str = "",
    custom_base_url: str = "",
    api_key: Optional[str] = None,
) -> ConnectionResult:
    """
    Perform a robust connectivity diagnostic and find the best working connection method.
    Specifically optimized for users in Russia and countries with Google AI Studio restrictions.
    """
    # 1. Custom Base URL (e.g. Cloudflare Worker or reverse proxy)
    if custom_base_url or preferred_mode == "custom_base_url":
        target_endpoint = custom_base_url or OFFICIAL_ENDPOINT
        res = test_endpoint(target_endpoint, proxy=None, api_key=api_key, timeout=4.0)
        if res and res["unblocked"]:
            return ConnectionResult(
                "custom_base_url",
                target_endpoint,
                proxy_url=None,
                latency_ms=res["latency"],
                geo_unblocked=True,
                details=f"Custom Base URL ({target_endpoint})",
                key_valid=res.get("key_valid", False),
            )

    # 2. Custom Proxy if user explicitly set one
    if custom_proxy or preferred_mode == "custom_proxy":
        target_proxy = custom_proxy
        res = test_endpoint(OFFICIAL_ENDPOINT, proxy=target_proxy, api_key=api_key, timeout=4.0)
        if res and res["unblocked"] and not res.get("blocked"):
            return ConnectionResult(
                "custom_proxy",
                OFFICIAL_ENDPOINT,
                proxy_url=target_proxy,
                latency_ms=res["latency"],
                geo_unblocked=True,
                details=f"Custom proxy ({target_proxy})",
                key_valid=res.get("key_valid", False),
            )

    # 3. If user explicitly requested direct connection
    if preferred_mode == "direct":
        res = test_endpoint(OFFICIAL_ENDPOINT, proxy=None, api_key=api_key, timeout=3.5)
        if res and res["unblocked"] and not res.get("blocked"):
            return ConnectionResult(
                "direct",
                OFFICIAL_ENDPOINT,
                proxy_url=None,
                latency_ms=res["latency"],
                geo_unblocked=True,
                details="Direct connection",
                key_valid=res.get("key_valid", False),
            )
        return ConnectionResult(
            "failed",
            OFFICIAL_ENDPOINT,
            proxy_url=None,
            latency_ms=res["latency"] if res else 0,
            geo_unblocked=False,
            details="Прямое подключение заблокировано Google (User location is not supported).",
        )

    # 4. Auto mode:
    has_real_key = bool(api_key and len(api_key.strip()) > 10)

    # If real API key is available, probe direct connection first
    if has_real_key:
        direct_res = test_endpoint(OFFICIAL_ENDPOINT, proxy=None, api_key=api_key, timeout=3.0)
        if direct_res and direct_res.get("key_valid"):
            # Direct connection works and key is valid!
            return ConnectionResult(
                "direct",
                OFFICIAL_ENDPOINT,
                proxy_url=None,
                latency_ms=direct_res["latency"],
                geo_unblocked=True,
                details="Direct connection (unrestricted)",
                key_valid=True,
            )
        elif direct_res and direct_res.get("blocked"):
            # Direct connection is geo-blocked by Google! Fall through to proxies.
            pass
        elif direct_res and direct_res.get("reason") == "API_KEY_INVALID":
            # Reached Google, but key itself is bad
            return ConnectionResult(
                "direct",
                OFFICIAL_ENDPOINT,
                proxy_url=None,
                latency_ms=direct_res["latency"],
                geo_unblocked=True,
                details="Direct connection (API key invalid)",
                key_valid=False,
            )

    # Check environment proxy (HTTP_PROXY / HTTPS_PROXY / ALL_PROXY)
    env_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("ALL_PROXY")
    if env_proxy:
        env_res = test_endpoint(OFFICIAL_ENDPOINT, proxy=env_proxy, api_key=api_key, timeout=3.5)
        if env_res and env_res.get("unblocked") and not env_res.get("blocked"):
            return ConnectionResult(
                "env_proxy",
                OFFICIAL_ENDPOINT,
                proxy_url=env_proxy,
                latency_ms=env_res["latency"],
                geo_unblocked=True,
                details=f"Environment proxy ({env_proxy})",
                key_valid=env_res.get("key_valid", False),
            )

    # Scan local proxy clients (V2Ray / Xray / Clash / Hiddify / Shadowsocks / Sing-box)
    local_match = scan_local_proxies(api_key=api_key, timeout=2.5)
    if local_match:
        return ConnectionResult(
            "local_proxy",
            OFFICIAL_ENDPOINT,
            proxy_url=local_match["url"],
            latency_ms=local_match["latency"],
            geo_unblocked=True,
            details=f"Auto-detected local proxy ({local_match['name']})",
            key_valid=local_match.get("key_valid", False),
        )

    # If no local proxy detected, test direct connection as fallback
    direct_res = test_endpoint(OFFICIAL_ENDPOINT, proxy=None, api_key=api_key, timeout=3.0)
    if direct_res and not direct_res.get("blocked"):
        return ConnectionResult(
            "direct",
            OFFICIAL_ENDPOINT,
            proxy_url=None,
            latency_ms=direct_res["latency"],
            geo_unblocked=True,
            details="Direct connection",
            key_valid=direct_res.get("key_valid", False),
        )

    # All avenues exhausted
    is_geo = direct_res and direct_res.get("blocked", False)
    msg = (
        "Google блокирует запросы из РФ (User location is not supported). Запустите VPN (V2Ray/Clash) или настройте /proxy."
        if is_geo
        else "Не удалось связаться с серверами Google Gemini. Проверьте интернет-соединение или настройте /proxy."
    )
    return ConnectionResult(
        "failed",
        OFFICIAL_ENDPOINT,
        proxy_url=None,
        latency_ms=0,
        geo_unblocked=False,
        details=msg,
    )
