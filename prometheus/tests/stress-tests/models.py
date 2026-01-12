"""
Data models for Prometheus stress testing.

This module defines the core data structures used for stress tests
including breaking point detection and failure mode tracking.

Requirements: 17.1, 17.6, 17.7
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class FailureMode(Enum):
    """Types of failure modes detected during stress tests."""

    NONE = "none"
    OOM = "out_of_memory"
    TIMEOUT = "timeout"
    QUERY_FAILURE = "query_failure"
    SCRAPE_FAILURE = "scrape_failure"
    INGESTION_FAILURE = "ingestion_failure"
    CRASH = "crash"
    DEGRADATION = "degradation"
    UNKNOWN = "unknown"


class StressTestType(Enum):
    """Types of stress tests."""

    PROGRESSIVE_LOAD = "progressive_load"
    HIGH_CARDINALITY = "high_cardinality"
    HIGH_INGESTION = "high_ingestion"
    CONCURRENT_QUERIES = "concurrent_queries"
    MEMORY_PRESSURE = "memory_pressure"


@dataclass
class BreakingPoint:
    """
    Represents the breaking point discovered during stress testing.

    Requirements: 17.6

    Attributes:
        max_series: Maximum number of series before failure
        max_ingestion_rate: Maximum samples per second before failure
        max_query_rate: Maximum queries per second before failure
        max_cardinality: Maximum label cardinality before failure
        max_concurrent_queries: Maximum concurrent queries before failure
        failure_mode: How Prometheus failed
        failure_timestamp: When the failure occurred
        failure_symptoms: Detailed symptoms of the failure
        last_healthy_metrics: Metrics from last healthy state
    """

    max_series: Optional[int] = None
    max_ingestion_rate: Optional[float] = None
    max_query_rate: Optional[float] = None
    max_cardinality: Optional[int] = None
    max_concurrent_queries: Optional[int] = None
    failure_mode: FailureMode = FailureMode.NONE
    failure_timestamp: Optional[datetime] = None
    failure_symptoms: list[str] = field(default_factory=list)
    last_healthy_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "max_series": self.max_series,
            "max_ingestion_rate": self.max_ingestion_rate,
            "max_query_rate": self.max_query_rate,
            "max_cardinality": self.max_cardinality,
            "max_concurrent_queries": self.max_concurrent_queries,
            "failure_mode": self.failure_mode.value,
            "failure_timestamp": (
                self.failure_timestamp.isoformat()
                if self.failure_timestamp else None
            ),
            "failure_symptoms": self.failure_symptoms,
            "last_healthy_metrics": self.last_healthy_metrics,
        }


@dataclass
class StressTestDataPoint:
    """
    A single measurement during stress testing.

    Attributes:
        load_level: Current load level (varies by test type)
        timestamp: When the measurement was taken
        query_latency_p50_ms: 50th percentile query latency
        query_latency_p99_ms: 99th percentile query latency
        success_rate_percent: Percentage of successful operations
        cpu_utilization_percent: CPU utilization
        memory_utilization_bytes: Memory usage in bytes
        memory_utilization_percent: Memory usage as percentage of limit
        active_series: Number of active time series
        samples_per_second: Current ingestion rate
        is_healthy: Whether Prometheus is still healthy
        error_messages: Any error messages observed
    """

    load_level: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    query_latency_p50_ms: float = 0.0
    query_latency_p99_ms: float = 0.0
    success_rate_percent: float = 100.0
    cpu_utilization_percent: float = 0.0
    memory_utilization_bytes: float = 0.0
    memory_utilization_percent: float = 0.0
    active_series: int = 0
    samples_per_second: float = 0.0
    is_healthy: bool = True
    error_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "load_level": self.load_level,
            "timestamp": self.timestamp.isoformat(),
            "query_latency_p50_ms": round(self.query_latency_p50_ms, 2),
            "query_latency_p99_ms": round(self.query_latency_p99_ms, 2),
            "success_rate_percent": round(self.success_rate_percent, 2),
            "cpu_utilization_percent": round(self.cpu_utilization_percent, 2),
            "memory_utilization_bytes": round(self.memory_utilization_bytes, 0),
            "memory_utilization_percent": round(self.memory_utilization_percent, 2),
            "active_series": self.active_series,
            "samples_per_second": round(self.samples_per_second, 2),
            "is_healthy": self.is_healthy,
            "error_messages": self.error_messages,
        }
