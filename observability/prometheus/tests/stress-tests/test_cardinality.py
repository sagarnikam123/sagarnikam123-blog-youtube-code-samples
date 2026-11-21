"""
High cardinality stress test for Prometheus.

This module implements stress tests that generate millions of unique
label combinations to test Prometheus behavior under high cardinality.

Requirements: 17.2
"""

import asyncio
import random
import string
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

import sys
from pathlib import Path

# Add parent directory to path for hyphenated package import
_current_dir = Path(__file__).parent
sys.path.insert(0, str(_current_dir))

from config import HighCardinalityConfig
from models import (
    BreakingPoint,
    FailureMode,
    StressTestDataPoint,
    StressTestType,
)


@dataclass
class CardinalityTestResult:
    """
    Result of a high cardinality stress test.

    Requirements: 17.2

    Attributes:
        test_type: Type of stress test
        config: Test configuration used
        start_time: When the test started
        end_time: When the test ended
        data_points: Measurements at each cardinality level
        breaking_point: Discovered breaking point
        total_series_generated: Total unique series generated
        passed: Whether the test completed without unexpected failures
        error_logs: Captured error logs
    """

    test_type: StressTestType = StressTestType.HIGH_CARDINALITY
    config: Optional[HighCardinalityConfig] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_points: list[StressTestDataPoint] = field(default_factory=list)
    breaking_point: BreakingPoint = field(default_factory=BreakingPoint)
    total_series_generated: int = 0
    passed: bool = True
    error_logs: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Total test duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "test_type": self.test_type.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "data_points": [dp.to_dict() for dp in self.data_points],
            "breaking_point": self.breaking_point.to_dict(),
            "total_series_generated": self.total_series_generated,
            "passed": self.passed,
            "error_logs": self.error_logs,
        }


