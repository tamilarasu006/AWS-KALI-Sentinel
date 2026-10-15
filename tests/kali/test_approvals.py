import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from OpenDEMON.kali.permissions.approval import KALIApprovalManager
from OpenDEMON.kali.permissions.models import ApprovalRequestStatus
from OpenDEMON.database.models.kali_approval_request import KaliApprovalRequest

@pytest.fixture
def mock_db():
    db = AsyncMock()
    # Ensure db.execute returns an object with scalars() that returns an object with first()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    db.execute.return_value = mock_result
    return db

@pytest.fixture
def approval_manager(mock_db):
    return KALIApprovalManager(mock_db)

@pytest.mark.asyncio
async def test_create_request(approval_manager, mock_db):
    req = await approval_manager.create_request(
        user_id="user1",
        project_id="proj1",
        task_id="task1",
        tool_name="tool1",
        action="execute",
        risk_level=MagicMock(value="HIGH"),
        reason="Because",
        inputs={"target": "10.0.0.1", "password": "supersecret"}
    )
    
    assert req.user_id == "user1"
    assert req.status == ApprovalRequestStatus.PENDING
    
    # Check secret redaction
    assert "password" in req.requested_input_summary
    assert req.requested_input_summary["password"] == "[REDACTED]"
    assert req.requested_input_summary["target"] == "10.0.0.1"

@pytest.mark.asyncio
async def test_get_request_auto_expire(approval_manager, mock_db):
    expired_req = KaliApprovalRequest(
        id="req1",
        user_id="user1",
        status=ApprovalRequestStatus.PENDING,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    
    mock_db.execute.return_value.scalars.return_value.first.return_value = expired_req
    
    req = await approval_manager.get_request("req1", "user1")
    assert req.status == ApprovalRequestStatus.EXPIRED

@pytest.mark.asyncio
async def test_approve_request(approval_manager, mock_db):
    valid_req = KaliApprovalRequest(
        id="req2",
        user_id="user1",
        status=ApprovalRequestStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    
    mock_db.execute.return_value.scalars.return_value.first.return_value = valid_req
    
    req = await approval_manager.approve_request("req2", "user1")
    assert req.status == ApprovalRequestStatus.APPROVED
    assert req.approved_by == "user1"

@pytest.mark.asyncio
async def test_reject_request(approval_manager, mock_db):
    valid_req = KaliApprovalRequest(
        id="req3",
        user_id="user1",
        status=ApprovalRequestStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    
    mock_db.execute.return_value.scalars.return_value.first.return_value = valid_req
    
    req = await approval_manager.reject_request("req3", "user1", "Not today")
    assert req.status == ApprovalRequestStatus.REJECTED
    assert req.rejection_reason == "Not today"
