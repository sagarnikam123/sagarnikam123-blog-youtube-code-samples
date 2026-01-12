"""
Concurrent query stress test for Prometheus.

This module implements stress tests that execute simultaneous PromQL
queries to find Prometheus query concurrency limits.

Requirements: 17.4
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

from config import ConcurrentQueryConfig
from models import (
    BreakingPoint,
    FailureMode,
    StressTestDataPoint,
    StressTestType,
)


@dataclass
class ConcurrentQueryResult:
    """
    Result of a concurrent query stress test.

    Requirements: 17.4

    Attributes:
        test_type: Type of stress test
        config: Test configuration used
        start_time: When the test started
        end_time: When the test ended
        data_points: Measurements at each concurrency level
        breaking_point: Discovered breaking point
        total_queries_executed: Total queries executed during test
        max_concurrent_achieved: Maximum concurrent queries achieved
        passed: Whether the test completed without unexpected failures
        error_logs: Captured error logs
    """

    test_type: StressTestType = StressTestType.CONCURRENT_QUERIES
    config: Optional[ConcurrentQueryConfig] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_points: list[StressTestDataPoint] = field(default_factory=list)
    breaking_point: BreakingPoint = field(default_factory=BreakingPoint)
    total_queries_executed: int = 0
    max_concurrent_achieved: int = 0
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
            "total_queries_executed": self.total_queries_executed,
            "max_concurrent_achieved": self.max_concurrent_achieved,
            "passed": self.passed,
            "error_logs": self.error_logs,
        }


class ConcurrentQueryTester:
    """
    Executes concurrent query stress tests against Prometheus.

    This class executes simultaneous PromQL queries at increasing
    concurrency levels to find the maximum sustainable concurrency.

    Requirements: 17.4
    """

    def __init__(self, config: ConcurrentQueryConfig):
        """Initialize the concurrent query tester.

        Args:
            config: Test configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._total_queries = 0

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
            "queries_concurrent": "prometheus_engine_queries",
            "query_duration_avg": "avg(prometheus_engine_query_duration_seconds)",
        }

        for name, query in metric_queries.items():
            success, _, result = await self._query_prometheus(query)
            if success and result:
                try:
                    metrics[name] = float(result[0].get("value", [0, 0])[1])
                except (IndexError, ValueError, TypeError):
                    pass

        return metrics

    async def _run_concurrent_queries(
        self,
        concurrency: int,
        num_batches: int = 10,
    ) -> tuple[list[float], int, int]:
        """Run concurrent queries and collect latencies.

        Args:
            concurrency: Number of concurrent queries
            num_batches: Number of batches to run

        Returns:
            Tuple of (latencies, successes, total)
        """
        latencies: list[float] = []
        successes = 0
        total = 0

        async def run_single_query(query: str) -> tuple[bool, float]:
            success, latency_ms, _ = await self._query_prometheus(query)
            return success, latency_ms

        for batch in range(num_batches):
            if not self._running:
                break

            # Create concurrent query tasks
            tasks = []
            for i in range(concurrency):
                query = self.config.query_types[i % len(self.config.query_types)]
                tasks.append(run_single_query(query))

            # Execute all queries concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                total += 1
                self._total_queries += 1

                if isinstance(res, tuple):
                    success, latency_ms = res
                    latencies.append(latency_ms)
                    if success:
                        successes += 1
                else:
                    # Exception occurred
                    latencies.append(self.config.timeout_seconds * 1000)

            # Brief pause between batches
            await asyncio.sleep(0.1)

        return latencies, successes, total

    async def _measure_at_concurrency_level(
        self,
        concurrency: int,
    ) -> StressTestDataPoint:
        """Measure performance at a specific concurrency level.

        Args:
            concurrency: Number of concurrent queries

        Returns:
            StressTestDataPoint with measurements
        """
        # Run concurrent queries
        latencies, successes, total = await self._run_concurrent_queries(
            concurrency=concurrency,
            num_batches=self.config.queries_per_batch // concurrency,
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

        success_rate = (successes / total * 100) if total > 0 else 0
        error_messages = []

        # Check for degradation
        if success_rate < 90:
            error_messages.append(f"Success rate dropped to {success_rate:.1f}%")

        if p99 > 30000:  # 30 second threshold for concurrent queries
            error_messages.append(f"P99 latency {p99:.1f}ms exceeds 30000ms threshold")

        # Check if queries are timing out
        timeout_count = sum(1 for l in latencies if l >= self.config.timeout_seconds * 1000)
        if timeout_count > total * 0.1:  # More than 10% timeouts
            error_messages.append(f"High timeout rate: {timeout_count}/{total} queries timed out")

        return StressTestDataPoint(
            load_level=concurrency,
            query_latency_p50_ms=p50,
            query_latency_p99_ms=p99,
            success_rate_percent=success_rate,
            cpu_utilization_percent=prom_metrics.get("cpu_seconds", 0) * 100,
            memory_utilization_bytes=prom_metrics.get("memory_bytes", 0),
            active_series=int(prom_metrics.get("active_series", 0)),
            is_healthy=is_healthy and success_rate >= 90 and not error_messages,
            error_messages=error_messages,
        )

    async def run(self) -> ConcurrentQueryResult:
        """Run the concurrent query stress test.

        Requirements: 17.4

        Returns:
            ConcurrentQueryResult with test results and breaking point
        """
        result = ConcurrentQueryResult(config=self.config)
        result.start_time = datetime.utcnow()
        self._running = True
        self._total_queries = 0

        last_healthy_data_point: Optional[StressTestDataPoint] = None

        async with httpx.AsyncClient() as client:
            self._client = client

            # Verify Prometheus is healthy before starting
            if not await self._check_health():
                result.passed = False
                result.error_logs.append("Prometheus not healthy at test start")
                result.end_time = datetime.utcnow()
                return result

            current_concurrency = self.config.initial_concurrency

            while (
                self._running
                and current_concurrency <= self.config.max_concurrency
                and result.duration_seconds < self.config.max_test_duration_seconds
            ):
                # Measure at current concurrency level
                data_point = await self._measure_at_concurrency_level(current_concurrency)
                result.data_points.append(data_point)

                # Track max concurrent achieved
                if data_point.is_healthy and current_concurrency > result.max_concurrent_achieved:
                    result.max_concurrent_achieved = current_concurrency

                if data_point.is_healthy:
                    last_healthy_data_point = data_point
                else:
                    # Failure detected - record breaking point
                    result.breaking_point = BreakingPoint(
                        max_concurrent_queries=(
                            int(last_healthy_data_point.load_level)
                            if last_healthy_data_point else 0
                        ),
                        max_series=data_point.active_series,
                        failure_mode=FailureMode.QUERY_FAILURE,
                        failure_timestamp=datetime.utcnow(),
                        failure_symptoms=data_point.error_messages,
                        last_healthy_metrics={
                            "concurrency": last_healthy_data_point.load_level if last_healthy_data_point else 0,
                            "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms if last_healthy_data_point else 0,
                            "success_rate": last_healthy_data_point.success_rate_percent if last_healthy_data_point else 0,
                        },
                    )

                    result.error_logs.extend(data_point.error_messages)
                    break

                # Increase concurrency
                current_concurrency += self.config.concurrency_increment

                # Brief pause between levels
                await asyncio.sleep(2)

        self._client = None
        self._running = False
        result.end_time = datetime.utcnow()
        result.total_queries_executed = self._total_queries

        # If we completed without failure, record the max achieved
        if result.breaking_point.failure_mode == FailureMode.NONE and last_healthy_data_point:
            result.breaking_point.max_concurrent_queries = int(last_healthy_data_point.load_level)
            result.breaking_point.max_series = last_healthy_data_point.active_series
            result.breaking_point.last_healthy_metrics = {
                "concurrency": last_healthy_data_point.load_level,
                "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms,
                "success_rate": last_healthy_data_point.success_rate_percent,
            }

        return result

    def stop(self) -> None:
        """Stop the stress test."""
        self._running = False


def run_concurrent_query_test_sync(
    prometheus_url: str = "http://localhost:9090",
    initial_concurrency: int = 1,
    max_concurrency: int = 100,
    concurrency_increment: int = 10,
) -> ConcurrentQueryResult:
    """Synchronous wrapper for running concurrent query test.

    Args:
        prometheus_url: URL of the Prometheus instance
        initial_concurrency: Starting concurrency level
        max_concurrency: Maximum concurrency to attempt
        concurrency_increment: Concurrency increase per step

    Returns:
        ConcurrentQueryResult
    """
    config = ConcurrentQueryConfig(
        prometheus_url=prometheus_url,
        initial_concurrency=initial_concurrency,
        max_concurrency=max_concurrency,
        concurrency_increment=concurrency_increment,
    )
    tester = ConcurrentQueryTester(config)
    return asyncio.run(tester.run())
