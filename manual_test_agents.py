import asyncio
from unittest.mock import MagicMock

from OpenDEMON.kali.agents.registry import AgentRegistry
from OpenDEMON.kali.agents.manager import AgentManager
from OpenDEMON.kali.agents.models import AgentContext
from OpenDEMON.kali.agents.specialists import (
    GeneralAgent, SoftwareAgent, DataAgent, ResearchAgent,
    CyberAgent, GameAgent, DevOpsAgent, AIEngineeringAgent
)
from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.orchestration.executor import KALIExecutor

async def run():
    print("Testing Multi-Agent System...")
    
    registry = AgentRegistry()
    for agent_cls in [GeneralAgent, SoftwareAgent, DataAgent, ResearchAgent, 
                      CyberAgent, GameAgent, DevOpsAgent, AIEngineeringAgent]:
        registry.register(agent_cls())
        
    mock_executor = MagicMock(spec=KALIExecutor)
    manager = AgentManager(registry, mock_executor)
    
    print("\n--- Test 1: Agent Selection ---")
    a1 = manager.select_agent("Can you do some coding for me?")
    print(f"Selected for coding: {a1.name}")
    assert a1.name == "SoftwareAgent"
    
    a2 = manager.select_agent("Do a search for news")
    print(f"Selected for search: {a2.name}")
    assert a2.name == "ResearchAgent"
    
    print("\n--- Test 2: CyberAgent Missing Authorization ---")
    ctx_unauth = AgentContext(user_id="u1", project_id="p1", task_id="t1")
    res1 = await manager.execute_agent("CyberAgent", "run nmap on 10.0.0.1", ctx_unauth)
    print(f"Success: {res1.success}")
    print(f"Error: {res1.error}")
    assert not res1.success
    assert "Missing authorization" in res1.error
    
    print("\n--- Test 3: CyberAgent With Authorization ---")
    scope = AuthorizationScope(authorization_id="auth1", allowed_targets=["10.0.0.1"])
    ctx_auth = AgentContext(user_id="u1", project_id="p1", task_id="t1", auth_scope=scope)
    res2 = await manager.execute_agent("CyberAgent", "run nmap on 10.0.0.1", ctx_auth)
    print(f"Success: {res2.success}")
    print(f"Output: {res2.output}")
    assert res2.success
    
    print("\nALL TESTS PASSED MANUALLY!")

if __name__ == "__main__":
    asyncio.run(run())
