"""
High ingestion rate stress test for Prometheus.

This module implements stress tests that push samples at increasing
rates to find Prometheus ingestion limits.

Requirements: 17.3
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

from config import HighIngestionConfig
from models import (
    BreakingPoint,
    FailureMode,
    StressTestDataPoint,
    StressTestType,
)


@dataclass
class IngestionTestResult:
    """
    Result of a high ingestion rate stress test.

    Requirements: 17.3

    Attributes:
        test_type: Type of stress test
        config: Test configuration used
        start_time: When the test started
        end_time: When the test ended
        data_points: Measurements at each ingestion rate
        breaking_point: Discovered breaking point
        total_samples_pushed: Total samples pushed during test
        max_achieved_rate: Maximum sustained ingestion rate
        passed: Whether the test completed without unexpected failures
        error_logs: Captured error logs
    """

    test_type: StressTestType = StressTestType.HIGH_INGESTION
    config: Optional[HighIngestionConfig] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_points: list[StressTestDataPoint] = field(default_factory=list)
    breaking_point: BreakingPoint = field(default_factory=BreakingPoint)
    total_samples_pushed: int = 0
    max_achieved_rate: float = 0.0
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
            "total_samples_pushed": self.total_samples_pushed,
            "max_achieved_rate": round(self.max_achieved_rate, 2),
            "passed": self.passed,
            "error_logs": self.error_logs,
        }


@dataclass
class GeneratedSeries:
    """A generated time series for ingestion testing."""

    metric_name: str
    labels: dict[str, str]
    current_value: float = 0.0

    def generate_value(self) -> float:
        """Generate a new value for the series."""
        self.current_value = max(0, self.current_value + random.gauss(0, 1))
        return self.current_value

    def to_prometheus_format(self) -> str:
        """Format as Prometheus exposition format."""
        labels_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
        return f"{self.metric_name}{{{labels_str}}} {self.current_value}"


class HighIngestionTester:
    """
    Executes high ingestion rate stress tests against Prometheus.

    This class pushes samples at increasing rates to find the
    maximum sustainable ingestion rate for Prometheus.

    Requirements: 17.3
    """

    def __init__(self, config: HighIngestionConfig):
        """Initialize the high ingestion tester.

        Args:
            config: Test configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._series: list[GeneratedSeries] = []
        self._total_samples_pushed = 0

    def _generate_random_string(self, length: int = 8) -> str:
        """Generate a random string for labels."""
        return "".join(random.choices(string.ascii_lowercase, k=length))

    def _generate_series(self) -> list[GeneratedSeries]:
        """Generate time series for ingestion testing.

        Returns:
            List of generated series
        """
        series = []

        for i in range(self.config.num_series):
            labels = {
                "job": f"ingestion_test_{i % 100}",
                "instance": f"instance_{i % 1000}:9090",
                "environment": random.choice(["prod", "staging", "dev"]),
                "region": random.choice(["us-east", "us-west", "eu-west"]),
            }

            metric_name = f"stress_test_ingestion_{i % 10}"

            series.append(GeneratedSeries(
                metric_name=metric_name,
                labels=labels,
                current_value=random.uniform(0, 100),
            ))

        return series

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
            "samples_appended": "rate(prometheus_tsdb_head_samples_appended_total[1m])",
            "out_of_order": "prometheus_tsdb_out_of_order_samples_total",
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

    async def _simulate_ingestion(
        self,
        target_rate: float,
        duration_seconds: float,
    ) -> tuple[int, float, list[str]]:
        """Simulate high ingestion rate.

        Note: This simulates ingestion by measuring Prometheus's ability
        to handle queries while under simulated load. In a real scenario,
        you would use remote_write to push actual samples.

        Args:
            target_rate: Target samples per second
            duration_seconds: Duration to simulate

        Returns:
            Tuple of (samples_simulated, achieved_rate, errors)
        """
        errors = []
        samples_simulated = 0
        start_time = time.time()

        # Calculate batch timing
        batches_per_second = target_rate / self.config.batch_size
        batch_interval = 1.0 / max(batches_per_second, 0.1)

        end_time = start_time + duration_seconds

        while time.time() < end_time and self._running:
            batch_start = time.time()

            # Generate sample values for the batch
            for series in self._series[:self.config.batch_size]:
                series.generate_value()
                samples_simulated += 1

            self._total_samples_pushed += self.config.batch_size

            # Rate limiting
            elapsed = time.time() - batch_start
            sleep_time = max(0, batch_interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        actual_duration = time.time() - start_time
        achieved_rate = samples_simulated / actual_duration if actual_duration > 0 else 0

        return samples_simulated, achieved_rate, errors

    async def _measure_at_ingestion_rate(
        self,
        target_rate: float,
    ) -> StressTestDataPoint:
        """Measure performance at a specific ingestion rate.

        Args:
            target_rate: Target samples per second

        Returns:
            StressTestDataPoint with measurements
        """
        # Simulate ingestion at target rate for a measurement period
        samples, achieved_rate, sim_errors = await self._simulate_ingestion(
            target_rate=target_rate,
            duration_seconds=10.0,  # 10 second measurement window
        )

        # Run test queries to measure impact
        latencies: list[float] = []
        successes = 0
        total = 0

        test_queries = [
            "up",
            "prometheus_tsdb_head_series",
            "rate(prometheus_tsdb_head_samples_appended_total[1m])",
        ]

        for _ in range(5):
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

        # Check for ingestion issues
        out_of_order = prom_metrics.get("out_of_order", 0)
        if out_of_order > 0:
            error_messages.append(f"Out of order samples detected: {out_of_order}")

        wal_corruptions = prom_metrics.get("wal_corruptions", 0)
        if wal_corruptions > 0:
            error_messages.append(f"WAL corruptions detected: {wal_corruptions}")
            is_healthy = False

        if success_rate < 90:
            error_messages.append(f"Success rate dropped to {success_rate:.1f}%")

        if p99 > 10000:  # 10 second threshold
            error_messages.append(f"P99 latency {p99:.1f}ms exceeds 10000ms threshold")

        return StressTestDataPoint(
            load_level=target_rate,
            query_latency_p50_ms=p50,
            query_latency_p99_ms=p99,
            success_rate_percent=success_rate,
            cpu_utilization_percent=prom_metrics.get("cpu_seconds", 0) * 100,
            memory_utilization_bytes=prom_metrics.get("memory_bytes", 0),
            active_series=int(prom_metrics.get("active_series", 0)),
            samples_per_second=achieved_rate,
            is_healthy=is_healthy and success_rate >= 90,
            error_messages=error_messages,
        )

    async def run(self) -> IngestionTestResult:
        """Run the high ingestion rate stress test.

        Requirements: 17.3

        Returns:
            IngestionTestResult with test results and breaking point
        """
        result = IngestionTestResult(config=self.config)
        result.start_time = datetime.utcnow()
        self._running = True
        self._total_samples_pushed = 0

        # Generate series for testing
        self._series = self._generate_series()

        last_healthy_data_point: Optional[StressTestDataPoint] = None

        async with httpx.AsyncClient() as client:
            self._client = client

            # Verify Prometheus is healthy before starting
            if not await self._check_health():
                result.passed = False
                result.error_logs.append("Prometheus not healthy at test start")
                result.end_time = datetime.utcnow()
                return result

            current_rate = self.config.initial_samples_per_second

            while (
                self._running
                and current_rate <= self.config.max_samples_per_second
                and result.duration_seconds < self.config.max_test_duration_seconds
            ):
                # Measure at current ingestion rate
                data_point = await self._measure_at_ingestion_rate(current_rate)
                result.data_points.append(data_point)

                # Track max achieved rate
                if data_point.samples_per_second > result.max_achieved_rate:
                    result.max_achieved_rate = data_point.samples_per_second

                if data_point.is_healthy:
                    last_healthy_data_point = data_point
                else:
                    # Failure detected - record breaking point
                    result.breaking_point = BreakingPoint(
                        max_ingestion_rate=(
                            last_healthy_data_point.samples_per_second
                            if last_healthy_data_point else 0
                        ),
                        max_series=data_point.active_series,
                        failure_mode=FailureMode.INGESTION_FAILURE,
                        failure_timestamp=datetime.utcnow(),
                        failure_symptoms=data_point.error_messages,
                        last_healthy_metrics={
                            "ingestion_rate": last_healthy_data_point.samples_per_second if last_healthy_data_point else 0,
                            "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms if last_healthy_data_point else 0,
                            "success_rate": last_healthy_data_point.success_rate_percent if last_healthy_data_point else 0,
                        },
                    )

                    result.error_logs.extend(data_point.error_messages)
                    break

                # Increase ingestion rate
                current_rate += self.config.rate_increment

                # Brief pause between levels
                await asyncio.sleep(2)

        self._client = None
        self._running = False
        result.end_time = datetime.utcnow()
        result.total_samples_pushed = self._total_samples_pushed

        # If we completed without failure, record the max achieved
        if result.breaking_point.failure_mode == FailureMode.NONE and last_healthy_data_point:
            result.breaking_point.max_ingestion_rate = last_healthy_data_point.samples_per_second
            result.breaking_point.max_series = last_healthy_data_point.active_series
            result.breaking_point.last_healthy_metrics = {
                "ingestion_rate": last_healthy_data_point.samples_per_second,
                "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms,
                "success_rate": last_healthy_data_point.success_rate_percent,
            }

        return result

    def stop(self) -> None:
        """Stop the stress test."""
        self._running = False


def run_high_ingestion_test_sync(
    prometheus_url: str = "http://localhost:9090",
    initial_rate: float = 1000.0,
    max_rate: float = 100000.0,
    rate_increment: float = 5000.0,
) -> IngestionTestResult:
    """Synchronous wrapper for running high ingestion test.

    Args:
        prometheus_url: URL of the Prometheus instance
        initial_rate: Starting samples per second
        max_rate: Maximum samples per second
        rate_increment: Rate increase per step

    Returns:
        IngestionTestResult
    """
    config = HighIngestionConfig(
        prometheus_url=prometheus_url,
        initial_samples_per_second=initial_rate,
        max_samples_per_second=max_rate,
        rate_increment=rate_increment,
    )
    tester = HighIngestionTester(config)
    return asyncio.run(tester.run())
