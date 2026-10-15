import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from OpenDEMON.kali.evaluation.metrics import MetricsCollector
from OpenDEMON.kali.evaluation.benchmarks import BenchmarkRunner
from OpenDEMON.kali.evaluation.evaluator import Evaluator
from OpenDEMON.kali.evaluation.regression import RegressionChecker

@pytest.mark.asyncio
async def test_metrics_collector():
    metrics = MetricsCollector()
    metrics.start_timer()
    await asyncio.sleep(0.1)
    metrics.stop_timer()
    metrics.record_tokens(10, 20)
    
    latency = metrics.get_latency()
    assert latency > 0
    assert metrics.get_tokens_per_sec() > 0
    assert metrics.get_prompt_processing_speed() > 0
    assert metrics.get_generation_speed() > 0
    assert metrics.get_memory_usage() > 0

@pytest.mark.asyncio
async def test_benchmark_runner():
    runner = BenchmarkRunner()
    model = MagicMock()
    
    results = await runner.run_all(model)
    assert "exact_match" in results
    assert "instruction_following" in results
    assert "context_retrieval" in results
    assert "rag_accuracy" in results
    assert results["exact_match"] == 0.95

@pytest.mark.asyncio
async def test_evaluator():
    mock_session = AsyncMock()
    evaluator = Evaluator(session=mock_session)
    model = MagicMock()
    
    await evaluator.evaluate_performance("version-123", model)
    assert mock_session.add.called
    assert mock_session.commit.called
    
    mock_session.reset_mock()
    await evaluator.evaluate_quality("version-123", model)
    assert mock_session.add.called
    assert mock_session.commit.called
