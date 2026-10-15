import pytest
import sys
import asyncio
from OpenDEMON.kali.sandbox.models import SandboxRequest, SandboxConfig, ResourceLimits
from OpenDEMON.kali.sandbox.manager import SandboxManager

@pytest.fixture
def sandbox():
    return SandboxManager()

@pytest.mark.asyncio
async def test_successful_python_execution(sandbox):
    req = SandboxRequest(
        language="python",
        code="print('Hello from sandbox!')"
    )
    result = await sandbox.execute(req)
    assert result.success is True
    assert result.exit_code == 0
    assert "Hello from sandbox!" in result.stdout
    assert not result.error

@pytest.mark.asyncio
async def test_python_timeout(sandbox):
    # Override timeout to be very short to ensure it catches
    sandbox.config.limits.timeout_seconds = 1.0
    req = SandboxRequest(
        language="python",
        code="import time; time.sleep(5); print('Done')"
    )
    result = await sandbox.execute(req)
    assert result.success is False
    assert result.exit_code == -1
    assert "timed out" in result.error.lower()
    assert "Done" not in result.stdout

@pytest.mark.asyncio
async def test_invalid_code(sandbox):
    req = SandboxRequest(
        language="python",
        code="print('Hello' # Syntax Error"
    )
    result = await sandbox.execute(req)
    assert result.success is False
    assert result.exit_code != 0
    assert "SyntaxError" in result.stderr

@pytest.mark.asyncio
async def test_output_limits(sandbox):
    # Set a tiny output limit
    sandbox.config.limits.max_output_size_bytes = 10
    req = SandboxRequest(
        language="python",
        code="print('A' * 100)"
    )
    result = await sandbox.execute(req)
    assert result.success is True
    assert "OUTPUT TRUNCATED" in result.stdout
    assert len(result.stdout) < 100

@pytest.mark.asyncio
async def test_artifact_generation(sandbox):
    req = SandboxRequest(
        language="python",
        code="with open('output.txt', 'w') as f: f.write('sandbox data')"
    )
    result = await sandbox.execute(req)
    assert result.success is True
    assert "output.txt" in result.artifacts
    assert result.artifacts["output.txt"] == b"sandbox data"

@pytest.mark.asyncio
async def test_invalid_runner():
    mgr = SandboxManager()
    req = SandboxRequest(language="unknown_lang", code="")
    result = await mgr.execute(req)
    assert result.success is False
    assert "Unsupported language runner" in result.error
