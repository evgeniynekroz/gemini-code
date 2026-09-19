"""
Network connectivity checker and auto-detector for Gemini access.
Handles direct check, local proxy port scanning, and proxy fallbacks.
"""

import socket
import time
from typing import Optional, Dict, Any
import httpx

from .proxies import OFFICIAL_ENDPOINT, LOCAL_PROXY_CANDIDATES, MIRROR_ENDPOINTS

class ConnectionResult:
    def __init__(
        self,
        mode: str,
        endpoint: str,
        proxy_url: Optional[str] = None,
        latency_ms: int = 0,
        geo_unblocked: bool = False,
        details: str = "",
    ):
        self.mode = mode
        self.endpoint = endpoint
        self.proxy_url = proxy_url
        self.latency_ms = latency_ms
        self.geo_unblocked = geo_unblocked
        self.details = details

    def is_success(self) -> bool:
        return self.geo_unblocked

def test_endpoint(endpoint: str, proxy: Optional[str] = None, timeout: float = 3.5) -> Optional[Dict[str, Any]]:
    """
    Send a lightweight probe to test if Gemini API responds and if geo-blocking is bypassed.
    Google returns code 400 'API key not valid' when geo-unblocked.
    Google returns code 400 'User location is not supported' when geo-blocked.
    """
    test_url = f"{endpoint.rstrip('/')}/v1beta/models?key=connectivity_probe"
    start_time = time.time()
    try:
        kwargs = {"timeout": timeout}
        if proxy:
            kwargs["proxy"] = proxy

        with httpx.Client(**kwargs) as client:
            resp = client.get(test_url)
            latency = int((time.time() - start_time) * 1000)
            text = resp.text
            ctype = resp.headers.get("content-type", "")

            # If response is HTML or not JSON, it is NOT a Gemini API endpoint
            if "application/json" not in ctype and not text.strip().startswith("{"):
                return None

            if "User location is not supported" in text or "FAILED_PRECONDITION" in text:
                return {"unblocked": False, "blocked": True, "latency": latency, "text": text}
            
            # API_KEY_INVALID or 400 with API key message means access is granted
            if resp.status_code == 400 or resp.status_code == 200:
                return {"unblocked": True, "blocked": False, "latency": latency, "text": text}

            return {"unblocked": False, "blocked": False, "latency": latency, "text": text}
    except Exception as e:
        return None

def check_port_open(host: str, port: int, timeout: float = 0.15) -> bool:
    """Check if a local TCP port is open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def diagnose_connection(preferred_mode: str = "auto", custom_proxy: str = "") -> ConnectionResult:
    """
    Perform a complete connectivity diagnostic and find the best working connection method.
    """
    # 1. Custom proxy if user set one
    if custom_proxy:
        res = test_endpoint(OFFICIAL_ENDPOINT, proxy=custom_proxy)
        if res and res["unblocked"]:
            return ConnectionResult("custom", OFFICIAL_ENDPOINT, proxy_url=custom_proxy, latency_ms=res["latency"], geo_unblocked=True, details="Custom proxy")

    # 2. Step 1: Direct connection check
    res = test_endpoint(OFFICIAL_ENDPOINT, proxy=None, timeout=3.0)
    if res and res["unblocked"]:
        return ConnectionResult("direct", OFFICIAL_ENDPOINT, proxy_url=None, latency_ms=res["latency"], geo_unblocked=True, details="Direct connection (VPN/Global IP active)")

    # 3. Step 2: Scan local proxy clients (V2Ray / Xray / Clash / Hiddify)
    for candidate in LOCAL_PROXY_CANDIDATES:
        url = candidate["url"]
        name = candidate["name"]
        try:
            # Extract port
            port = int(url.split(":")[-1])
            if check_port_open("127.0.0.1", port):
                res = test_endpoint(OFFICIAL_ENDPOINT, proxy=url, timeout=3.0)
                if res and res["unblocked"]:
                    return ConnectionResult("local_proxy", OFFICIAL_ENDPOINT, proxy_url=url, latency_ms=res["latency"], geo_unblocked=True, details=f"Auto-detected local proxy ({name})")
        except Exception:
            continue

    # 4. Step 3: Check fallback reverse proxy mirrors
    for mirror in MIRROR_ENDPOINTS:
        res = test_endpoint(mirror, proxy=None, timeout=3.5)
        if res and res["unblocked"]:
            return ConnectionResult("mirror", mirror, proxy_url=None, latency_ms=res["latency"], geo_unblocked=True, details=f"Public mirror ({mirror})")

    # 5. Failed
    return ConnectionResult("failed", OFFICIAL_ENDPOINT, proxy_url=None, latency_ms=0, geo_unblocked=False, details="No working route found to Google Gemini")
