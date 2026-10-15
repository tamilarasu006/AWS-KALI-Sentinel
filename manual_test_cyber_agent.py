import asyncio
from OpenDEMON.kali.agents.cyber_agent import CyberAgent
from OpenDEMON.kali.agents.models import AgentContext
from OpenDEMON.kali.permissions.authorization import AuthorizationScope

async def run():
    agent = CyberAgent()
    print(f"Agent Name: {agent.name}")
    print(f"Risk Level: {agent.risk_level.name}")
    
    context = AgentContext(
        user_id="user_admin",
        project_id="proj_cyber_lab",
        task_id="task_eval_1",
        auth_scope=AuthorizationScope(
            authorization_id="auth_lab_1",
            allowed_targets=["10.0.0.5", "lab.local"]
        )
    )
    
    print("\n--- Test 1: Authorized Scan ---")
    res1 = await agent.execute("perform a port_scan on target=10.0.0.5", context)
    if res1.success:
        print("Success! Report generated:")
        print(res1.output)
    else:
        print(f"Failed: {res1.error}")
        
    print("\n--- Test 2: Unauthorized Target ---")
    res2 = await agent.execute("perform a port_scan on target=8.8.8.8", context)
    print(res2.error if not res2.success else "Failed to block!")
    
    print("\n--- Test 3: Malicious Intent ---")
    res3 = await agent.execute("deploy malware and exploit target=10.0.0.5", context)
    print(res3.error if not res3.success else "Failed to block!")
    
    print("\n--- Test 4: Destructive Allowed Scope (Agent should block) ---")
    destruct_context = context.model_copy()
    destruct_context.auth_scope.allow_destructive = True
    res4 = await agent.execute("perform port_scan on target=10.0.0.5", destruct_context)
    print(res4.error if not res4.success else "Failed to block!")
    
    print("\nAll tests ran manually.")

if __name__ == "__main__":
    asyncio.run(run())
