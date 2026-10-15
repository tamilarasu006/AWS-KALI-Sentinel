import re
from typing import Dict, Any

class SecurityFilter:
    """
    Filters text to prevent training on sensitive information.
    """
    def __init__(self):
        self.deny_patterns = [
            re.compile(r"(?i)(api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?"),
            re.compile(r"(?i)(password|passwd|pwd)['\"]?\s*[:=]\s*['\"]?[^\s\"']{8,}['\"]?"),
            re.compile(r"(?i)(secret|token)['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?"),
            re.compile(r"(?i)eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"), # JWT
            re.compile(r"(?i)(postgres|mysql|mongodb\+srv)://[a-zA-Z0-9_]+:[^@\s]+@[a-zA-Z0-9_.-]+"), # DB URI
            re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
            re.compile(r"(?im)^[A-Z0-9_]+=[^\s]+$") # Common .env pattern
        ]

    def contains_sensitive_data(self, text: str) -> bool:
        for pattern in self.deny_patterns:
            if pattern.search(text):
                return True
        return False

class QualityFilter:
    """
    Filters for empty content, garbled text, excessive repetition, etc.
    """
    def __init__(self):
        self.stats = {"removed": 0, "total": 0}

    def is_quality_sample(self, text: str) -> bool:
        self.stats["total"] += 1
        if not text or len(text.strip()) < 10:
            self.stats["removed"] += 1
            return False
        # simple check for excessive repetition
        words = text.split()
        if len(words) > 50 and len(set(words)) / len(words) < 0.1:
            self.stats["removed"] += 1
            return False
        return True
