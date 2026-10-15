from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from OpenDEMON.database.models import KaliProject, KaliTask
from OpenDEMON.kali.core.task import TaskValidator
from OpenDEMON.kali.core.events import EventManager
from OpenDEMON.kali.core.state import TaskStatus, EventType
from OpenDEMON.kali.core.errors import ExecutionLimitExceeded, InvalidStateTransitionError

from OpenDEMON.kali.capabilities.registry import CapabilityRegistry
from OpenDEMON.kali.capabilities.resolver import CapabilityResolver
from OpenDEMON.kali.tools.registry import ToolRegistry
from OpenDEMON.kali.tools.executor import SafeExecutor
from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.permissions.manager import KALIPermissionManager
from OpenDEMON.kali.permissions.approval import KALIApprovalManager
from .context import ExecutionLimits

class KALIRuntime:
    """Core execution engine for managing long-running, multi-step tasks."""
    
    def __init__(self, db_session: AsyncSession, orchestrator: Any):
        self.db = db_session
        self.orchestrator = orchestrator
        self.events = EventManager(db_session)
        self.limits = ExecutionLimits()
        
        # Initialize KALI capability and tool systems
        self.capability_registry = CapabilityRegistry()
        self.capability_resolver = CapabilityResolver(self.capability_registry)
        self.tool_registry = ToolRegistry()
        self.approval_manager = KALIApprovalManager(self.db)
        self.permission_manager = KALIPermissionManager(self.db, self.approval_manager)

    async def create_project(self, user_id: str, name: str, description: str = "", objective: str = "", workspace: dict = None) -> KaliProject:
        project = KaliProject(user_id=user_id, name=name, description=description, objective=objective, workspace=workspace or {})
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project(self, project_id: str) -> Optional[KaliProject]:
        result = await self.db.execute(select(KaliProject).where(KaliProject.id == project_id))
        return result.scalars().first()

    async def get_projects(self, user_id: str) -> List[KaliProject]:
        result = await self.db.execute(select(KaliProject).where(KaliProject.user_id == user_id))
        return result.scalars().all()

    async def update_project(self, project_id: str, **kwargs) -> KaliProject:
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
                
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def create_task(self, user_id: str, objective: str, project_id: Optional[str] = None, parent_task_id: Optional[str] = None, dependencies: List[str] = None) -> KaliTask:
        if parent_task_id:
            # Check depth limits
            depth = await self._get_task_depth(parent_task_id)
            if depth >= self.limits.max_depth:
                raise ExecutionLimitExceeded(f"Task depth exceeds maximum limit of {self.limits.max_depth}")
        
        task = KaliTask(
            user_id=user_id,
            objective=objective,
            project_id=project_id,
            parent_task_id=parent_task_id,
            dependencies=dependencies or []
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        await self.events.dispatch(task.id, EventType.TASK_CREATED, "Task created successfully.")
        return task

    async def _get_task_depth(self, task_id: str) -> int:
        depth = 0
        current_id = task_id
        while current_id:
            task = await self.get_task(current_id)
            if not task or not task.parent_task_id:
                break
            depth += 1
            current_id = task.parent_task_id
        return depth

    async def get_task(self, task_id: str) -> Optional[KaliTask]:
        result = await self.db.execute(select(KaliTask).where(KaliTask.id == task_id))
        return result.scalars().first()

    async def start_task(self, task_id: str) -> KaliTask:
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        if task.status != TaskStatus.PENDING.value and task.status != TaskStatus.WAITING.value:
            raise InvalidStateTransitionError(f"Cannot start task from state {task.status}")
            
        task.status = TaskStatus.RUNNING.value
        await self.db.commit()
        
        await self.events.dispatch(task.id, EventType.TASK_STARTED, "Task started executing.")
        return task

    async def pause_task(self, task_id: str) -> KaliTask:
        task = await self.get_task(task_id)
        if task and task.status == TaskStatus.RUNNING.value:
            task.status = TaskStatus.WAITING.value
            await self.db.commit()
            await self.events.dispatch(task.id, EventType.TASK_WAITING_APPROVAL, "Task paused/waiting.")
        return task

    async def cancel_task(self, task_id: str) -> KaliTask:
        task = await self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
            
        task.status = TaskStatus.CANCELLED.value
        await self.db.commit()
        
        await self.events.dispatch(task.id, EventType.TASK_CANCELLED, "Task manually cancelled.")
        
        # Propagate to children
        children_result = await self.db.execute(select(KaliTask).where(KaliTask.parent_task_id == task_id))
        children = children_result.scalars().all()
        for child in children:
            if child.status not in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
                await self.cancel_task(child.id)
                
        return task

    async def complete_task(self, task_id: str, output_data: dict) -> KaliTask:
        task = await self.get_task(task_id)
        task.status = TaskStatus.COMPLETED.value
        task.output_data = output_data
        await self.db.commit()
        await self.events.dispatch(task.id, EventType.TASK_COMPLETED, "Task completed successfully.")
        return task

    async def fail_task(self, task_id: str, error_message: str) -> KaliTask:
        task = await self.get_task(task_id)
        task.status = TaskStatus.FAILED.value
        task.errors = {"message": error_message}
        await self.db.commit()
        await self.events.dispatch(task.id, EventType.TASK_FAILED, f"Task failed: {error_message}")
        return task

    async def update_task(self, task_id: str, **kwargs) -> KaliTask:
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
                
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def retry_task(self, task_id: str) -> KaliTask:
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        if task.status != TaskStatus.FAILED.value:
            raise InvalidStateTransitionError("Can only retry FAILED tasks")
            
        if task.retry_count >= self.limits.max_retries:
            raise ExecutionLimitExceeded(f"Task exceeded max retries ({self.limits.max_retries})")
            
        task.status = TaskStatus.PENDING.value
        task.retry_count += 1
        await self.db.commit()
        
        await self.events.dispatch(task.id, EventType.TASK_RETRYING, f"Task retrying. Attempt {task.retry_count}")
        return task

    async def execute_task(self, task_id: str, auth_scope: Optional[AuthorizationScope] = None) -> KaliTask:
        """
        End-to-end task execution pipeline:
        Resolves capabilities -> Maps tools -> Executes via SafeExecutor -> Updates Task
        """
        task = await self.start_task(task_id)
        
        try:
            # 1. Capability Resolution
            capabilities = self.capability_resolver.resolve(task.objective)
            if not capabilities:
                return await self.fail_task(task_id, "Could not resolve any capabilities for this objective.")
                
            await self.events.dispatch(task.id, EventType.TASK_STARTED, f"Resolved {len(capabilities)} capabilities.")
            
            # 2. Tool Mapping
            # For simplicity in this step, we match the first tool that provides any of the required capabilities.
            # In a real scenario, this would be an LLM-driven planning step.
            selected_tool = None
            for cap in capabilities:
                for tool in self.tool_registry._tools.values():
                    if tool.required_capability == cap.name:
                        selected_tool = tool
                        break
                if selected_tool:
                    break
                    
            if not selected_tool:
                return await self.fail_task(task_id, "No registered tools found for the resolved capabilities.")
                
            await self.events.dispatch(task.id, EventType.TASK_STARTED, f"Selected tool: {selected_tool.name}")
            
            # 3. Tool Execution setup
            # Mocking default inputs for now, since we don't have an LLM generating JSON here yet.
            default_inputs = {}
            if selected_tool.name == "auth_recon":
                default_inputs = {"target": "10.0.0.1"} # Hardcoded for testing the mock
                
            # 3.5 Permission Check
            decision = await self.permission_manager.check_permission(
                user_id=task.user_id,
                project_id=task.project_id or "",
                task_id=task.id,
                tool=selected_tool,
                inputs=default_inputs,
                auth_scope=auth_scope
            )
            
            if decision.decision == "DENY":
                return await self.fail_task(task_id, f"Permission denied: {decision.reason}")
            elif decision.decision == "REQUIRE_APPROVAL":
                # Create an approval request
                await self.approval_manager.create_request(
                    user_id=task.user_id,
                    project_id=task.project_id or "",
                    task_id=task.id,
                    tool_name=selected_tool.name,
                    action="execute",
                    risk_level=selected_tool.risk_level,
                    reason=decision.reason,
                    inputs=default_inputs,
                    resource=default_inputs.get("target")
                )
                return await self.pause_task(task_id)

            # 4. Tool Execution
            result = await SafeExecutor.execute_tool(selected_tool, default_inputs, auth_scope)
            
            # 4. Result Handling
            if not result.success:
                return await self.fail_task(task_id, f"Tool execution failed: {result.error}")
                
            # 5. Completion
            output_data = result.output.model_dump() if hasattr(result.output, "model_dump") else result.output.dict()
            return await self.complete_task(task_id, output_data)
            
        except Exception as e:
            return await self.fail_task(task_id, f"Unexpected execution error: {str(e)}")

    async def get_project_tasks(self, project_id: str) -> List[KaliTask]:
        result = await self.db.execute(select(KaliTask).where(KaliTask.project_id == project_id))
        return result.scalars().all()
