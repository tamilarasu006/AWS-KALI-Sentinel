import asyncio
from unittest.mock import AsyncMock, MagicMock
from OpenDEMON.kali.agents.software_agent import SoftwareAgent
from OpenDEMON.kali.agents.models import AgentContext

async def run():
    agent = SoftwareAgent()
    print(f"Agent Name: {agent.name}")
    print(f"Risk Level: {agent.risk_level.name}")
    
    context = AgentContext(
        user_id="user_admin",
        project_id="proj_software_lab",
        task_id="task_dev_1",
    )
    
    print("\n--- Test 1: Simulated Run (Straight Pass) ---")
    res1 = await agent.execute("requirement=build a React frontend", context)
    if res1.success:
        print("Success! Report generated:")
        print(res1.output)
    else:
        print(f"Failed: {res1.error}")
        
    print("\n--- Test 2: Execution with Mock Sandbox (Fail & Repair Loop) ---")
    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(return_value={"output": "Success"})
    
    res2 = await agent.execute("requirement=build node.js backend fail_test", context, mock_executor)
    if res2.success:
        print("Success! Report generated:")
        print(res2.output)
        print("Sandbox calls:", mock_executor.execute.call_count)
    else:
        print(f"Failed: {res2.error}")
    
    print("\nAll tests ran manually.")

if __name__ == "__main__":
    asyncio.run(run())
