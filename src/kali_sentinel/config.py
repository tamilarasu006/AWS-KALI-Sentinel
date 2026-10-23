"""Configuration module for KALI Sentinel.

Reads configuration from environment variables with safe defaults.
Enforces authorization scope and security boundaries.
"""

from __future__ import annotations

import ipaddress
import os
import re
from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class SentinelConfig:
    """Runtime configuration for KALI Sentinel."""

    # AWS & Amazon Bedrock
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_temperature: float = 0.2
    bedrock_max_tokens: int = 1024
    bedrock_mock_fallback: bool = True

    # Strands Decider 2B
    strands_decider_url: str = "http://127.0.0.1:8000"
    strands_decider_model: str = "StrandsAgents/strands-decider-2B-hobson-v21"
    strands_decider_timeout: float = 5.0
    strands_mock_fallback: bool = True

    # Security & Authorization Scope
    safe_mode: bool = True
    authorized_targets: Set[str] = field(default_factory=lambda: {
        "localhost",
        "127.0.0.1",
        "::1",
        "test.local",
        "lab.local",
        "example.com",
        "scanme.nmap.org",  # Public authorized scanner testing domain
    })

    # Allowed private subnets for lab environments (RFC 1918 + loopback)
    allowed_subnets: List[str] = field(default_factory=lambda: [
        "127.0.0.0/8",      # Loopback
        "10.0.0.0/8",       # Private-use Class A
        "172.16.0.0/12",    # Private-use Class B
        "192.168.0.0/16",   # Private-use Class C
    ])

    # Database Persistence (PostgreSQL + pgvector / in-memory fallback)
    database_url: Optional[str] = None
    database_required: bool = False

    # KALI Model Live API (hosted / ngrok endpoint)
    kali_api_url: str = "https://unportentous-vanna-unpretentiously.ngrok-free.dev"
    kali_model_name: str = "Qwen3-8B"

    @classmethod
    def from_env(cls) -> SentinelConfig:
        """Construct configuration from environment variables."""
        targets_raw = os.getenv(
            "SENTINEL_AUTHORIZED_TARGETS",
            "localhost,127.0.0.1,::1,test.local,lab.local,example.com,scanme.nmap.org",
        )
        authorized_targets = {t.strip().lower() for t in targets_raw.split(",") if t.strip()}

        safe_mode_raw = os.getenv("SENTINEL_SAFE_MODE", "true").lower()
        safe_mode = safe_mode_raw in ("1", "true", "yes", "on")

        bedrock_mock = os.getenv("SENTINEL_MOCK_BEDROCK", "true").lower() in ("1", "true", "yes", "on")
        decider_mock = os.getenv("SENTINEL_MOCK_DECIDER", "true").lower() in ("1", "true", "yes", "on")

        db_req_raw = os.getenv("SENTINEL_DB_REQUIRED", "false").lower()
        db_required = db_req_raw in ("1", "true", "yes", "on")

        return cls(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            bedrock_model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
            bedrock_temperature=float(os.getenv("BEDROCK_TEMPERATURE", "0.2")),
            bedrock_max_tokens=int(os.getenv("BEDROCK_MAX_TOKENS", "1024")),
            bedrock_mock_fallback=bedrock_mock,
            strands_decider_url=os.getenv("STRANDS_DECIDER_URL", "http://127.0.0.1:8000"),
            strands_decider_model=os.getenv("STRANDS_DECIDER_MODEL", "StrandsAgents/strands-decider-2B-hobson-v21"),
            strands_decider_timeout=float(os.getenv("STRANDS_DECIDER_TIMEOUT", "5.0")),
            strands_mock_fallback=decider_mock,
            safe_mode=safe_mode,
            authorized_targets=authorized_targets,
            database_url=os.getenv("DATABASE_URL", None),
            database_required=db_required,
            kali_api_url=os.getenv("KALI_API_URL", "https://unportentous-vanna-unpretentiously.ngrok-free.dev"),
            kali_model_name=os.getenv("KALI_MODEL_NAME", "Qwen3-8B"),
        )

    def is_target_authorized(self, target: str) -> bool:
        """Validate whether a target hostname, domain, or IP address is authorized.
        
        Enforces defensive safety policies:
        1. Checks exact match against authorized_targets.
        2. If IP, validates against private RFC1918/loopback ranges.
        3. If domain, checks if domain or parent domain is authorized.
        """
        if not target:
            return False

        cleaned = target.strip().lower()
        # Remove protocol if user passed e.g. http://localhost:8080
        cleaned = re.sub(r"^https?://", "", cleaned)
        # Remove trailing paths or query params
        cleaned = cleaned.split("/")[0].split(":")[0]

        if not cleaned:
            return False

        if not self.safe_mode:
            # If safe mode disabled, still check against authorized list
            return cleaned in self.authorized_targets

        # Check explicit authorized list
        if cleaned in self.authorized_targets:
            return True

        # Check subdomains of authorized targets
        for auth in self.authorized_targets:
            if cleaned.endswith("." + auth):
                return True

        # Check IP address validity
        try:
            ip = ipaddress.ip_address(cleaned)
            for subnet in self.allowed_subnets:
                if ip in ipaddress.ip_network(subnet):
                    return True
        except ValueError:
            pass

        return False


# Singleton config instance
_GLOBAL_CONFIG: SentinelConfig | None = None


def get_sentinel_config() -> SentinelConfig:
    """Get or initialize global Sentinel configuration."""
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = SentinelConfig.from_env()
    return _GLOBAL_CONFIG