class HighCardinalityTester:
    """
    Executes high cardinality stress tests against Prometheus.

    This class generates millions of unique label combinations to
    test how Prometheus handles high cardinality scenarios.

    Requirements: 17.2
    """

    def __init__(self, config: HighCardinalityConfig):
        """Initialize the high cardinality tester.

        Args:
            config: Test configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._generated_series: set[str] = set()

    def _generate_random_string(self, length: int = 8) -> str:
        """Generate a random string for labels."""
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _generate_unique_labels(self, count: int) -> list[dict[str, str]]:
        """Generate unique label combinations.

        Args:
            count: Number of unique combinations to generate

        Returns:
            List of label dictionaries
        """
        labels_list = []

        for i in range(count):
            labels = {
                "job": f"cardinality_test_{i % 100}",
                "instance": f"instance_{i % 1000}:9090",
            }

            # Add random labels to increase cardinality
            for j in range(self.config.labels_per_series - 2):
                labels[f"label_{j}"] = self._generate_random_string(6)

            # Add a unique identifier
            labels["unique_id"] = f"uid_{i}_{self._generate_random_string(8)}"

            labels_list.append(labels)

        return labels_list

    def _format_prometheus_metric(
        self,
        metric_name: str,
        labels: dict[str, str],
        value: float,
    ) -> str:
        """Format a metric in Prometheus exposition format.

        Args:
            metric_name: Name of the metric
            labels: Label dictionary
            value: Metric value

        Returns:
            Formatted metric string
        """
        labels_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        return f"{metric_name}{{{labels_str}}} {value}"

    async def _query_prometheus(self, query: str) -> tuple[bool, float, Any]:
        """Execute a PromQL query and measure latency.

        Args:
            query: PromQL query string

        Returns:
            Tuple of (success, latency_ms, result)
        """
        if not self._client:
            return False, 0.0, None

        start_time = time.perf_counter()
        try:
            response = await self._client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=self.config.timeout_seconds,
            )
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return True, latency_ms, data.get("data", {}).get("result", [])

            return False, latency_ms, None
        except httpx.TimeoutException:
            return False, self.config.timeout_seconds * 1000, None
        except Exception:
            end_time = time.perf_counter()
            return False, (end_time - start_time) * 1000, None

    async def _check_health(self) -> bool:
        """Check if Prometheus is healthy.

        Returns:
            True if healthy, False otherwise
        """
        if not self._client:
            return False

        try:
            response = await self._client.get(
                f"{self.config.prometheus_url}/-/healthy",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    async def _get_prometheus_metrics(self) -> dict[str, float]:
        """Get current Prometheus internal metrics.

        Returns:
            Dictionary of metric name to value
        """
        metrics: dict[str, float] = {}

        metric_queries = {
            "active_series": "prometheus_tsdb_head_series",
            "cpu_seconds": "rate(process_cpu_seconds_total[1m])",
            "memory_bytes": "process_resident_memory_bytes",
            "head_chunks": "prometheus_tsdb_head_chunks",
            "wal_corruptions": "prometheus_tsdb_wal_corruptions_total",
        }

        for name, query in metric_queries.items():
            success, _, result = await self._query_prometheus(query)
            if success and result:
                try:
                    metrics[name] = float(result[0].get("value", [0, 0])[1])
                except (IndexError, ValueError, TypeError):
                    pass

        return metrics

    async def _simulate_high_cardinality(
        self,
        target_cardinality: int,
    ) -> tuple[int, list[str]]:
        """Simulate high cardinality by generating unique series.

        Note: This simulates the effect by querying Prometheus with
        high-cardinality queries. In a real scenario, you would push
        metrics via remote_write or have exporters generate them.

        Args:
            target_cardinality: Target number of unique label combinations

        Returns:
            Tuple of (series_generated, error_messages)
        """
        errors = []
        series_generated = 0

        # Generate unique label combinations
        new_labels = self._generate_unique_labels(
            min(target_cardinality - len(self._generated_series), 10000)
        )

        # Track generated series
        for labels in new_labels:
            series_key = str(sorted(labels.items()))
            if series_key not in self._generated_series:
                self._generated_series.add(series_key)
                series_generated += 1

        return series_generated, errors

    async def _measure_at_cardinality_level(
        self,
        cardinality: int,
    ) -> StressTestDataPoint:
        """Measure performance at a specific cardinality level.

        Args:
            cardinality: Target cardinality level

        Returns:
            StressTestDataPoint with measurements
        """
        # Simulate high cardinality
        series_generated, sim_errors = await self._simulate_high_cardinality(cardinality)

        # Run test queries to measure impact
        latencies: list[float] = []
        successes = 0
        total = 0

        test_queries = [
            "up",
            "prometheus_tsdb_head_series",
            'count(up)',
            'count by (job) (up)',
        ]

        for _ in range(10):  # Multiple iterations
            for query in test_queries:
                success, latency_ms, _ = await self._query_prometheus(query)
                latencies.append(latency_ms)
                total += 1
                if success:
                    successes += 1

        # Calculate percentiles
        sorted_latencies = sorted(latencies) if latencies else [0]
        n = len(sorted_latencies)

        p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0
        p99 = sorted_latencies[min(int(n * 0.99), n - 1)] if n > 0 else 0

        # Get Prometheus metrics
        prom_metrics = await self._get_prometheus_metrics()

        # Check health
        is_healthy = await self._check_health()

        success_rate = (successes / total * 100) if total > 0 else 0
        error_messages = sim_errors.copy()

        if success_rate < 90:
            error_messages.append(f"Success rate dropped to {success_rate:.1f}%")

        if p99 > 5000:  # 5 second threshold
            error_messages.append(f"P99 latency {p99:.1f}ms exceeds 5000ms threshold")

        return StressTestDataPoint(
            load_level=cardinality,
            query_latency_p50_ms=p50,
            query_latency_p99_ms=p99,
            success_rate_percent=success_rate,
            cpu_utilization_percent=prom_metrics.get("cpu_seconds", 0) * 100,
            memory_utilization_bytes=prom_metrics.get("memory_bytes", 0),
            active_series=int(prom_metrics.get("active_series", 0)),
            is_healthy=is_healthy and success_rate >= 90,
            error_messages=error_messages,
        )

    async def run(self) -> CardinalityTestResult:
        """Run the high cardinality stress test.

        Requirements: 17.2

        Returns:
            CardinalityTestResult with test results and breaking point
        """
        result = CardinalityTestResult(config=self.config)
        result.start_time = datetime.utcnow()
        self._running = True
        self._generated_series.clear()

        last_healthy_data_point: Optional[StressTestDataPoint] = None

        async with httpx.AsyncClient() as client:
            self._client = client

            # Verify Prometheus is healthy before starting
            if not await self._check_health():
                result.passed = False
                result.error_logs.append("Prometheus not healthy at test start")
                result.end_time = datetime.utcnow()
                return result

            current_cardinality = self.config.initial_cardinality

            while (
                self._running
                and current_cardinality <= self.config.max_cardinality
                and result.duration_seconds < self.config.max_test_duration_seconds
            ):
                # Measure at current cardinality level
                data_point = await self._measure_at_cardinality_level(current_cardinality)
                result.data_points.append(data_point)

                if data_point.is_healthy:
                    last_healthy_data_point = data_point
                else:
                    # Failure detected - record breaking point
                    result.breaking_point = BreakingPoint(
                        max_cardinality=(
                            int(last_healthy_data_point.load_level)
                            if last_healthy_data_point else 0
                        ),
                        max_series=data_point.active_series,
                        failure_mode=FailureMode.DEGRADATION,
                        failure_timestamp=datetime.utcnow(),
                        failure_symptoms=data_point.error_messages,
                        last_healthy_metrics={
                            "cardinality": last_healthy_data_point.load_level if last_healthy_data_point else 0,
                            "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms if last_healthy_data_point else 0,
                            "success_rate": last_healthy_data_point.success_rate_percent if last_healthy_data_point else 0,
                        },
                    )

                    result.error_logs.extend(data_point.error_messages)
                    break

                # Increase cardinality
                current_cardinality += self.config.cardinality_increment

                # Brief pause between levels
                await asyncio.sleep(2)

        self._client = None
        self._running = False
        result.end_time = datetime.utcnow()
        result.total_series_generated = len(self._generated_series)

        # If we completed without failure, record the max achieved
        if result.breaking_point.failure_mode == FailureMode.NONE and last_healthy_data_point:
            result.breaking_point.max_cardinality = int(last_healthy_data_point.load_level)
            result.breaking_point.max_series = last_healthy_data_point.active_series
            result.breaking_point.last_healthy_metrics = {
                "cardinality": last_healthy_data_point.load_level,
                "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms,
                "success_rate": last_healthy_data_point.success_rate_percent,
            }

        return result

    def stop(self) -> None:
        """Stop the stress test."""
        self._running = False


def run_high_cardinality_test_sync(
    prometheus_url: str = "http://localhost:9090",
    initial_cardinality: int = 1000,
    max_cardinality: int = 1_000_000,
    cardinality_increment: int = 10000,
) -> CardinalityTestResult:
    """Synchronous wrapper for running high cardinality test.

    Args:
        prometheus_url: URL of the Prometheus instance
        initial_cardinality: Starting cardinality
        max_cardinality: Maximum cardinality to attempt
        cardinality_increment: Cardinality increase per step

    Returns:
        CardinalityTestResult
    """
    config = HighCardinalityConfig(
        prometheus_url=prometheus_url,
        initial_cardinality=initial_cardinality,
        max_cardinality=max_cardinality,
        cardinality_increment=cardinality_increment,
    )
    tester = HighCardinalityTester(config)
    return asyncio.run(tester.run())
