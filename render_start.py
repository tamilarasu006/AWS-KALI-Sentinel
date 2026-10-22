"""Render.com entry point — starts KALI Sentinel Unified API server.

Runs the complete KALI Sentinel agent with Bedrock integration,
Strands Decider 2B routing, PostgreSQL persistence (with safe fallback),
and serves the React SPA frontend from static assets.
"""
from __future__ import annotations

import logging
import os
import sys

# Ensure src is on Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uvicorn
from kali_sentinel.server.routes import create_sentinel_app

app = create_sentinel_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print(f"[KALI Sentinel] Starting unified server on http://{host}:{port}", flush=True)
    uvicorn.run(app, host=host, port=port, log_level="info")
