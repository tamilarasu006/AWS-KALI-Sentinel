"""FastAPI router and application server for KALI Sentinel.

Exposes REST endpoints for executing the agent workflow, querying
available security tools, checking health, and inspecting configuration.
Supports both /v1/sentinel/* and /api/v1/sentinel/* route conventions.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from kali_sentinel.agent.sentinel_agent import KaliSentinelAgent, SentinelAgentResponse
from kali_sentinel.config import get_sentinel_config
from kali_sentinel.database import (
    check_db_health,
    get_sentinel_repository,
    is_database_required,
)

logger = logging.getLogger(__name__)

# Routers mounted for both standard /v1/sentinel and legacy /api/v1/sentinel
router = APIRouter(prefix="/api/v1/sentinel", tags=["KALI Sentinel"])
v1_router = APIRouter(prefix="/v1/sentinel", tags=["KALI Sentinel"])

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


class AnalyzeRequest(BaseModel):
    """Payload for KALI Sentinel analysis workflow (Step 6 API convention)."""

    request: Optional[str] = Field(None, description="User prompt describing the authorized security task")
    prompt: Optional[str] = Field(None, description="Alias for request")
    target: Optional[str] = Field(None, description="Target hostname or IP")
    authorized: Optional[bool] = Field(True, description="Whether authorization is confirmed for the target")
    authorization_confirmed: Optional[bool] = Field(None, description="Alias for authorized")
    session_id: Optional[str] = Field(None, description="Optional session ID for session audit and memory")

    def get_prompt_text(self) -> str:
        text = self.request or self.prompt or ""
        return text.strip()


class AnalyzeResponse(BaseModel):
    """Structured response for KALI Sentinel analysis workflow (Step 6 API convention)."""

    decision: str = Field(..., description="Strands Decider 2B typed tool selection (e.g. PORT_SCAN, DNS_CHECK, NO_TOOL)")
    confidence: float = Field(..., description="Decision confidence from Strands Decider 2B (0.0 to 1.0)")
    tool: str = Field(..., description="Selected security tool identifier")
    execution_status: str = Field(..., description="COMPLETED, BLOCKED, or NO_TOOL")
    result: Dict[str, Any] = Field(default_factory=dict, description="Execution findings or result payload")
    latency_ms: float = Field(..., description="Total execution latency in milliseconds")
    explanation: str = Field("", description="Bedrock-generated security analysis report")

    # Additional fields providing full compatibility with SentinelAgentResponse / UI
    request: Optional[str] = None
    intent: Optional[Dict[str, Any]] = None
    decider_decision: Optional[Dict[str, Any]] = None
    guardrail_decision: Optional[Dict[str, Any]] = None
    selected_tool: Optional[str] = None
    total_latency_ms: Optional[float] = None

    # Audit & Persistence tracking
    audit_request_id: Optional[str] = None
    persistence_status: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response for KALI Sentinel."""

    status: str
    version: str
    bedrock_live: bool
    bedrock_model: str
    decider_model: str
    safe_mode: bool
    authorized_targets: List[str]
    database: Optional[Dict[str, Any]] = None


def _run_agent_workflow(
    prompt_text: str,
    target: Optional[str] = None,
    authorized: Optional[bool] = None,
) -> SentinelAgentResponse:
    """Core executor invoking the KALI Sentinel pipeline."""
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Prompt/request cannot be empty.")

    agent = get_agent()
    effective_prompt = prompt_text
    if target and target.lower() not in prompt_text.lower():
        effective_prompt = f"{prompt_text} target={target}"

    return agent.run(effective_prompt, target=target, authorized=authorized)


