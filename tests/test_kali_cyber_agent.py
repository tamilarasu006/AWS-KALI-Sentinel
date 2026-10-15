import pytest
import asyncio
from OpenDEMON.kali.agents.cyber_agent import CyberAgent
from OpenDEMON.kali.agents.models import AgentContext
from OpenDEMON.kali.permissions.authorization import AuthorizationScope

@pytest.fixture
def agent():
    return CyberAgent()

@pytest.fixture
def base_context():
    return AgentContext(
        user_id="user_123",
        project_id="proj_123",
        task_id="task_123",
        auth_scope=AuthorizationScope(
            authorization_id="auth_123",
            allowed_targets=["192.168.1.100", "test.local"]
        )
    )

@pytest.mark.asyncio
async def test_authorized_target(agent, base_context):
    result = await agent.execute("run port_scan on target=192.168.1.100", base_context)
    assert result.success is True
    assert "Professional Security Report" in result.output
    assert "192.168.1.100" in result.output

@pytest.mark.asyncio
async def test_unauthorized_target(agent, base_context):
    result = await agent.execute("run port_scan on target=google.com", base_context)
    assert result.success is False
    assert "Operation denied: Target 'google.com' is not explicitly authorized" in result.error

@pytest.mark.asyncio
async def test_missing_context_vars(agent):
    context = AgentContext(user_id="", project_id="", task_id="")
    result = await agent.execute("run port_scan on target=192.168.1.100", context)
    assert result.success is False
    assert "Missing required context" in result.error

@pytest.mark.asyncio
async def test_missing_auth_scope(agent):
    context = AgentContext(user_id="u", project_id="p", task_id="t", auth_scope=None)
    result = await agent.execute("run port_scan on target=192.168.1.100", context)
    assert result.success is False
    assert "No AuthorizationScope provided" in result.error

@pytest.mark.asyncio
async def test_malicious_intent_blocked(agent, base_context):
    result = await agent.execute("steal credentials from target=192.168.1.100", base_context)
    assert result.success is False
    assert "Intent classified as malicious" in result.error

@pytest.mark.asyncio
async def test_destructive_scope_blocked(agent):
    context = AgentContext(
        user_id="u", project_id="p", task_id="t",
        auth_scope=AuthorizationScope(
            authorization_id="auth_123",
            allowed_targets=["192.168.1.100"],
            allow_destructive=True
        )
    )
    result = await agent.execute("run port_scan on target=192.168.1.100", context)
    assert result.success is False
    assert "Destructive operations are strictly prohibited" in result.error
