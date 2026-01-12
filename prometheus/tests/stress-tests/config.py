"""
Configuration for Prometheus stress tests.

This module defines configuration classes for various stress test types.

Requirements: 17.1, 17.2, 17.3, 17.4, 17.5
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StressTestConfig:
    """
    Base configuration for stress tests.

    Attributes:
        prometheus_url: URL of the Prometheus instance
        timeout_seconds: Query timeout in seconds
        health_check_interval_seconds: Interval between health checks
        max_test_duration_seconds: Maximum test duration
        memory_limit_bytes: Memory limit for OOM detection (if known)
    """

    prometheus_url: str = "http://localhost:9090"
    timeout_seconds: float = 30.0
    health_check_interval_seconds: float = 5.0
    max_test_duration_seconds: int = 3600  # 1 hour
    memory_limit_bytes: Optional[int] = None


@dataclass
class ProgressiveLoadConfig(StressTestConfig):
    """
    Configuration for progressive load stress test.

    Requirements: 17.1, 17.6

    Attributes:
        initial_load: Starting load level (e.g., queries per second)
        load_increment: How much to increase load each step
        load_increment_interval_seconds: Time between load increases
        max_load: Maximum load to attempt
        failure_threshold_success_rate: Success rate below which is failure
        failure_threshold_latency_ms: Latency above which is degradation
    """

    initial_load: float = 1.0
    load_increment: float = 5.0
    load_increment_interval_seconds: int = 30
    max_load: float = 1000.0
    failure_threshold_success_rate: float = 90.0
    failure_threshold_latency_ms: float = 5000.0


@dataclass
class HighCardinalityConfig(StressTestConfig):
    """
    Configuration for high cardinality stress test.

    Requirements: 17.2

    Attributes:
        initial_cardinality: Starting number of unique label combinations
        cardinality_increment: How much to increase cardinality each step
        max_cardinality: Maximum cardinality to attempt
        labels_per_series: Number of labels per series
        metric_name_prefix: Prefix for generated metric names
    """

    initial_cardinality: int = 1000
    cardinality_increment: int = 10000
    max_cardinality: int = 10_000_000
    labels_per_series: int = 5
    metric_name_prefix: str = "stress_test_cardinality"


@dataclass
class HighIngestionConfig(StressTestConfig):
    """
    Configuration for high ingestion rate stress test.

    Requirements: 17.3

    Attributes:
        initial_samples_per_second: Starting ingestion rate
        rate_increment: How much to increase rate each step
        max_samples_per_second: Maximum rate to attempt
        batch_size: Number of samples per batch
        num_series: Number of unique series to use
    """

    initial_samples_per_second: float = 1000.0
    rate_increment: float = 5000.0
    max_samples_per_second: float = 1_000_000.0
    batch_size: int = 1000
    num_series: int = 10000


@dataclass
class ConcurrentQueryConfig(StressTestConfig):
    """
    Configuration for concurrent query stress test.

    Requirements: 17.4

    Attributes:
        initial_concurrency: Starting number of concurrent queries
        concurrency_increment: How much to increase concurrency each step
        max_concurrency: Maximum concurrency to attempt
        query_types: Types of queries to execute
        queries_per_batch: Number of queries per measurement batch
    """

    initial_concurrency: int = 1
    concurrency_increment: int = 10
    max_concurrency: int = 500
    query_types: list[str] = field(default_factory=lambda: [
        "up",
        "prometheus_tsdb_head_series",
        'rate(prometheus_http_requests_total[5m])',
        'sum(rate(prometheus_http_requests_total[5m])) by (handler)',
        'histogram_quantile(0.99, rate(prometheus_http_request_duration_seconds_bucket[5m]))',
    ])
    queries_per_batch: int = 100


@dataclass
class MemoryPressureConfig(StressTestConfig):
    """
    Configuration for memory pressure stress test.

    Requirements: 17.5, 17.7

    Attributes:
        initial_series: Starting number of series
        series_increment: How much to increase series each step
        max_series: Maximum series to attempt
        labels_per_series: Number of labels per series
        sample_interval_seconds: Interval between sample pushes
        memory_warning_threshold_percent: Memory usage warning threshold
        memory_critical_threshold_percent: Memory usage critical threshold
    """

    initial_series: int = 10000
    series_increment: int = 50000
    max_series: int = 50_000_000
    labels_per_series: int = 10
    sample_interval_seconds: float = 1.0
    memory_warning_threshold_percent: float = 80.0
    memory_critical_threshold_percent: float = 95.0
