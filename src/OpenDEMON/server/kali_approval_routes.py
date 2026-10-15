from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

from OpenDEMON.database.engine import AsyncSessionLocal
from OpenDEMON.kali.permissions.approval import KALIApprovalManager
from OpenDEMON.kali.permissions.models import ApprovalRequestStatus
from OpenDEMON.kali.core.runtime import KALIRuntime

router = APIRouter(prefix="/v1/kali/approvals", tags=["KALI Approvals"])


class ApprovalRequestResponse(BaseModel):
    id: str
    user_id: str
    project_id: str
    task_id: str
    tool_name: str
    action: str
    resource: Optional[str] = None
    risk_level: str
    reason: str
    requested_input_summary: Dict[str, Any]
    status: str
    created_at: str
    expires_at: str

    class Config:
        from_attributes = True


class RejectRequest(BaseModel):
    reason: str


async def get_current_user_id(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return str(user_id)


def _serialize(req) -> ApprovalRequestResponse:
    """Convert a KaliApprovalRequest ORM object to the response model."""
    return ApprovalRequestResponse(
        id=req.id,
        user_id=req.user_id,
        project_id=req.project_id,
        task_id=req.task_id,
        tool_name=req.tool_name,
        action=req.action,
        resource=req.resource,
        risk_level=req.risk_level,
        reason=req.reason,
        requested_input_summary=req.requested_input_summary or {},
        status=req.status,
        created_at=req.created_at.isoformat() if req.created_at else "",
        expires_at=req.expires_at.isoformat() if req.expires_at else "",
    )


@router.get("", response_model=List[ApprovalRequestResponse])
async def list_pending_approvals(user_id: str = Depends(get_current_user_id)):
    """List all pending approval requests for the current user."""
    async with AsyncSessionLocal() as db:
        manager = KALIApprovalManager(db)
        requests = await manager.list_pending_requests(user_id)
        return [_serialize(r) for r in requests]


@router.get("/{approval_id}", response_model=ApprovalRequestResponse)
async def get_approval(approval_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific approval request by ID."""
    async with AsyncSessionLocal() as db:
        manager = KALIApprovalManager(db)
        req = await manager.get_request(approval_id, user_id)
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
        return _serialize(req)


@router.post("/{approval_id}/approve", response_model=ApprovalRequestResponse)
async def approve_request(approval_id: str, user_id: str = Depends(get_current_user_id)):
    """Approve a pending request."""
    async with AsyncSessionLocal() as db:
        manager = KALIApprovalManager(db)
        req = await manager.approve_request(approval_id, user_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending approval request not found",
            )
        return _serialize(req)


@router.post("/{approval_id}/reject", response_model=ApprovalRequestResponse)
async def reject_request(
    approval_id: str,
    data: RejectRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Reject a pending request."""
    async with AsyncSessionLocal() as db:
        manager = KALIApprovalManager(db)
        req = await manager.reject_request(approval_id, user_id, data.reason)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending approval request not found",
            )
        # Fail the associated task
        try:
            runtime = KALIRuntime(db, None)
            await runtime.fail_task(req.task_id, f"Human rejected approval: {data.reason}")
        except Exception:
            pass  # Best-effort; don't fail the response if the task is already gone
        return _serialize(req)


@router.post("/{approval_id}/cancel", response_model=ApprovalRequestResponse)
async def cancel_request(approval_id: str, user_id: str = Depends(get_current_user_id)):
    """Cancel a pending request."""
    async with AsyncSessionLocal() as db:
        manager = KALIApprovalManager(db)
        req = await manager.cancel_request(approval_id, user_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending approval request not found",
            )
        return _serialize(req)
