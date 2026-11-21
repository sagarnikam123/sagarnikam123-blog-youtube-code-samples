"""
Data models for Prometheus endurance (soak) testing.

This module defines the core data structures used for endurance tests
including stability metrics and degradation tracking.

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class StabilityStatus(Enum):
    """Status of system stability during endurance tests."""

    STABLE = "stable"
    DEGRADING = "degrading"
    UNSTABLE = "unstable"
    FAILED = "failed"


class DegradationType(Enum):
    """Types of degradation detected during endurance tests."""

    NONE = "none"
    MEMORY_LEAK = "memory_leak"
    DISK_GROWTH = "disk_growth"
    LATENCY_INCREASE = "latency_increase"
    COMPACTION_FAILURE = "compaction_failure"
    QUERY_DEGRADATION = "query_degradation"
    SCRAPE_DEGRADATION = "scrape_degradation"


@dataclass
class ResourceSnapshot:
    """
    A snapshot of resource usage at a point in time.

    Requirements: 18.2, 18.3

    Attributes:
        timestamp: When the snapshot was taken
        memory_bytes: Memory usage in bytes
        memory_percent: Memory usage as percentage
        disk_bytes: Disk usage in bytes
        cpu_percent: CPU utilization percentage
        active_series: Number of active time series
        samples_ingested: Total samples ingested
        goroutines: Number of goroutines (Go runtime)
    """

    timestamp: datetime = field(default_factory=datetime.utcnow)
    memory_bytes: float = 0.0
    memory_percent: float = 0.0
    disk_bytes: float = 0.0
    cpu_percent: float = 0.0
    active_series: int = 0
    samples_ingested: int = 0
    goroutines: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "memory_bytes": round(self.memory_bytes, 0),
            "memory_percent": round(self.memory_percent, 2),
            "disk_bytes": round(self.disk_bytes, 0),
            "cpu_percent": round(self.cpu_percent, 2),
            "active_series": self.active_series,
            "samples_ingested": self.samples_ingested,
            "goroutines": self.goroutines,
        }


@dataclass
class PerformanceSnapshot:
    """
    A snapshot of query performance at a point in time.

    Requirements: 18.5, 18.6

    Attributes:
        timestamp: When the snapshot was taken
        query_latency_p50_ms: 50th percentile query latency
        query_latency_p90_ms: 90th percentile query latency
        query_latency_p99_ms: 99th percentile query latency
        query_success_rate: Percentage of successful queries
        scrape_duration_avg_ms: Average scrape duration
        scrape_success_rate: Percentage of successful scrapes
    """

    timestamp: datetime = field(default_factory=datetime.utcnow)
    query_latency_p50_ms: float = 0.0
    query_latency_p90_ms: float = 0.0
    query_latency_p99_ms: float = 0.0
    query_success_rate: float = 100.0
    scrape_duration_avg_ms: float = 0.0
    scrape_success_rate: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "query_latency_p50_ms": round(self.query_latency_p50_ms, 2),
            "query_latency_p90_ms": round(self.query_latency_p90_ms, 2),
            "query_latency_p99_ms": round(self.query_latency_p99_ms, 2),
            "query_success_rate": round(self.query_success_rate, 2),
            "scrape_duration_avg_ms": round(self.scrape_duration_avg_ms, 2),
            "scrape_success_rate": round(self.scrape_success_rate, 2),
        }


@dataclass
class CompactionInfo:
    """
    Information about TSDB compaction cycles.

    Requirements: 18.4

    Attributes:
        timestamp: When the info was collected
        compactions_total: Total number of compactions
        compaction_duration_seconds: Duration of last compaction
        compaction_failed: Whether last compaction failed
        head_chunks: Number of chunks in head block
        head_series: Number of series in head block
    """

    timestamp: datetime = field(default_factory=datetime.utcnow)
    compactions_total: int = 0
    compaction_duration_seconds: float = 0.0
    compaction_failed: bool = False
    head_chunks: int = 0
    head_series: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "compactions_total": self.compactions_total,
            "compaction_duration_seconds": round(self.compaction_duration_seconds, 2),
            "compaction_failed": self.compaction_failed,
            "head_chunks": self.head_chunks,
            "head_series": self.head_series,
        }


@dataclass
class DegradationEvent:
    """
    Represents a detected degradation event.

    Requirements: 18.6, 18.7

    Attributes:
        timestamp: When the degradation was detected
        degradation_type: Type of degradation
        severity: Severity level (0-100)
        description: Human-readable description
        baseline_value: The baseline value for comparison
        current_value: The current value showing degradation
        threshold: The threshold that was exceeded
    """

    timestamp: datetime = field(default_factory=datetime.utcnow)
    degradation_type: DegradationType = DegradationType.NONE
    severity: float = 0.0
    description: str = ""
    baseline_value: float = 0.0
    current_value: float = 0.0
    threshold: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "degradation_type": self.degradation_type.value,
            "severity": round(self.severity, 2),
            "description": self.description,
            "baseline_value": round(self.baseline_value, 4),
            "current_value": round(self.current_value, 4),
            "threshold": round(self.threshold, 4),
        }


@dataclass
class SoakTestDataPoint:
    """
    A single measurement during soak testing.

    Requirements: 18.1, 18.2, 18.3

    Attributes:
        timestamp: When the measurement was taken
        elapsed_hours: Hours since test start
        resources: Resource usage snapshot
        performance: Performance metrics snapshot
        compaction: Compaction information
        is_stable: Whether the system is stable
        degradation_events: Any degradation events detected
    """

    timestamp: datetime = field(default_factory=datetime.utcnow)
    elapsed_hours: float = 0.0
    resources: ResourceSnapshot = field(default_factory=ResourceSnapshot)
    performance: PerformanceSnapshot = field(default_factory=PerformanceSnapshot)
    compaction: Optional[CompactionInfo] = None
    is_stable: bool = True
    degradation_events: list[DegradationEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "elapsed_hours": round(self.elapsed_hours, 2),
            "resources": self.resources.to_dict(),
            "performance": self.performance.to_dict(),
            "compaction": self.compaction.to_dict() if self.compaction else None,
            "is_stable": self.is_stable,
            "degradation_events": [e.to_dict() for e in self.degradation_events],
        }


@dataclass
class StabilityMetrics:
    """
    Aggregated stability metrics over the test duration.

    Requirements: 18.7

    Attributes:
        memory_growth_rate_bytes_per_hour: Rate of memory growth
        disk_growth_rate_bytes_per_hour: Rate of disk growth
        latency_trend_percent_per_hour: Latency change rate
        compaction_success_rate: Percentage of successful compactions
        overall_stability_score: 0-100 stability score
        degradation_count: Number of degradation events
    """

    memory_growth_rate_bytes_per_hour: float = 0.0
    disk_growth_rate_bytes_per_hour: float = 0.0
    latency_trend_percent_per_hour: float = 0.0
    compaction_success_rate: float = 100.0
    overall_stability_score: float = 100.0
    degradation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "memory_growth_rate_bytes_per_hour": round(
                self.memory_growth_rate_bytes_per_hour, 2
            ),
            "disk_growth_rate_bytes_per_hour": round(
                self.disk_growth_rate_bytes_per_hour, 2
            ),
            "latency_trend_percent_per_hour": round(
                self.latency_trend_percent_per_hour, 4
            ),
            "compaction_success_rate": round(self.compaction_success_rate, 2),
            "overall_stability_score": round(self.overall_stability_score, 2),
            "degradation_count": self.degradation_count,
        }
