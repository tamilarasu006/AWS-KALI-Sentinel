import asyncio
from unittest.mock import AsyncMock
from OpenDEMON.kali.agents.models import AgentContext, AgentResult
from OpenDEMON.kali.intelligence.models import PlanStep
from OpenDEMON.kali.intelligence.correction.manager import RetryManager
from OpenDEMON.kali.intelligence.correction.models import RetryPolicy

async def run():
    print("Testing Self-Correction Loop...")
    
    manager = RetryManager(RetryPolicy(max_retries=2, retry_delay_seconds=0.1))
    step = PlanStep(id="1", description="Test", assigned_agent="A", verification_criteria="must contain 'success'")
    ctx = AgentContext(user_id="u", project_id="p", task_id="t")
    
    print("\n--- Test 1: Immediate Success ---")
    mock_agent_1 = AsyncMock(return_value=AgentResult(agent_id="A", success=True, output="the process was a success!"))
    res1 = await manager.execute_with_retry(step, "test", ctx, mock_agent_1)
    print(f"Attempts: {mock_agent_1.call_count}, Success: {res1.success}")
    assert mock_agent_1.call_count == 1
    assert res1.success
    
    print("\n--- Test 2: Retry on Verification Failure ---")
    mock_agent_2 = AsyncMock(side_effect=[
        AgentResult(agent_id="A", success=True, output="failed first try"),
        AgentResult(agent_id="A", success=True, output="failed second try"),
        AgentResult(agent_id="A", success=True, output="now it is a success!")
    ])
    res2 = await manager.execute_with_retry(step, "test", ctx, mock_agent_2)
    print(f"Attempts: {mock_agent_2.call_count}, Success: {res2.success}")
    assert mock_agent_2.call_count == 3
    assert res2.success
    
    print("\n--- Test 3: Hard Stop on Permission Denial ---")
    mock_agent_3 = AsyncMock(return_value=AgentResult(agent_id="A", success=False, output="", error="Action blocked. Permission denied."))
    res3 = await manager.execute_with_retry(step, "test", ctx, mock_agent_3)
    print(f"Attempts: {mock_agent_3.call_count}, Success: {res3.success}, Error: {res3.error}")
    assert mock_agent_3.call_count == 1
    assert not res3.success
    assert "Hard Stop" in res3.error
    
    print("\nALL TESTS PASSED MANUALLY!")

if __name__ == "__main__":
    asyncio.run(run())
