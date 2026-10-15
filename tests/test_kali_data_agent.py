import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from OpenDEMON.kali.agents.data_agent import DataAgent
from OpenDEMON.kali.agents.models import AgentContext

@pytest.fixture
def agent():
    return DataAgent()

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
async def test_data_agent_missing_dataset(agent, base_context):
    result = await agent.execute("analyze data", base_context)
    assert result.success is False
    assert "Missing dataset_path" in result.error

@pytest.mark.asyncio
async def test_data_agent_simulated_pipeline(agent, base_context):
    result = await agent.execute("analyze dataset_path=data.csv analysis_goal=basic", base_context)
    assert result.success is True
    assert "Simulated Profiling" in result.output
    assert "Simulated Cleaning" in result.output
    assert "Simulated Visualization" in result.output
    assert "chart_task_123.png" in result.data["artifacts"]
    assert "cleaned_data.csv" in result.data["artifacts"]

@pytest.mark.asyncio
async def test_data_agent_with_executor(agent, base_context, mock_executor):
    result = await agent.execute("analyze dataset_path=data.csv analysis_goal=full", base_context, mock_executor)
    assert result.success is True
    # The executor should have been called 3 times (profile, clean, visualize)
    assert mock_executor.execute.call_count == 3
    assert "Mocked Executor Output" in result.output
