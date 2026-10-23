"""Client for the hosted KALI Sentinel Model API.

Integrates with the live hosted KALI model at:
https://unportentous-vanna-unpretentiously.ngrok-free.dev

Handles:
- POST /generate with {"message": "<prompt>"}
- Header injection (ngrok-skip-browser-warning)
- Output parsing and clean extraction of reasoning and response blocks
- Safe offline fallback when API is unreachable
"""
from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_KALI_API_URL = os.getenv(
    "KALI_API_URL", "https://unportentous-vanna-unpretentiously.ngrok-free.dev"
)

_CLIENT_INSTANCE: Optional[KaliModelClient] = None


class KaliModelClient:
    """Client for generating security responses via the hosted KALI Sentinel Model API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 35.0) -> None:
        raw_url = base_url or os.getenv("KALI_API_URL") or DEFAULT_KALI_API_URL
        self.base_url = raw_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> bool:
        """Check if the KALI Model API is reachable."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/health",
                headers={
                    "ngrok-skip-browser-warning": "true",
                    "User-Agent": "curl/7.68.0",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status == 200
        except Exception as exc:
            logger.debug("KALI API health check failed: %s", exc)
            return False

    def generate(self, message: str) -> Optional[str]:
        """Generate text from KALI model using /generate endpoint."""
        if not message or not message.strip():
            return None

        clean_message = message.strip()
        try:
            url = f"{self.base_url}/generate"
            payload = json.dumps({"message": clean_message}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "ngrok-skip-browser-warning": "true",
                    "User-Agent": "curl/7.68.0",
                },
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                if r.status != 200:
                    logger.warning("KALI Model API returned HTTP %d", r.status)
                    return None
                data = json.loads(r.read().decode("utf-8", errors="ignore"))
                raw_response = data.get("response", "")
                cleaned = self.clean_output(raw_response)
                if cleaned:
                    return cleaned
        except Exception as exc:
            logger.info("KALI Model API invocation failed (%s); falling back to local Astra-6 knowledge base", exc)

        return None

    @staticmethod
    def clean_output(raw: str) -> str:
        """Format and clean output from KALI model, removing or formatting thinking tags."""
        if not raw:
            return ""
        text = raw.strip()
        # If model generated a reasoning block followed by answer:
        if "</think>" in text:
            parts = text.split("</think>", 1)
            ans = parts[1].strip()
            if ans:
                return ans
            # If nothing after </think>, take what was inside
            inside = parts[0].replace("<think>", "").strip()
            if inside:
                return inside

        # If generation stopped within <think>, strip the opening tag so thought is readable
        if text.startswith("<think>"):
            text = text[len("<think>"):].strip()

        return text


def get_kali_client(base_url: Optional[str] = None) -> KaliModelClient:
    """Retrieve or create singleton KALI Model Client."""
    global _CLIENT_INSTANCE
    if _CLIENT_INSTANCE is None or (base_url and base_url != _CLIENT_INSTANCE.base_url):
        _CLIENT_INSTANCE = KaliModelClient(base_url=base_url)
    return _CLIENT_INSTANCE
