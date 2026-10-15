import asyncio
from unittest.mock import AsyncMock, MagicMock
from OpenDEMON.kali.agents.data_agent import DataAgent
from OpenDEMON.kali.agents.models import AgentContext

async def run():
    agent = DataAgent()
    print(f"Agent Name: {agent.name}")
    print(f"Risk Level: {agent.risk_level.name}")
    
    context = AgentContext(
        user_id="user_admin",
        project_id="proj_data_lab",
        task_id="task_data_1",
    )
    
    print("\n--- Test 1: Simulated Run (No Executor) ---")
    res1 = await agent.execute("analyze dataset_path=sales.csv analysis_goal=insights", context)
    if res1.success:
        print("Success! Report generated:")
        print(res1.output)
        print("Artifacts generated:", res1.data.get("artifacts"))
    else:
        print(f"Failed: {res1.error}")
        
    print("\n--- Test 2: Execution with Mock Sandbox ---")
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={"output": "Rows: 1000\\nColumns: 5"})
    
    res2 = await agent.execute("clean dataset_path=raw_sales.csv analysis_goal=clean", context, mock_executor)
    if res2.success:
        print("Success! Report generated:")
        print(res2.output)
        print("Sandbox calls:", mock_executor.execute.call_count)
    else:
        print(f"Failed: {res2.error}")
    
    print("\nAll tests ran manually.")

if __name__ == "__main__":
    asyncio.run(run())
