from __future__ import annotations
import json
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from OpenDEMON.database.models.kali_permission_policy import KaliPermissionPolicy
from OpenDEMON.database.models.kali_approval_request import KaliApprovalRequest
from OpenDEMON.database.models.kali_permission_decision import KaliPermissionDecision
from OpenDEMON.kali.permissions.models import ApprovalRequestStatus
from OpenDEMON.kali.permissions.decisions import PermissionDecision
from OpenDEMON.kali.permissions.approval import KALIApprovalManager
from OpenDEMON.kali.permissions.scope import ScopeValidator
from typing import Optional, Dict, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from OpenDEMON.kali.tools.tool import KaliTool

from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.permissions.risk import RiskLevel

class KALIPermissionManager:
    """
    Evaluates permissions for tool executions based on user identity, project policies, 
    tool risk levels, and human approvals. Default behavior is DENY.
    """
    def __init__(self, db: AsyncSession, approval_manager: KALIApprovalManager):
        self.db = db
        self.approval_manager = approval_manager

    async def _log_decision(self, decision: PermissionDecision) -> None:
        """Persists the decision into the audit log."""
        record = KaliPermissionDecision(
            user_id=decision.user_id,
            project_id=decision.project_id,
            task_id=decision.task_id,
            tool_name=decision.tool_name,
            action="execute",
            risk_level=decision.risk_level.value,
            decision=decision.decision,
            allowed=decision.allowed,
            reason=decision.reason,
            approval_id=decision.approval_id,
            policy_id=decision.policy_id,
            scope=None,
            timestamp=decision.timestamp
        )
        self.db.add(record)
        await self.db.commit()

    async def _get_policy(self, user_id: str, project_id: str) -> Optional[KaliPermissionPolicy]:
        """Fetches the project-specific policy, or user-level fallback."""
        result = await self.db.execute(
            select(KaliPermissionPolicy).where(
                KaliPermissionPolicy.user_id == user_id,
                KaliPermissionPolicy.project_id == project_id
            )
        )
        policy = result.scalars().first()
        if not policy:
            result = await self.db.execute(
                select(KaliPermissionPolicy).where(
                    KaliPermissionPolicy.user_id == user_id,
                    KaliPermissionPolicy.project_id == None
                )
            )
            policy = result.scalars().first()
        return policy

    def _create_deny(self, reason: str, user_id: str, project_id: str, task_id: str, tool: KaliTool) -> PermissionDecision:
        return PermissionDecision(
            allowed=False,
            decision="DENY",
            reason=reason,
            risk_level=tool.risk_level,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            tool_name=tool.name
        )
        
    def _create_require_approval(self, reason: str, user_id: str, project_id: str, task_id: str, tool: KaliTool, policy_id: Optional[str]) -> PermissionDecision:
        return PermissionDecision(
            allowed=False,
            decision="REQUIRE_APPROVAL",
            reason=reason,
            risk_level=tool.risk_level,
            requires_approval=True,
            policy_id=policy_id,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            tool_name=tool.name
        )

    def _create_allow(self, reason: str, user_id: str, project_id: str, task_id: str, tool: KaliTool, policy_id: Optional[str], approval_id: Optional[str] = None) -> PermissionDecision:
        return PermissionDecision(
            allowed=True,
            decision="ALLOW",
            reason=reason,
            risk_level=tool.risk_level,
            approval_id=approval_id,
            policy_id=policy_id,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            tool_name=tool.name
        )

    async def check_permission(self, user_id: str, project_id: str, task_id: str, tool: KaliTool, 
                               inputs: Dict[str, Any], auth_scope: Optional[AuthorizationScope] = None) -> PermissionDecision:
        """
        Deterministic policy evaluation order:
        1. Validate identity (Implicitly verified by caller context but checks if provided)
        2. Validate tool (Enabled?)
        3. Validate authorization scope (Cybersecurity)
        4. Check Policy rules (Allowed tools/permissions)
        5. Evaluate Risk Level & check for explicit Approvals
        """
        # 1. Validate tool state
        if not getattr(tool, "enabled", True):
            decision = self._create_deny("Tool is disabled.", user_id, project_id, task_id, tool)
            await self._log_decision(decision)
            return decision

        if not user_id or not project_id or not task_id:
            decision = self._create_deny("Missing execution context (user/project/task).", user_id, project_id, task_id, tool)
            await self._log_decision(decision)
            return decision

        # 2. Scope Validation for cybersecurity tools
        if tool.category == "cybersecurity":
            if not auth_scope:
                decision = self._create_deny("Cybersecurity tools require an explicit AuthorizationScope.", user_id, project_id, task_id, tool)
                await self._log_decision(decision)
                return decision
            
            target = inputs.get("target")
            if not target:
                decision = self._create_deny("Missing 'target' in cybersecurity tool inputs.", user_id, project_id, task_id, tool)
                await self._log_decision(decision)
                return decision
                
            # Verify target against auth_scope
            scope_list = getattr(auth_scope, "allowed_targets", [])
            if not ScopeValidator.is_target_in_scope(target, scope_list):
                decision = self._create_deny(f"Target {target} is outside authorized scope {scope_list}.", user_id, project_id, task_id, tool)
                await self._log_decision(decision)
                return decision

        # 3. Policy Evaluation
        policy = await self._get_policy(user_id, project_id)
        policy_id = policy.id if policy else None
        
        if policy:
            # Check explicit denies first
            if tool.name in (policy.denied_permissions or []):
                decision = self._create_deny("Tool is explicitly denied by project policy.", user_id, project_id, task_id, tool)
                decision.policy_id = policy_id
                await self._log_decision(decision)
                return decision
                
            for p in (tool.permissions or []):
                if p in (policy.denied_permissions or []):
                    decision = self._create_deny(f"Required permission '{p}' is explicitly denied by project policy.", user_id, project_id, task_id, tool)
                    decision.policy_id = policy_id
                    await self._log_decision(decision)
                    return decision
            
            # Check explicit allows (allows MEDIUM without human approval)
            is_policy_allowed = tool.name in (policy.allowed_tools or [])
            if not is_policy_allowed:
                for p in (tool.permissions or []):
                    if p in (policy.allowed_permissions or []):
                        is_policy_allowed = True
                        break
        else:
            is_policy_allowed = False

        # 4. Risk Level Evaluation
        if tool.risk_level == RiskLevel.LOW:
            decision = self._create_allow("Auto-approved LOW risk tool.", user_id, project_id, task_id, tool, policy_id)
            await self._log_decision(decision)
            return decision

        if tool.risk_level == RiskLevel.MEDIUM:
            if is_policy_allowed:
                decision = self._create_allow("MEDIUM risk tool allowed by policy.", user_id, project_id, task_id, tool, policy_id)
                await self._log_decision(decision)
                return decision
            else:
                decision = self._create_deny("MEDIUM risk tool requires explicit policy allow.", user_id, project_id, task_id, tool)
                decision.policy_id = policy_id
                await self._log_decision(decision)
                return decision

        # HIGH and CRITICAL always require explicit human approval, unless an approval already exists
        # Let's check for an existing APPROVED request in the DB for this exact task/tool
        existing_approvals = await self.db.execute(
            select(KaliApprovalRequest).where(
                KaliApprovalRequest.user_id == user_id,
                KaliApprovalRequest.project_id == project_id,
                KaliApprovalRequest.task_id == task_id,
                KaliApprovalRequest.tool_name == tool.name,
                KaliApprovalRequest.status == ApprovalRequestStatus.APPROVED
            )
        )
        approved_request = existing_approvals.scalars().first()
        
        if approved_request:
            # Check expiration
            expires_at = approved_request.expires_at.replace(tzinfo=timezone.utc) if approved_request.expires_at.tzinfo is None else approved_request.expires_at
            if expires_at < datetime.now(timezone.utc):
                approved_request.status = ApprovalRequestStatus.EXPIRED
                await self.db.commit()
            else:
                decision = self._create_allow("Execution explicitly approved by human.", user_id, project_id, task_id, tool, policy_id, approved_request.id)
                await self._log_decision(decision)
                return decision
        
        # Check if there is already a PENDING or REJECTED request
        pending_approvals = await self.db.execute(
            select(KaliApprovalRequest).where(
                KaliApprovalRequest.user_id == user_id,
                KaliApprovalRequest.project_id == project_id,
                KaliApprovalRequest.task_id == task_id,
                KaliApprovalRequest.tool_name == tool.name,
                KaliApprovalRequest.status.in_([ApprovalRequestStatus.PENDING, ApprovalRequestStatus.REJECTED])
            )
        )
        existing_req = pending_approvals.scalars().first()
        if existing_req:
            if existing_req.status == ApprovalRequestStatus.REJECTED:
                decision = self._create_deny("Execution was explicitly REJECTED by human.", user_id, project_id, task_id, tool)
                decision.approval_id = existing_req.id
                await self._log_decision(decision)
                return decision
            else:
                decision = self._create_require_approval("Approval is still PENDING.", user_id, project_id, task_id, tool, policy_id)
                decision.approval_id = existing_req.id
                await self._log_decision(decision)
                return decision

        # Need to create an approval request
        reason = f"{tool.risk_level.name} risk tool execution requires human approval."
        
        # The runtime is responsible for taking the decision and actually calling create_request, 
        # but to keep the flow smooth, the PermissionManager returns REQUIRE_APPROVAL
        
        decision = self._create_require_approval(reason, user_id, project_id, task_id, tool, policy_id)
        await self._log_decision(decision)
        return decision
