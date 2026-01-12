"""
Configuration for Prometheus endurance (soak) tests.

This module defines configuration classes for endurance tests that
verify Prometheus stability over extended periods.

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EnduranceTestConfig:
    """
    Base configuration for endurance tests.

    Attributes:
        prometheus_url: URL of the Prometheus instance
        timeout_seconds: Query timeout in seconds
        health_check_interval_seconds: Interval between health checks
    """

    prometheus_url: str = "http://localhost:9090"
    timeout_seconds: float = 30.0
    health_check_interval_seconds: float = 60.0


@dataclass
class SoakTestConfig(EnduranceTestConfig):
    """
    Configuration for soak (sustained load) tests.

    Requirements: 18.1, 18.2, 18.3

    Attributes:
        duration_seconds: Total duration of the soak test
        load_queries_per_second: Sustained query load
        measurement_interval_seconds: Interval between measurements
        memory_growth_threshold_percent_per_hour: Max acceptable memory growth
        disk_growth_threshold_bytes_per_hour: Max acceptable disk growth
        num_series: Number of series to maintain
        scrape_interval_seconds: Simulated scrape interval
    """

    duration_seconds: int = 86400  # 24 hours default
    load_queries_per_second: float = 10.0
    measurement_interval_seconds: int = 300  # 5 minutes
    memory_growth_threshold_percent_per_hour: float = 1.0
    disk_growth_threshold_bytes_per_hour: int = 100_000_000  # 100MB
    num_series: int = 10000
    scrape_interval_seconds: float = 15.0


@dataclass
class StabilityMonitorConfig(EnduranceTestConfig):
    """
    Configuration for stability monitoring during endurance tests.

    Requirements: 18.4, 18.5, 18.6, 18.7

    Attributes:
        compaction_check_interval_seconds: Interval to check compaction
        query_performance_check_interval_seconds: Interval to check query perf
        degradation_threshold_percent: Max acceptable performance degradation
        baseline_measurement_duration_seconds: Duration for baseline measurement
        min_compaction_cycles: Minimum compaction cycles to verify
        latency_degradation_threshold_percent: Max latency increase allowed
    """

    compaction_check_interval_seconds: int = 600  # 10 minutes
    query_performance_check_interval_seconds: int = 300  # 5 minutes
    degradation_threshold_percent: float = 10.0
    baseline_measurement_duration_seconds: int = 300  # 5 minutes
    min_compaction_cycles: int = 3
    latency_degradation_threshold_percent: float = 20.0
