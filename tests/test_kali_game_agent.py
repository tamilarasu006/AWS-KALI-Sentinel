import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from OpenDEMON.kali.agents.game_agent import GameAgent
from OpenDEMON.kali.agents.models import AgentContext

@pytest.fixture
def agent():
    return GameAgent()

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
    # Let detect engine return 0 (success) so it defaults to pygame
    executor.execute = AsyncMock(return_value={"exit_code": 0})
    return executor

@pytest.mark.asyncio
async def test_game_agent_missing_context(agent):
    context = AgentContext(user_id="", project_id="", task_id="")
    result = await agent.execute("concept=2d platformer", context)
    assert result.success is False
    assert "Missing required context" in result.error

@pytest.mark.asyncio
async def test_game_agent_simulated_success(agent, base_context):
    result = await agent.execute("concept=2d platformer", base_context)
    assert result.success is True
    assert "Simulated: Checked sandbox environments" in result.output
    assert "Simulated: Wrote code files" in result.output
    assert "performance_metrics" in result.data
    assert result.data["performance_metrics"]["fps"] == 60

@pytest.mark.asyncio
async def test_game_agent_simulated_optimization_loop(agent, base_context):
    result = await agent.execute("concept=2d platformer low_fps", base_context)
    assert result.success is True
    assert "Detected low FPS. Applying optimizations:" in result.output
    assert "Retest post-optimization" in result.output
    assert result.data["performance_metrics"]["fps"] == 60  # optimized

@pytest.mark.asyncio
async def test_game_agent_with_executor_and_optimization(agent, base_context, mock_executor):
    result = await agent.execute("concept=3d shooter low_fps", base_context, mock_executor)
    assert result.success is True
    # The executor should have been called multiple times
    # 1. detect, 2. write main, 3. write asset, 4. compile, 5. profile test, 6. optimize write patch, 7. package zip
    assert mock_executor.execute.call_count == 7
    assert "Detected Pygame." in result.output
    assert "Executed headless test run" in result.output
    assert "Detected low FPS." in result.output
