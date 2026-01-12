"""
Scaling dimension tests for Prometheus scalability testing.

This module provides functionality to test Prometheus performance
across different scaling dimensions: targets, series, cardinality,
retention, and query concurrency.

Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
"""

import asyncio
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import httpx


class ScalingDimension(Enum):
    """Types of scaling dimensions to test."""

    TARGETS = "targets"
    SERIES = "series"
    CARDINALITY = "cardinality"
    RETENTION = "retention"
    QUERY_CONCURRENCY = "query_concurrency"


@dataclass
class ScalingDataPoint:
    """A single data point in a scaling test.

    Attributes:
        scale_value: The scale value (e.g., number of targets)
        query_latency_p50_ms: 50th percentile query latency
        query_latency_p90_ms: 90th percentile query latency
        query_latency_p99_ms: 99th percentile query latency
        cpu_utilization_percent: CPU utilization percentage
        memory_utilization_bytes: Memory utilization in bytes
        scrape_duration_avg_ms: Average scrape duration
        success_rate_percent: Success rate percentage
        timestamp: When the measurement was taken
        metadata: Additional context
    """

    scale_value: int
    query_latency_p50_ms: float = 0.0
    query_latency_p90_ms: float = 0.0
    query_latency_p99_ms: float = 0.0
    cpu_utilization_percent: float = 0.0
    memory_utilization_bytes: float = 0.0
    scrape_duration_avg_ms: float = 0.0
    success_rate_percent: float = 100.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "scale_value": self.scale_value,
            "query_latency_p50_ms": round(self.query_latency_p50_ms, 2),
            "query_latency_p90_ms": round(self.query_latency_p90_ms, 2),
            "query_latency_p99_ms": round(self.query_latency_p99_ms, 2),
            "cpu_utilization_percent": round(self.cpu_utilization_percent, 2),
            "memory_utilization_bytes": round(self.memory_utilization_bytes, 0),
            "scrape_duration_avg_ms": round(self.scrape_duration_avg_ms, 2),
            "success_rate_percent": round(self.success_rate_percent, 2),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ScalingTestResult:
    """Result of a scaling dimension test.

    Attributes:
        dimension: The scaling dimension tested
        data_points: List of measurements at different scale values
        start_time: When the test started
        end_time: When the test ended
        degradation_point: Scale value where performance degraded non-linearly
        passed: Whether the test passed
        failures: List of failure messages
    """

    dimension: ScalingDimension
    data_points: list[ScalingDataPoint] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    degradation_point: Optional[int] = None
    passed: bool = True
    failures: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Total test duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def add_data_point(self, data_point: ScalingDataPoint) -> None:
        """Add a data point to the result."""
        self.data_points.append(data_point)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "dimension": self.dimension.value,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "degradation_point": self.degradation_point,
            "passed": self.passed,
            "failures": self.failures,
        }


@dataclass
class ScalingTestConfig:
    """Configuration for scaling tests.

    Attributes:
        prometheus_url: URL of the Prometheus instance
        target_scale_values: Scale values for target scaling test
        series_scale_values: Scale values for series scaling test
        cardinality_scale_values: Scale values for cardinality test
        retention_scale_values: Scale values for retention test (days)
        concurrency_scale_values: Scale values for query concurrency test
        measurement_duration_seconds: Duration to measure at each scale
        query_iterations: Number of queries per measurement
        timeout_seconds: Query timeout
    """

    prometheus_url: str = "http://localhost:9090"
    target_scale_values: list[int] = field(
        default_factory=lambda: [10, 100, 500, 1000, 5000, 10000]
    )
    series_scale_values: list[int] = field(
        default_factory=lambda: [10000, 50000, 100000, 500000, 1000000, 5000000, 10000000]
    )
    cardinality_scale_values: list[int] = field(
        default_factory=lambda: [100, 1000, 10000, 100000, 500000, 1000000]
    )
    retention_scale_values: list[int] = field(
        default_factory=lambda: [1, 7, 15, 30, 60, 90]
    )
    concurrency_scale_values: list[int] = field(
        default_factory=lambda: [1, 5, 10, 25, 50, 100]
    )
    measurement_duration_seconds: int = 30
    query_iterations: int = 20
    timeout_seconds: float = 30.0


