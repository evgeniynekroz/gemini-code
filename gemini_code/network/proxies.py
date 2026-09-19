"""
Proxy endpoints, mirrors, and SmartDNS definitions.
"""

from typing import List, Dict

# Official Google Gemini API Endpoint
OFFICIAL_ENDPOINT = "https://generativelanguage.googleapis.com"

# Standard ports used by local VPN/Proxy clients in Russia/CIS
LOCAL_PROXY_CANDIDATES: List[Dict[str, str]] = [
    {"type": "socks5", "url": "socks5://127.0.0.1:10808", "name": "V2Ray/Xray (SOCKS5 10808)"},
    {"type": "http",   "url": "http://127.0.0.1:10809",   "name": "V2Ray/Xray (HTTP 10809)"},
    {"type": "http",   "url": "http://127.0.0.1:7890",    "name": "Clash/Mihomo (HTTP 7890)"},
    {"type": "socks5", "url": "socks5://127.0.0.1:7890",  "name": "Clash/Mihomo (SOCKS5 7890)"},
    {"type": "http",   "url": "http://127.0.0.1:2080",    "name": "Hiddify (HTTP 2080)"},
    {"type": "socks5", "url": "socks5://127.0.0.1:1080",  "name": "Shadowsocks (SOCKS5 1080)"},
]

# SmartDNS servers that bypass geo-blocking by routing SNI through European proxies
SMART_DNS_SERVERS = [
    {"name": "Comss.one DNS", "doh": "https://dns.comss.one/dns-query", "ip": "92.223.109.31"},
    {"name": "Luna DNS",      "doh": "https://dns.lunadns.ru/dns-query", "ip": "94.131.119.85"},
    {"name": "Xbox / SmartDNS", "doh": "", "ip": "176.99.11.77"},
]

# Fallback reverse proxy mirrors for Gemini API
MIRROR_ENDPOINTS = [
    "https://api.gemini-proxy.ru",
    "https://gemini.chat-api.net",
    "https://api.aiproxy.io",
]
