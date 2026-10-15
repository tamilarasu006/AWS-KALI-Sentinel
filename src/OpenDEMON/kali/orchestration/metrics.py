"""KALI Production Metrics and Telemetry."""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import psutil
import torch

logger = logging.getLogger("DEMON.kali.metrics")

@dataclass
class KALIMetrics:
    request_latency_ms: float = 0.0
    ttft_ms: float = 0.0
    tokens_per_sec: float = 0.0
    gpu_memory_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    ram_usage_mb: float = 0.0
    model_load_time_ms: float = 0.0
    rag_latency_ms: float = 0.0
    database_latency_ms: float = 0.0
    active_requests: int = 0
    
class MetricsCollector:
    """Collects and reports real-time metrics for KALI optimization."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsCollector, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
        
    def _init(self):
        self.metrics = KALIMetrics()
        self._active_requests = 0
        
    def increment_active(self):
        self._active_requests += 1
        self.metrics.active_requests = self._active_requests
        
    def decrement_active(self):
        self._active_requests = max(0, self._active_requests - 1)
        self.metrics.active_requests = self._active_requests
        
    def update_hardware_stats(self):
        self.metrics.cpu_usage_percent = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        self.metrics.ram_usage_mb = mem.used / (1024 * 1024)
        
        if torch.cuda.is_available():
            self.metrics.gpu_memory_mb = torch.cuda.memory_allocated() / (1024 * 1024)
            
    def record_ttft(self, ms: float):
        self.metrics.ttft_ms = ms
        
    def record_latency(self, ms: float):
        self.metrics.request_latency_ms = ms
        
    def record_tokens_sec(self, tps: float):
        self.metrics.tokens_per_sec = tps
        
    def record_rag_latency(self, ms: float):
        self.metrics.rag_latency_ms = ms
        
    def log_summary(self, session_id: str):
        """Dump the current metrics to the logger for monitoring."""
        self.update_hardware_stats()
        logger.info(
            f"KALI Metrics [Session {session_id}]: "
            f"Latency={self.metrics.request_latency_ms:.2f}ms, "
            f"TTFT={self.metrics.ttft_ms:.2f}ms, "
            f"TPS={self.metrics.tokens_per_sec:.2f}, "
            f"RAG={self.metrics.rag_latency_ms:.2f}ms, "
            f"Active={self.metrics.active_requests}, "
            f"GPU_Mem={self.metrics.gpu_memory_mb:.2f}MB, "
            f"RAM={self.metrics.ram_usage_mb:.2f}MB, "
            f"CPU={self.metrics.cpu_usage_percent:.1f}%"
        )
