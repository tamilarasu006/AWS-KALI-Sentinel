import asyncio
from OpenDEMON.kali.sandbox.models import SandboxRequest
from OpenDEMON.kali.sandbox.manager import SandboxManager

async def run():
    print("Testing Sandbox...")
    mgr = SandboxManager()
    
    print("\n--- Test 1: Python Hello World ---")
    req1 = SandboxRequest(language="python", code="print('Hello from sandbox!')")
    res1 = await mgr.execute(req1)
    print(f"Success: {res1.success}")
    print(f"Stdout: {res1.stdout.strip()}")
    assert res1.success is True
    
    print("\n--- Test 2: Output Limits ---")
    mgr.config.limits.max_output_size_bytes = 10
    req2 = SandboxRequest(language="python", code="print('A' * 100)")
    res2 = await mgr.execute(req2)
    print(f"Success: {res2.success}")
    print(f"Stdout: {res2.stdout.strip()}")
    assert "OUTPUT TRUNCATED" in res2.stdout
    
    print("\n--- Test 3: Python Timeout ---")
    mgr.config.limits.max_output_size_bytes = 1024 * 1024
    mgr.config.limits.timeout_seconds = 1.0
    req3 = SandboxRequest(language="python", code="import time; time.sleep(5); print('Done')")
    res3 = await mgr.execute(req3)
    print(f"Success: {res3.success}")
    print(f"Error: {res3.error}")
    assert res3.success is False
    assert "timed out" in res3.error.lower()
    
    print("\n--- Test 4: Artifact Generation ---")
    req4 = SandboxRequest(language="python", code="with open('test_artifact.txt', 'w') as f: f.write('secret data')")
    res4 = await mgr.execute(req4)
    print(f"Success: {res4.success}")
    print(f"Artifacts: {list(res4.artifacts.keys())}")
    assert "test_artifact.txt" in res4.artifacts
    assert res4.artifacts["test_artifact.txt"] == b"secret data"
    
    print("\nALL TESTS PASSED MANUALLY!")

if __name__ == "__main__":
    asyncio.run(run())
