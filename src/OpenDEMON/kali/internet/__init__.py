"""KALI Internet Gateway"""
from OpenDEMON.kali.internet.models import NetworkPolicy, DomainPolicy, GatewayRequest, GatewayResponse
from OpenDEMON.kali.internet.gateway import InternetGateway
from OpenDEMON.kali.internet.protection import SSRFProtection, URLValidator

__all__ = [
    "NetworkPolicy",
    "DomainPolicy",
    "GatewayRequest",
    "GatewayResponse",
    "InternetGateway",
    "SSRFProtection",
    "URLValidator"
]
