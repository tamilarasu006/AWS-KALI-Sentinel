import pytest
import asyncio
from unittest.mock import MagicMock

from OpenDEMON.kali.agents.registry import AgentRegistry
from OpenDEMON.kali.agents.manager import AgentManager
from OpenDEMON.kali.agents.models import AgentContext
from OpenDEMON.kali.agents.specialists import (
    GeneralAgent, SoftwareAgent, CyberAgent, ResearchAgent
)
from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.orchestration.executor import KALIExecutor

@pytest.fixture
def manager():
    registry = AgentRegistry()
    registry.register(GeneralAgent())
    registry.register(SoftwareAgent())
    registry.register(CyberAgent())
    registry.register(ResearchAgent())
    
    mock_executor = MagicMock(spec=KALIExecutor)
    return AgentManager(registry, mock_executor)

def test_find_by_capability(manager):
    agents = manager.find_by_capability("software_engineering")
    assert len(agents) == 1
    assert agents[0].name == "SoftwareAgent"
    
    agents = manager.find_by_capability("search")
    assert any(a.name == "ResearchAgent" for a in agents)

def test_select_agent(manager):
    agent = manager.select_agent("Please build a python web server")
    assert agent.name == "SoftwareAgent"
    
    agent = manager.select_agent("Search the web for news")
    assert agent.name == "ResearchAgent"
    
    # Fallback
    agent = manager.select_agent("Do some generic task")
    assert agent.name == "GeneralAgent"

@pytest.mark.asyncio
async def test_cyber_agent_no_scope(manager):
    ctx = AgentContext(user_id="u1", project_id="p1", task_id="t1", auth_scope=None)
    res = await manager.execute_agent("CyberAgent", "Run nmap", ctx)
    assert not res.success
    assert "Missing authorization" in res.error

@pytest.mark.asyncio
async def test_cyber_agent_with_scope(manager):
    scope = AuthorizationScope(authorization_id="auth-1", allowed_targets=["10.0.0.1"])
    ctx = AgentContext(user_id="u1", project_id="p1", task_id="t1", auth_scope=scope)
    res = await manager.execute_agent("CyberAgent", "Run nmap", ctx)
    assert res.success
    assert res.error is None
    assert "CyberAgent" in res.output
