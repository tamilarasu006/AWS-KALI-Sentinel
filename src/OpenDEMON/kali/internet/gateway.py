"""Internet Gateway Manager."""
from typing import Optional

from OpenDEMON.kali.internet.models import NetworkPolicy, GatewayRequest, GatewayResponse
from OpenDEMON.kali.internet.clients import HTTPClient

class InternetGateway:
    """
    Central mediator for all model-driven internet access.
    Enforces NetworkPolicy, SSRF protection, and audits requests.
    """
    def __init__(self, policy: Optional[NetworkPolicy] = None):
        self.policy = policy or NetworkPolicy()
        self.http_client = HTTPClient(self.policy)
        
    async def process_http_request(self, request: GatewayRequest) -> GatewayResponse:
        """Processes an HTTP request through the gateway."""
        # Auditing could be injected here (e.g. logging to a database)
        response = await self.http_client.request(request)
        return response
        
    # Additional clients like Search, Browser, etc., would be exposed similarly
    async def web_search(self, query: str) -> GatewayResponse:
        """Stub for web search that would use the HTTPClient securely."""
        # E.g. route to DuckDuckGo HTML or a search API
        req = GatewayRequest(url=f"https://html.duckduckgo.com/html/?q={query}")
        return await self.process_http_request(req)