def _format_analyze_response(response: SentinelAgentResponse) -> AnalyzeResponse:
    """Format an agent response into the typed AnalyzeResponse schema."""
    decision_val = response.decider_decision.tool.value.upper()
    return AnalyzeResponse(
        decision=decision_val,
        confidence=round(response.decider_decision.confidence, 4),
        tool=response.selected_tool,
        execution_status=response.execution_status.lower(),
        result=response.result,
        latency_ms=round(response.total_latency_ms, 2),
        explanation=response.explanation,
        request=response.request,
        intent=response.intent.model_dump(),
        decider_decision=response.decider_decision.model_dump(),
        guardrail_decision=response.guardrail_decision.model_dump(),
        selected_tool=response.selected_tool,
        total_latency_ms=response.total_latency_ms,
    )


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=AnalyzeResponse)
@v1_router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_sentinel(req: AnalyzeRequest) -> AnalyzeResponse:
    """Run KALI Sentinel analysis workflow conforming to the Step 6 API schema.
    
    1. Amazon Bedrock generative reasoning parses the request and target.
    2. Strands Decider 2B selects the security tool (recon, port_scan, web_scan, dns_check, no_tool).
    3. Grounding & authorization guardrail verifies the target is in authorized scope.
    4. Selected tool executes against the authorized target.
    5. Amazon Bedrock synthesizes the final report.
    6. Audit Persistence: Records security_request, decision, and tool_execution.
    """
    prompt_str = req.get_prompt_text()
    auth_val = req.authorized if req.authorized is not None else req.authorization_confirmed
    try:
        response = _run_agent_workflow(prompt_str, req.target, authorized=auth_val)
        analyze_res = _format_analyze_response(response)

        # Audit Persistence Layer
        repo = get_sentinel_repository()
        persistence_status = "unpersisted"
        audit_id: Optional[str] = None
        try:
            req_record = await repo.create_security_request(
                request_text=response.request or prompt_str,
                target=response.intent.target if response.intent else req.target,
                authorized=bool(response.intent.authorization_claimed) if response.intent else bool(auth_val),
                session_id=req.session_id,
            )
            audit_id = req_record["id"]

            await repo.record_decision(
                request_id=audit_id,
                decision=analyze_res.decision,
                confidence=analyze_res.confidence,
                latency_ms=response.decider_decision.latency_ms,
            )

            await repo.record_tool_execution(
                request_id=audit_id,
                tool_name=analyze_res.tool,
                status=analyze_res.execution_status.upper(),
                result=analyze_res.result,
                execution_latency_ms=max(0.0, analyze_res.latency_ms - response.decider_decision.latency_ms),
            )
            persistence_status = "persisted"
        except Exception as exc:
            logger.warning("Audit persistence failed: %s", exc)
            if is_database_required():
                raise HTTPException(status_code=500, detail=f"Database persistence failed: {exc}")
            persistence_status = f"persistence_fallback: {exc}"

        analyze_res.audit_request_id = audit_id
        analyze_res.persistence_status = persistence_status
        return analyze_res
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error executing KALI Sentinel analyze: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/execute", response_model=SentinelAgentResponse)
@v1_router.post("/execute", response_model=SentinelAgentResponse)
async def execute_sentinel(request: ExecuteRequest) -> SentinelAgentResponse:
    """Run the complete KALI Sentinel agent workflow returning full internal model."""
    try:
        return _run_agent_workflow(
            request.prompt, request.target, authorized=request.authorization_confirmed
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error executing KALI Sentinel agent: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/tools")
@v1_router.get("/tools")
async def list_tools() -> List[Dict[str, Any]]:
    """List all available defensive security tools registered with KALI Sentinel."""
    agent = get_agent()
    return agent.tools.list_tools()


@router.get("/config")
@v1_router.get("/config")
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
        "database_configured": bool(cfg.database_url),
        "database_required": cfg.database_required,
    }


@router.get("/health", response_model=HealthResponse)
@v1_router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Return health status of Sentinel subsystem, Bedrock, Decider, and Database."""
    agent = get_agent()
    cfg = agent.config
    db_health = await check_db_health()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        bedrock_live=agent.bedrock.is_live,
        bedrock_model=cfg.bedrock_model_id,
        decider_model=cfg.strands_decider_model,
        safe_mode=cfg.safe_mode,
        authorized_targets=sorted(list(cfg.authorized_targets)),
        database=db_health,
    )


@router.get("/health/db")
@v1_router.get("/health/db")
async def get_database_health() -> Dict[str, Any]:
    """Dedicated health check for database and pgvector connectivity."""
    return await check_db_health()


@router.get("/history/requests")
@v1_router.get("/history/requests")
async def get_request_history(limit: int = 50, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve audit history of security requests."""
    repo = get_sentinel_repository()
    return await repo.get_request_history(limit=limit, session_id=session_id)


