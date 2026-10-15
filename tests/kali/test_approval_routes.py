import pytest
from fastapi.testclient import TestClient
from OpenDEMON.server.app import create_app
from OpenDEMON.database.models import User
from unittest.mock import patch, MagicMock, AsyncMock

app = create_app(engine=None, model="test-model")
client = TestClient(app)

@pytest.fixture
def mock_current_user():
    user = User(id="user_1", email="test@example.com")
    with patch("OpenDEMON.server.kali_approval_routes.get_current_user_id", return_value="user_1"):
        yield user

@pytest.fixture
def mock_db_session():
    with patch("OpenDEMON.server.kali_approval_routes.get_db_session") as mock:
        session = AsyncMock()
        mock.return_value.__aenter__.return_value = session
        yield session

def test_list_pending_approvals(mock_current_user, mock_db_session):
    with patch("OpenDEMON.server.kali_approval_routes.KALIApprovalManager.list_pending_requests", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = []
        response = client.get("/api/v1/kali/approvals")
        # Ensure it requires auth or passes (depends on how router is mounted)
        # Note: If router is not mounted in app.py, this will 404
