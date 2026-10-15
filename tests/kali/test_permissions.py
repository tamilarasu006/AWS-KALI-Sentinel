import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from OpenDEMON.kali.permissions.manager import KALIPermissionManager
from OpenDEMON.kali.permissions.approval import KALIApprovalManager
from OpenDEMON.kali.permissions.scope import ScopeValidator
from OpenDEMON.kali.tools.tool import KaliTool
from OpenDEMON.kali.tools.permissions import AuthorizationScope
from OpenDEMON.kali.capabilities.schemas import RiskLevel
from OpenDEMON.database.models.kali_permission_policy import KaliPermissionPolicy
from OpenDEMON.database.models.kali_approval_request import KaliApprovalRequest

@pytest.fixture
def mock_db():
    db = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    db.execute.return_value = mock_result
    return db

from pydantic import BaseModel

class DummySchema(BaseModel):
    pass

class DummyTool(KaliTool):
    input_schema: type[BaseModel] = DummySchema
    output_schema: type[BaseModel] = DummySchema
    
    async def execute(self, inputs, auth_scope=None):
        pass


@pytest.fixture
def approval_manager(mock_db):
    return KALIApprovalManager(mock_db)

@pytest.fixture
def permission_manager(mock_db, approval_manager):
    return KALIPermissionManager(mock_db, approval_manager)

def test_scope_validator():
    # Test CIDR
    assert ScopeValidator.is_target_in_scope("192.168.1.10", ["192.168.1.0/24"]) is True
    assert ScopeValidator.is_target_in_scope("192.168.2.10", ["192.168.1.0/24"]) is False
    
    # Test Exact IP
    assert ScopeValidator.is_target_in_scope("10.0.0.1", ["10.0.0.1"]) is True
    
    # Test Wildcard domain
    assert ScopeValidator.is_target_in_scope("test.example.com", ["*.example.com"]) is True
    assert ScopeValidator.is_target_in_scope("example.com", ["*.example.com"]) is True
    assert ScopeValidator.is_target_in_scope("other.com", ["*.example.com"]) is False

@pytest.mark.asyncio
async def test_permission_manager_low_risk(permission_manager, mock_db):
    tool = DummyTool(
        name="test_tool",
        description="A low risk tool",
        version="1.0.0",
        required_capability="test",
        risk_level=RiskLevel.LOW
    )
    
    # Mock no policy
    mock_db.execute.return_value.scalars.return_value.first.return_value = None
    
    decision = await permission_manager.check_permission(
        user_id="user1", project_id="proj1", task_id="task1", tool=tool, inputs={}
    )
    
    assert decision.allowed is True
    assert decision.decision == "ALLOW"
    assert "LOW risk" in decision.reason

@pytest.mark.asyncio
async def test_permission_manager_medium_risk_no_policy(permission_manager, mock_db):
    tool = DummyTool(
        name="med_tool",
        description="A medium risk tool",
        version="1.0.0",
        required_capability="test",
        risk_level=RiskLevel.MEDIUM
    )
    
    # Mock no policy
    mock_db.execute.return_value.scalars.return_value.first.return_value = None
    
    decision = await permission_manager.check_permission(
        user_id="user1", project_id="proj1", task_id="task1", tool=tool, inputs={}
    )
    
    assert decision.allowed is False
    assert decision.decision == "DENY"

@pytest.mark.asyncio
async def test_permission_manager_medium_risk_with_policy(permission_manager, mock_db):
    tool = DummyTool(
        name="med_tool",
        description="A medium risk tool",
        version="1.0.0",
        required_capability="test",
        risk_level=RiskLevel.MEDIUM
    )
    
    policy = KaliPermissionPolicy(allowed_tools=["med_tool"])
    mock_db.execute.return_value.scalars.return_value.first.return_value = policy
    
    decision = await permission_manager.check_permission(
        user_id="user1", project_id="proj1", task_id="task1", tool=tool, inputs={}
    )
    
    assert decision.allowed is True
    assert decision.decision == "ALLOW"

@pytest.mark.asyncio
async def test_permission_manager_high_risk_require_approval(permission_manager, mock_db):
    tool = DummyTool(
        name="high_tool",
        description="A high risk tool",
        version="1.0.0",
        required_capability="test",
        risk_level=RiskLevel.HIGH
    )
    
    # Return no policy, then return no existing approvals, then return no pending approvals
    mock_db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(first=lambda: None)), # policy project
        MagicMock(scalars=lambda: MagicMock(first=lambda: None)), # policy user
        MagicMock(scalars=lambda: MagicMock(first=lambda: None)), # approved reqs
        MagicMock(scalars=lambda: MagicMock(first=lambda: None))  # pending reqs
    ]
    
    decision = await permission_manager.check_permission(
        user_id="user1", project_id="proj1", task_id="task1", tool=tool, inputs={}
    )
    
    assert decision.allowed is False
    assert decision.decision == "REQUIRE_APPROVAL"
    assert decision.requires_approval is True

@pytest.mark.asyncio
async def test_permission_manager_high_risk_already_approved(permission_manager, mock_db):
    tool = DummyTool(
        name="high_tool",
        description="A high risk tool",
        version="1.0.0",
        required_capability="test",
        risk_level=RiskLevel.HIGH
    )
    
    approved_req = KaliApprovalRequest(id="appr1", status="APPROVED", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    
    mock_db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(first=lambda: None)), # policy project
        MagicMock(scalars=lambda: MagicMock(first=lambda: None)), # policy user
        MagicMock(scalars=lambda: MagicMock(first=lambda: approved_req)) # approved reqs
    ]
    
    decision = await permission_manager.check_permission(
        user_id="user1", project_id="proj1", task_id="task1", tool=tool, inputs={}
    )
    
    assert decision.allowed is True
    assert decision.decision == "ALLOW"

@pytest.mark.asyncio
async def test_cybersecurity_scope_validation(permission_manager, mock_db):
    tool = DummyTool(
        name="cyber_tool",
        description="Cyber tool",
        version="1.0.0",
        required_capability="test",
        category="cybersecurity",
        risk_level=RiskLevel.LOW
    )
    
    # Missing auth scope
    decision = await permission_manager.check_permission(
        user_id="user1", project_id="proj1", task_id="task1", tool=tool, inputs={"target": "10.0.0.1"}
    )
    assert decision.allowed is False
    assert decision.decision == "DENY"
    
    # Out of scope
    auth_scope = AuthorizationScope(allowed_targets=["192.168.1.0/24"])
    decision = await permission_manager.check_permission(
        user_id="user1", project_id="proj1", task_id="task1", tool=tool, inputs={"target": "10.0.0.1"}, auth_scope=auth_scope
    )
    assert decision.allowed is False
    assert decision.decision == "DENY"
    
    # In scope
    mock_db.execute.return_value.scalars.return_value.first.return_value = None
    decision = await permission_manager.check_permission(
        user_id="user1", project_id="proj1", task_id="task1", tool=tool, inputs={"target": "192.168.1.10"}, auth_scope=auth_scope
    )
    assert decision.allowed is True
    assert decision.decision == "ALLOW"
