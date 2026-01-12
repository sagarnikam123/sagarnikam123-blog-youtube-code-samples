"""
Metrics collection for Prometheus load testing.

This module provides functionality to collect and analyze metrics
during load tests including query latency, scrape duration, and
resource utilization.

Requirements: 14.3, 14.4, 14.5
"""

import asyncio
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx


@dataclass
class LatencyMetrics:
    """Latency metrics with percentiles.

    Attributes:
        samples: Raw latency samples in milliseconds
        p50: 50th percentile (median)
        p90: 90th percentile
        p99: 99th percentile
        min_latency: Minimum latency
        max_latency: Maximum latency
        avg_latency: Average latency
    """

    samples: list[float] = field(default_factory=list)
    p50: float = 0.0
    p90: float = 0.0
    p99: float = 0.0
    min_latency: float = 0.0
    max_latency: float = 0.0
    avg_latency: float = 0.0

    def calculate_percentiles(self) -> None:
        """Calculate percentiles from samples."""
        if not self.samples:
            return

        sorted_samples = sorted(self.samples)
        n = len(sorted_samples)

        self.p50 = sorted_samples[int(n * 0.50)]
        self.p90 = sorted_samples[int(n * 0.90)]
        self.p99 = sorted_samples[min(int(n * 0.99), n - 1)]
        self.min_latency = sorted_samples[0]
        self.max_latency = sorted_samples[-1]
        self.avg_latency = statistics.mean(sorted_samples)

    def add_sample(self, latency_ms: float) -> None:
        """Add a latency sample."""
        self.samples.append(latency_ms)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        self.calculate_percentiles()
        return {
            "p50_ms": round(self.p50, 2),
            "p90_ms": round(self.p90, 2),
            "p99_ms": round(self.p99, 2),
            "min_ms": round(self.min_latency, 2),
            "max_ms": round(self.max_latency, 2),
            "avg_ms": round(self.avg_latency, 2),
            "sample_count": len(self.samples),
        }


