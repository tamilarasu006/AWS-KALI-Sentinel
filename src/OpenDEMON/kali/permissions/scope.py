import ipaddress
import re
from typing import List
from urllib.parse import urlparse

class ScopeValidator:
    """
    Validates targets against authorized scopes.
    Supports IPs, CIDRs, hostnames, and URLs.
    """

    @staticmethod
    def is_target_in_scope(target: str, scope: List[str]) -> bool:
        """
        Returns True if the target is covered by ANY of the scope definitions.
        """
        if not scope:
            return False
            
        # Normalize target
        target = ScopeValidator._extract_host(target)

        for s in scope:
            if ScopeValidator._matches_scope(target, s):
                return True
        return False

    @staticmethod
    def _extract_host(target: str) -> str:
        """Extracts hostname or IP from URL, or returns it as-is."""
        if target.startswith("http://") or target.startswith("https://"):
            try:
                return urlparse(target).hostname or target
            except Exception:
                return target
        return target

    @staticmethod
    def _matches_scope(target: str, scope_item: str) -> bool:
        """Checks if a target matches a single scope item."""
        target = target.lower()
        scope_item = scope_item.lower()

        if target == scope_item:
            return True

        # Check CIDR
        try:
            if "/" in scope_item:
                network = ipaddress.ip_network(scope_item, strict=False)
                ip = ipaddress.ip_address(target)
                if ip in network:
                    return True
        except ValueError:
            pass # Not a valid IP/Network

        # Check wildcard domains (e.g., *.example.com)
        if scope_item.startswith("*."):
            domain = scope_item[2:]
            if target == domain or target.endswith("." + domain):
                return True

        return False
