"""
Performance benchmark utilities for Prometheus.

This module provides core benchmarking functionality for measuring
query latency, remote write performance, and TSDB operations.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
"""

import asyncio
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import httpx


class QueryComplexity(Enum):
    """Classification of query complexity."""

    SIMPLE = "simple"
    COMPLEX = "complex"
    RANGE = "range"


@dataclass
class BenchmarkSample:
    """A single benchmark measurement.

    Attributes:
        latency_ms: Latency in milliseconds
        success: Whether the operation succeeded
        timestamp: When the sample was taken
        metadata: Additional context
    """

    latency_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run.

    Attributes:
        name: Name of the benchmark
        samples: List of benchmark samples
        iterations: Number of iterations run
        start_time: When the benchmark started
        end_time: When the benchmark ended
    """

    name: str
    samples: list[BenchmarkSample] = field(default_factory=list)
    iterations: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def successful_samples(self) -> list[BenchmarkSample]:
        """Get only successful samples."""
        return [s for s in self.samples if s.success]

    @property
    def latencies(self) -> list[float]:
        """Get latencies from successful samples."""
        return [s.latency_ms for s in self.successful_samples]

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if not self.samples:
            return 0.0
        return (len(self.successful_samples) / len(self.samples)) * 100

    @property
    def p50(self) -> float:
        """50th percentile latency."""
        latencies = sorted(self.latencies)
        if not latencies:
            return 0.0
        return latencies[int(len(latencies) * 0.50)]

    @property
    def p90(self) -> float:
        """90th percentile latency."""
        latencies = sorted(self.latencies)
        if not latencies:
            return 0.0
        return latencies[int(len(latencies) * 0.90)]

    @property
    def p99(self) -> float:
        """99th percentile latency."""
        latencies = sorted(self.latencies)
        if not latencies:
            return 0.0
        return latencies[min(int(len(latencies) * 0.99), len(latencies) - 1)]

    @property
    def min_latency(self) -> float:
        """Minimum latency."""
        latencies = self.latencies
        return min(latencies) if latencies else 0.0

    @property
    def max_latency(self) -> float:
        """Maximum latency."""
        latencies = self.latencies
        return max(latencies) if latencies else 0.0

    @property
    def avg_latency(self) -> float:
        """Average latency."""
        latencies = self.latencies
        return statistics.mean(latencies) if latencies else 0.0

    @property
    def std_dev(self) -> float:
        """Standard deviation of latencies."""
        latencies = self.latencies
        if len(latencies) < 2:
            return 0.0
        return statistics.stdev(latencies)

    @property
    def duration_seconds(self) -> float:
        """Total benchmark duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "success_rate_percent": round(self.success_rate, 2),
            "latency": {
                "p50_ms": round(self.p50, 2),
                "p90_ms": round(self.p90, 2),
                "p99_ms": round(self.p99, 2),
                "min_ms": round(self.min_latency, 2),
                "max_ms": round(self.max_latency, 2),
                "avg_ms": round(self.avg_latency, 2),
                "std_dev_ms": round(self.std_dev, 2),
            },
            "duration_seconds": round(self.duration_seconds, 2),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "sample_count": len(self.samples),
            "successful_count": len(self.successful_samples),
        }


@dataclass
class QueryBenchmarkConfig:
    """Configuration for query benchmarks.

    Attributes:
        prometheus_url: URL of the Prometheus instance
        iterations: Number of iterations per query
        warmup_iterations: Number of warmup iterations
        timeout_seconds: Query timeout
        delay_between_queries_ms: Delay between queries
    """

    prometheus_url: str = "http://localhost:9090"
    iterations: int = 100
    warmup_iterations: int = 5
    timeout_seconds: float = 30.0
    delay_between_queries_ms: float = 100.0


