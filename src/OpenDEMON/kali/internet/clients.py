"""Concrete clients for internet interactions."""
import httpx
from typing import Optional

from OpenDEMON.kali.internet.models import NetworkPolicy, GatewayRequest, GatewayResponse
from OpenDEMON.kali.internet.protection import URLValidator

class HTTPClient:
    """Provides secure HTTP requests with size and redirect limits."""
    
    def __init__(self, policy: NetworkPolicy):
        self.policy = policy
        self.validator = URLValidator(policy)
        
    async def request(self, req: GatewayRequest) -> GatewayResponse:
        is_valid, error = self.validator.validate(req.url)
        if not is_valid:
            return GatewayResponse(success=False, error=f"Policy Block: {error}")
            
        try:
            # We use httpx AsyncClient
            # We do NOT allow it to auto-follow redirects immediately without SSRF checking the next hop.
            # To be truly safe against SSRF redirect attacks, we must follow redirects manually and check the URL.
            
            current_url = req.url
            redirect_count = 0
            
            async with httpx.AsyncClient(timeout=self.policy.timeout_seconds) as client:
                while True:
                    # Execute request
                    response = await client.request(
                        method=req.method,
                        url=current_url,
                        headers=req.headers,
                        content=req.body,
                        follow_redirects=False # Manual handling
                    )
                    
                    if 300 <= response.status_code < 400 and "location" in response.headers:
                        redirect_count += 1
                        if redirect_count > self.policy.max_redirects:
                            return GatewayResponse(success=False, error="Max redirects exceeded")
                            
                        next_url = response.headers["location"]
                        # Resolve relative URLs
                        if next_url.startswith("/"):
                            from urllib.parse import urlparse
                            parsed = urlparse(current_url)
                            next_url = f"{parsed.scheme}://{parsed.netloc}{next_url}"
                            
                        # Validate the new URL for SSRF/Policy!
                        is_valid, error = self.validator.validate(next_url)
                        if not is_valid:
                            return GatewayResponse(success=False, error=f"Redirect Policy Block: {error}")
                            
                        current_url = next_url
                        continue
                        
                    # Target reached, read content securely
                    # Check Content-Length first
                    content_length = int(response.headers.get("content-length", 0))
                    if content_length > self.policy.max_response_bytes:
                        return GatewayResponse(success=False, status_code=response.status_code, error="Response exceeds maximum allowed size")
                        
                    # Stream read to enforce limits on chunked transfer
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > self.policy.max_response_bytes:
                            return GatewayResponse(success=False, status_code=response.status_code, error="Response stream exceeds maximum allowed size")
                            
                    return GatewayResponse(
                        success=True,
                        status_code=response.status_code,
                        content=body.decode("utf-8", errors="replace"),
                        redirected_to=current_url if current_url != req.url else None
                    )
                    
        except httpx.TimeoutException:
            return GatewayResponse(success=False, error="Request timed out")
        except Exception as e:
            return GatewayResponse(success=False, error=str(e))
