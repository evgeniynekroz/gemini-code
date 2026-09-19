"""
Real-time RPM, RPD, and token quota tracker for Gemini Free Tier limits.
"""

import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from .models import get_model_info
from ..config import config

class QuotaTracker:
    def __init__(self):
        self._request_timestamps: List[float] = []
        self._daily_requests: int = 0
        self._daily_date: str = self._current_utc_date()
        self._total_session_requests: int = 0
        self._total_tokens_used: int = 0

    def _current_utc_date(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _clean_minute_window(self):
        now = time.time()
        # Keep timestamps from the last 60 seconds
        self._request_timestamps = [t for t in self._request_timestamps if now - t < 60.0]

        # Reset daily counter if day has passed
        current_date = self._current_utc_date()
        if current_date != self._daily_date:
            self._daily_requests = 0
            self._daily_date = current_date

    def record_request(self, estimated_tokens: int = 0):
        self._clean_minute_window()
        now = time.time()
        self._request_timestamps.append(now)
        self._daily_requests += 1
        self._total_session_requests += 1
        self._total_tokens_used += estimated_tokens

    @property
    def current_rpm(self) -> int:
        self._clean_minute_window()
        return len(self._request_timestamps)

    @property
    def current_rpd(self) -> int:
        self._clean_minute_window()
        return self._daily_requests

    def get_status(self, model_id: str = "") -> Dict[str, Any]:
        mid = model_id or config.model
        info = get_model_info(mid)
        rpm = self.current_rpm
        rpd = self.current_rpd
        max_rpm = info["max_rpm"]
        max_rpd = info["max_rpd"]

        return {
            "model": info["name"],
            "model_id": mid,
            "rpm": rpm,
            "max_rpm": max_rpm,
            "rpm_remaining": max(0, max_rpm - rpm),
            "rpd": rpd,
            "max_rpd": max_rpd,
            "rpd_remaining": max(0, max_rpd - rpd),
            "session_total": self._total_session_requests,
            "context_window": info["context_window"],
        }

    def format_hud(self, model_id: str = "") -> str:
        status = self.get_status(model_id)
        return (
            f"[{status['model']} | RPM: {status['rpm']}/{status['max_rpm']} | "
            f"Day: {status['rpd']}/{status['max_rpd']}]"
        )

# Global singleton
quota_tracker = QuotaTracker()
