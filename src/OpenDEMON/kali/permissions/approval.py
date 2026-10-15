import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from OpenDEMON.database.models.kali_approval_request import KaliApprovalRequest
from OpenDEMON.kali.permissions.models import ApprovalRequestStatus
from OpenDEMON.kali.permissions.risk import RiskLevel

class KALIApprovalManager:
    """
    Manages the lifecycle of human approval requests for KALI tool executions.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        
    def _redact_secrets(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redacts sensitive fields to prevent logging them in approval requests."""
        if not data:
            return {}
        redacted = {}
        sensitive_keys = {"password", "api_key", "token", "secret", "private_key", "credential"}
        
        for k, v in data.items():
            if any(sk in k.lower() for sk in sensitive_keys):
                redacted[k] = "[REDACTED]"
            elif isinstance(v, dict):
                redacted[k] = self._redact_secrets(v)
            else:
                redacted[k] = v
        return redacted

    async def create_request(self, user_id: str, project_id: str, task_id: str, tool_name: str, action: str, 
                             risk_level: RiskLevel, reason: str, inputs: Dict[str, Any], resource: Optional[str] = None,
                             ttl_seconds: int = 3600) -> KaliApprovalRequest:
        
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        redacted_inputs = self._redact_secrets(inputs)
        
        request = KaliApprovalRequest(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            tool_name=tool_name,
            action=action,
            resource=resource,
            risk_level=risk_level.value,
            reason=reason,
            requested_input_summary=redacted_inputs,
            status=ApprovalRequestStatus.PENDING,
            expires_at=expires_at
        )
        
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def get_request(self, approval_id: str, user_id: str) -> Optional[KaliApprovalRequest]:
        result = await self.db.execute(
            select(KaliApprovalRequest).where(
                KaliApprovalRequest.id == approval_id,
                KaliApprovalRequest.user_id == user_id
            )
        )
        request = result.scalars().first()
        
        if request and request.status == ApprovalRequestStatus.PENDING:
            if request.expires_at.tzinfo is None:
                expires_at = request.expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_at = request.expires_at
                
            if expires_at < datetime.now(timezone.utc):
                request.status = ApprovalRequestStatus.EXPIRED
                await self.db.commit()
                
        return request

    async def list_pending_requests(self, user_id: str) -> List[KaliApprovalRequest]:
        result = await self.db.execute(
            select(KaliApprovalRequest).where(
                KaliApprovalRequest.user_id == user_id,
                KaliApprovalRequest.status == ApprovalRequestStatus.PENDING
            )
        )
        requests = result.scalars().all()
        
        # Expire stale
        valid_requests = []
        now = datetime.now(timezone.utc)
        has_changes = False
        for req in requests:
            expires_at = req.expires_at.replace(tzinfo=timezone.utc) if req.expires_at.tzinfo is None else req.expires_at
            if expires_at < now:
                req.status = ApprovalRequestStatus.EXPIRED
                has_changes = True
            else:
                valid_requests.append(req)
                
        if has_changes:
            await self.db.commit()
            
        return valid_requests

    async def approve_request(self, approval_id: str, user_id: str) -> Optional[KaliApprovalRequest]:
        request = await self.get_request(approval_id, user_id)
        if not request or request.status != ApprovalRequestStatus.PENDING:
            return None
            
        request.status = ApprovalRequestStatus.APPROVED
        request.approved_at = datetime.now(timezone.utc)
        request.approved_by = user_id
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def reject_request(self, approval_id: str, user_id: str, reason: str) -> Optional[KaliApprovalRequest]:
        request = await self.get_request(approval_id, user_id)
        if not request or request.status != ApprovalRequestStatus.PENDING:
            return None
            
        request.status = ApprovalRequestStatus.REJECTED
        request.rejected_at = datetime.now(timezone.utc)
        request.rejection_reason = reason
        await self.db.commit()
        await self.db.refresh(request)
        return request
        
    async def cancel_request(self, approval_id: str, user_id: str) -> Optional[KaliApprovalRequest]:
        request = await self.get_request(approval_id, user_id)
        if not request or request.status != ApprovalRequestStatus.PENDING:
            return None
            
        request.status = ApprovalRequestStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(request)
        return request
