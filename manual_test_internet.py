import asyncio
from OpenDEMON.kali.internet.models import NetworkPolicy, DomainPolicy, GatewayRequest
from OpenDEMON.kali.internet.gateway import InternetGateway

async def run():
    print("Testing Internet Gateway...")
    gateway = InternetGateway()
    
    print("\n--- Test 1: SSRF Localhost ---")
    req1 = GatewayRequest(url="https://127.0.0.1")
    res1 = await gateway.process_http_request(req1)
    print(f"Success: {res1.success}")
    print(f"Error: {res1.error}")
    assert not res1.success
    assert "SSRF" in res1.error
    
    print("\n--- Test 2: HTTP blocked by default ---")
    req2 = GatewayRequest(url="http://example.com")
    res2 = await gateway.process_http_request(req2)
    print(f"Success: {res2.success}")
    print(f"Error: {res2.error}")
    assert not res2.success
    
    print("\n--- Test 3: Normal HTTPS ---")
    req3 = GatewayRequest(url="https://example.com")
    res3 = await gateway.process_http_request(req3)
    print(f"Success: {res3.success}")
    print(f"Status Code: {res3.status_code}")
    print(f"Content Sample: {res3.content[:50]}")
    assert res3.success
    assert "Example Domain" in res3.content
    
    print("\n--- Test 4: Domain Allowlist ---")
    gateway.policy.domain_policy.allowed_domains = ["google.com"]
    req4 = GatewayRequest(url="https://example.com")
    res4 = await gateway.process_http_request(req4)
    print(f"Success: {res4.success}")
    print(f"Error: {res4.error}")
    assert not res4.success
    
    print("\nALL TESTS PASSED MANUALLY!")

if __name__ == "__main__":
    asyncio.run(run())
