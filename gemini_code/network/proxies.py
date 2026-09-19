"""
Proxy endpoints, mirrors, and SmartDNS definitions.
"""

from typing import List, Dict

# Official Google Gemini API Endpoint
OFFICIAL_ENDPOINT = "https://generativelanguage.googleapis.com"

# Expanded list of ports used by local VPN/Proxy clients in Russia/CIS
LOCAL_PROXY_CANDIDATES: List[Dict[str, str]] = [
    {"type": "http",   "url": "http://127.0.0.1:10809",   "name": "V2RayN / Xray (HTTP 10809)"},
    {"type": "socks5", "url": "socks5://127.0.0.1:10808", "name": "V2RayN / Xray (SOCKS5 10808)"},
    {"type": "http",   "url": "http://127.0.0.1:7890",    "name": "Clash / Mihomo (HTTP 7890)"},
    {"type": "socks5", "url": "socks5://127.0.0.1:7890",  "name": "Clash / Mihomo (SOCKS5 7890)"},
    {"type": "http",   "url": "http://127.0.0.1:7897",    "name": "Clash Verge Rev (HTTP 7897)"},
    {"type": "http",   "url": "http://127.0.0.1:2080",    "name": "Hiddify Next (HTTP 2080)"},
    {"type": "socks5", "url": "socks5://127.0.0.1:2081",  "name": "Hiddify Next (SOCKS5 2081)"},
    {"type": "socks5", "url": "socks5://127.0.0.1:1080",  "name": "Shadowsocks (SOCKS5 1080)"},
    {"type": "socks5", "url": "socks5://127.0.0.1:20808", "name": "NekoBox (SOCKS5 20808)"},
    {"type": "http",   "url": "http://127.0.0.1:20809",   "name": "NekoBox (HTTP 20809)"},
    {"type": "http",   "url": "http://127.0.0.1:9090",    "name": "Sing-box (Mixed 9090)"},
    {"type": "http",   "url": "http://127.0.0.1:8080",    "name": "Local HTTP (8080)"},
]

# Cloudflare Worker template for instant, free reverse proxy from Russia
CLOUDFLARE_WORKER_SCRIPT = """
// Free deployment at https://workers.cloudflare.com
// 1. Create a Worker, e.g. 'gemini-worker'
// 2. Paste this code and click 'Deploy'
// 3. In Gemini Code, run /proxy -> Option 3 and paste your worker URL!

export default {
  async fetch(request) {
    const url = new URL(request.url);
    url.hostname = 'generativelanguage.googleapis.com';
    url.port = '443';
    url.protocol = 'https:';

    const newHeaders = new Headers(request.headers);
    newHeaders.set('host', 'generativelanguage.googleapis.com');

    const newRequest = new Request(url, {
      method: request.method,
      headers: newHeaders,
      body: request.body,
      redirect: 'follow',
    });
    return fetch(newRequest);
  }
};
""".strip()
