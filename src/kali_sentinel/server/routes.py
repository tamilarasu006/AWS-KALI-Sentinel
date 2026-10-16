"""FastAPI router for KALI Sentinel.

Exposes REST endpoints for executing the agent workflow, querying
available security tools, checking health, and inspecting configuration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from kali_sentinel.agent.sentinel_agent import KaliSentinelAgent, SentinelAgentResponse
from kali_sentinel.config import get_sentinel_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sentinel", tags=["KALI Sentinel"])

# Lazy singleton agent instance
_AGENT: Optional[KaliSentinelAgent] = None


def get_agent() -> KaliSentinelAgent:
    """Retrieve or initialize the singleton Sentinel Agent."""
    global _AGENT
    if _AGENT is None:
        _AGENT = KaliSentinelAgent()
    return _AGENT


class ExecuteRequest(BaseModel):
    """Payload for Sentinel Agent execution."""

    prompt: str = Field(..., description="User prompt describing the authorized security task")
    target: Optional[str] = Field(None, description="Optional explicit target hostname or IP")
    authorization_confirmed: Optional[bool] = Field(
        None, description="Whether the user explicitly confirmed authorization in the UI"
    )


class HealthResponse(BaseModel):
    """Health check response for KALI Sentinel."""

    status: str
    version: str
    bedrock_live: bool
    bedrock_model: str
    decider_model: str
    safe_mode: bool
    authorized_targets: List[str]


@router.post("/execute", response_model=SentinelAgentResponse)
async def execute_sentinel(request: ExecuteRequest) -> SentinelAgentResponse:
    """Run the complete KALI Sentinel agent workflow on a security task.
    
    1. Amazon Bedrock interprets intent & target.
    2. Strands Decider 2B selects the security tool.
    3. Grounding & scope guardrail verifies safety.
    4. Selected tool executes against authorized target.
    5. Amazon Bedrock synthesizes the final report.
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    agent = get_agent()
    try:
        response = agent.run(request.prompt)
        return response
    except Exception as exc:
        logger.error("Error executing KALI Sentinel agent: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tools")
async def list_tools() -> List[Dict[str, Any]]:
    """List all available defensive security tools registered with KALI Sentinel."""
    agent = get_agent()
    return agent.tools.list_tools()


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """Retrieve safe configuration metadata for KALI Sentinel."""
    cfg = get_sentinel_config()
    return {
        "aws_region": cfg.aws_region,
        "bedrock_model_id": cfg.bedrock_model_id,
        "bedrock_mock_fallback": cfg.bedrock_mock_fallback,
        "strands_decider_model": cfg.strands_decider_model,
        "strands_mock_fallback": cfg.strands_mock_fallback,
        "safe_mode": cfg.safe_mode,
        "authorized_targets": sorted(list(cfg.authorized_targets)),
    }


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Return health status of Sentinel subsystem, Bedrock, and Decider."""
    agent = get_agent()
    cfg = agent.config
    return HealthResponse(
        status="ok",
        version="1.0.0",
        bedrock_live=agent.bedrock.is_live,
        bedrock_model=cfg.bedrock_model_id,
        decider_model=cfg.strands_decider_model,
        safe_mode=cfg.safe_mode,
        authorized_targets=sorted(list(cfg.authorized_targets)),
    )


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="KALI Sentinel Standalone API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    print("Starting KALI Sentinel API Server on http://127.0.0.1:8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