class QueryLatencyBenchmark:
    """
    Benchmarks query latency for Prometheus.

    This class measures query performance for simple, complex,
    and range queries to establish baseline metrics.

    Requirements: 15.1, 15.2, 15.3, 15.7
    """

    # Simple queries - single metric lookups
    SIMPLE_QUERIES = [
        ("up", "Basic up metric"),
        ("prometheus_build_info", "Build info metric"),
        ("prometheus_tsdb_head_series", "TSDB head series count"),
        ("process_cpu_seconds_total", "Process CPU time"),
        ("process_resident_memory_bytes", "Process memory"),
    ]

    # Complex queries - aggregations, rate, joins
    COMPLEX_QUERIES = [
        (
            'rate(prometheus_http_requests_total[5m])',
            "HTTP request rate"
        ),
        (
            'sum(rate(prometheus_http_requests_total[5m])) by (handler)',
            "HTTP request rate by handler"
        ),
        (
            'histogram_quantile(0.99, rate(prometheus_http_request_duration_seconds_bucket[5m]))',
            "99th percentile request duration"
        ),
        (
            'avg(rate(process_cpu_seconds_total[5m])) * 100',
            "Average CPU usage percentage"
        ),
        (
            'topk(10, sum(rate(prometheus_http_requests_total[5m])) by (handler))',
            "Top 10 handlers by request rate"
        ),
    ]

    # Range query durations
    RANGE_DURATIONS = [
        ("1h", 3600),
        ("6h", 21600),
        ("24h", 86400),
        ("7d", 604800),
    ]

    def __init__(self, config: QueryBenchmarkConfig):
        """Initialize the benchmark.

        Args:
            config: Benchmark configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _execute_query(
        self,
        query: str,
        is_range: bool = False,
        range_seconds: int = 3600,
    ) -> BenchmarkSample:
        """Execute a single query and measure latency.

        Args:
            query: PromQL query string
            is_range: Whether this is a range query
            range_seconds: Duration for range queries

        Returns:
            Benchmark sample with latency measurement
        """
        if not self._client:
            return BenchmarkSample(latency_ms=0, success=False)

        start_time = time.perf_counter()
        success = False
        metadata: dict[str, Any] = {"query": query}

        try:
            if is_range:
                end_ts = time.time()
                start_ts = end_ts - range_seconds
                response = await self._client.get(
                    f"{self.config.prometheus_url}/api/v1/query_range",
                    params={
                        "query": query,
                        "start": start_ts,
                        "end": end_ts,
                        "step": "60s",
                    },
                    timeout=self.config.timeout_seconds,
                )
            else:
                response = await self._client.get(
                    f"{self.config.prometheus_url}/api/v1/query",
                    params={"query": query},
                    timeout=self.config.timeout_seconds,
                )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    success = True
                    result = data.get("data", {}).get("result", [])
                    metadata["result_count"] = len(result)

            metadata["status_code"] = response.status_code

        except httpx.TimeoutException:
            metadata["error"] = "timeout"
        except Exception as e:
            metadata["error"] = str(e)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        return BenchmarkSample(
            latency_ms=latency_ms,
            success=success,
            metadata=metadata,
        )

    async def _run_warmup(self, query: str, is_range: bool = False) -> None:
        """Run warmup iterations for a query.

        Args:
            query: Query to warm up
            is_range: Whether this is a range query
        """
        for _ in range(self.config.warmup_iterations):
            await self._execute_query(query, is_range)
            await asyncio.sleep(self.config.delay_between_queries_ms / 1000)

    async def benchmark_simple_queries(self) -> list[BenchmarkResult]:
        """Benchmark simple query latency.

        Requirements: 15.1

        Returns:
            List of benchmark results for simple queries
        """
        results = []

        async with httpx.AsyncClient() as client:
            self._client = client

            for query, description in self.SIMPLE_QUERIES:
                result = BenchmarkResult(
                    name=f"simple_query_{description.lower().replace(' ', '_')}",
                )
                result.start_time = datetime.utcnow()

                # Warmup
                await self._run_warmup(query)

                # Benchmark iterations
                for _ in range(self.config.iterations):
                    sample = await self._execute_query(query)
                    result.samples.append(sample)
                    result.iterations += 1
                    await asyncio.sleep(self.config.delay_between_queries_ms / 1000)

                result.end_time = datetime.utcnow()
                results.append(result)

        self._client = None
        return results

    async def benchmark_complex_queries(self) -> list[BenchmarkResult]:
        """Benchmark complex query latency.

        Requirements: 15.2

        Returns:
            List of benchmark results for complex queries
        """
        results = []

        async with httpx.AsyncClient() as client:
            self._client = client

            for query, description in self.COMPLEX_QUERIES:
                result = BenchmarkResult(
                    name=f"complex_query_{description.lower().replace(' ', '_')}",
                )
                result.start_time = datetime.utcnow()

                # Warmup
                await self._run_warmup(query)

                # Benchmark iterations
                for _ in range(self.config.iterations):
                    sample = await self._execute_query(query)
                    result.samples.append(sample)
                    result.iterations += 1
                    await asyncio.sleep(self.config.delay_between_queries_ms / 1000)

                result.end_time = datetime.utcnow()
                results.append(result)

        self._client = None
        return results

    async def benchmark_range_queries(self) -> list[BenchmarkResult]:
        """Benchmark range query latency for different time ranges.

        Requirements: 15.3

        Returns:
            List of benchmark results for range queries
        """
        results = []
        base_query = "rate(prometheus_http_requests_total[5m])"

        async with httpx.AsyncClient() as client:
            self._client = client

            for duration_name, duration_seconds in self.RANGE_DURATIONS:
                result = BenchmarkResult(
                    name=f"range_query_{duration_name}",
                )
                result.start_time = datetime.utcnow()

                # Warmup
                await self._run_warmup(base_query, is_range=True)

                # Benchmark iterations
                for _ in range(self.config.iterations):
                    sample = await self._execute_query(
                        base_query,
                        is_range=True,
                        range_seconds=duration_seconds,
                    )
                    sample.metadata["range_duration"] = duration_name
                    result.samples.append(sample)
                    result.iterations += 1
                    await asyncio.sleep(self.config.delay_between_queries_ms / 1000)

                result.end_time = datetime.utcnow()
                results.append(result)

        self._client = None
        return results

    async def run_all_benchmarks(self) -> dict[str, list[BenchmarkResult]]:
        """Run all query latency benchmarks.

        Returns:
            Dictionary with results for each query type
        """
        return {
            "simple": await self.benchmark_simple_queries(),
            "complex": await self.benchmark_complex_queries(),
            "range": await self.benchmark_range_queries(),
        }
