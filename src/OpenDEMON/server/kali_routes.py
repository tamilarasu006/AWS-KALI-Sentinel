from fastapi import APIRouter, Request, HTTPException
import os

router = APIRouter(prefix="/api/kali", tags=["kali"])

@router.get("/health")
async def kali_health(request: Request):
    """Check KALI specific health status."""
    orchestrator = getattr(request.app.state, "kali_orchestrator", None)
    enabled = os.environ.get("KALI_ENABLED", "false").lower() == "true"
    
    status = "disabled"
    if enabled:
        status = "healthy" if orchestrator else "failed"

    return {
        "status": status,
        "enabled": enabled,
        "engine": "kali" if orchestrator else "opendemon"
    }

@router.get("/models")
async def kali_models(request: Request):
    """List available KALI specific models."""
    orchestrator = getattr(request.app.state, "kali_orchestrator", None)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="KALI is not enabled or failed to initialize.")
    
    # We could theoretically query model registry, but for now return config default
    model_name = os.environ.get("KALI_DEFAULT_MODEL", "kali-mini")
    return {
        "models": [
            {
                "id": model_name,
                "object": "model",
                "owned_by": "kali"
            }
        ]
    }

from pydantic import BaseModel
from typing import List, Optional

class CreateTaskRequest(BaseModel):
    user_id: str
    objective: str
    project_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: List[str] = []

@router.post("/v1/tasks")
async def create_task(req: CreateTaskRequest, request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available")
    
    try:
        task = await runtime.create_task(
            user_id=req.user_id,
            objective=req.objective,
            project_id=req.project_id,
            parent_task_id=req.parent_task_id,
            dependencies=req.dependencies
        )
        return {"task_id": task.id, "status": task.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/v1/tasks/{task_id}")
async def get_task(task_id: str, request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available")
    
    task = await runtime.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {
        "task_id": task.id,
        "status": task.status,
        "objective": task.objective,
        "project_id": task.project_id
    }

@router.post("/v1/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available")
        
    try:
        task = await runtime.cancel_task(task_id)
        return {"task_id": task.id, "status": task.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/v1/tasks/{task_id}/events")
async def get_task_events(task_id: str, request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available")
        
    events = await runtime.events.get_events(task_id)
    return {
        "task_id": task_id, 
        "events": [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "summary": ev.summary,
                "timestamp": str(ev.timestamp)
            } for ev in events
        ]
    }

class CreateProjectRequest(BaseModel):
    user_id: str
    name: str
    description: Optional[str] = ""
    objective: Optional[str] = ""
    workspace: Optional[dict] = {}

@router.post("/v1/projects")
async def create_project(req: CreateProjectRequest, request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available")
    
    project = await runtime.create_project(
        user_id=req.user_id,
        name=req.name,
        description=req.description,
        objective=req.objective,
        workspace=req.workspace
    )
    return {"project_id": project.id, "status": project.status}

@router.get("/v1/projects")
async def get_projects(user_id: str, request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available")
        
    projects = await runtime.get_projects(user_id)
    return {
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status
            } for p in projects
        ]
    }

@router.get("/v1/projects/{project_id}")
async def get_project(project_id: str, request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available")
        
    project = await runtime.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return {
        "project_id": project.id,
        "name": project.name,
        "status": project.status,
        "objective": project.objective,
        "workspace": project.workspace
    }

class CreateProjectTaskRequest(BaseModel):
    user_id: str
    objective: str
    parent_task_id: Optional[str] = None
    dependencies: List[str] = []

@router.post("/v1/projects/{project_id}/tasks")
async def create_project_task(project_id: str, req: CreateProjectTaskRequest, request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available")
        
    try:
        task = await runtime.create_task(
            user_id=req.user_id,
            objective=req.objective,
            project_id=project_id,
            parent_task_id=req.parent_task_id,
            dependencies=req.dependencies
        )
        return {"task_id": task.id, "status": task.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/v1/projects/{project_id}/tasks")
async def get_project_tasks(project_id: str, request: Request):
    runtime = getattr(request.app.state, "kali_runtime", None)
    if not runtime:
        raise HTTPException(status_code=503, detail="KALI Runtime not available")
        
    tasks = await runtime.get_project_tasks(project_id)
    return {
        "tasks": [
            {
                "id": t.id,
                "status": t.status,
                "objective": t.objective,
                "parent_task_id": t.parent_task_id
            } for t in tasks
        ]
    }
