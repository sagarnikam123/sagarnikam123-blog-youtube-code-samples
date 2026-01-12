"""
Configuration for Prometheus regression tests.

This module defines configuration structures for regression testing
including version comparison settings and test parameters.

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RegressionTestConfig:
    """Configuration for regression tests.

    Attributes:
        baseline_version: Baseline Prometheus version to compare against
        baseline_url: URL of the baseline Prometheus instance
        target_version: Target Prometheus version being tested
        target_url: URL of the target Prometheus instance
        queries: List of PromQL queries to compare
        performance_threshold_percent: Acceptable performance difference
        value_tolerance: Numeric tolerance for value comparison
        timeout_seconds: Timeout for API requests
    """

    baseline_version: str = "v3.4.0"
    baseline_url: str = "http://localhost:9090"
    target_version: str = "v3.5.0"
    target_url: str = "http://localhost:9091"
    queries: list[str] = field(default_factory=list)
    performance_threshold_percent: float = 10.0
    value_tolerance: float = 0.001
    timeout_seconds: float = 30.0

    def __post_init__(self):
        """Set default queries if none provided."""
        if not self.queries:
            self.queries = self.default_queries()

    @staticmethod
    def default_queries() -> list[str]:
        """Get default queries for regression testing."""
        return [
            # Basic metric queries
            "up",
            "prometheus_build_info",
            "prometheus_tsdb_head_series",
            "prometheus_engine_query_duration_seconds_count",

            # Aggregation queries
            "sum(up)",
            "count(up)",
            "avg(prometheus_engine_query_duration_seconds_sum)",

            # Rate queries
            "rate(prometheus_http_requests_total[5m])",
            "irate(prometheus_http_requests_total[5m])",

            # Complex queries
            "sum by (handler) (rate(prometheus_http_requests_total[5m]))",
            "topk(5, prometheus_http_requests_total)",
            "histogram_quantile(0.99, rate(prometheus_http_request_duration_seconds_bucket[5m]))",
        ]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegressionTestConfig":
        """Create configuration from dictionary."""
        return cls(
            baseline_version=data.get("baseline_version", "v3.4.0"),
            baseline_url=data.get("baseline_url", "http://localhost:9090"),
            target_version=data.get("target_version", "v3.5.0"),
            target_url=data.get("target_url", "http://localhost:9091"),
            queries=data.get("queries", []),
            performance_threshold_percent=data.get("performance_threshold_percent", 10.0),
            value_tolerance=data.get("value_tolerance", 0.001),
            timeout_seconds=data.get("timeout_seconds", 30.0),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "baseline_version": self.baseline_version,
            "baseline_url": self.baseline_url,
            "target_version": self.target_version,
            "target_url": self.target_url,
            "queries": self.queries,
            "performance_threshold_percent": self.performance_threshold_percent,
            "value_tolerance": self.value_tolerance,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class RuleComparisonConfig:
    """Configuration for rule comparison tests.

    Attributes:
        alerting_rules: List of alerting rule names to compare
        recording_rules: List of recording rule names to compare
        include_all_rules: Whether to compare all discovered rules
    """

    alerting_rules: list[str] = field(default_factory=list)
    recording_rules: list[str] = field(default_factory=list)
    include_all_rules: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuleComparisonConfig":
        """Create configuration from dictionary."""
        return cls(
            alerting_rules=data.get("alerting_rules", []),
            recording_rules=data.get("recording_rules", []),
            include_all_rules=data.get("include_all_rules", True),
        )


@dataclass
class ConfigCompatibilityConfig:
    """Configuration for configuration compatibility tests.

    Attributes:
        scrape_configs: List of scrape config names to test
        remote_write_configs: List of remote write config names to test
        test_all_configs: Whether to test all discovered configs
    """

    scrape_configs: list[str] = field(default_factory=list)
    remote_write_configs: list[str] = field(default_factory=list)
    test_all_configs: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfigCompatibilityConfig":
        """Create configuration from dictionary."""
        return cls(
            scrape_configs=data.get("scrape_configs", []),
            remote_write_configs=data.get("remote_write_configs", []),
            test_all_configs=data.get("test_all_configs", True),
        )


@dataclass
class PerformanceComparisonConfig:
    """Configuration for performance comparison tests.

    Attributes:
        metrics: List of performance metrics to compare
        threshold_percent: Acceptable difference threshold
        iterations: Number of iterations for benchmarks
    """

    metrics: list[str] = field(default_factory=list)
    threshold_percent: float = 10.0
    iterations: int = 10

    def __post_init__(self):
        """Set default metrics if none provided."""
        if not self.metrics:
            self.metrics = [
                "query_latency_p50",
                "query_latency_p90",
                "query_latency_p99",
                "scrape_duration_avg",
                "memory_usage_bytes",
                "cpu_usage_percent",
            ]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PerformanceComparisonConfig":
        """Create configuration from dictionary."""
        return cls(
            metrics=data.get("metrics", []),
            threshold_percent=data.get("threshold_percent", 10.0),
            iterations=data.get("iterations", 10),
        )
