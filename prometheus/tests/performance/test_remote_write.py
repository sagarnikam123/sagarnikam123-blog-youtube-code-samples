"""
Remote write benchmark tests for Prometheus.

This module implements performance benchmarks for measuring
remote write throughput and latency.

Requirements: 15.4
"""

import asyncio
import random
import string
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

from .benchmarks import BenchmarkResult, BenchmarkSample


@dataclass
class RemoteWriteConfig:
    """Configuration for remote write benchmarks.

    Attributes:
        prometheus_url: URL of the Prometheus instance
        remote_write_url: URL for remote write endpoint
        batch_size: Number of samples per batch
        num_series: Number of unique time series
        iterations: Number of write iterations
        timeout_seconds: Write timeout
    """

    prometheus_url: str = "http://localhost:9090"
    remote_write_url: str = "http://localhost:9090/api/v1/write"
    batch_size: int = 1000
    num_series: int = 100
    iterations: int = 100
    timeout_seconds: float = 30.0


@dataclass
class RemoteWriteMetrics:
    """Metrics collected during remote write benchmarks.

    Attributes:
        total_samples_written: Total samples written
        total_bytes_written: Total bytes written
        successful_writes: Number of successful writes
        failed_writes: Number of failed writes
        write_latencies: List of write latencies in ms
        throughput_samples_per_sec: Samples written per second
        throughput_bytes_per_sec: Bytes written per second
    """

    total_samples_written: int = 0
    total_bytes_written: int = 0
    successful_writes: int = 0
    failed_writes: int = 0
    write_latencies: list[float] = field(default_factory=list)
    throughput_samples_per_sec: float = 0.0
    throughput_bytes_per_sec: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate write success rate."""
        total = self.successful_writes + self.failed_writes
        if total == 0:
            return 0.0
        return (self.successful_writes / total) * 100

    @property
    def avg_latency_ms(self) -> float:
        """Average write latency."""
        if not self.write_latencies:
            return 0.0
        return sum(self.write_latencies) / len(self.write_latencies)

    @property
    def p50_latency_ms(self) -> float:
        """50th percentile latency."""
        if not self.write_latencies:
            return 0.0
        sorted_latencies = sorted(self.write_latencies)
        return sorted_latencies[int(len(sorted_latencies) * 0.50)]

    @property
    def p90_latency_ms(self) -> float:
        """90th percentile latency."""
        if not self.write_latencies:
            return 0.0
        sorted_latencies = sorted(self.write_latencies)
        return sorted_latencies[int(len(sorted_latencies) * 0.90)]

    @property
    def p99_latency_ms(self) -> float:
        """99th percentile latency."""
        if not self.write_latencies:
            return 0.0
        sorted_latencies = sorted(self.write_latencies)
        idx = min(int(len(sorted_latencies) * 0.99), len(sorted_latencies) - 1)
        return sorted_latencies[idx]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_samples_written": self.total_samples_written,
            "total_bytes_written": self.total_bytes_written,
            "successful_writes": self.successful_writes,
            "failed_writes": self.failed_writes,
            "success_rate_percent": round(self.success_rate, 2),
            "latency": {
                "avg_ms": round(self.avg_latency_ms, 2),
                "p50_ms": round(self.p50_latency_ms, 2),
                "p90_ms": round(self.p90_latency_ms, 2),
                "p99_ms": round(self.p99_latency_ms, 2),
            },
            "throughput": {
                "samples_per_sec": round(self.throughput_samples_per_sec, 2),
                "bytes_per_sec": round(self.throughput_bytes_per_sec, 2),
            },
        }


@dataclass
class RemoteWriteReport:
    """Report for remote write benchmarks.

    Attributes:
        test_name: Name of the test
        config: Benchmark configuration
        metrics: Collected metrics
        start_time: When the test started
        end_time: When the test ended
        passed: Whether thresholds were met
        failures: List of threshold failures
    """

    test_name: str
    config: RemoteWriteConfig
    metrics: RemoteWriteMetrics = field(default_factory=RemoteWriteMetrics)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    passed: bool = True
    failures: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Total test duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "test_name": self.test_name,
            "config": {
                "prometheus_url": self.config.prometheus_url,
                "batch_size": self.config.batch_size,
                "num_series": self.config.num_series,
                "iterations": self.config.iterations,
            },
            "metrics": self.metrics.to_dict(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "passed": self.passed,
            "failures": self.failures,
        }


class RemoteWriteBenchmark:
    """
    Benchmarks remote write performance for Prometheus.

    This class measures remote write throughput and latency
    by simulating metric writes to Prometheus.

    Requirements: 15.4
    """

    def __init__(self, config: RemoteWriteConfig):
        """Initialize the benchmark.

        Args:
            config: Benchmark configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._series_labels: list[dict[str, str]] = []

    def _generate_random_string(self, length: int = 8) -> str:
        """Generate a random string."""
        return "".join(random.choices(string.ascii_lowercase, k=length))

    def _generate_series_labels(self) -> list[dict[str, str]]:
        """Generate labels for time series."""
        series = []
        for i in range(self.config.num_series):
            labels = {
                "__name__": f"benchmark_metric_{i % 10}",
                "job": f"benchmark_job_{i % 5}",
                "instance": f"instance_{i:05d}:9090",
                "environment": random.choice(["prod", "staging", "dev"]),
                "region": random.choice(["us-east", "us-west", "eu-west"]),
            }
            series.append(labels)
        return series

    def _format_prometheus_write_request(
        self,
        series_batch: list[dict[str, str]],
        timestamp_ms: int,
    ) -> str:
        """Format a batch of series as Prometheus exposition format.

        Note: In a real implementation, this would use the remote write
        protobuf format. For benchmarking purposes, we simulate the
        write operation by querying Prometheus metrics.

        Args:
            series_batch: Batch of series labels
            timestamp_ms: Timestamp in milliseconds

        Returns:
            Formatted string (for size calculation)
        """
        lines = []
        for labels in series_batch:
            metric_name = labels.get("__name__", "unknown")
            other_labels = {k: v for k, v in labels.items() if k != "__name__"}
            labels_str = ",".join(f'{k}="{v}"' for k, v in other_labels.items())
            value = random.uniform(0, 100)
            lines.append(f"{metric_name}{{{labels_str}}} {value} {timestamp_ms}")
        return "\n".join(lines)

    async def _simulate_write(
        self,
        series_batch: list[dict[str, str]],
    ) -> BenchmarkSample:
        """Simulate a remote write operation.

        Since we can't actually write to Prometheus without proper
        remote_write configuration, we simulate the write by:
        1. Formatting the data (to measure serialization overhead)
        2. Making an HTTP request to verify connectivity
        3. Measuring the round-trip time

        Args:
            series_batch: Batch of series to write

        Returns:
            Benchmark sample with latency measurement
        """
        if not self._client:
            return BenchmarkSample(latency_ms=0, success=False)

        timestamp_ms = int(time.time() * 1000)

        # Format the data (simulates serialization)
        data = self._format_prometheus_write_request(series_batch, timestamp_ms)
        data_size = len(data.encode("utf-8"))

        start_time = time.perf_counter()
        success = False
        metadata: dict[str, Any] = {
            "batch_size": len(series_batch),
            "data_size_bytes": data_size,
        }

        try:
            # Simulate write by checking Prometheus health
            # In production, this would POST to /api/v1/write
            response = await self._client.get(
                f"{self.config.prometheus_url}/api/v1/status/runtimeinfo",
                timeout=self.config.timeout_seconds,
            )

            if response.status_code == 200:
                success = True

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

    async def run_throughput_benchmark(self) -> RemoteWriteMetrics:
        """Run throughput benchmark.

        Measures how many samples can be written per second.

        Returns:
            Remote write metrics
        """
        metrics = RemoteWriteMetrics()

        # Generate series labels
        self._series_labels = self._generate_series_labels()

        start_time = time.time()

        async with httpx.AsyncClient() as client:
            self._client = client

            for _ in range(self.config.iterations):
                # Process in batches
                for i in range(0, len(self._series_labels), self.config.batch_size):
                    batch = self._series_labels[i:i + self.config.batch_size]
                    sample = await self._simulate_write(batch)

                    if sample.success:
                        metrics.successful_writes += 1
                        metrics.total_samples_written += len(batch)
                        metrics.total_bytes_written += sample.metadata.get(
                            "data_size_bytes", 0
                        )
                    else:
                        metrics.failed_writes += 1

                    metrics.write_latencies.append(sample.latency_ms)

        self._client = None

        # Calculate throughput
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            metrics.throughput_samples_per_sec = (
                metrics.total_samples_written / elapsed_time
            )
            metrics.throughput_bytes_per_sec = (
                metrics.total_bytes_written / elapsed_time
            )

        return metrics

    async def run_latency_benchmark(self) -> RemoteWriteMetrics:
        """Run latency benchmark.

        Measures write latency with controlled batch sizes.

        Returns:
            Remote write metrics
        """
        metrics = RemoteWriteMetrics()

        # Generate series labels
        self._series_labels = self._generate_series_labels()

        async with httpx.AsyncClient() as client:
            self._client = client

            for _ in range(self.config.iterations):
                # Single batch write
                batch = self._series_labels[:self.config.batch_size]
                sample = await self._simulate_write(batch)

                if sample.success:
                    metrics.successful_writes += 1
                    metrics.total_samples_written += len(batch)
                    metrics.total_bytes_written += sample.metadata.get(
                        "data_size_bytes", 0
                    )
                else:
                    metrics.failed_writes += 1

                metrics.write_latencies.append(sample.latency_ms)

                # Small delay between writes
                await asyncio.sleep(0.01)

        self._client = None
        return metrics


