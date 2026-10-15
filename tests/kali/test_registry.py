import pytest

from OpenDEMON.kali.model.config import KALIModelConfig
from OpenDEMON.kali.model.kali_model import KALIModel
from OpenDEMON.kali.registry import KALIModelRegistry


@pytest.fixture
def registry():
    return KALIModelRegistry()

@pytest.fixture
def dummy_model():
    config = KALIModelConfig(model_name="dummy", model_path="/path")
    return KALIModel(config)

def test_registry_register_and_get(registry, dummy_model):
    registry.register_model("dummy", dummy_model)
    retrieved = registry.get_model("dummy")
    assert retrieved is dummy_model

def test_registry_register_duplicate(registry, dummy_model):
    registry.register_model("dummy", dummy_model)
    with pytest.raises(ValueError):
        registry.register_model("dummy", dummy_model)

def test_registry_unregister(registry, dummy_model):
    registry.register_model("dummy", dummy_model)
    registry.unregister_model("dummy")
    with pytest.raises(KeyError):
        registry.get_model("dummy")

def test_registry_list_models(registry, dummy_model):
    assert registry.list_models() == []
    registry.register_model("dummy", dummy_model)
    assert registry.list_models() == ["dummy"]

def test_registry_default_model(registry, dummy_model):
    assert registry.default_model() is None
    registry.register_model("dummy", dummy_model)
    assert registry.default_model() is dummy_model

    # Registering another without is_default shouldn't change the default
    model2 = KALIModel(KALIModelConfig(model_name="dummy2", model_path="/path2"))
    registry.register_model("dummy2", model2)
    assert registry.default_model() is dummy_model

    # Registering with is_default=True should change the default
    registry.register_model("dummy3", model2, is_default=True)
    assert registry.default_model() is model2
