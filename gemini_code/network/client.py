"""
Asynchronous Google Gemini REST and SSE streaming client.
Supports custom base URLs, HTTP/SOCKS5 proxies, thinking/reasoning parts, and function calling.
"""

import json
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx

from .connectivity import diagnose_connection, ConnectionResult
from ..config import config
from ..quota.models import resolve_model_id

class GeoBlockedException(Exception):
    """Raised when Google AI Studio blocks request due to Russian IP / geo-location."""
    pass

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.api_key
        self._conn_result: Optional[ConnectionResult] = None
        self.reconnect()

    def reconnect(self):
        """Re-diagnose network route and configure HTTP client."""
        custom_proxy = config.custom_proxy_url
        custom_base = config.custom_base_url
        self._conn_result = diagnose_connection(
            preferred_mode=config.proxy_mode,
            custom_proxy=custom_proxy,
            custom_base_url=custom_base,
            api_key=self.api_key,
        )

    @property
    def connection_status(self) -> Optional[ConnectionResult]:
        return self._conn_result

    def get_http_client(self) -> httpx.AsyncClient:
        kwargs: Dict[str, Any] = {"timeout": 90.0, "follow_redirects": True}
        if self._conn_result and self._conn_result.proxy_url:
            kwargs["proxy"] = self._conn_result.proxy_url
        elif config.custom_proxy_url:
            kwargs["proxy"] = config.custom_proxy_url
        return httpx.AsyncClient(**kwargs)

    @property
    def base_url(self) -> str:
        url = "https://generativelanguage.googleapis.com"
        if config.custom_base_url:
            url = config.custom_base_url.rstrip("/")
        elif self._conn_result and self._conn_result.endpoint:
            url = self._conn_result.endpoint.rstrip("/")
        if url.endswith("/v1beta"):
            url = url[:-7]
        return url

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "GeminiCode/1.0",
        }
        if self.api_key:
            headers["x-goog-api-key"] = self.api_key
        return headers

    async def list_models(self) -> List[Dict[str, Any]]:
        """Fetch list of available models from Google AI Studio."""
        url = f"{self.base_url}/v1beta/models?key={self.api_key}"
        async with self.get_http_client() as client:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code != 200:
                text = resp.text
                if "User location is not supported" in text or "FAILED_PRECONDITION" in text:
                    raise GeoBlockedException(
                        "Google блокирует доступ из вашего региона (User location is not supported). "
                        "Включите VPN/прокси или настройте адрес через команду /proxy."
                    )
                raise RuntimeError(f"Error fetching models ({resp.status_code}): {text}")
            data = resp.json()
            return data.get("models", [])

    async def stream_generate_content(
        self,
        model: str,
        contents: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response tokens, thinking blocks, and function calls from Gemini using Server-Sent Events (SSE).
        """
        # Resolve any alias (e.g. 'flash' -> 'gemini-2.0-flash')
        resolved_model = resolve_model_id(model)
        clean_model = resolved_model.strip().replace("models/", "")
        model_name = f"models/{clean_model}"
        url = f"{self.base_url}/v1beta/{model_name}:streamGenerateContent?alt=sse&key={self.api_key}"

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if tools:
            payload["tools"] = tools

        async with self.get_http_client() as client:
            async with client.stream("POST", url, json=payload, headers=self._get_headers()) as resp:
                if resp.status_code != 200:
                    error_bytes = await resp.aread()
                    error_str = error_bytes.decode("utf-8", errors="replace")
                    lower_err = error_str.lower()
                    if "user location is not supported" in lower_err or "failed_precondition" in lower_err:
                        raise GeoBlockedException(
                            "Google блокирует запросы из вашего региона (User location is not supported). "
                            "Настройте прокси или бесплатный Cloudflare Worker через команду /proxy."
                        )
                    raise RuntimeError(f"Gemini API error ({resp.status_code}): {error_str}")

                buffer = ""
                async for chunk in resp.aiter_text():
                    buffer += chunk
                    lines = buffer.split("\n")
                    buffer = lines.pop()  # Keep incomplete line

                    for line in lines:
                        line = line.strip()
                        if line.startswith("data: "):
                            json_str = line[6:].strip()
                            if not json_str:
                                continue
                            try:
                                data = json.loads(json_str)
                                candidates = data.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        yield part
                            except Exception:
                                pass
