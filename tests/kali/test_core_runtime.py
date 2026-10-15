import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from OpenDEMON.kali.core import TaskValidator, TaskDAGNode, CircularDependencyError, KALIRuntime, ExecutionLimitExceeded
from OpenDEMON.kali.core.state import TaskStatus
from OpenDEMON.kali.tools.permissions import AuthorizationScope
from OpenDEMON.kali.tools.results import ToolResult
from OpenDEMON.database.models import KaliTask, KaliProject

def test_circular_dependency_detection():
    # A -> B -> C -> A
    tasks = {
        "A": TaskDAGNode("A", ["B"]),
        "B": TaskDAGNode("B", ["C"]),
        "C": TaskDAGNode("C", ["A"]),
    }
    with pytest.raises(CircularDependencyError):
        TaskValidator.check_circular_dependencies(tasks)

def test_valid_dag():
    # A -> B -> C
    tasks = {
        "A": TaskDAGNode("A", ["B"]),
        "B": TaskDAGNode("B", ["C"]),
        "C": TaskDAGNode("C", []),
    }
    # Should not raise
    TaskValidator.check_circular_dependencies(tasks)

@pytest.mark.asyncio
async def test_runtime_cancellation_propagation():
    db_mock = AsyncMock()
    runtime = KALIRuntime(db_mock, MagicMock())
    
    # Mock get_task to return a dummy task
    dummy_task = KaliTask(id="task_1", status="RUNNING")
    
    # We patch get_task to avoid db select logic
    def mock_get_task(tid):
        if tid == "task_1":
            return dummy_task
        elif tid == "child_1":
            return child_task
        return None
    runtime.get_task = AsyncMock(side_effect=mock_get_task)
    
    # Mock the children select
    child_task = KaliTask(id="child_1", status="RUNNING")
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [child_task]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    
    # First call returns children, subsequent calls for children return no children
    db_mock.execute.side_effect = [mock_result, MagicMock(scalars=lambda: MagicMock(all=lambda: []))]
    
    await runtime.cancel_task("task_1")
    
    assert dummy_task.status == TaskStatus.CANCELLED.value
    assert child_task.status == TaskStatus.CANCELLED.value

@pytest.mark.asyncio
async def test_execution_depth_limit():
    db_mock = AsyncMock()
    runtime = KALIRuntime(db_mock, MagicMock())
    
    # Mock _get_task_depth to return the max depth (5)
    runtime._get_task_depth = AsyncMock(return_value=5)
    
    with pytest.raises(ExecutionLimitExceeded):
        await runtime.create_task("user_1", "objective", parent_task_id="parent_1")

@pytest.mark.asyncio
async def test_task_retry_limits():
    db_mock = AsyncMock()
    runtime = KALIRuntime(db_mock, MagicMock())
    
    failed_task = KaliTask(id="task_fail", status=TaskStatus.FAILED.value, retry_count=3)
    runtime.get_task = AsyncMock(return_value=failed_task)
    runtime.limits.max_retries = 3
    
    with pytest.raises(ExecutionLimitExceeded):
        await runtime.retry_task("task_fail")

@pytest.mark.asyncio
async def test_project_workspace_update():
    db_mock = AsyncMock()
    runtime = KALIRuntime(db_mock, MagicMock())
    
    project = KaliProject(id="proj_1", name="App", workspace={"git": "none"})
    runtime.get_project = AsyncMock(return_value=project)
    
@pytest.mark.asyncio
async def test_execute_task_pipeline_success():
    db_mock = AsyncMock()
    runtime = KALIRuntime(db_mock, MagicMock())
    
    task = KaliTask(id="task_2", objective="Search the web for OpenDEMON docs", status=TaskStatus.PENDING.value)
    runtime.get_task = AsyncMock(return_value=task)
    
    # Execute
    completed_task = await runtime.execute_task("task_2")
    
    assert completed_task.status == TaskStatus.COMPLETED.value
    assert "result" in completed_task.output_data
    assert completed_task.output_data["result"] == "Search results mock"

@pytest.mark.asyncio
async def test_execute_task_pipeline_unauthorized_recon():
    db_mock = AsyncMock()
    runtime = KALIRuntime(db_mock, MagicMock())
    
    # This objective will map to AUTHORIZED_RECONNAISSANCE -> auth_recon tool
    task = KaliTask(id="task_3", objective="Perform authorized reconnaissance on 10.0.0.1", status=TaskStatus.PENDING.value)
    runtime.get_task = AsyncMock(return_value=task)
    
    # We execute without an AuthorizationScope, which should fail
    failed_task = await runtime.execute_task("task_3")
    
    assert failed_task.status == TaskStatus.FAILED.value
    assert "requires an AuthorizationScope" in failed_task.errors["message"]
