"""Tests for KALI Sentinel FastAPI routes."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from kali_sentinel.server.routes import router


def get_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_health_route():
    client = get_test_client()
    resp = client.get("/api/v1/sentinel/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "authorized_targets" in data


def test_tools_route():
    client = get_test_client()
    resp = client.get("/api/v1/sentinel/tools")
    assert resp.status_code == 200
    tools = resp.json()
    assert len(tools) >= 4
    tool_ids = [t["id"] for t in tools]
    assert "port_scan" in tool_ids
    assert "dns_check" in tool_ids


def test_config_route():
    client = get_test_client()
    resp = client.get("/api/v1/sentinel/config")
    assert resp.status_code == 200
    cfg = resp.json()
    assert "bedrock_model_id" in cfg
    assert "strands_decider_model" in cfg


def test_execute_route():
    client = get_test_client()
    payload = {"prompt": "Check open ports on my authorized lab server 127.0.0.1"}
    resp = client.post("/api/v1/sentinel/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["selected_tool"] == "port_scan"
    assert data["decider_decision"]["tool"] == "port_scan"
    assert data["guardrail_decision"]["verdict"] == "ALLOW"
    assert data["execution_status"] == "COMPLETED"
    assert "PORT_SCAN" in data["explanation"]