class ScalingDimensionTester:
    """
    Tests Prometheus performance across different scaling dimensions.

    This class measures how Prometheus performance changes as various
    dimensions scale up, helping identify non-linear degradation points.

    Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
    """

    # Test queries for measuring performance
    TEST_QUERIES = [
        "up",
        "prometheus_tsdb_head_series",
        'rate(prometheus_http_requests_total[5m])',
        'sum(rate(prometheus_http_requests_total[5m])) by (handler)',
    ]

    def __init__(self, config: ScalingTestConfig):
        """Initialize the scaling dimension tester.

        Args:
            config: Test configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

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
        except Exception:
            end_time = time.perf_counter()
            return False, (end_time - start_time) * 1000, None

    async def _get_prometheus_metrics(self) -> dict[str, float]:
        """Get current Prometheus internal metrics.

        Returns:
            Dictionary of metric name to value
        """
        metrics = {}

        metric_queries = {
            "head_series": "prometheus_tsdb_head_series",
            "cpu_seconds": "process_cpu_seconds_total",
            "memory_bytes": "process_resident_memory_bytes",
            "scrape_duration": "avg(scrape_duration_seconds)",
        }

        for name, query in metric_queries.items():
            success, _, result = await self._query_prometheus(query)
            if success and result:
                try:
                    metrics[name] = float(result[0].get("value", [0, 0])[1])
                except (IndexError, ValueError, TypeError):
                    metrics[name] = 0.0
            else:
                metrics[name] = 0.0

        return metrics

    async def _measure_performance(
        self,
        scale_value: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ScalingDataPoint:
        """Measure performance at a given scale.

        Args:
            scale_value: Current scale value
            metadata: Additional metadata

        Returns:
            ScalingDataPoint with measurements
        """
        latencies: list[float] = []
        successes = 0
        total = 0

        # Run query iterations
        for _ in range(self.config.query_iterations):
            for query in self.TEST_QUERIES:
                success, latency_ms, _ = await self._query_prometheus(query)
                latencies.append(latency_ms)
                total += 1
                if success:
                    successes += 1

        # Get Prometheus metrics
        prom_metrics = await self._get_prometheus_metrics()

        # Calculate percentiles
        sorted_latencies = sorted(latencies) if latencies else [0]
        n = len(sorted_latencies)

        p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0
        p90 = sorted_latencies[int(n * 0.90)] if n > 0 else 0
        p99 = sorted_latencies[min(int(n * 0.99), n - 1)] if n > 0 else 0

        return ScalingDataPoint(
            scale_value=scale_value,
            query_latency_p50_ms=p50,
            query_latency_p90_ms=p90,
            query_latency_p99_ms=p99,
            cpu_utilization_percent=prom_metrics.get("cpu_seconds", 0) * 100,
            memory_utilization_bytes=prom_metrics.get("memory_bytes", 0),
            scrape_duration_avg_ms=prom_metrics.get("scrape_duration", 0) * 1000,
            success_rate_percent=(successes / total * 100) if total > 0 else 0,
            metadata=metadata or {},
        )

    async def test_target_scaling(self) -> ScalingTestResult:
        """Test performance as number of scrape targets increases.

        Requirements: 16.1

        Returns:
            ScalingTestResult with measurements at each target count
        """
        result = ScalingTestResult(dimension=ScalingDimension.TARGETS)
        result.start_time = datetime.utcnow()

        async with httpx.AsyncClient() as client:
            self._client = client

            for target_count in self.config.target_scale_values:
                # Measure performance at this scale
                data_point = await self._measure_performance(
                    scale_value=target_count,
                    metadata={"dimension": "targets", "target_count": target_count},
                )
                result.add_data_point(data_point)

                # Brief pause between measurements
                await asyncio.sleep(1)

        self._client = None
        result.end_time = datetime.utcnow()

        # Detect degradation point
        result.degradation_point = self._detect_degradation_point(result.data_points)

        return result

    async def test_series_scaling(self) -> ScalingTestResult:
        """Test performance as number of active series increases.

        Requirements: 16.2

        Returns:
            ScalingTestResult with measurements at each series count
        """
        result = ScalingTestResult(dimension=ScalingDimension.SERIES)
        result.start_time = datetime.utcnow()

        async with httpx.AsyncClient() as client:
            self._client = client

            for series_count in self.config.series_scale_values:
                # Measure performance at this scale
                data_point = await self._measure_performance(
                    scale_value=series_count,
                    metadata={"dimension": "series", "series_count": series_count},
                )
                result.add_data_point(data_point)

                await asyncio.sleep(1)

        self._client = None
        result.end_time = datetime.utcnow()

        result.degradation_point = self._detect_degradation_point(result.data_points)

        return result

    async def test_cardinality_scaling(self) -> ScalingTestResult:
        """Test performance as label cardinality increases.

        Requirements: 16.3

        Returns:
            ScalingTestResult with measurements at each cardinality level
        """
        result = ScalingTestResult(dimension=ScalingDimension.CARDINALITY)
        result.start_time = datetime.utcnow()

        async with httpx.AsyncClient() as client:
            self._client = client

            for cardinality in self.config.cardinality_scale_values:
                data_point = await self._measure_performance(
                    scale_value=cardinality,
                    metadata={"dimension": "cardinality", "cardinality": cardinality},
                )
                result.add_data_point(data_point)

                await asyncio.sleep(1)

        self._client = None
        result.end_time = datetime.utcnow()

        result.degradation_point = self._detect_degradation_point(result.data_points)

        return result

    async def test_retention_scaling(self) -> ScalingTestResult:
        """Test performance as retention period increases.

        Requirements: 16.4

        Returns:
            ScalingTestResult with measurements at each retention period
        """
        result = ScalingTestResult(dimension=ScalingDimension.RETENTION)
        result.start_time = datetime.utcnow()

        async with httpx.AsyncClient() as client:
            self._client = client

            for retention_days in self.config.retention_scale_values:
                data_point = await self._measure_performance(
                    scale_value=retention_days,
                    metadata={
                        "dimension": "retention",
                        "retention_days": retention_days,
                    },
                )
                result.add_data_point(data_point)

                await asyncio.sleep(1)

        self._client = None
        result.end_time = datetime.utcnow()

        result.degradation_point = self._detect_degradation_point(result.data_points)

        return result

    async def test_query_concurrency_scaling(self) -> ScalingTestResult:
        """Test performance as concurrent query count increases.

        Requirements: 16.5

        Returns:
            ScalingTestResult with measurements at each concurrency level
        """
        result = ScalingTestResult(dimension=ScalingDimension.QUERY_CONCURRENCY)
        result.start_time = datetime.utcnow()

        async with httpx.AsyncClient() as client:
            self._client = client

            for concurrency in self.config.concurrency_scale_values:
                # Run concurrent queries
                data_point = await self._measure_concurrent_performance(
                    concurrency=concurrency,
                )
                result.add_data_point(data_point)

                await asyncio.sleep(1)

        self._client = None
        result.end_time = datetime.utcnow()

        result.degradation_point = self._detect_degradation_point(result.data_points)

        return result

    async def _measure_concurrent_performance(
        self,
        concurrency: int,
    ) -> ScalingDataPoint:
        """Measure performance with concurrent queries.

        Args:
            concurrency: Number of concurrent queries

        Returns:
            ScalingDataPoint with measurements
        """
        latencies: list[float] = []
        successes = 0
        total = 0

        async def run_query(query: str) -> tuple[bool, float]:
            success, latency_ms, _ = await self._query_prometheus(query)
            return success, latency_ms

        # Run batches of concurrent queries
        for _ in range(self.config.query_iterations):
            tasks = []
            for i in range(concurrency):
                query = self.TEST_QUERIES[i % len(self.TEST_QUERIES)]
                tasks.append(run_query(query))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                total += 1
                if isinstance(res, tuple):
                    success, latency_ms = res
                    latencies.append(latency_ms)
                    if success:
                        successes += 1
                else:
                    latencies.append(self.config.timeout_seconds * 1000)

        # Get Prometheus metrics
        prom_metrics = await self._get_prometheus_metrics()

        # Calculate percentiles
        sorted_latencies = sorted(latencies) if latencies else [0]
        n = len(sorted_latencies)

        p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0
        p90 = sorted_latencies[int(n * 0.90)] if n > 0 else 0
        p99 = sorted_latencies[min(int(n * 0.99), n - 1)] if n > 0 else 0

        return ScalingDataPoint(
            scale_value=concurrency,
            query_latency_p50_ms=p50,
            query_latency_p90_ms=p90,
            query_latency_p99_ms=p99,
            cpu_utilization_percent=prom_metrics.get("cpu_seconds", 0) * 100,
            memory_utilization_bytes=prom_metrics.get("memory_bytes", 0),
            scrape_duration_avg_ms=prom_metrics.get("scrape_duration", 0) * 1000,
            success_rate_percent=(successes / total * 100) if total > 0 else 0,
            metadata={"dimension": "concurrency", "concurrency": concurrency},
        )

    def _detect_degradation_point(
        self,
        data_points: list[ScalingDataPoint],
    ) -> Optional[int]:
        """Detect the point where performance degrades non-linearly.

        This uses a simple heuristic: find where the rate of latency
        increase exceeds 2x the average rate.

        Args:
            data_points: List of scaling data points

        Returns:
            Scale value where degradation was detected, or None
        """
        if len(data_points) < 3:
            return None

        # Calculate latency increases between consecutive points
        increases = []
        for i in range(1, len(data_points)):
            prev = data_points[i - 1]
            curr = data_points[i]

            scale_diff = curr.scale_value - prev.scale_value
            if scale_diff > 0:
                latency_increase = curr.query_latency_p99_ms - prev.query_latency_p99_ms
                rate = latency_increase / scale_diff
                increases.append((curr.scale_value, rate))

        if not increases:
            return None

        # Calculate average rate
        avg_rate = statistics.mean([r for _, r in increases])

        # Find first point where rate exceeds 2x average
        for scale_value, rate in increases:
            if rate > avg_rate * 2 and avg_rate > 0:
                return scale_value

        return None

    async def run_all_scaling_tests(self) -> dict[str, ScalingTestResult]:
        """Run all scaling dimension tests.

        Returns:
            Dictionary mapping dimension name to test result
        """
        results = {}

        results["targets"] = await self.test_target_scaling()
        results["series"] = await self.test_series_scaling()
        results["cardinality"] = await self.test_cardinality_scaling()
        results["retention"] = await self.test_retention_scaling()
        results["query_concurrency"] = await self.test_query_concurrency_scaling()

        return results
