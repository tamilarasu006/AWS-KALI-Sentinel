import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio

from OpenDEMON.kali.permissions.manager import KALIPermissionManager
from OpenDEMON.kali.permissions.approval import KALIApprovalManager
from OpenDEMON.kali.permissions.authorization import AuthorizationScope
from OpenDEMON.kali.tools.tool import KaliTool
from OpenDEMON.kali.permissions.risk import RiskLevel
from OpenDEMON.database.models.kali_permission_policy import KaliPermissionPolicy
from OpenDEMON.database.models.kali_approval_request import KaliApprovalRequest
from OpenDEMON.kali.permissions.models import ApprovalRequestStatus

@pytest.fixture
def mock_db():
    db = AsyncMock()
    # By default, pretend no policy matches
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    db.execute.return_value = mock_result
    return db

@pytest.fixture
def manager(mock_db):
    approval_mgr = KALIApprovalManager(mock_db)
    return KALIPermissionManager(mock_db, approval_mgr)

@pytest.mark.asyncio
async def test_deny_disabled_tool(manager):
    tool = KaliTool(name="test_tool", description="", risk_level=RiskLevel.LOW, enabled=False)
    decision = await manager.check_permission("u1", "p1", "t1", tool, {})
    assert not decision.allowed
    assert decision.decision == "DENY"
    assert "disabled" in decision.reason.lower()

@pytest.mark.asyncio
async def test_deny_missing_context(manager):
    tool = KaliTool(name="test_tool", description="", risk_level=RiskLevel.LOW, enabled=True)
    decision = await manager.check_permission(None, "p1", "t1", tool, {})
    assert not decision.allowed
    assert decision.decision == "DENY"
    assert "missing execution context" in decision.reason.lower()

@pytest.mark.asyncio
async def test_deny_cybersecurity_without_scope(manager):
    tool = KaliTool(name="nmap", description="", risk_level=RiskLevel.HIGH, category="cybersecurity")
    decision = await manager.check_permission("u1", "p1", "t1", tool, {"target": "10.0.0.1"}, auth_scope=None)
    assert not decision.allowed
    assert decision.decision == "DENY"
    assert "authorization" in decision.reason.lower()

@pytest.mark.asyncio
async def test_allow_low_risk(manager):
    tool = KaliTool(name="calculator", description="", risk_level=RiskLevel.LOW)
    decision = await manager.check_permission("u1", "p1", "t1", tool, {})
    assert decision.allowed
    assert decision.decision == "ALLOW"
    assert "auto-approved" in decision.reason.lower()

@pytest.mark.asyncio
async def test_deny_medium_risk_without_policy(manager):
    tool = KaliTool(name="db_query", description="", risk_level=RiskLevel.MEDIUM)
    decision = await manager.check_permission("u1", "p1", "t1", tool, {})
    assert not decision.allowed
    assert decision.decision == "DENY"
    assert "explicit policy allow" in decision.reason.lower()

@pytest.mark.asyncio
async def test_allow_medium_risk_with_policy(manager, mock_db):
    policy = KaliPermissionPolicy(allowed_tools=["db_query"])
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = policy
    mock_db.execute.return_value = mock_result
    
    tool = KaliTool(name="db_query", description="", risk_level=RiskLevel.MEDIUM)
    decision = await manager.check_permission("u1", "p1", "t1", tool, {})
    assert decision.allowed
    assert decision.decision == "ALLOW"
    assert "policy" in decision.reason.lower()

@pytest.mark.asyncio
async def test_require_approval_high_risk(manager):
    tool = KaliTool(name="shell", description="", risk_level=RiskLevel.HIGH)
    decision = await manager.check_permission("u1", "p1", "t1", tool, {})
    assert not decision.allowed
    assert decision.decision == "REQUIRE_APPROVAL"

@pytest.mark.asyncio
async def test_allow_high_risk_with_existing_approval(manager, mock_db):
    # Setup mock to return no policy, then return an approval request
    policy_mock = MagicMock()
    policy_mock.scalars.return_value.first.return_value = None
    
    approval = KaliApprovalRequest(id="appr-123", status=ApprovalRequestStatus.APPROVED)
    approval_mock = MagicMock()
    approval_mock.scalars.return_value.first.return_value = approval
    
    mock_db.execute.side_effect = [policy_mock, approval_mock, MagicMock()]
    
    tool = KaliTool(name="shell", description="", risk_level=RiskLevel.HIGH)
    decision = await manager.check_permission("u1", "p1", "t1", tool, {})
    
    # Needs ALLOW since there's an active approval
    assert decision.allowed
    assert decision.decision == "ALLOW"
    assert decision.approval_id == "appr-123"
