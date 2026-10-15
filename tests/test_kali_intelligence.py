import pytest
import asyncio
from unittest.mock import MagicMock

from OpenDEMON.kali.intelligence.planner import Planner
from OpenDEMON.kali.intelligence.executor import IntelligentExecutor
from OpenDEMON.kali.agents.registry import AgentRegistry
from OpenDEMON.kali.agents.manager import AgentManager
from OpenDEMON.kali.agents.models import AgentContext
from OpenDEMON.kali.agents.specialists import (
    GeneralAgent, SoftwareAgent, CyberAgent, ResearchAgent
)
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

@pytest.fixture
def planner():
    return Planner()

@pytest.mark.asyncio
async def test_simple_plan_execution(planner, manager):
    executor = IntelligentExecutor(manager)
    raw_plan = [
        {
            "id": "step1",
            "description": "Write a python function",
            "assigned_agent": "SoftwareAgent"
        }
    ]
    plan = planner.create_plan_from_json("Write code", raw_plan)
    ctx = AgentContext(user_id="u", project_id="p", task_id="t")
    
    res = await executor.execute_plan(plan, ctx)
    assert res.success
    assert res.plan.status == "COMPLETED"
    assert res.plan.steps[0].status == "COMPLETED"

@pytest.mark.asyncio
async def test_dependency_execution(planner, manager):
    executor = IntelligentExecutor(manager)
    raw_plan = [
        {
            "id": "step2",
            "description": "Run the code",
            "assigned_agent": "SoftwareAgent",
            "dependencies": ["step1"]
        },
        {
            "id": "step1",
            "description": "Write a python function",
            "assigned_agent": "SoftwareAgent"
        }
    ]
    plan = planner.create_plan_from_json("Write and run code", raw_plan)
    ctx = AgentContext(user_id="u", project_id="p", task_id="t")
    
    res = await executor.execute_plan(plan, ctx)
    assert res.success
    assert res.plan.status == "COMPLETED"

@pytest.mark.asyncio
async def test_permission_denial_cascades(planner, manager):
    executor = IntelligentExecutor(manager)
    raw_plan = [
        {
            "id": "step1",
            "description": "Run nmap",
            "assigned_agent": "CyberAgent"
        },
        {
            "id": "step2",
            "description": "Analyze nmap",
            "assigned_agent": "DataAgent",
            "dependencies": ["step1"]
        }
    ]
    plan = planner.create_plan_from_json("Scan and analyze", raw_plan)
    ctx = AgentContext(user_id="u", project_id="p", task_id="t", auth_scope=None)
    
    res = await executor.execute_plan(plan, ctx)
    assert not res.success
    assert res.plan.status == "FAILED"
    assert res.plan.get_step("step1").status == "FAILED"
    assert res.plan.get_step("step2").status == "PENDING"  # Never ran
    assert "Missing authorization" in res.errors[0]
