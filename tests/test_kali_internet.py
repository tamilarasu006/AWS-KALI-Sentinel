import pytest
import asyncio
from unittest.mock import patch, MagicMock

from OpenDEMON.kali.internet.models import NetworkPolicy, DomainPolicy, GatewayRequest
from OpenDEMON.kali.internet.gateway import InternetGateway

@pytest.fixture
def gateway():
    return InternetGateway()

@pytest.mark.asyncio
async def test_invalid_url(gateway):
    req = GatewayRequest(url="not_a_url")
    result = await gateway.process_http_request(req)
    assert not result.success
    assert "Invalid URL" in result.error or "Missing hostname" in result.error

@pytest.mark.asyncio
async def test_http_denied_by_policy(gateway):
    gateway.policy.allow_http = False
    req = GatewayRequest(url="http://example.com")
    result = await gateway.process_http_request(req)
    assert not result.success
    assert "HTTP is denied" in result.error

@pytest.mark.asyncio
async def test_ssrf_localhost_blocked(gateway):
    req = GatewayRequest(url="https://127.0.0.1")
    result = await gateway.process_http_request(req)
    assert not result.success
    assert "SSRF Protection" in result.error
    assert "127.0.0.1" in result.error

@pytest.mark.asyncio
async def test_ssrf_private_ip_blocked(gateway):
    req = GatewayRequest(url="https://192.168.1.100")
    result = await gateway.process_http_request(req)
    assert not result.success
    assert "SSRF Protection" in result.error

@pytest.mark.asyncio
@patch('socket.gethostbyname')
async def test_ssrf_dns_rebinding_simulation(mock_gethostbyname, gateway):
    # Simulate a domain that resolves to localhost
    mock_gethostbyname.return_value = "127.0.0.1"
    req = GatewayRequest(url="https://myfakedomain.com")
    result = await gateway.process_http_request(req)
    assert not result.success
    assert "SSRF Protection" in result.error

@pytest.mark.asyncio
async def test_domain_allowlist(gateway):
    gateway.policy.domain_policy = DomainPolicy(allowed_domains=["example.com"])
    
    req1 = GatewayRequest(url="https://example.com")
    # Will fail network request because we aren't mocking httpx, but shouldn't fail validation
    # Actually example.com is real, we might get a 200 or timeout.
    
    req2 = GatewayRequest(url="https://google.com")
    result2 = await gateway.process_http_request(req2)
    assert not result2.success
    assert "not in the allowed list" in result2.error

@pytest.mark.asyncio
async def test_domain_denylist(gateway):
    gateway.policy.domain_policy = DomainPolicy(denied_domains=["evil.com"])
    req = GatewayRequest(url="https://evil.com")
    result = await gateway.process_http_request(req)
    assert not result.success
    assert "explicitly denied" in result.error
