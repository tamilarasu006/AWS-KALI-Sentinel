import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from OpenDEMON.kali.agents.models import AgentContext, AgentResult
from OpenDEMON.kali.intelligence.models import PlanStep
from OpenDEMON.kali.intelligence.correction.manager import RetryManager
from OpenDEMON.kali.intelligence.correction.models import RetryPolicy

@pytest.fixture
def retry_manager():
    return RetryManager(RetryPolicy(max_retries=2, retry_delay_seconds=0.01))

@pytest.mark.asyncio
async def test_successful_verification(retry_manager):
    step = PlanStep(id="1", description="Test", assigned_agent="A", verification_criteria="must contain 'hello'")
    ctx = AgentContext(user_id="u", project_id="p", task_id="t")
    
    mock_agent = AsyncMock()
    mock_agent.return_value = AgentResult(agent_id="A", success=True, output="This says hello world")
    
    res = await retry_manager.execute_with_retry(step, "prompt", ctx, mock_agent)
    assert res.success
    assert mock_agent.call_count == 1

@pytest.mark.asyncio
async def test_verification_failure_and_retry(retry_manager):
    step = PlanStep(id="1", description="Test", assigned_agent="A", verification_criteria="must contain 'hello'")
    ctx = AgentContext(user_id="u", project_id="p", task_id="t")
    
    mock_agent = AsyncMock()
    # Fails first time, succeeds second time
    mock_agent.side_effect = [
        AgentResult(agent_id="A", success=True, output="This says wrong"),
        AgentResult(agent_id="A", success=True, output="This says hello world")
    ]
    
    res = await retry_manager.execute_with_retry(step, "prompt", ctx, mock_agent)
    assert res.success
    assert mock_agent.call_count == 2

@pytest.mark.asyncio
async def test_permission_denial_hard_stop(retry_manager):
    step = PlanStep(id="1", description="Test", assigned_agent="A", verification_criteria="")
    ctx = AgentContext(user_id="u", project_id="p", task_id="t")
    
    mock_agent = AsyncMock()
    mock_agent.return_value = AgentResult(agent_id="A", success=False, error="Missing authorization")
    
    res = await retry_manager.execute_with_retry(step, "prompt", ctx, mock_agent)
    assert not res.success
    assert "Hard Stop" in res.error
    assert mock_agent.call_count == 1  # No retries on permission failure
