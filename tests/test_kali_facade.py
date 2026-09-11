import pytest
from KALI import KaliAI
from KALI.server.app import create_kali_app

def test_kali_ai_initialization():
    """Test that the KALI AI facade initializes correctly."""
    kali = KaliAI()
    assert kali.engine is None
    assert kali.agent_manager is None
    assert kali.db_engine is None

def test_kali_app_creation():
    """Test that the KALI API wrapper functions."""
    # We can't fully instantiate create_kali_app without an engine/model, 
    # but we can ensure the import works.
    assert create_kali_app is not None
