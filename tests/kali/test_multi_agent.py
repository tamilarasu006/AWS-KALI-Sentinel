import pytest
import asyncio
from unittest.mock import patch, MagicMock
from OpenDEMON.kali.orchestration.planner import KALIPlanner
from OpenDEMON.kali.agents.software_agent import SoftwareAgent
from OpenDEMON.kali.agents.data_agent import DataAgent
from OpenDEMON.kali.agents.cyber_agent import CyberAgent
from OpenDEMON.kali.sandbox.tools import SandboxTools
from OpenDEMON.kali.sandbox.docker_sandbox import DockerSandbox

def test_planner_routing():
    planner = KALIPlanner(available_tools=["execute_python", "run_nmap"])
    
    # Software routing
    plan = planner.plan("Can you debug this python code?")
    assert "kali_software_agent" in plan.target_agents
    assert "execute_python" in plan.tool_names
    
    # Data routing
    plan = planner.plan("Analyze this pandas dataframe")
    assert "kali_data_agent" in plan.target_agents
    
    # Cyber routing
    plan = planner.plan("Run an nmap scan on 10.0.0.1")
    assert "kali_cyber_agent" in plan.target_agents
    assert "run_nmap" in plan.tool_names

@pytest.mark.asyncio
async def test_agent_execution():
    agent = SoftwareAgent()
    assert agent.can_handle("Write some python code")
    
    result = await agent.execute("Write some python code", {})
    assert "[Software Agent]" in result

@patch('docker.from_env')
def test_docker_sandbox_fallback(mock_docker):
    mock_docker.side_effect = Exception("No docker daemon")
    
    sandbox = DockerSandbox()
    assert not sandbox.health()
    
    res = sandbox.execute_code("print('hello')")
    assert not res["success"]
    assert "offline" in res["output"].lower()

@patch('docker.from_env')
def test_sandbox_tools_mock(mock_docker):
    mock_client = MagicMock()
    mock_docker.return_value = mock_client
    
    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.return_value = b"Hello from python"
    mock_client.containers.run.return_value = mock_container
    
    tools = SandboxTools()
    res = tools.execute_python("print('hello')")
    
    assert res["success"]
    assert "Hello from python" in res["output"]
