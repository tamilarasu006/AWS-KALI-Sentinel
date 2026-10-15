import pytest
import logging
from OpenDEMON.security.audit_logger import configure_production_logging, SecretSanitizerFilter
from OpenDEMON.security.ssrf import check_ssrf

def test_secret_sanitizer():
    sanitizer = SecretSanitizerFilter()
    
    # Test Password / API Key Masking
    record = logging.LogRecord("test", logging.INFO, "test.py", 1, "Connecting with api_key: 'sk-1234567890abcdef1234567890abcdef'", None, None)
    sanitizer.filter(record)
    assert "sk-1234567890" not in record.msg
    assert "[REDACTED]" in record.msg
    
    # Test JWT Masking
    record2 = logging.LogRecord("test", logging.INFO, "test.py", 1, "Token is eyJhbGciOiJIUzI1NiIsInR5cCI.eyJzdWIiOiIxMjM0NTY3ODkwIiwib.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", None, None)
    sanitizer.filter(record2)
    assert "eyJhbGci" not in record2.msg
    assert "[REDACTED]" in record2.msg

def test_ssrf_mitigation():
    # Test loopback protection
    err = check_ssrf("http://127.0.0.1:8080/admin")
    assert err is not None
    assert "private" in err.lower()
    
    # Test metadata service protection
    err2 = check_ssrf("http://169.254.169.254/latest/meta-data")
    assert err2 is not None
    assert "metadata" in err2.lower()
    
    # Valid external URL should pass
    err3 = check_ssrf("https://www.google.com")
    assert err3 is None

def test_path_traversal_prevention_logic():
    # Simulating what happens in app.py's spa_catch_all
    import pathlib
    static_root = pathlib.Path("/var/www/static").resolve()
    
    # Safe path
    safe_path = (static_root / "assets/style.css").resolve()
    assert safe_path.is_relative_to(static_root)
    
    # Malicious path
    malicious_path = (static_root / "../../etc/passwd").resolve()
    assert not malicious_path.is_relative_to(static_root)
