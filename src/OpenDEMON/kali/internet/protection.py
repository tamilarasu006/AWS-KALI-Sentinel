"""URL Validation and SSRF Protection."""
import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, Optional

from OpenDEMON.kali.internet.models import NetworkPolicy

class SSRFProtection:
    """Provides mechanisms to detect and block Server-Side Request Forgery."""
    
    @staticmethod
    def is_ip_private(ip_str: str) -> bool:
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved
        except ValueError:
            return False

class URLValidator:
    """Validates URLs against network policies and SSRF checks."""
    
    def __init__(self, policy: NetworkPolicy):
        self.policy = policy
        
    def validate(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validates a URL before it is fetched.
        Returns: (is_valid, error_reason)
        """
        try:
            parsed = urlparse(url)
        except Exception:
            return False, "Invalid URL format"
            
        if parsed.scheme not in ("http", "https"):
            return False, f"Unsupported scheme: {parsed.scheme}"
            
        if parsed.scheme == "http" and not self.policy.allow_http:
            return False, "HTTP is denied by policy (HTTPS required)"
            
        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname"
            
        # Check domain policies
        if self.policy.domain_policy.denied_domains:
            if any(hostname == d or hostname.endswith(f".{d}") for d in self.policy.domain_policy.denied_domains):
                return False, "Domain is explicitly denied"
                
        if self.policy.domain_policy.allowed_domains:
            if not any(hostname == d or hostname.endswith(f".{d}") for d in self.policy.domain_policy.allowed_domains):
                return False, "Domain is not in the allowed list"
                
        # SSRF Protection: Resolve IP to prevent DNS rebinding or direct IP access
        try:
            # gethostbyname resolves the IP
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            return False, "DNS resolution failed"
            
        if SSRFProtection.is_ip_private(ip):
            return False, f"Access to private/internal IP ({ip}) is blocked (SSRF Protection)"
            
        return True, None
