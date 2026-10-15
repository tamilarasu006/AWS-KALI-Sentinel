import asyncio
from unittest.mock import MagicMock

from OpenDEMON.kali.intelligence.planner import Planner
from OpenDEMON.kali.intelligence.executor import IntelligentExecutor
from OpenDEMON.kali.agents.registry import AgentRegistry
from OpenDEMON.kali.agents.manager import AgentManager
from OpenDEMON.kali.agents.models import AgentContext
from OpenDEMON.kali.agents.specialists import (
    GeneralAgent, SoftwareAgent, CyberAgent, ResearchAgent, DataAgent
)
from OpenDEMON.kali.orchestration.executor import KALIExecutor

async def run():
    print("Testing Planner & Executor...")
    
    registry = AgentRegistry()
    registry.register(GeneralAgent())
    registry.register(SoftwareAgent())
    registry.register(CyberAgent())
    registry.register(ResearchAgent())
    registry.register(DataAgent())
    
    mock_executor = MagicMock(spec=KALIExecutor)
    manager = AgentManager(registry, mock_executor)
    planner = Planner()
    executor = IntelligentExecutor(manager)
    
    print("\n--- Test 1: Simple Sequential Plan ---")
    raw_plan_1 = [
        {"id": "s1", "description": "Write code", "assigned_agent": "SoftwareAgent"},
        {"id": "s2", "description": "Test code", "assigned_agent": "SoftwareAgent", "dependencies": ["s1"]}
    ]
    plan1 = planner.create_plan_from_json("Code and test", raw_plan_1)
    ctx1 = AgentContext(user_id="u", project_id="p", task_id="t")
    res1 = await executor.execute_plan(plan1, ctx1)
    print(f"Success: {res1.success}")
    assert res1.success
    assert res1.plan.get_step("s1").status == "COMPLETED"
    assert res1.plan.get_step("s2").status == "COMPLETED"
    
    print("\n--- Test 2: Dependency Graph & Permission Denial Cascade ---")
    raw_plan_2 = [
        {"id": "scan", "description": "Run nmap", "assigned_agent": "CyberAgent"},
        {"id": "analyze", "description": "Analyze nmap", "assigned_agent": "DataAgent", "dependencies": ["scan"]}
    ]
    plan2 = planner.create_plan_from_json("Scan and analyze", raw_plan_2)
    # Context lacking auth_scope will fail the CyberAgent
    res2 = await executor.execute_plan(plan2, ctx1)
    print(f"Success: {res2.success}")
    print(f"Errors: {res2.errors}")
    assert not res2.success
    assert res2.plan.get_step("scan").status == "FAILED"
    assert res2.plan.get_step("analyze").status == "PENDING"  # Did not execute because dep failed
    
    print("\nALL TESTS PASSED MANUALLY!")

if __name__ == "__main__":
    asyncio.run(run())
