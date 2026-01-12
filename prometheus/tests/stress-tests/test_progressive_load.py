"""
Progressive load stress test for Prometheus.

This module implements stress tests that progressively increase load
until Prometheus fails or degrades, recording the breaking point.

Requirements: 17.1, 17.6
"""

import asyncio
import statistics
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

from config import ProgressiveLoadConfig
from models import (
    BreakingPoint,
    FailureMode,
    StressTestDataPoint,
    StressTestType,
)


@dataclass
class ProgressiveLoadResult:
    """
    Result of a progressive load stress test.

    Requirements: 17.1, 17.6

    Attributes:
        test_type: Type of stress test
        config: Test configuration used
        start_time: When the test started
        end_time: When the test ended
        data_points: Measurements at each load level
        breaking_point: Discovered breaking point
        passed: Whether the test completed without unexpected failures
        error_logs: Captured error logs
    """

    test_type: StressTestType = StressTestType.PROGRESSIVE_LOAD
    config: Optional[ProgressiveLoadConfig] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_points: list[StressTestDataPoint] = field(default_factory=list)
    breaking_point: BreakingPoint = field(default_factory=BreakingPoint)
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
            "passed": self.passed,
            "error_logs": self.error_logs,
        }


class ProgressiveLoadTester:
    """
    Executes progressive load stress tests against Prometheus.

    This class progressively increases query load until Prometheus
    fails or degrades significantly, recording the breaking point.

    Requirements: 17.1, 17.6
    """

    # Test queries of varying complexity
    TEST_QUERIES = [
        "up",
        "prometheus_tsdb_head_series",
        'rate(prometheus_http_requests_total[5m])',
        'sum(rate(prometheus_http_requests_total[5m])) by (handler)',
        'histogram_quantile(0.99, rate(prometheus_http_request_duration_seconds_bucket[5m]))',
    ]

    def __init__(self, config: ProgressiveLoadConfig):
        """Initialize the progressive load tester.

        Args:
            config: Test configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False

    async def _query_prometheus(self, query: str) -> tuple[bool, float]:
        """Execute a PromQL query and measure latency.

        Args:
            query: PromQL query string

        Returns:
            Tuple of (success, latency_ms)
        """
        if not self._client:
            return False, 0.0

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
                    return True, latency_ms

            return False, latency_ms
        except httpx.TimeoutException:
            return False, self.config.timeout_seconds * 1000
        except Exception:
            end_time = time.perf_counter()
            return False, (end_time - start_time) * 1000

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
        }

        for name, query in metric_queries.items():
            success, _ = await self._query_prometheus(query)
            if success:
                try:
                    response = await self._client.get(
                        f"{self.config.prometheus_url}/api/v1/query",
                        params={"query": query},
                        timeout=10.0,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        result = data.get("data", {}).get("result", [])
                        if result:
                            metrics[name] = float(result[0].get("value", [0, 0])[1])
                except Exception:
                    pass

        return metrics

    async def _run_load_batch(
        self,
        queries_per_second: float,
        duration_seconds: float,
    ) -> tuple[list[float], int, int]:
        """Run a batch of queries at a specified rate.

        Args:
            queries_per_second: Target query rate
            duration_seconds: Duration to run

        Returns:
            Tuple of (latencies, successes, total)
        """
        latencies: list[float] = []
        successes = 0
        total = 0

        interval = 1.0 / max(queries_per_second, 0.1)
        end_time = time.time() + duration_seconds

        while time.time() < end_time and self._running:
            query = self.TEST_QUERIES[total % len(self.TEST_QUERIES)]
            success, latency_ms = await self._query_prometheus(query)

            latencies.append(latency_ms)
            total += 1
            if success:
                successes += 1

            # Rate limiting
            await asyncio.sleep(interval)

        return latencies, successes, total

    async def _measure_at_load_level(
        self,
        load_level: float,
    ) -> StressTestDataPoint:
        """Measure performance at a specific load level.

        Args:
            load_level: Queries per second

        Returns:
            StressTestDataPoint with measurements
        """
        # Run queries at the specified rate
        latencies, successes, total = await self._run_load_batch(
            queries_per_second=load_level,
            duration_seconds=self.config.load_increment_interval_seconds,
        )

        # Calculate percentiles
        sorted_latencies = sorted(latencies) if latencies else [0]
        n = len(sorted_latencies)

        p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0
        p99 = sorted_latencies[min(int(n * 0.99), n - 1)] if n > 0 else 0

        # Get Prometheus metrics
        prom_metrics = await self._get_prometheus_metrics()

        # Check health
        is_healthy = await self._check_health()

        # Determine if this is a failure state
        success_rate = (successes / total * 100) if total > 0 else 0
        error_messages = []

        if success_rate < self.config.failure_threshold_success_rate:
            error_messages.append(
                f"Success rate {success_rate:.1f}% below threshold "
                f"{self.config.failure_threshold_success_rate}%"
            )

        if p99 > self.config.failure_threshold_latency_ms:
            error_messages.append(
                f"P99 latency {p99:.1f}ms exceeds threshold "
                f"{self.config.failure_threshold_latency_ms}ms"
            )

        return StressTestDataPoint(
            load_level=load_level,
            query_latency_p50_ms=p50,
            query_latency_p99_ms=p99,
            success_rate_percent=success_rate,
            cpu_utilization_percent=prom_metrics.get("cpu_seconds", 0) * 100,
            memory_utilization_bytes=prom_metrics.get("memory_bytes", 0),
            active_series=int(prom_metrics.get("active_series", 0)),
            samples_per_second=prom_metrics.get("samples_appended", 0),
            is_healthy=is_healthy and not error_messages,
            error_messages=error_messages,
        )

    def _detect_failure_mode(
        self,
        data_point: StressTestDataPoint,
    ) -> FailureMode:
        """Detect the failure mode from a data point.

        Args:
            data_point: The data point to analyze

        Returns:
            Detected failure mode
        """
        if data_point.is_healthy:
            return FailureMode.NONE

        # Check for timeout (very high latency)
        if data_point.query_latency_p99_ms >= self.config.timeout_seconds * 1000:
            return FailureMode.TIMEOUT

        # Check for query failures (low success rate)
        if data_point.success_rate_percent < 50:
            return FailureMode.QUERY_FAILURE

        # Check for degradation (high latency but still responding)
        if data_point.query_latency_p99_ms > self.config.failure_threshold_latency_ms:
            return FailureMode.DEGRADATION

        return FailureMode.UNKNOWN

    async def run(self) -> ProgressiveLoadResult:
        """Run the progressive load stress test.

        Requirements: 17.1, 17.6

        Returns:
            ProgressiveLoadResult with test results and breaking point
        """
        result = ProgressiveLoadResult(config=self.config)
        result.start_time = datetime.utcnow()
        self._running = True

        last_healthy_data_point: Optional[StressTestDataPoint] = None

        async with httpx.AsyncClient() as client:
            self._client = client

            # Verify Prometheus is healthy before starting
            if not await self._check_health():
                result.passed = False
                result.error_logs.append("Prometheus not healthy at test start")
                result.end_time = datetime.utcnow()
                return result

            current_load = self.config.initial_load

            while (
                self._running
                and current_load <= self.config.max_load
                and result.duration_seconds < self.config.max_test_duration_seconds
            ):
                # Measure at current load level
                data_point = await self._measure_at_load_level(current_load)
                result.data_points.append(data_point)

                if data_point.is_healthy:
                    last_healthy_data_point = data_point
                else:
                    # Failure detected - record breaking point
                    failure_mode = self._detect_failure_mode(data_point)

                    result.breaking_point = BreakingPoint(
                        max_query_rate=last_healthy_data_point.load_level if last_healthy_data_point else 0,
                        max_series=data_point.active_series,
                        failure_mode=failure_mode,
                        failure_timestamp=datetime.utcnow(),
                        failure_symptoms=data_point.error_messages,
                        last_healthy_metrics={
                            "load_level": last_healthy_data_point.load_level if last_healthy_data_point else 0,
                            "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms if last_healthy_data_point else 0,
                            "success_rate": last_healthy_data_point.success_rate_percent if last_healthy_data_point else 0,
                        },
                    )

                    result.error_logs.extend(data_point.error_messages)
                    break

                # Increase load
                current_load += self.config.load_increment

        self._client = None
        self._running = False
        result.end_time = datetime.utcnow()

        # If we completed without failure, record the max achieved
        if result.breaking_point.failure_mode == FailureMode.NONE and last_healthy_data_point:
            result.breaking_point.max_query_rate = last_healthy_data_point.load_level
            result.breaking_point.max_series = last_healthy_data_point.active_series
            result.breaking_point.last_healthy_metrics = {
                "load_level": last_healthy_data_point.load_level,
                "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms,
                "success_rate": last_healthy_data_point.success_rate_percent,
            }

        return result

    def stop(self) -> None:
        """Stop the stress test."""
        self._running = False


def run_progressive_load_test_sync(
    prometheus_url: str = "http://localhost:9090",
    initial_load: float = 1.0,
    max_load: float = 100.0,
    load_increment: float = 5.0,
) -> ProgressiveLoadResult:
    """Synchronous wrapper for running progressive load test.

    Args:
        prometheus_url: URL of the Prometheus instance
        initial_load: Starting queries per second
        max_load: Maximum queries per second
        load_increment: Load increase per step

    Returns:
        ProgressiveLoadResult
    """
    config = ProgressiveLoadConfig(
        prometheus_url=prometheus_url,
        initial_load=initial_load,
        max_load=max_load,
        load_increment=load_increment,
    )
    tester = ProgressiveLoadTester(config)
    return asyncio.run(tester.run())
