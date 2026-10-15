import pytest
from OpenDEMON.kali.model.router import KALIModelRouter, EngineSpec

@pytest.fixture
def router():
    engines = [
        EngineSpec(id="e1", type="kali", models=["kali"], max_context=8000, available=True),
        EngineSpec(id="e2", type="kali-mini", models=["kali-mini"], max_context=4000, available=True),
        EngineSpec(id="e3", type="openai", models=["gpt-4"], max_context=128000, available=True),
        EngineSpec(id="e4", type="kali-offline", models=["kali"], max_context=8000, available=False)
    ]
    return KALIModelRouter(engines)

def test_selects_kali_when_available(router):
    engine, diag = router.route("kali", context_size=2000)
    assert engine is not None
    assert engine.id == "e1"
    assert diag.selected_model == "kali"
    assert not diag.fallback_used

def test_fails_silent_fallback_for_kali(router):
    # Ask for kali but with massive context, e1 will fail
    engine, diag = router.route("kali", context_size=10000)
    assert engine is None
    assert diag.selected_model is None
    assert "SILENT FALLBACK STRICTLY FORBIDDEN FOR KALI" in diag.reason

def test_allows_explicit_fallback_for_kali(router):
    # Ask for kali with massive context, but allow fallback
    # Actually wait, kali-mini only has 4000 context so it will still fail
    # Let's ask for kali when e1 is offline
    
    # Override e1 to offline
    router.engines[0].available = False
    
    engine, diag = router.route("kali", context_size=2000, allow_fallback=True)
    assert engine is not None
    assert engine.id == "e2"
    assert diag.selected_model == "kali-mini"
    assert diag.fallback_used

def test_unknown_model(router):
    engine, diag = router.route("unknown-model", context_size=100)
    assert engine is None
    assert diag.selected_model is None
    assert "completely unknown" in diag.reason
