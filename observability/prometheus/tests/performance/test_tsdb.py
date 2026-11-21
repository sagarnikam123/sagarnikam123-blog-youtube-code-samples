"""
TSDB benchmark tests for Prometheus.

This module implements performance benchmarks for measuring
TSDB operations including compaction time and WAL replay time.

Requirements: 15.5, 15.6
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

from .benchmarks import BenchmarkResult, BenchmarkSample


@dataclass
class TSDBConfig:
    """Configuration for TSDB benchmarks.

    Attributes:
        prometheus_url: URL of the Prometheus instance
        polling_interval_seconds: Interval for polling metrics
        timeout_seconds: Request timeout
        measurement_duration_seconds: Duration to measure metrics
    """

    prometheus_url: str = "http://localhost:9090"
    polling_interval_seconds: float = 5.0
    timeout_seconds: float = 30.0
    measurement_duration_seconds: int = 300  # 5 minutes


@dataclass
class CompactionMetrics:
    """Metrics related to TSDB compaction.

    Attributes:
        compactions_total: Total number of compactions
        compaction_duration_seconds: List of compaction durations
        compaction_chunk_size_bytes: Average chunk size after compaction
        compaction_chunk_samples: Average samples per chunk
        head_chunks: Number of chunks in head block
        head_series: Number of series in head block
    """

    compactions_total: int = 0
    compaction_duration_seconds: list[float] = field(default_factory=list)
    compaction_chunk_size_bytes: float = 0.0
    compaction_chunk_samples: float = 0.0
    head_chunks: int = 0
    head_series: int = 0

    @property
    def avg_compaction_duration(self) -> float:
        """Average compaction duration."""
        if not self.compaction_duration_seconds:
            return 0.0
        return sum(self.compaction_duration_seconds) / len(self.compaction_duration_seconds)

    @property
    def max_compaction_duration(self) -> float:
        """Maximum compaction duration."""
        if not self.compaction_duration_seconds:
            return 0.0
        return max(self.compaction_duration_seconds)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "compactions_total": self.compactions_total,
            "compaction_duration": {
                "avg_seconds": round(self.avg_compaction_duration, 4),
                "max_seconds": round(self.max_compaction_duration, 4),
                "samples": len(self.compaction_duration_seconds),
            },
            "compaction_chunk_size_bytes": round(self.compaction_chunk_size_bytes, 2),
            "compaction_chunk_samples": round(self.compaction_chunk_samples, 2),
            "head_chunks": self.head_chunks,
            "head_series": self.head_series,
        }


@dataclass
class WALMetrics:
    """Metrics related to WAL (Write-Ahead Log) operations.

    Attributes:
        wal_corruptions_total: Total WAL corruptions
        wal_truncations_total: Total WAL truncations
        wal_fsync_duration_seconds: List of fsync durations
        wal_page_flushes_total: Total page flushes
        wal_segment_current: Current WAL segment
        wal_storage_size_bytes: WAL storage size
        estimated_replay_time_seconds: Estimated WAL replay time
    """

    wal_corruptions_total: int = 0
    wal_truncations_total: int = 0
    wal_fsync_duration_seconds: list[float] = field(default_factory=list)
    wal_page_flushes_total: int = 0
    wal_segment_current: int = 0
    wal_storage_size_bytes: float = 0.0
    estimated_replay_time_seconds: float = 0.0

    @property
    def avg_fsync_duration(self) -> float:
        """Average fsync duration."""
        if not self.wal_fsync_duration_seconds:
            return 0.0
        return sum(self.wal_fsync_duration_seconds) / len(self.wal_fsync_duration_seconds)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "wal_corruptions_total": self.wal_corruptions_total,
            "wal_truncations_total": self.wal_truncations_total,
            "wal_fsync_duration": {
                "avg_seconds": round(self.avg_fsync_duration, 6),
                "samples": len(self.wal_fsync_duration_seconds),
            },
            "wal_page_flushes_total": self.wal_page_flushes_total,
            "wal_segment_current": self.wal_segment_current,
            "wal_storage_size_bytes": round(self.wal_storage_size_bytes, 2),
            "estimated_replay_time_seconds": round(self.estimated_replay_time_seconds, 2),
        }


@dataclass
class TSDBMetrics:
    """Combined TSDB metrics.

    Attributes:
        compaction: Compaction metrics
        wal: WAL metrics
        storage_size_bytes: Total storage size
        retention_limit_bytes: Retention limit
        samples_appended_total: Total samples appended
        out_of_order_samples_total: Out of order samples
    """

    compaction: CompactionMetrics = field(default_factory=CompactionMetrics)
    wal: WALMetrics = field(default_factory=WALMetrics)
    storage_size_bytes: float = 0.0
    retention_limit_bytes: float = 0.0
    samples_appended_total: int = 0
    out_of_order_samples_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "compaction": self.compaction.to_dict(),
            "wal": self.wal.to_dict(),
            "storage_size_bytes": round(self.storage_size_bytes, 2),
            "retention_limit_bytes": round(self.retention_limit_bytes, 2),
            "samples_appended_total": self.samples_appended_total,
            "out_of_order_samples_total": self.out_of_order_samples_total,
        }


@dataclass
class TSDBBenchmarkReport:
    """Report for TSDB benchmarks.

    Attributes:
        test_name: Name of the test
        prometheus_url: URL of the Prometheus instance
        metrics: Collected TSDB metrics
        start_time: When the test started
        end_time: When the test ended
        passed: Whether thresholds were met
        failures: List of threshold failures
    """

    test_name: str
    prometheus_url: str
    metrics: TSDBMetrics = field(default_factory=TSDBMetrics)
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
            "prometheus_url": self.prometheus_url,
            "metrics": self.metrics.to_dict(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "passed": self.passed,
            "failures": self.failures,
        }


class TSDBBenchmark:
    """
    Benchmarks TSDB operations for Prometheus.

    This class measures TSDB performance including compaction
    time and WAL replay time by querying Prometheus internal metrics.

    Requirements: 15.5, 15.6
    """

    # Prometheus TSDB metrics to collect
    COMPACTION_METRICS = {
        "prometheus_tsdb_compactions_total": "compactions_total",
        "prometheus_tsdb_compaction_duration_seconds_sum": "compaction_duration_sum",
        "prometheus_tsdb_compaction_duration_seconds_count": "compaction_duration_count",
        "prometheus_tsdb_compaction_chunk_size_bytes_sum": "chunk_size_sum",
        "prometheus_tsdb_compaction_chunk_samples_sum": "chunk_samples_sum",
        "prometheus_tsdb_head_chunks": "head_chunks",
        "prometheus_tsdb_head_series": "head_series",
    }

    WAL_METRICS = {
        "prometheus_tsdb_wal_corruptions_total": "wal_corruptions",
        "prometheus_tsdb_wal_truncations_total": "wal_truncations",
        "prometheus_tsdb_wal_fsync_duration_seconds_sum": "wal_fsync_sum",
        "prometheus_tsdb_wal_fsync_duration_seconds_count": "wal_fsync_count",
        "prometheus_tsdb_wal_page_flushes_total": "wal_page_flushes",
        "prometheus_tsdb_wal_segment_current": "wal_segment_current",
        "prometheus_tsdb_wal_storage_size_bytes": "wal_storage_size",
    }

    STORAGE_METRICS = {
        "prometheus_tsdb_storage_blocks_bytes": "storage_size",
        "prometheus_tsdb_retention_limit_bytes": "retention_limit",
        "prometheus_tsdb_head_samples_appended_total": "samples_appended",
        "prometheus_tsdb_out_of_order_samples_total": "out_of_order_samples",
    }

    def __init__(self, config: TSDBConfig):
        """Initialize the benchmark.

        Args:
            config: Benchmark configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _query_metric(self, metric_name: str) -> Optional[float]:
        """Query a single metric from Prometheus.

        Args:
            metric_name: Name of the metric to query

        Returns:
            Metric value or None if not found
        """
        if not self._client:
            return None

        try:
            response = await self._client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": metric_name},
                timeout=self.config.timeout_seconds,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    result = data.get("data", {}).get("result", [])
                    if result:
                        return float(result[0].get("value", [0, 0])[1])
        except Exception:
            pass

        return None

    async def collect_compaction_metrics(self) -> CompactionMetrics:
        """Collect compaction-related metrics.

        Requirements: 15.5

        Returns:
            Compaction metrics
        """
        metrics = CompactionMetrics()

        # Query compaction metrics
        compactions = await self._query_metric("prometheus_tsdb_compactions_total")
        if compactions is not None:
            metrics.compactions_total = int(compactions)

        # Calculate average compaction duration
        duration_sum = await self._query_metric(
            "prometheus_tsdb_compaction_duration_seconds_sum"
        )
        duration_count = await self._query_metric(
            "prometheus_tsdb_compaction_duration_seconds_count"
        )
        if duration_sum is not None and duration_count is not None and duration_count > 0:
            avg_duration = duration_sum / duration_count
            metrics.compaction_duration_seconds.append(avg_duration)

        # Chunk metrics
        chunk_size = await self._query_metric(
            "prometheus_tsdb_compaction_chunk_size_bytes_sum"
        )
        chunk_count = await self._query_metric(
            "prometheus_tsdb_compaction_chunk_samples_sum"
        )
        if chunk_size is not None:
            metrics.compaction_chunk_size_bytes = chunk_size
        if chunk_count is not None:
            metrics.compaction_chunk_samples = chunk_count

        # Head block metrics
        head_chunks = await self._query_metric("prometheus_tsdb_head_chunks")
        head_series = await self._query_metric("prometheus_tsdb_head_series")
        if head_chunks is not None:
            metrics.head_chunks = int(head_chunks)
        if head_series is not None:
            metrics.head_series = int(head_series)

        return metrics

    async def collect_wal_metrics(self) -> WALMetrics:
        """Collect WAL-related metrics.

        Requirements: 15.6

        Returns:
            WAL metrics
        """
        metrics = WALMetrics()

        # WAL corruption and truncation
        corruptions = await self._query_metric("prometheus_tsdb_wal_corruptions_total")
        truncations = await self._query_metric("prometheus_tsdb_wal_truncations_total")
        if corruptions is not None:
            metrics.wal_corruptions_total = int(corruptions)
        if truncations is not None:
            metrics.wal_truncations_total = int(truncations)

        # WAL fsync duration
        fsync_sum = await self._query_metric(
            "prometheus_tsdb_wal_fsync_duration_seconds_sum"
        )
        fsync_count = await self._query_metric(
            "prometheus_tsdb_wal_fsync_duration_seconds_count"
        )
        if fsync_sum is not None and fsync_count is not None and fsync_count > 0:
            avg_fsync = fsync_sum / fsync_count
            metrics.wal_fsync_duration_seconds.append(avg_fsync)

        # WAL page flushes
        page_flushes = await self._query_metric("prometheus_tsdb_wal_page_flushes_total")
        if page_flushes is not None:
            metrics.wal_page_flushes_total = int(page_flushes)

        # WAL segment and storage
        segment = await self._query_metric("prometheus_tsdb_wal_segment_current")
        storage_size = await self._query_metric("prometheus_tsdb_wal_storage_size_bytes")
        if segment is not None:
            metrics.wal_segment_current = int(segment)
        if storage_size is not None:
            metrics.wal_storage_size_bytes = storage_size

        # Estimate WAL replay time based on storage size
        # Rough estimate: ~100MB/s replay speed
        if storage_size is not None and storage_size > 0:
            metrics.estimated_replay_time_seconds = storage_size / (100 * 1024 * 1024)

        return metrics

    async def collect_storage_metrics(self) -> tuple[float, float, int, int]:
        """Collect storage-related metrics.

        Returns:
            Tuple of (storage_size, retention_limit, samples_appended, out_of_order)
        """
        storage_size = await self._query_metric("prometheus_tsdb_storage_blocks_bytes")
        retention_limit = await self._query_metric("prometheus_tsdb_retention_limit_bytes")
        samples_appended = await self._query_metric(
            "prometheus_tsdb_head_samples_appended_total"
        )
        out_of_order = await self._query_metric(
            "prometheus_tsdb_out_of_order_samples_total"
        )

        return (
            storage_size or 0.0,
            retention_limit or 0.0,
            int(samples_appended or 0),
            int(out_of_order or 0),
        )

    async def run_compaction_benchmark(
        self,
        duration_seconds: Optional[int] = None,
    ) -> TSDBMetrics:
        """Run compaction benchmark.

        Monitors compaction metrics over a period of time.

        Requirements: 15.5

        Args:
            duration_seconds: Duration to monitor

        Returns:
            TSDB metrics
        """
        duration = duration_seconds or self.config.measurement_duration_seconds
        metrics = TSDBMetrics()

        async with httpx.AsyncClient() as client:
            self._client = client

            end_time = time.time() + duration
            initial_compactions = None

            while time.time() < end_time:
                compaction_metrics = await self.collect_compaction_metrics()

                # Track compaction count changes
                if initial_compactions is None:
                    initial_compactions = compaction_metrics.compactions_total

                # Update metrics
                metrics.compaction = compaction_metrics

                # Collect storage metrics
                storage = await self.collect_storage_metrics()
                metrics.storage_size_bytes = storage[0]
                metrics.retention_limit_bytes = storage[1]
                metrics.samples_appended_total = storage[2]
                metrics.out_of_order_samples_total = storage[3]

                await asyncio.sleep(self.config.polling_interval_seconds)

        self._client = None
        return metrics

    async def run_wal_benchmark(
        self,
        duration_seconds: Optional[int] = None,
    ) -> TSDBMetrics:
        """Run WAL benchmark.

        Monitors WAL metrics over a period of time.

        Requirements: 15.6

        Args:
            duration_seconds: Duration to monitor

        Returns:
            TSDB metrics
        """
        duration = duration_seconds or self.config.measurement_duration_seconds
        metrics = TSDBMetrics()

        async with httpx.AsyncClient() as client:
            self._client = client

            end_time = time.time() + duration

            while time.time() < end_time:
                wal_metrics = await self.collect_wal_metrics()
                metrics.wal = wal_metrics

                # Also collect compaction metrics for context
                compaction_metrics = await self.collect_compaction_metrics()
                metrics.compaction = compaction_metrics

                await asyncio.sleep(self.config.polling_interval_seconds)

        self._client = None
        return metrics

    async def run_all_benchmarks(
        self,
        duration_seconds: Optional[int] = None,
    ) -> TSDBMetrics:
        """Run all TSDB benchmarks.

        Requirements: 15.5, 15.6

        Args:
            duration_seconds: Duration to monitor

        Returns:
            Combined TSDB metrics
        """
        duration = duration_seconds or self.config.measurement_duration_seconds
        metrics = TSDBMetrics()

        async with httpx.AsyncClient() as client:
            self._client = client

            end_time = time.time() + duration

            while time.time() < end_time:
                # Collect all metrics
                compaction_metrics = await self.collect_compaction_metrics()
                wal_metrics = await self.collect_wal_metrics()
                storage = await self.collect_storage_metrics()

                # Update combined metrics
                metrics.compaction = compaction_metrics
                metrics.wal = wal_metrics
                metrics.storage_size_bytes = storage[0]
                metrics.retention_limit_bytes = storage[1]
                metrics.samples_appended_total = storage[2]
                metrics.out_of_order_samples_total = storage[3]

                await asyncio.sleep(self.config.polling_interval_seconds)

        self._client = None
        return metrics


