"""
Query latency benchmark tests for Prometheus.

This module implements performance benchmarks for measuring
query latency across simple, complex, and range queries.

Requirements: 15.1, 15.2, 15.3, 15.7
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .benchmarks import (
    BenchmarkResult,
    QueryBenchmarkConfig,
    QueryLatencyBenchmark,
)


@dataclass
class QueryLatencyReport:
    """Report for query latency benchmarks.

    Attributes:
        test_name: Name of the test
        prometheus_url: URL of the Prometheus instance
        start_time: When the test started
        end_time: When the test ended
        simple_results: Results for simple queries
        complex_results: Results for complex queries
        range_results: Results for range queries
        thresholds: Pass/fail thresholds
        passed: Whether all thresholds were met
    """

    test_name: str
    prometheus_url: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    simple_results: list[BenchmarkResult] = field(default_factory=list)
    complex_results: list[BenchmarkResult] = field(default_factory=list)
    range_results: list[BenchmarkResult] = field(default_factory=list)
    thresholds: dict[str, float] = field(default_factory=dict)
    passed: bool = True
    failures: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Total test duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def _aggregate_results(
        self,
        results: list[BenchmarkResult],
    ) -> dict[str, float]:
        """Aggregate results across multiple benchmarks."""
        if not results:
            return {}

        all_latencies = []
        for result in results:
            all_latencies.extend(result.latencies)

        if not all_latencies:
            return {}

        sorted_latencies = sorted(all_latencies)
        n = len(sorted_latencies)

        return {
            "p50_ms": sorted_latencies[int(n * 0.50)],
            "p90_ms": sorted_latencies[int(n * 0.90)],
            "p99_ms": sorted_latencies[min(int(n * 0.99), n - 1)],
            "avg_ms": sum(all_latencies) / n,
            "min_ms": sorted_latencies[0],
            "max_ms": sorted_latencies[-1],
        }

    def check_thresholds(self) -> None:
        """Check if results meet thresholds."""
        self.passed = True
        self.failures = []

        # Check simple query threshold
        simple_agg = self._aggregate_results(self.simple_results)
        if simple_agg and "simple_query_latency_ms" in self.thresholds:
            threshold = self.thresholds["simple_query_latency_ms"]
            if simple_agg.get("p99_ms", 0) > threshold:
                self.passed = False
                self.failures.append(
                    f"Simple query p99 ({simple_agg['p99_ms']:.2f}ms) "
                    f"exceeds threshold ({threshold}ms)"
                )

        # Check complex query threshold
        complex_agg = self._aggregate_results(self.complex_results)
        if complex_agg and "complex_query_latency_ms" in self.thresholds:
            threshold = self.thresholds["complex_query_latency_ms"]
            if complex_agg.get("p99_ms", 0) > threshold:
                self.passed = False
                self.failures.append(
                    f"Complex query p99 ({complex_agg['p99_ms']:.2f}ms) "
                    f"exceeds threshold ({threshold}ms)"
                )

        # Check range query thresholds
        for result in self.range_results:
            if "1h" in result.name and "range_query_1h_latency_ms" in self.thresholds:
                threshold = self.thresholds["range_query_1h_latency_ms"]
                if result.p99 > threshold:
                    self.passed = False
                    self.failures.append(
                        f"Range query 1h p99 ({result.p99:.2f}ms) "
                        f"exceeds threshold ({threshold}ms)"
                    )
            elif "24h" in result.name and "range_query_24h_latency_ms" in self.thresholds:
                threshold = self.thresholds["range_query_24h_latency_ms"]
                if result.p99 > threshold:
                    self.passed = False
                    self.failures.append(
                        f"Range query 24h p99 ({result.p99:.2f}ms) "
                        f"exceeds threshold ({threshold}ms)"
                    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "test_name": self.test_name,
            "prometheus_url": self.prometheus_url,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "passed": self.passed,
            "failures": self.failures,
            "summary": {
                "simple_queries": self._aggregate_results(self.simple_results),
                "complex_queries": self._aggregate_results(self.complex_results),
                "range_queries": {
                    r.name: {"p50_ms": r.p50, "p90_ms": r.p90, "p99_ms": r.p99}
                    for r in self.range_results
                },
            },
            "detailed_results": {
                "simple": [r.to_dict() for r in self.simple_results],
                "complex": [r.to_dict() for r in self.complex_results],
                "range": [r.to_dict() for r in self.range_results],
            },
            "thresholds": self.thresholds,
        }


class QueryLatencyBenchmarkRunner:
    """
    Runs query latency benchmarks against Prometheus.

    This class orchestrates the execution of simple, complex,
    and range query benchmarks and generates reports.

    Requirements: 15.1, 15.2, 15.3, 15.7
    """

    DEFAULT_THRESHOLDS = {
        "simple_query_latency_ms": 50,
        "complex_query_latency_ms": 500,
        "range_query_1h_latency_ms": 200,
        "range_query_24h_latency_ms": 1000,
    }

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        iterations: int = 100,
        thresholds: Optional[dict[str, float]] = None,
    ):
        """Initialize the benchmark runner.

        Args:
            prometheus_url: URL of the Prometheus instance
            iterations: Number of iterations per benchmark
            thresholds: Pass/fail thresholds
        """
        self.prometheus_url = prometheus_url
        self.iterations = iterations
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS

    async def run_simple_query_benchmarks(
        self,
        iterations: Optional[int] = None,
    ) -> list[BenchmarkResult]:
        """Run simple query benchmarks.

        Requirements: 15.1

        Args:
            iterations: Override default iterations

        Returns:
            List of benchmark results
        """
        config = QueryBenchmarkConfig(
            prometheus_url=self.prometheus_url,
            iterations=iterations or self.iterations,
        )
        benchmark = QueryLatencyBenchmark(config)
        return await benchmark.benchmark_simple_queries()

    async def run_complex_query_benchmarks(
        self,
        iterations: Optional[int] = None,
    ) -> list[BenchmarkResult]:
        """Run complex query benchmarks.

        Requirements: 15.2

        Args:
            iterations: Override default iterations

        Returns:
            List of benchmark results
        """
        config = QueryBenchmarkConfig(
            prometheus_url=self.prometheus_url,
            iterations=iterations or self.iterations,
        )
        benchmark = QueryLatencyBenchmark(config)
        return await benchmark.benchmark_complex_queries()

    async def run_range_query_benchmarks(
        self,
        iterations: Optional[int] = None,
    ) -> list[BenchmarkResult]:
        """Run range query benchmarks.

        Requirements: 15.3

        Args:
            iterations: Override default iterations

        Returns:
            List of benchmark results
        """
        config = QueryBenchmarkConfig(
            prometheus_url=self.prometheus_url,
            iterations=iterations or self.iterations,
        )
        benchmark = QueryLatencyBenchmark(config)
        return await benchmark.benchmark_range_queries()

    async def run_all_benchmarks(
        self,
        iterations: Optional[int] = None,
    ) -> QueryLatencyReport:
        """Run all query latency benchmarks.

        Requirements: 15.1, 15.2, 15.3, 15.7

        Args:
            iterations: Override default iterations

        Returns:
            Complete benchmark report
        """
        report = QueryLatencyReport(
            test_name="query_latency_benchmark",
            prometheus_url=self.prometheus_url,
            thresholds=self.thresholds,
        )
        report.start_time = datetime.utcnow()

        config = QueryBenchmarkConfig(
            prometheus_url=self.prometheus_url,
            iterations=iterations or self.iterations,
        )
        benchmark = QueryLatencyBenchmark(config)

        # Run all benchmarks
        results = await benchmark.run_all_benchmarks()

        report.simple_results = results.get("simple", [])
        report.complex_results = results.get("complex", [])
        report.range_results = results.get("range", [])

        report.end_time = datetime.utcnow()
        report.check_thresholds()

        return report


def run_query_latency_benchmarks_sync(
    prometheus_url: str = "http://localhost:9090",
    iterations: int = 100,
    thresholds: Optional[dict[str, float]] = None,
) -> QueryLatencyReport:
    """Synchronous wrapper for running query latency benchmarks.

    Args:
        prometheus_url: URL of the Prometheus instance
        iterations: Number of iterations per benchmark
        thresholds: Pass/fail thresholds

    Returns:
        Benchmark report
    """
    runner = QueryLatencyBenchmarkRunner(
        prometheus_url=prometheus_url,
        iterations=iterations,
        thresholds=thresholds,
    )
    return asyncio.run(runner.run_all_benchmarks())
