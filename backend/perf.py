"""
Performance instrumentation for the troubleshooting engine.

Provides monotonic-clock timers and request-level metrics collection.
All timing uses time.monotonic() for accuracy (immune to wall-clock drift).
"""
import time
from typing import Dict, List, Optional
from contextlib import contextmanager


class RequestMetrics:
    """Collects timing and call-count metrics for a single request."""

    __slots__ = (
        "_timings", "_counts", "_start", "_path_taken",
    )

    def __init__(self):
        self._timings: Dict[str, float] = {}
        self._counts: Dict[str, int] = {}
        self._start: float = time.monotonic()
        self._path_taken: str = "unknown"

    # ── Timing helpers ─────────────────────────────────────────

    @contextmanager
    def measure(self, label: str):
        """Context manager to measure elapsed time for a labelled section."""
        t0 = time.monotonic()
        try:
            yield
        finally:
            elapsed_ms = (time.monotonic() - t0) * 1000.0
            self._timings[label] = self._timings.get(label, 0.0) + elapsed_ms

    def record_time(self, label: str, ms: float):
        """Manually record a timing measurement."""
        self._timings[label] = self._timings.get(label, 0.0) + ms

    # ── Counter helpers ────────────────────────────────────────

    def increment(self, label: str, n: int = 1):
        """Increment a named counter."""
        self._counts[label] = self._counts.get(label, 0) + n

    # ── Path tracking ──────────────────────────────────────────

    def set_path(self, path: str):
        """Record which request processing path was taken."""
        self._path_taken = path

    # ── Output ─────────────────────────────────────────────────

    @property
    def total_ms(self) -> float:
        return (time.monotonic() - self._start) * 1000.0

    def summary(self) -> Dict:
        """Return a compact summary dict suitable for logging/response headers."""
        return {
            "path": self._path_taken,
            "total_ms": round(self.total_ms, 1),
            "timings_ms": {k: round(v, 1) for k, v in self._timings.items()},
            "counts": dict(self._counts),
        }


# ── Global aggregate stats (optional, lightweight) ─────────────

class _AggregateStats:
    """Simple in-process aggregate statistics collector. Not thread-safe
    in the strictest sense, but acceptable for a single-process hackathon
    prototype where atomicity of individual counter increments is not
    critical."""

    __slots__ = ("_request_count", "_total_ms", "_path_counts",
                 "_laya_calls", "_db_queries", "_llm_calls")

    def __init__(self):
        self._request_count: int = 0
        self._total_ms: float = 0.0
        self._path_counts: Dict[str, int] = {}
        self._laya_calls: int = 0
        self._db_queries: int = 0
        self._llm_calls: int = 0

    def record(self, metrics: RequestMetrics):
        self._request_count += 1
        self._total_ms += metrics.total_ms
        path = metrics._path_taken
        self._path_counts[path] = self._path_counts.get(path, 0) + 1
        self._laya_calls += metrics._counts.get("laya_calls", 0)
        self._db_queries += metrics._counts.get("kb_searches", 0)
        self._llm_calls += metrics._counts.get("llm_calls", 0)

    def summary(self) -> Dict:
        avg = (self._total_ms / self._request_count) if self._request_count else 0
        return {
            "total_requests": self._request_count,
            "avg_latency_ms": round(avg, 1),
            "path_distribution": dict(self._path_counts),
            "total_laya_calls": self._laya_calls,
            "total_db_queries": self._db_queries,
            "total_llm_calls": self._llm_calls,
        }


aggregate_stats = _AggregateStats()
