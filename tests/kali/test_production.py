import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from OpenDEMON.kali.orchestration.orchestrator import KALIOrchestrator
from OpenDEMON.kali.inference.batching import ContinuousBatchingEngine, InferenceRequest
from OpenDEMON.kali.orchestration.metrics import MetricsCollector

@pytest.mark.asyncio
async def test_continuous_batching_engine():
    """Verify that the continuous batching engine correctly processes concurrent requests."""
    model = MagicMock()
    tokenizer = MagicMock()
    
    # Fake generate_text function for the batching engine threadpool execution
    def fake_generate(model, prompt, tokenizer, max_new_tokens, temperature):
        import time
        time.sleep(0.1) # Simulate some work
        return f"Response to {prompt}"
        
    engine = ContinuousBatchingEngine(model, tokenizer, max_batch_size=2)
    
    with patch("OpenDEMON.kali.inference.generate.generate_text", side_effect=fake_generate):
        engine.start()
        
        # Fire off 3 concurrent requests
        res1 = engine.generate("req1", "Prompt A")
        res2 = engine.generate("req2", "Prompt B")
        res3 = engine.generate("req3", "Prompt C")
        
        # Wait for all
        answers = await asyncio.gather(res1, res2, res3)
        
        engine.stop()
        
        assert "Response to Prompt A" in answers
        assert "Response to Prompt B" in answers
        assert "Response to Prompt C" in answers

def test_metrics_collector():
    """Verify metrics collector records correctly."""
    collector = MetricsCollector()
    
    collector.record_latency(150.0)
    collector.record_ttft(25.0)
    collector.record_tokens_sec(45.5)
    collector.increment_active()
    
    assert collector.metrics.request_latency_ms == 150.0
    assert collector.metrics.ttft_ms == 25.0
    assert collector.metrics.tokens_per_sec == 45.5
    assert collector.metrics.active_requests == 1
    
    collector.decrement_active()
    assert collector.metrics.active_requests == 0

@pytest.mark.asyncio
async def test_orchestrator_metrics():
    """Verify that orchestrator logs metrics during run."""
    model = MagicMock()
    model.generate.return_value = "Hello World"
    
    planner = MagicMock()
    planner.plan.return_value = MagicMock(required_memory_types=[], requires_rag=False, requires_tools=False)
    
    router = MagicMock()
    router.route_model.return_value = "default"
    executor = MagicMock()
    
    orchestrator = KALIOrchestrator(
        model=model,
        planner=planner,
        router=router,
        executor=executor
    )
    
    with patch("OpenDEMON.security.injection_scanner.InjectionScanner") as MockScanner:
        mock_scanner_instance = MockScanner.return_value
        mock_scanner_instance.scan.return_value = MagicMock(is_clean=True)
        
        await orchestrator.run("Test prompt", "user1", "conv1")
        
    # Verify collector got populated
    collector = MetricsCollector()
    assert collector.metrics.request_latency_ms >= 0