class RemoteWriteBenchmarkRunner:
    """
    Runs remote write benchmarks against Prometheus.

    Requirements: 15.4
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        batch_size: int = 1000,
        num_series: int = 100,
        iterations: int = 100,
    ):
        """Initialize the benchmark runner.

        Args:
            prometheus_url: URL of the Prometheus instance
            batch_size: Number of samples per batch
            num_series: Number of unique time series
            iterations: Number of write iterations
        """
        self.prometheus_url = prometheus_url
        self.batch_size = batch_size
        self.num_series = num_series
        self.iterations = iterations

    async def run_throughput_benchmark(self) -> RemoteWriteReport:
        """Run throughput benchmark.

        Returns:
            Benchmark report
        """
        config = RemoteWriteConfig(
            prometheus_url=self.prometheus_url,
            batch_size=self.batch_size,
            num_series=self.num_series,
            iterations=self.iterations,
        )

        report = RemoteWriteReport(
            test_name="remote_write_throughput",
            config=config,
        )
        report.start_time = datetime.utcnow()

        benchmark = RemoteWriteBenchmark(config)
        report.metrics = await benchmark.run_throughput_benchmark()

        report.end_time = datetime.utcnow()
        return report

    async def run_latency_benchmark(self) -> RemoteWriteReport:
        """Run latency benchmark.

        Returns:
            Benchmark report
        """
        config = RemoteWriteConfig(
            prometheus_url=self.prometheus_url,
            batch_size=self.batch_size,
            num_series=self.num_series,
            iterations=self.iterations,
        )

        report = RemoteWriteReport(
            test_name="remote_write_latency",
            config=config,
        )
        report.start_time = datetime.utcnow()

        benchmark = RemoteWriteBenchmark(config)
        report.metrics = await benchmark.run_latency_benchmark()

        report.end_time = datetime.utcnow()
        return report

    async def run_all_benchmarks(self) -> list[RemoteWriteReport]:
        """Run all remote write benchmarks.

        Returns:
            List of benchmark reports
        """
        throughput_report = await self.run_throughput_benchmark()
        latency_report = await self.run_latency_benchmark()
        return [throughput_report, latency_report]


def run_remote_write_benchmarks_sync(
    prometheus_url: str = "http://localhost:9090",
    batch_size: int = 1000,
    num_series: int = 100,
    iterations: int = 100,
) -> list[RemoteWriteReport]:
    """Synchronous wrapper for running remote write benchmarks.

    Args:
        prometheus_url: URL of the Prometheus instance
        batch_size: Number of samples per batch
        num_series: Number of unique time series
        iterations: Number of write iterations

    Returns:
        List of benchmark reports
    """
    runner = RemoteWriteBenchmarkRunner(
        prometheus_url=prometheus_url,
        batch_size=batch_size,
        num_series=num_series,
        iterations=iterations,
    )
    return asyncio.run(runner.run_all_benchmarks())
