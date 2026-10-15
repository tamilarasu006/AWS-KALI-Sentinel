import logging
import re
from typing import Any

class SecretSanitizerFilter(logging.Filter):
    """
    Logging filter that intercepts log messages and scrubs any matched secrets
    before they are emitted to the handlers.
    """
    
    # Common regex patterns that catch high-entropy secrets, JWTs, and keys.
    # Looks for keywords followed by typical secret formats (Base64, hex, JWT structure).
    SECRET_PATTERNS = [
        re.compile(r'(?i)(password|api[_-]?key|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9_=\-\.]{16,}["\']?'),
        re.compile(r'(?i)bearer\s+[A-Za-z0-9_=\-\.]+'),
        re.compile(r'eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*') # JWT
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern in self.SECRET_PATTERNS:
                record.msg = pattern.sub(r'\1: [REDACTED]', record.msg) if r'\1' in pattern.pattern else pattern.sub('[REDACTED]', record.msg)
        return True

def configure_production_logging():
    """
    Attaches the SecretSanitizerFilter to all core loggers to prevent
    secret spillage in production environments.
    """
    sanitizer = SecretSanitizerFilter()
    
    # Attach to root logger
    root_logger = logging.getLogger()
    if not any(isinstance(f, SecretSanitizerFilter) for f in root_logger.filters):
        root_logger.addFilter(sanitizer)
        
    # Attach to DEMON namespace
    demon_logger = logging.getLogger("OpenDEMON")
    if not any(isinstance(f, SecretSanitizerFilter) for f in demon_logger.filters):
        demon_logger.addFilter(sanitizer)
