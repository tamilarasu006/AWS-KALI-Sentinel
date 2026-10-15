import asyncio
import time
import random
from .metrics import LoadMetrics

class LoadRunner:
    def __init__(self, concurrency):
        self.concurrency = concurrency
        
    async def simulate_user(self, metrics, scenario):
        start = time.time()
        # Simulated Network and Database IO delays
        await asyncio.sleep(random.uniform(0.1, 0.4))
        
        # Simulate Model Inference bound by CPU local mock
        latency = (time.time() - start) + random.uniform(0.5, 1.2)
        success = random.random() > 0.05  # 5% failure rate simulated due to pool timeouts
        metrics.add(latency, success)
        
    async def execute(self):
        metrics = LoadMetrics()
        tasks = [self.simulate_user(metrics, "chat") for _ in range(self.concurrency)]
        await asyncio.gather(*tasks)
        return metrics.compute()\n