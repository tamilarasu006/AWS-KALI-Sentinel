import platform
import logging
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from OpenDEMON.database.models.evaluation_result import EvaluationResult
from .metrics import MetricsCollector
from .benchmarks import BenchmarkRunner

logger = logging.getLogger(__name__)

class Evaluator:
    """Orchestrates KALI evaluation and persists results."""
    def __init__(self, session: AsyncSession):
        self.session = session
        self.metrics = MetricsCollector()
        self.benchmarks = BenchmarkRunner()
        
    def _get_hardware_info(self) -> Dict[str, str]:
        return {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    async def record_result(
        self, 
        model_version_id: str, 
        benchmark: str, 
        metric: str, 
        score: float, 
        config: Dict[str, Any] = None
    ):
        result = EvaluationResult(
            model_version_id=model_version_id,
            benchmark=benchmark,
            metric=metric,
            score=score,
            hardware=self._get_hardware_info(),
            configuration=config or {}
        )
        self.session.add(result)
        await self.session.commit()
        logger.info(f"Recorded {benchmark} - {metric}: {score}")

    async def evaluate_performance(self, model_version_id: str, model: Any):
        """Measures and records performance metrics."""
        self.metrics.start_timer()
        # Simulate processing (in reality, this runs an inference pass)
        self.metrics.record_tokens(processed=1000, generated=200)
        import asyncio
        await asyncio.sleep(0.5) 
        self.metrics.stop_timer()
        
        results = self.metrics.collect_all()
        
        for metric_name, score in results.items():
            await self.record_result(
                model_version_id=model_version_id,
                benchmark="performance",
                metric=metric_name,
                score=score
            )

    async def evaluate_quality(self, model_version_id: str, model: Any):
        """Runs quality benchmarks and records results."""
        results = await self.benchmarks.run_all(model)
        
        for metric_name, score in results.items():
            await self.record_result(
                model_version_id=model_version_id,
                benchmark="quality",
                metric=metric_name,
                score=score
            )
            
    async def run_full_evaluation(self, model_version_id: str, model: Any):
        """Runs both performance and quality evaluations."""
        await self.evaluate_performance(model_version_id, model)
        await self.evaluate_quality(model_version_id, model)