@dataclass
class ScrapeMetrics:
    """Scrape-related metrics.

    Attributes:
        total_scrapes: Total number of scrapes
        successful_scrapes: Number of successful scrapes
        failed_scrapes: Number of failed scrapes
        scrape_durations: List of scrape durations in seconds
        success_rate: Percentage of successful scrapes
    """

    total_scrapes: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    scrape_durations: list[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate scrape success rate."""
        if self.total_scrapes == 0:
            return 0.0
        return (self.successful_scrapes / self.total_scrapes) * 100

    @property
    def avg_duration(self) -> float:
        """Calculate average scrape duration."""
        if not self.scrape_durations:
            return 0.0
        return statistics.mean(self.scrape_durations)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_scrapes": self.total_scrapes,
            "successful_scrapes": self.successful_scrapes,
            "failed_scrapes": self.failed_scrapes,
            "success_rate_percent": round(self.success_rate, 2),
            "avg_duration_seconds": round(self.avg_duration, 4),
        }


@dataclass
class ResourceMetrics:
    """Resource utilization metrics.

    Attributes:
        cpu_samples: CPU utilization samples (percentage)
        memory_samples: Memory utilization samples (bytes)
        cpu_avg: Average CPU utilization
        memory_avg: Average memory utilization
        cpu_max: Maximum CPU utilization
        memory_max: Maximum memory utilization
    """

    cpu_samples: list[float] = field(default_factory=list)
    memory_samples: list[float] = field(default_factory=list)

    @property
    def cpu_avg(self) -> float:
        """Calculate average CPU utilization."""
        if not self.cpu_samples:
            return 0.0
        return statistics.mean(self.cpu_samples)

    @property
    def memory_avg(self) -> float:
        """Calculate average memory utilization."""
        if not self.memory_samples:
            return 0.0
        return statistics.mean(self.memory_samples)

    @property
    def cpu_max(self) -> float:
        """Get maximum CPU utilization."""
        if not self.cpu_samples:
            return 0.0
        return max(self.cpu_samples)

    @property
    def memory_max(self) -> float:
        """Get maximum memory utilization."""
        if not self.memory_samples:
            return 0.0
        return max(self.memory_samples)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_avg_percent": round(self.cpu_avg, 2),
            "cpu_max_percent": round(self.cpu_max, 2),
            "memory_avg_bytes": round(self.memory_avg, 0),
            "memory_max_bytes": round(self.memory_max, 0),
            "sample_count": len(self.cpu_samples),
        }


@dataclass
class LoadTestMetrics:
    """Aggregated metrics from a load test.

    Attributes:
        query_latency: Query latency metrics
        scrape_metrics: Scrape-related metrics
        resource_metrics: Resource utilization metrics
        start_time: When metrics collection started
        end_time: When metrics collection ended
        prometheus_internal: Internal Prometheus metrics
    """

    query_latency: LatencyMetrics = field(default_factory=LatencyMetrics)
    scrape_metrics: ScrapeMetrics = field(default_factory=ScrapeMetrics)
    resource_metrics: ResourceMetrics = field(default_factory=ResourceMetrics)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    prometheus_internal: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_latency": self.query_latency.to_dict(),
            "scrape_metrics": self.scrape_metrics.to_dict(),
            "resource_metrics": self.resource_metrics.to_dict(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "prometheus_internal": self.prometheus_internal,
        }


class LoadTestMetricsCollector:
    """
    Collects metrics during Prometheus load tests.

    This class queries Prometheus to collect performance metrics
    including query latency, scrape statistics, and resource usage.

    Requirements: 14.3, 14.4, 14.5
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        collection_interval: float = 5.0,
    ):
        """Initialize the metrics collector.

        Args:
            prometheus_url: URL of the Prometheus instance
            collection_interval: Interval between metric collections in seconds
        """
        self.prometheus_url = prometheus_url.rstrip("/")
        self.collection_interval = collection_interval
        self.metrics = LoadTestMetrics()
        self._running = False
        self._client: Optional[httpx.AsyncClient] = None

    async def _query_prometheus(self, query: str) -> Optional[Any]:
        """Execute a PromQL query.

        Args:
            query: PromQL query string

        Returns:
            Query result or None if failed
        """
        if not self._client:
            return None

        try:
            response = await self._client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", {}).get("result", [])
        except Exception:
            pass
        return None

    async def _measure_query_latency(self, query: str) -> Optional[float]:
        """Measure latency of a PromQL query.

        Args:
            query: PromQL query to execute

        Returns:
            Query latency in milliseconds or None if failed
        """
        if not self._client:
            return None

        start_time = time.perf_counter()
        try:
            response = await self._client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=30.0,
            )
            end_time = time.perf_counter()

            if response.status_code == 200:
                latency_ms = (end_time - start_time) * 1000
                return latency_ms
        except Exception:
            pass
        return None

    async def collect_query_latency(self) -> None:
        """Collect query latency samples."""
        # Test queries of varying complexity
        test_queries = [
            "up",
            "prometheus_tsdb_head_series",
            'rate(prometheus_http_requests_total[5m])',
            'sum(rate(prometheus_http_requests_total[5m])) by (handler)',
        ]

        for query in test_queries:
            latency = await self._measure_query_latency(query)
            if latency is not None:
                self.metrics.query_latency.add_sample(latency)

    async def collect_scrape_metrics(self) -> None:
        """Collect scrape-related metrics from Prometheus."""
        # Query scrape duration
        result = await self._query_prometheus(
            "prometheus_target_scrape_pool_sync_total"
        )
        if result:
            for item in result:
                value = float(item.get("value", [0, 0])[1])
                self.metrics.scrape_metrics.total_scrapes = int(value)

        # Query successful scrapes
        result = await self._query_prometheus(
            'sum(up)'
        )
        if result:
            for item in result:
                value = float(item.get("value", [0, 0])[1])
                self.metrics.scrape_metrics.successful_scrapes = int(value)

        # Query scrape duration
        result = await self._query_prometheus(
            "avg(scrape_duration_seconds)"
        )
        if result:
            for item in result:
                value = float(item.get("value", [0, 0])[1])
                self.metrics.scrape_metrics.scrape_durations.append(value)

    async def collect_resource_metrics(self) -> None:
        """Collect resource utilization metrics."""
        # Query process CPU usage
        result = await self._query_prometheus(
            "rate(process_cpu_seconds_total[1m]) * 100"
        )
        if result:
            for item in result:
                value = float(item.get("value", [0, 0])[1])
                self.metrics.resource_metrics.cpu_samples.append(value)

        # Query process memory usage
        result = await self._query_prometheus(
            "process_resident_memory_bytes"
        )
        if result:
            for item in result:
                value = float(item.get("value", [0, 0])[1])
                self.metrics.resource_metrics.memory_samples.append(value)

    async def collect_prometheus_internal_metrics(self) -> None:
        """Collect internal Prometheus metrics."""
        internal_queries = {
            "head_series": "prometheus_tsdb_head_series",
            "head_chunks": "prometheus_tsdb_head_chunks",
            "head_samples_appended": "prometheus_tsdb_head_samples_appended_total",
            "compactions_total": "prometheus_tsdb_compactions_total",
            "wal_corruptions": "prometheus_tsdb_wal_corruptions_total",
            "query_duration_avg": "avg(prometheus_engine_query_duration_seconds)",
        }

        for name, query in internal_queries.items():
            result = await self._query_prometheus(query)
            if result:
                for item in result:
                    value = float(item.get("value", [0, 0])[1])
                    self.metrics.prometheus_internal[name] = value

    async def collect_all(self) -> None:
        """Collect all metrics once."""
        await asyncio.gather(
            self.collect_query_latency(),
            self.collect_scrape_metrics(),
            self.collect_resource_metrics(),
            self.collect_prometheus_internal_metrics(),
        )

    async def run(self, duration_seconds: int) -> LoadTestMetrics:
        """Run metrics collection for a specified duration.

        Args:
            duration_seconds: Duration to collect metrics

        Returns:
            Collected metrics
        """
        self._running = True
        self.metrics = LoadTestMetrics()
        self.metrics.start_time = datetime.utcnow()

        async with httpx.AsyncClient() as client:
            self._client = client
            end_time = time.time() + duration_seconds

            while self._running and time.time() < end_time:
                await self.collect_all()
                await asyncio.sleep(self.collection_interval)

        self._client = None
        self.metrics.end_time = datetime.utcnow()
        self.metrics.query_latency.calculate_percentiles()

        return self.metrics

    def stop(self) -> None:
        """Stop metrics collection."""
        self._running = False

    def get_metrics(self) -> LoadTestMetrics:
        """Get current metrics.

        Returns:
            Current collected metrics
        """
        self.metrics.query_latency.calculate_percentiles()
        return self.metrics
