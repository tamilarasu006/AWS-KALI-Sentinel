import time
import psutil
from typing import Dict, Any

class MetricsCollector:
    """Collects low-level performance metrics for KALI."""
    def __init__(self):
        self._start_time = None
        self._end_time = None
        self._tokens_processed = 0
        self._tokens_generated = 0

    def start_timer(self):
        self._start_time = time.perf_counter()

    def stop_timer(self):
        self._end_time = time.perf_counter()

    def record_tokens(self, processed: int = 0, generated: int = 0):
        self._tokens_processed = processed
        self._tokens_generated = generated

    def get_latency(self) -> float:
        if self._start_time is None or self._end_time is None:
            return 0.0
        return self._end_time - self._start_time

    def get_tokens_per_sec(self) -> float:
        latency = self.get_latency()
        if latency <= 0:
            return 0.0
        return (self._tokens_processed + self._tokens_generated) / latency

    def get_prompt_processing_speed(self) -> float:
        latency = self.get_latency()
        if latency <= 0:
            return 0.0
        return self._tokens_processed / latency

    def get_generation_speed(self) -> float:
        latency = self.get_latency()
        if latency <= 0:
            return 0.0
        return self._tokens_generated / latency

    def get_memory_usage(self) -> float:
        """Returns memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def collect_all(self) -> Dict[str, float]:
        return {
            "latency": self.get_latency(),
            "tokens_per_sec": self.get_tokens_per_sec(),
            "prompt_processing_speed": self.get_prompt_processing_speed(),
            "generation_speed": self.get_generation_speed(),
            "memory_usage": self.get_memory_usage(),
        }
