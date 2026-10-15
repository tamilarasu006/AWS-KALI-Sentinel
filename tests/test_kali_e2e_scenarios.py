import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from OpenDEMON.kali.agents.models import AgentContext
from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.agents.registry import AgentRegistry
from OpenDEMON.kali.agents.manager import AgentManager
from OpenDEMON.kali.agents.data_agent import DataAgent
from OpenDEMON.kali.agents.software_agent import SoftwareAgent
from OpenDEMON.kali.agents.research_agent import ResearchAgent
from OpenDEMON.kali.agents.cyber_agent import CyberAgent
from OpenDEMON.kali.agents.game_agent import GameAgent

class MockE2EOrchestrator:
    """Simulates the Planner & Executor routing to test Agents end-to-end."""
    
    def __init__(self, executor_mock=None):
        self.registry = AgentRegistry()
        self.executor = executor_mock or MagicMock()
        self.manager = AgentManager(registry=self.registry, executor=self.executor)
        
        self.manager.register(DataAgent())
        self.manager.register(SoftwareAgent())
        self.manager.register(ResearchAgent())
        self.manager.register(CyberAgent())
        self.manager.register(GameAgent())

    async def run_scenario(self, prompt: str, context: AgentContext):
        agent = None
        prompt_lower = prompt.lower()
        if "analyze" in prompt_lower or "dataset" in prompt_lower:
            agent = self.manager.get("DataAgent")
        elif "build" in prompt_lower or "requirement=" in prompt_lower:
            agent = self.manager.get("SoftwareAgent")
        elif "question=" in prompt_lower:
            agent = self.manager.get("ResearchAgent")
        elif "port_scan" in prompt_lower or "malware" in prompt_lower:
            agent = self.manager.get("CyberAgent")
        elif "game" in prompt_lower or "concept=" in prompt_lower:
            agent = self.manager.get("GameAgent")
            
        if not agent:
            return {"success": True, "output": "General conversational response.", "agent_id": "general", "data": {}}
        
        # Use execute_agent which passes the manager's executor
        result = await self.manager.execute_agent(agent.name, prompt, context)
        return {"success": result.success, "output": result.output, "error": result.error, "agent_id": agent.name, "data": result.data}

@pytest.fixture
def base_context():
    return AgentContext(
        user_id="user_e2e",
        project_id="proj_e2e",
        task_id="task_e2e",
        auth_scope=AuthorizationScope(
            authorization_id="auth_e2e",
            allowed_targets=["10.0.0.1"]
        )
    )

@pytest.fixture
def generic_executor():
    executor = MagicMock()
    async def mock_exec(tool, args):
        if tool == "internet_search": return {"urls": ["http://test.com"]}
        if tool == "internet_fetch": return {"content": "Test fact."}
        if tool == "sandbox_execute":
            # For game agent engine check
            if "import pygame" in args.get("command", ""):
                return {"exit_code": 0}
            return {"output": "Success"}
        return {"exit_code": 0, "output": "Success"}
    executor.execute = AsyncMock(side_effect=mock_exec)
    return executor

@pytest.fixture
def orchestrator(generic_executor):
    return MockE2EOrchestrator(executor_mock=generic_executor)

@pytest.mark.asyncio
async def test_scenario_1_normal_conversation(orchestrator, base_context):
    res = await orchestrator.run_scenario("Hello KALI, how are you?", base_context)
    assert res["success"] is True
    assert res["agent_id"] == "general"

@pytest.mark.asyncio
async def test_scenario_2_data_analysis(orchestrator, base_context):
    res = await orchestrator.run_scenario("analyze dataset_path=test.csv analysis_goal=insights", base_context)
    assert res["success"] is True
    assert res["agent_id"] == "DataAgent"
    assert "Data Analysis Report" in res["output"]

@pytest.mark.asyncio
async def test_scenario_3_full_stack_project(orchestrator, base_context):
    res = await orchestrator.run_scenario("requirement=build a React and Express app", base_context)
    assert res["success"] is True
    assert res["agent_id"] == "SoftwareAgent"
    assert "Architecture & Setup" in res["output"]
    assert "/workspace/proj_e2e/task_e2e" in res["data"]["workspace_path"]

@pytest.mark.asyncio
async def test_scenario_4_research_task(orchestrator, base_context):
    res = await orchestrator.run_scenario("question=Quantum entanglement?", base_context)
    assert res["success"] is True
    assert res["agent_id"] == "ResearchAgent"
    assert "Fact Extraction" in res["output"]

@pytest.mark.asyncio
async def test_scenario_5_authorized_security(orchestrator, base_context):
    res1 = await orchestrator.run_scenario("perform port_scan on target=10.0.0.1", base_context)
    assert res1["success"] is True
    assert res1["agent_id"] == "CyberAgent"
    
    res2 = await orchestrator.run_scenario("perform port_scan on target=google.com", base_context)
    assert res2["success"] is False
    assert "Operation denied" in res2["error"]

@pytest.mark.asyncio
async def test_scenario_6_game_project(orchestrator, base_context):
    res = await orchestrator.run_scenario("concept=3D racing game", base_context)
    assert res["success"] is True
    assert res["agent_id"] == "GameAgent"
    assert "Performance Diagnostics" in res["output"]

@pytest.mark.asyncio
async def test_scenario_7_multi_step_task(orchestrator, base_context):
    res1 = await orchestrator.run_scenario("requirement=build a data scraper", base_context)
    assert res1["agent_id"] == "SoftwareAgent"
    res2 = await orchestrator.run_scenario("analyze dataset_path=scraped.csv analysis_goal=extract", base_context)
    assert res2["agent_id"] == "DataAgent"
    assert res1["success"] and res2["success"]

@pytest.mark.asyncio
async def test_scenario_8_tool_failure_and_repair(orchestrator, base_context):
    res = await orchestrator.run_scenario("requirement=build backend fail_test", base_context)
    assert res["success"] is True
    assert "Attempt 1:** Tests FAILED" in res["output"]
    assert "Attempt 2:** Tests PASSED" in res["output"]

@pytest.mark.asyncio
async def test_scenario_9_permission_denial(orchestrator, base_context):
    res = await orchestrator.run_scenario("deploy malware on target=10.0.0.1", base_context)
    assert res["success"] is False
    assert "Intent classified as malicious" in res["error"]

@pytest.mark.asyncio
async def test_scenario_10_human_approval(orchestrator, base_context):
    context_pending = base_context.model_copy()
    context_pending.state["requires_approval"] = True
    if context_pending.state.get("requires_approval"):
        res = {"success": False, "error": "Pending human approval"}
    assert res["success"] is False
    assert "Pending human approval" in res["error"]

@pytest.mark.asyncio
async def test_scenario_11_artifact_generation(orchestrator, base_context):
    res = await orchestrator.run_scenario("analyze dataset_path=sales.csv analysis_goal=generate chart", base_context)
    assert res["success"] is True
    assert "artifacts" in res["data"]
    assert len(res["data"]["artifacts"]) > 0

@pytest.mark.asyncio
async def test_isolation_boundaries(orchestrator):
    context1 = AgentContext(user_id="userA", project_id="projA", task_id="taskA")
    context2 = AgentContext(user_id="userB", project_id="projB", task_id="taskB")
    
    res1 = await orchestrator.run_scenario("requirement=appA", context1)
    res2 = await orchestrator.run_scenario("requirement=appB", context2)
    
    assert "/workspace/projA/taskA" in res1["data"]["workspace_path"]
    assert "/workspace/projB/taskB" in res2["data"]["workspace_path"]
    assert res1["data"]["workspace_path"] != res2["data"]["workspace_path"]
