"""KALI AI Server Facade.

This module wraps the OpenDEMON FastAPI application to provide KALI-specific
branding, middleware, or endpoints if needed in the future.
"""

from fastapi import FastAPI
from OpenDEMON.server.app import create_app as create_opendemon_app

def create_kali_app(*args, **kwargs) -> FastAPI:
    """Create the KALI AI FastAPI application.
    
    Currently this directly proxies to the underlying OpenDEMON app creation,
    but it serves as an injection point for future KALI-specific routes or middleware.
    """
    app = create_opendemon_app(*args, **kwargs)
    # Future: override title/description here if not already handled
    app.title = "KALI API"
    app.description = "OpenAI-compatible API server for KALI AI"
    return app
