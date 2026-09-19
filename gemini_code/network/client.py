"""
Asynchronous Google Gemini REST and SSE streaming client.
Supports custom base URLs, HTTP/SOCKS5 proxies, and function calling.
"""

import json
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx

from .connectivity import diagnose_connection, ConnectionResult
from ..config import config

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.api_key
        self._conn_result: Optional[ConnectionResult] = None
        self._init_connection()

    def _init_connection(self):
        """Initialize connection route based on config and network tests."""
        custom_proxy = config.custom_proxy_url if config.proxy_mode == "custom" else ""
        self._conn_result = diagnose_connection(
            preferred_mode=config.proxy_mode,
            custom_proxy=custom_proxy,
        )

    def get_http_client(self) -> httpx.AsyncClient:
        kwargs: Dict[str, Any] = {"timeout": 60.0}
        if self._conn_result and self._conn_result.proxy_url:
            kwargs["proxy"] = self._conn_result.proxy_url
        return httpx.AsyncClient(**kwargs)

    @property
    def base_url(self) -> str:
        if self._conn_result:
            return self._conn_result.endpoint.rstrip("/")
        return "https://generativelanguage.googleapis.com"

    async def list_models(self) -> List[Dict[str, Any]]:
        """Fetch list of available models from Google AI Studio."""
        url = f"{self.base_url}/v1beta/models?key={self.api_key}"
        async with self.get_http_client() as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise RuntimeError(f"Error fetching models ({resp.status_code}): {resp.text}")
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
        Stream response tokens and function calls from Gemini using Server-Sent Events (SSE).
        """
        # Ensure model has 'models/' prefix
        model_name = model if model.startswith("models/") else f"models/{model}"
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
            async with client.stream("POST", url, json=payload, headers={"Content-Type": "application/json"}) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    raise RuntimeError(f"Gemini API error ({resp.status_code}): {error_body.decode('utf-8', errors='replace')}")

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