@router.get("/history/decisions")
@v1_router.get("/history/decisions")
async def get_decision_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve audit history of Decider 2B typed decisions."""
    repo = get_sentinel_repository()
    return await repo.get_decision_history(limit=limit)


# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------

def _load_env_safely() -> None:
    """Load .env file if available, and ensure JWT_SECRET has a safe fallback."""
    try:
        from dotenv import load_dotenv
        here = Path.cwd()
        for candidate in [here, *here.parents[:3]]:
            env_file = candidate / ".env"
            if env_file.exists():
                load_dotenv(env_file, override=False)
                break
    except Exception:
        pass
    os.environ.setdefault("JWT_SECRET", "sentinel-local-dev-jwt-secret-key-32b")


def create_sentinel_app():
    """Build the complete, unified KALI Sentinel backend application.
    
    Serves:
    - Root /health check (probe target for frontend banner)
    - KALI Sentinel API at both /v1/sentinel/* and /api/v1/sentinel/*
    - Core OpenDEMON endpoints (/v1/models, /v1/info, /v1/savings, /v1/connectors)
    - Approvals, telemetry, speech, and managed-agent endpoints
    - Complete CORS configuration for local Vite development (port 5173)
    """
    _load_env_safely()

    from fastapi import FastAPI
    from OpenDEMON.engine._stubs import InferenceEngine
    from OpenDEMON.agents.manager import AgentManager

    class SentinelInferenceEngine(InferenceEngine):
        engine_id = "kali_sentinel"

        def _extract_prompt(self, messages) -> str:
            if not messages:
                return ""
            for m in reversed(messages):
                if isinstance(m, dict):
                    if m.get("role") == "user" and m.get("content"):
                        return str(m["content"])
                elif hasattr(m, "role") and hasattr(m, "content"):
                    if m.role == "user" and m.content:
                        return str(m.content)
            return ""

        def generate(self, messages, **kwargs):
            agent = get_agent()
            prompt = self._extract_prompt(messages) or "System health status"
            resp = agent.run(prompt)
            content = resp.explanation
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": max(1, len(prompt.split())),
                    "completion_tokens": max(1, len(content.split())),
                    "total_tokens": max(2, len(prompt.split()) + len(content.split())),
                },
            }

        async def stream(self, messages, **kwargs):
            import asyncio
            agent = get_agent()
            prompt = self._extract_prompt(messages) or "System health status"
            resp = agent.run(prompt)
            content = resp.explanation
            words = content.split(" ")
            for i, word in enumerate(words):
                suffix = " " if i < len(words) - 1 else ""
                yield word + suffix
                await asyncio.sleep(0.01)

        def list_models(self) -> List[str]:
            return [
                "kali-sentinel-v1",
                "kali",
                "StrandsAgents/strands-decider-2B-hobson-v21",
                "anthropic.claude-3-haiku-20240307-v1:0",
            ]

        def health(self) -> bool:
            return True

    class SentinelKaliOrchestrator:
        async def run(self, query_text: str, user_id: str = "default", conversation_id: str = "default") -> str:
            agent = get_agent()
            resp = agent.run(query_text or "System status")
            return resp.explanation

    app = FastAPI(
        title="KALI Sentinel API Server",
        description="AWS Builder Center Hackathon: KALI Sentinel with Bedrock & Strands Decider 2B",
        version="1.0.0",
    )

    # CORS configuration
    cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "tauri://localhost",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "*",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize app state for dependencies
    app.state.engine = SentinelInferenceEngine()
    app.state.kali_orchestrator = SentinelKaliOrchestrator()
    app.state.model = "kali-sentinel-v1"
    app.state.engine_name = "kali_sentinel"
    app.state.session_start = time.time()

    # Agent Manager in-memory fallback so /v1/managed-agents never 404s
    try:
        app.state.agent_manager = AgentManager(":memory:", clear_stale_running=True)
    except Exception as exc:
        logger.debug("AgentManager init: %s", exc)
        app.state.agent_manager = None

    # Root health endpoint
    @app.get("/health")
    async def root_health():
        agent = get_agent()
        return {
            "status": "ok",
            "service": "kali-sentinel",
            "version": "1.0.0",
            "bedrock_live": agent.bedrock.is_live,
            "decider_model": agent.config.strands_decider_model,
        }

    # Mount OpenDEMON core routes (/v1/models, /v1/info, /v1/savings, etc.)
    try:
        from OpenDEMON.server.routes import router as core_router
        app.include_router(core_router)
    except Exception as exc:
        logger.warning("Failed to mount core OpenDEMON routes: %s", exc)

    # Mount auth routes (/v1/auth/*)
    try:
        from OpenDEMON.server.auth_routes import router as auth_router
        app.include_router(auth_router)
    except Exception as exc:
        logger.warning("Failed to mount auth routes: %s", exc)

    # Mount connectors routes (/v1/connectors/*)
    try:
        from OpenDEMON.server.connectors_router import create_connectors_router
        app.include_router(create_connectors_router())
    except Exception as exc:
        logger.warning("Failed to mount connectors routes: %s", exc)

    # Mount approval routes (/v1/approvals/*)
    try:
        from OpenDEMON.server.approval_routes import router as approval_router
        app.include_router(approval_router)
    except Exception as exc:
        logger.warning("Failed to mount approval routes: %s", exc)

    # Mount digest routes (/api/digest)
    try:
        from OpenDEMON.server.digest_routes import create_digest_router
        app.include_router(create_digest_router())
    except Exception as exc:
        logger.warning("Failed to mount digest routes: %s", exc)

    # Mount extended routes (telemetry, speech, managed-agents, etc.)
    try:
        from OpenDEMON.server.api_routes import include_all_routes
        include_all_routes(app)
    except Exception as exc:
        logger.warning("Failed to mount extended api routes: %s", exc)

    # Mount KALI Sentinel routes on both /api/v1/sentinel and /v1/sentinel
    app.include_router(router)
    app.include_router(v1_router)

    return app


if __name__ == "__main__":
    import uvicorn

    server_app = create_sentinel_app()
    port = int(os.environ.get("API_PORT", 8000))
    host = "127.0.0.1"

    print(f"Starting KALI Sentinel API Server on http://{host}:{port}...", flush=True)
    uvicorn.run(server_app, host=host, port=port)