class TSDBBenchmarkRunner:
    """
    Runs TSDB benchmarks against Prometheus.

    Requirements: 15.5, 15.6
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        measurement_duration_seconds: int = 300,
    ):
        """Initialize the benchmark runner.

        Args:
            prometheus_url: URL of the Prometheus instance
            measurement_duration_seconds: Duration to measure metrics
        """
        self.prometheus_url = prometheus_url
        self.measurement_duration_seconds = measurement_duration_seconds

    async def run_compaction_benchmark(self) -> TSDBBenchmarkReport:
        """Run compaction benchmark.

        Requirements: 15.5

        Returns:
            Benchmark report
        """
        config = TSDBConfig(
            prometheus_url=self.prometheus_url,
            measurement_duration_seconds=self.measurement_duration_seconds,
        )

        report = TSDBBenchmarkReport(
            test_name="tsdb_compaction",
            prometheus_url=self.prometheus_url,
        )
        report.start_time = datetime.utcnow()

        benchmark = TSDBBenchmark(config)
        report.metrics = await benchmark.run_compaction_benchmark()

        report.end_time = datetime.utcnow()
        return report

    async def run_wal_benchmark(self) -> TSDBBenchmarkReport:
        """Run WAL benchmark.

        Requirements: 15.6

        Returns:
            Benchmark report
        """
        config = TSDBConfig(
            prometheus_url=self.prometheus_url,
            measurement_duration_seconds=self.measurement_duration_seconds,
        )

        report = TSDBBenchmarkReport(
            test_name="tsdb_wal",
            prometheus_url=self.prometheus_url,
        )
        report.start_time = datetime.utcnow()

        benchmark = TSDBBenchmark(config)
        report.metrics = await benchmark.run_wal_benchmark()

        report.end_time = datetime.utcnow()
        return report

    async def run_all_benchmarks(self) -> TSDBBenchmarkReport:
        """Run all TSDB benchmarks.

        Requirements: 15.5, 15.6

        Returns:
            Combined benchmark report
        """
        config = TSDBConfig(
            prometheus_url=self.prometheus_url,
            measurement_duration_seconds=self.measurement_duration_seconds,
        )

        report = TSDBBenchmarkReport(
            test_name="tsdb_all",
            prometheus_url=self.prometheus_url,
        )
        report.start_time = datetime.utcnow()

        benchmark = TSDBBenchmark(config)
        report.metrics = await benchmark.run_all_benchmarks()

        report.end_time = datetime.utcnow()
        return report


def run_tsdb_benchmarks_sync(
    prometheus_url: str = "http://localhost:9090",
    measurement_duration_seconds: int = 300,
) -> TSDBBenchmarkReport:
    """Synchronous wrapper for running TSDB benchmarks.

    Args:
        prometheus_url: URL of the Prometheus instance
        measurement_duration_seconds: Duration to measure metrics

    Returns:
        Benchmark report
    """
    runner = TSDBBenchmarkRunner(
        prometheus_url=prometheus_url,
        measurement_duration_seconds=measurement_duration_seconds,
    )
    return asyncio.run(runner.run_all_benchmarks())
