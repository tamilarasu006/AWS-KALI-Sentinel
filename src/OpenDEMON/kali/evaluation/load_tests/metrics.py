import time
import numpy as np

class LoadMetrics:
    def __init__(self):
        self.latencies = []
        self.errors = 0
        self.success = 0
        
    def add(self, latency, success):
        self.latencies.append(latency)
        if success:
            self.success += 1
        else:
            self.errors += 1
            
    def compute(self):
        if not self.latencies: return {}
        return {
            "p50": np.percentile(self.latencies, 50),
            "p95": np.percentile(self.latencies, 95),
            "p99": np.percentile(self.latencies, 99),
            "mean": np.mean(self.latencies),
            "total": len(self.latencies),
            "success_rate": self.success / max(1, len(self.latencies)),
            "errors": self.errors
        }\n