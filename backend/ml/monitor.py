"""Inference monitoring — tracks latency, throughput, errors.

Production-grade metrics for MLOps monitoring dashboard.
"""

import time
import statistics
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InferenceRecord:
    """Single inference event."""
    timestamp: float
    model: str
    latency: float  # seconds
    tokens: int
    endpoint: str
    success: bool
    tokens_per_sec: float = 0.0

    def __post_init__(self):
        if self.latency > 0 and self.tokens > 0:
            self.tokens_per_sec = self.tokens / self.latency


class InferenceMonitor:
    """Tracks inference metrics with a rolling window."""

    def __init__(self, max_records: int = 1000):
        self._records: deque[InferenceRecord] = deque(maxlen=max_records)
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._start_time: float = time.time()

    def log_inference(
        self,
        model: str,
        latency: float,
        tokens: int,
        endpoint: str,
        success: bool,
    ):
        """Log a single inference event."""
        record = InferenceRecord(
            timestamp=time.time(),
            model=model,
            latency=latency,
            tokens=tokens,
            endpoint=endpoint,
            success=success,
        )
        self._records.append(record)
        self._total_requests += 1
        if not success:
            self._total_errors += 1

    def get_metrics(self) -> dict:
        """Get comprehensive metrics snapshot."""
        now = time.time()
        uptime = now - self._start_time

        if not self._records:
            return {
                "total_requests": 0,
                "total_errors": 0,
                "error_rate": 0.0,
                "uptime_seconds": round(uptime, 1),
                "latency": {"p50": 0, "p95": 0, "p99": 0, "avg": 0},
                "throughput": {"tokens_per_sec_avg": 0, "requests_per_min": 0},
                "recent_records": [],
            }

        successful = [r for r in self._records if r.success]
        latencies = [r.latency for r in successful] if successful else [0]
        tps_values = [r.tokens_per_sec for r in successful if r.tokens_per_sec > 0]

        # Last 5 minutes of requests for throughput calc
        five_min_ago = now - 300
        recent_count = sum(1 for r in self._records if r.timestamp > five_min_ago)

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        return {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "error_rate": round(self._total_errors / max(self._total_requests, 1) * 100, 2),
            "uptime_seconds": round(uptime, 1),
            "latency": {
                "p50": round(sorted_latencies[n // 2] * 1000, 1) if n else 0,
                "p95": round(sorted_latencies[int(n * 0.95)] * 1000, 1) if n else 0,
                "p99": round(sorted_latencies[int(n * 0.99)] * 1000, 1) if n else 0,
                "avg": round(statistics.mean(latencies) * 1000, 1) if latencies else 0,
            },
            "throughput": {
                "tokens_per_sec_avg": round(statistics.mean(tps_values), 1) if tps_values else 0,
                "requests_per_min": round(recent_count / 5, 1) if recent_count else 0,
            },
            "recent_records": [
                {
                    "timestamp": r.timestamp,
                    "model": r.model,
                    "latency_ms": round(r.latency * 1000, 1),
                    "tokens": r.tokens,
                    "tokens_per_sec": round(r.tokens_per_sec, 1),
                    "endpoint": r.endpoint,
                    "success": r.success,
                }
                for r in list(self._records)[-20:]  # Last 20 records
            ],
        }

    def get_model_stats(self) -> dict:
        """Per-model breakdown of metrics."""
        models: dict[str, list[InferenceRecord]] = {}
        for r in self._records:
            models.setdefault(r.model, []).append(r)

        stats = {}
        for model, records in models.items():
            successful = [r for r in records if r.success]
            latencies = [r.latency for r in successful]
            stats[model] = {
                "total": len(records),
                "success": len(successful),
                "errors": len(records) - len(successful),
                "avg_latency_ms": round(statistics.mean(latencies) * 1000, 1) if latencies else 0,
                "avg_tokens_per_sec": round(
                    statistics.mean([r.tokens_per_sec for r in successful if r.tokens_per_sec > 0]), 1
                ) if any(r.tokens_per_sec > 0 for r in successful) else 0,
            }
        return stats


# Singleton
monitor = InferenceMonitor()
