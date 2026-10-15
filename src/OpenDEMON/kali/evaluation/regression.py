from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models.evaluation_result import EvaluationResult

class RegressionChecker:
    """Checks for regressions against previous model versions."""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_regression(self, benchmark: str, metric: str, current_score: float) -> bool:
        """
        Returns True if there is a significant regression compared to historical averages.
        """
        stmt = select(EvaluationResult).where(
            EvaluationResult.benchmark == benchmark,
            EvaluationResult.metric == metric
        ).order_by(EvaluationResult.timestamp.desc()).limit(5)
        
        result = await self.session.execute(stmt)
        historical_results = result.scalars().all()
        
        if not historical_results:
            return False # No history to regress against
            
        avg_historical = sum(r.score for r in historical_results) / len(historical_results)
        
        # Determine if higher is better based on metric name
        lower_is_better = metric in ["latency", "memory_usage"]
        
        margin = 0.1 # 10% threshold
        
        if lower_is_better:
            return current_score > avg_historical * (1 + margin)
        else:
            return current_score < avg_historical * (1 - margin)
