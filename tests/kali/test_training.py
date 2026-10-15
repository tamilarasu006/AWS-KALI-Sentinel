import pytest
import os
import torch
from OpenDEMON.kali.data.filters import SecurityFilter
from OpenDEMON.kali.data.cleaners import clean_text
from OpenDEMON.kali.data.dedup import Deduplicator
from OpenDEMON.kali.training.checkpoint import CheckpointManager

def test_security_filter():
    f = SecurityFilter()
    assert f.contains_sensitive_data("Here is my API_KEY='1234567890abcdef123'")
    assert f.contains_sensitive_data("password = 'supersecretpassword'")
    assert f.contains_sensitive_data("postgres://user:pass@localhost:5432/db")
    assert f.contains_sensitive_data("API_SECRET=mysecretkey1234567890")
    
    assert not f.contains_sensitive_data("This is a normal sentence.")
    assert not f.contains_sensitive_data("api = 'some_api_module'")

def test_cleaner():
    text = "Hello\u200b \t World!  "
    assert clean_text(text) == "Hello World!"

def test_deduplicator():
    d = Deduplicator()
    assert not d.is_duplicate("Hello World")
    assert d.is_duplicate("Hello World")
    assert not d.is_duplicate("Hello World!")
    
    d.reset()
    assert not d.is_duplicate("Hello World")

def test_checkpoint_manager(tmpdir):
    manager = CheckpointManager(str(tmpdir))
    model = torch.nn.Linear(10, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    
    # Fake scheduler with state_dict
    class MockScheduler:
        def state_dict(self): return {"step": 1}
        def load_state_dict(self, d): pass
        
    scheduler = MockScheduler()
    
    manager.save(model, optimizer, scheduler, epoch=1, step=10, loss=0.5, filename="test.pt")
    
    # Load it back
    model_new = torch.nn.Linear(10, 2)
    meta = manager.load(os.path.join(str(tmpdir), "test.pt"), model_new)
    
    assert meta["epoch"] == 1
    assert meta["loss"] == 0.5
