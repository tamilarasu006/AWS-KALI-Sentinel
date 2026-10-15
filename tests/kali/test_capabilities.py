import pytest
from OpenDEMON.kali.capabilities.registry import CapabilityRegistry
from OpenDEMON.kali.capabilities.resolver import CapabilityResolver
from OpenDEMON.kali.capabilities.schemas import RiskLevel

def test_registry_initialization():
    registry = CapabilityRegistry()
    capabilities = registry.get_all()
    assert len(capabilities) > 0
    
    cyber = registry.get("CYBERSECURITY_ASSESSMENT")
    assert cyber is not None
    assert cyber.risk_level == RiskLevel.CRITICAL
    assert "security:audit" in cyber.permission_requirements

def test_capability_resolution():
    registry = CapabilityRegistry()
    resolver = CapabilityResolver(registry)
    
    # Test Data Analysis
    caps = resolver.resolve("Analyze this Excel file")
    names = [c.name for c in caps]
    assert "DATA_ANALYSIS" in names
    assert "REASONING" in names
    
    # Test Full Stack
    caps = resolver.resolve("Build React + Node application")
    names = [c.name for c in caps]
    assert "FULL_STACK_DEVELOPMENT" in names
    
    # Test Cyber
    caps = resolver.resolve("Assess my authorized lab server")
    names = [c.name for c in caps]
    assert "CYBERSECURITY_ASSESSMENT" in names
    
    # Ensure risk levels are fetched correctly
    cyber_cap = next(c for c in caps if c.name == "CYBERSECURITY_ASSESSMENT")
    assert cyber_cap.risk_level == RiskLevel.CRITICAL
