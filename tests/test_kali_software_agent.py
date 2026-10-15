import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from OpenDEMON.kali.agents.software_agent import SoftwareAgent
from OpenDEMON.kali.agents.models import AgentContext

@pytest.fixture
def agent():
    return SoftwareAgent()

@pytest.fixture
def base_context():
    return AgentContext(
        user_id="user_123",
        project_id="proj_123",
        task_id="task_123",
    )

@pytest.fixture
def mock_executor():
    executor = MagicMock()
    executor.execute = AsyncMock(return_value={"output": "Mocked Executor Output"})
    return executor

@pytest.mark.asyncio
async def test_software_agent_missing_context(agent):
    context = AgentContext(user_id="", project_id="", task_id="")
    result = await agent.execute("build app", context)
    assert result.success is False
    assert "Missing required context" in result.error

@pytest.mark.asyncio
async def test_software_agent_simulated_success(agent, base_context):
    result = await agent.execute("requirement=build a React app", base_context)
    assert result.success is True
    assert "Simulated: Generated project structure" in result.output
    assert "Simulated: Build and tests passed successfully." in result.output
    assert "workspace_path" in result.data
    assert result.data["workspace_path"] == "/workspace/proj_123/task_123"

@pytest.mark.asyncio
async def test_software_agent_simulated_repair_loop(agent, base_context):
    result = await agent.execute("requirement=build a FastApi app fail_test", base_context)
    assert result.success is True
    assert "Diagnosed issue -> Repaired code -> Retested successfully" in result.output

@pytest.mark.asyncio
async def test_software_agent_with_executor_repair_loop(agent, base_context, mock_executor):
    result = await agent.execute("requirement=build an Express app fail_test", base_context, mock_executor)
    assert result.success is True
    # The executor should have been called multiple times
    # 1. init package.json, 2. npm install, 3. repair route (workspace_write), 4. docker build
    assert mock_executor.execute.call_count >= 4
    assert "Attempt 1:** Tests FAILED" in result.output
    assert "Attempt 2:** Tests PASSED" in result.output
    assert "Diagnosed `TypeError`" in result.output
