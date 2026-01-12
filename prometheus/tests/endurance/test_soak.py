"""
Soak test implementation for Prometheus endurance testing.

This module implements soak tests that run Prometheus under sustained
load for extended periods to detect memory leaks, disk growth issues,
and gradual performance degradation.

Requirements: 18.1, 18.2, 18.3
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

from .config import SoakTestConfig
from .models import (
    CompactionInfo,
    DegradationEvent,
    DegradationType,
    PerformanceSnapshot,
    ResourceSnapshot,
    SoakTestDataPoint,
    StabilityMetrics,
    StabilityStatus,
)


@dataclass
class SoakTestResult:
    """
    Result of a soak test execution.

    Requirements: 18.1, 18.2, 18.3

    Attributes:
        config: Test configuration used
        start_time: When the test started
        end_time: When the test ended
        data_points: Measurements over time
        stability_metrics: Aggregated stability metrics
        status: Overall stability status
        degradation_events: All detected degradation events
        passed: Whether the test passed thresholds
        error_messages: Any error messages
    """

    config: Optional[SoakTestConfig] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_points: list[SoakTestDataPoint] = field(default_factory=list)
    stability_metrics: StabilityMetrics = field(default_factory=StabilityMetrics)
    status: StabilityStatus = StabilityStatus.STABLE
    degradation_events: list[DegradationEvent] = field(default_factory=list)
    passed: bool = True
    error_messages: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Total test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def duration_hours(self) -> float:
        """Total test duration in hours."""
        return self.duration_seconds / 3600.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_hours": round(self.duration_hours, 2),
            "status": self.status.value,
            "passed": self.passed,
            "stability_metrics": self.stability_metrics.to_dict(),
            "data_points_count": len(self.data_points),
            "degradation_events_count": len(self.degradation_events),
            "error_messages": self.error_messages,
        }


class SoakTester:
    """
    Executes soak tests against Prometheus.

    This class runs Prometheus under sustained load for extended periods,
    monitoring memory growth, disk growth, and performance stability.

    Requirements: 18.1, 18.2, 18.3
    """

    # Test queries for sustained load
    TEST_QUERIES = [
        "up",
        "prometheus_tsdb_head_series",
        "prometheus_tsdb_head_chunks",
        'rate(prometheus_http_requests_total[5m])',
        'sum(rate(prometheus_http_requests_total[5m])) by (handler)',
        'histogram_quantile(0.99, rate(prometheus_http_request_duration_seconds_bucket[5m]))',
        "process_resident_memory_bytes",
        "prometheus_tsdb_storage_blocks_bytes",
    ]

    def __init__(self, config: SoakTestConfig):
        """Initialize the soak tester.

        Args:
            config: Test configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._baseline_resources: Optional[ResourceSnapshot] = None
        self._baseline_performance: Optional[PerformanceSnapshot] = None

    async def _query_prometheus(self, query: str) -> tuple[bool, float, Any]:
        """Execute a PromQL query and measure latency.

        Args:
            query: PromQL query string

        Returns:
            Tuple of (success, latency_ms, result_value)
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
                    result = data.get("data", {}).get("result", [])
                    value = None
                    if result:
                        value = result[0].get("value", [0, 0])[1]
                    return True, latency_ms, value

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

    async def _collect_resource_snapshot(self) -> ResourceSnapshot:
        """Collect current resource usage metrics.

        Requirements: 18.2, 18.3

        Returns:
            ResourceSnapshot with current metrics
        """
        snapshot = ResourceSnapshot()

        metric_queries = {
            "memory_bytes": "process_resident_memory_bytes",
            "cpu_seconds": "rate(process_cpu_seconds_total[1m])",
            "active_series": "prometheus_tsdb_head_series",
            "samples_ingested": "prometheus_tsdb_head_samples_appended_total",
            "goroutines": "go_goroutines",
            "disk_bytes": "prometheus_tsdb_storage_blocks_bytes",
        }

        for name, query in metric_queries.items():
            success, _, value = await self._query_prometheus(query)
            if success and value is not None:
                try:
                    float_value = float(value)
                    if name == "memory_bytes":
                        snapshot.memory_bytes = float_value
                    elif name == "cpu_seconds":
                        snapshot.cpu_percent = float_value * 100
                    elif name == "active_series":
                        snapshot.active_series = int(float_value)
                    elif name == "samples_ingested":
                        snapshot.samples_ingested = int(float_value)
                    elif name == "goroutines":
                        snapshot.goroutines = int(float_value)
                    elif name == "disk_bytes":
                        snapshot.disk_bytes = float_value
                except (ValueError, TypeError):
                    pass

        return snapshot

    async def _collect_performance_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance metrics.

        Requirements: 18.5, 18.6

        Returns:
            PerformanceSnapshot with current metrics
        """
        latencies: list[float] = []
        successes = 0
        total = 0

        # Run a batch of queries to measure performance
        for query in self.TEST_QUERIES:
            success, latency_ms, _ = await self._query_prometheus(query)
            latencies.append(latency_ms)
            total += 1
            if success:
                successes += 1

        # Calculate percentiles
        sorted_latencies = sorted(latencies) if latencies else [0]
        n = len(sorted_latencies)

        snapshot = PerformanceSnapshot(
            query_latency_p50_ms=sorted_latencies[int(n * 0.50)] if n > 0 else 0,
            query_latency_p90_ms=sorted_latencies[int(n * 0.90)] if n > 0 else 0,
            query_latency_p99_ms=sorted_latencies[min(int(n * 0.99), n - 1)] if n > 0 else 0,
            query_success_rate=(successes / total * 100) if total > 0 else 0,
        )

        # Get scrape metrics
        success, _, value = await self._query_prometheus(
            'avg(scrape_duration_seconds) * 1000'
        )
        if success and value:
            try:
                snapshot.scrape_duration_avg_ms = float(value)
            except (ValueError, TypeError):
                pass

        success, _, value = await self._query_prometheus(
            'avg(up) * 100'
        )
        if success and value:
            try:
                snapshot.scrape_success_rate = float(value)
            except (ValueError, TypeError):
                pass

        return snapshot

    async def _collect_compaction_info(self) -> CompactionInfo:
        """Collect TSDB compaction information.

        Requirements: 18.4

        Returns:
            CompactionInfo with current compaction metrics
        """
        info = CompactionInfo()

        metric_queries = {
            "compactions_total": "prometheus_tsdb_compactions_total",
            "compaction_duration": "prometheus_tsdb_compaction_duration_seconds_sum",
            "compaction_failed": "prometheus_tsdb_compactions_failed_total",
            "head_chunks": "prometheus_tsdb_head_chunks",
            "head_series": "prometheus_tsdb_head_series",
        }

        for name, query in metric_queries.items():
            success, _, value = await self._query_prometheus(query)
            if success and value is not None:
                try:
                    float_value = float(value)
                    if name == "compactions_total":
                        info.compactions_total = int(float_value)
                    elif name == "compaction_duration":
                        info.compaction_duration_seconds = float_value
                    elif name == "compaction_failed":
                        info.compaction_failed = int(float_value) > 0
                    elif name == "head_chunks":
                        info.head_chunks = int(float_value)
                    elif name == "head_series":
                        info.head_series = int(float_value)
                except (ValueError, TypeError):
                    pass

        return info

    async def _generate_sustained_load(self, duration_seconds: float) -> None:
        """Generate sustained query load.

        Args:
            duration_seconds: Duration to generate load
        """
        interval = 1.0 / max(self.config.load_queries_per_second, 0.1)
        end_time = time.time() + duration_seconds
        query_index = 0

        while time.time() < end_time and self._running:
            query = self.TEST_QUERIES[query_index % len(self.TEST_QUERIES)]
            await self._query_prometheus(query)
            query_index += 1
            await asyncio.sleep(interval)

    def _detect_memory_degradation(
        self,
        current: ResourceSnapshot,
        elapsed_hours: float,
    ) -> Optional[DegradationEvent]:
        """Detect memory leak or excessive growth.

        Requirements: 18.2

        Args:
            current: Current resource snapshot
            elapsed_hours: Hours since test start

        Returns:
            DegradationEvent if detected, None otherwise
        """
        if not self._baseline_resources or elapsed_hours < 0.1:
            return None

        memory_growth = current.memory_bytes - self._baseline_resources.memory_bytes
        growth_rate_per_hour = memory_growth / elapsed_hours if elapsed_hours > 0 else 0

        # Calculate growth as percentage of baseline
        if self._baseline_resources.memory_bytes > 0:
            growth_percent_per_hour = (
                (growth_rate_per_hour / self._baseline_resources.memory_bytes) * 100
            )
        else:
            growth_percent_per_hour = 0

        if growth_percent_per_hour > self.config.memory_growth_threshold_percent_per_hour:
            return DegradationEvent(
                degradation_type=DegradationType.MEMORY_LEAK,
                severity=min(100, growth_percent_per_hour * 10),
                description=(
                    f"Memory growing at {growth_percent_per_hour:.2f}% per hour, "
                    f"exceeds threshold of "
                    f"{self.config.memory_growth_threshold_percent_per_hour}%"
                ),
                baseline_value=self._baseline_resources.memory_bytes,
                current_value=current.memory_bytes,
                threshold=self.config.memory_growth_threshold_percent_per_hour,
            )

        return None

    def _detect_disk_degradation(
        self,
        current: ResourceSnapshot,
        elapsed_hours: float,
    ) -> Optional[DegradationEvent]:
        """Detect excessive disk growth.

        Requirements: 18.3

        Args:
            current: Current resource snapshot
            elapsed_hours: Hours since test start

        Returns:
            DegradationEvent if detected, None otherwise
        """
        if not self._baseline_resources or elapsed_hours < 0.1:
            return None

        disk_growth = current.disk_bytes - self._baseline_resources.disk_bytes
        growth_rate_per_hour = disk_growth / elapsed_hours if elapsed_hours > 0 else 0

        if growth_rate_per_hour > self.config.disk_growth_threshold_bytes_per_hour:
            return DegradationEvent(
                degradation_type=DegradationType.DISK_GROWTH,
                severity=min(100, (growth_rate_per_hour /
                    self.config.disk_growth_threshold_bytes_per_hour) * 50),
                description=(
                    f"Disk growing at {growth_rate_per_hour:.0f} bytes/hour, "
                    f"exceeds threshold of "
                    f"{self.config.disk_growth_threshold_bytes_per_hour} bytes/hour"
                ),
                baseline_value=self._baseline_resources.disk_bytes,
                current_value=current.disk_bytes,
                threshold=float(self.config.disk_growth_threshold_bytes_per_hour),
            )

        return None

    async def _collect_data_point(
        self,
        elapsed_hours: float,
    ) -> SoakTestDataPoint:
        """Collect a complete data point with all metrics.

        Args:
            elapsed_hours: Hours since test start

        Returns:
            SoakTestDataPoint with all measurements
        """
        resources = await self._collect_resource_snapshot()
        performance = await self._collect_performance_snapshot()
        compaction = await self._collect_compaction_info()

        degradation_events: list[DegradationEvent] = []

        # Check for memory degradation
        memory_event = self._detect_memory_degradation(resources, elapsed_hours)
        if memory_event:
            degradation_events.append(memory_event)

        # Check for disk degradation
        disk_event = self._detect_disk_degradation(resources, elapsed_hours)
        if disk_event:
            degradation_events.append(disk_event)

        is_stable = len(degradation_events) == 0

        return SoakTestDataPoint(
            elapsed_hours=elapsed_hours,
            resources=resources,
            performance=performance,
            compaction=compaction,
            is_stable=is_stable,
            degradation_events=degradation_events,
        )

    def _calculate_stability_metrics(
        self,
        data_points: list[SoakTestDataPoint],
    ) -> StabilityMetrics:
        """Calculate aggregated stability metrics.

        Requirements: 18.7

        Args:
            data_points: All collected data points

        Returns:
            StabilityMetrics with aggregated values
        """
        if len(data_points) < 2:
            return StabilityMetrics()

        # Calculate memory growth rate
        first = data_points[0]
        last = data_points[-1]
        duration_hours = last.elapsed_hours - first.elapsed_hours

        if duration_hours > 0:
            memory_growth = (
                last.resources.memory_bytes - first.resources.memory_bytes
            )
            memory_growth_rate = memory_growth / duration_hours

            disk_growth = last.resources.disk_bytes - first.resources.disk_bytes
            disk_growth_rate = disk_growth / duration_hours
        else:
            memory_growth_rate = 0
            disk_growth_rate = 0

        # Calculate latency trend
        latencies = [dp.performance.query_latency_p99_ms for dp in data_points]
        if len(latencies) >= 2 and latencies[0] > 0:
            latency_change = (latencies[-1] - latencies[0]) / latencies[0] * 100
            latency_trend = latency_change / duration_hours if duration_hours > 0 else 0
        else:
            latency_trend = 0

        # Calculate compaction success rate
        compaction_failures = sum(
            1 for dp in data_points
            if dp.compaction and dp.compaction.compaction_failed
        )
        compaction_checks = sum(1 for dp in data_points if dp.compaction)
        compaction_success_rate = (
            ((compaction_checks - compaction_failures) / compaction_checks * 100)
            if compaction_checks > 0 else 100
        )

        # Count degradation events
        degradation_count = sum(
            len(dp.degradation_events) for dp in data_points
        )

        # Calculate overall stability score
        stability_score = 100.0
        stability_score -= min(30, degradation_count * 5)
        stability_score -= min(20, abs(latency_trend) * 2)
        stability_score -= min(20, (100 - compaction_success_rate))
        stability_score = max(0, stability_score)

        return StabilityMetrics(
            memory_growth_rate_bytes_per_hour=memory_growth_rate,
            disk_growth_rate_bytes_per_hour=disk_growth_rate,
            latency_trend_percent_per_hour=latency_trend,
            compaction_success_rate=compaction_success_rate,
            overall_stability_score=stability_score,
            degradation_count=degradation_count,
        )

    async def run(self) -> SoakTestResult:
        """Run the soak test.

        Requirements: 18.1, 18.2, 18.3

        Returns:
            SoakTestResult with test results
        """
        result = SoakTestResult(config=self.config)
        result.start_time = datetime.utcnow()
        self._running = True

        async with httpx.AsyncClient() as client:
            self._client = client

            # Verify Prometheus is healthy
            if not await self._check_health():
                result.passed = False
                result.status = StabilityStatus.FAILED
                result.error_messages.append("Prometheus not healthy at test start")
                result.end_time = datetime.utcnow()
                return result

            # Collect baseline measurements
            self._baseline_resources = await self._collect_resource_snapshot()
            self._baseline_performance = await self._collect_performance_snapshot()

            # Run the soak test
            test_start = time.time()
            last_measurement = test_start

            while self._running:
                elapsed_seconds = time.time() - test_start
                elapsed_hours = elapsed_seconds / 3600.0

                # Check if test duration exceeded
                if elapsed_seconds >= self.config.duration_seconds:
                    break

                # Generate sustained load
                time_until_measurement = (
                    self.config.measurement_interval_seconds -
                    (time.time() - last_measurement)
                )
                if time_until_measurement > 0:
                    await self._generate_sustained_load(
                        min(time_until_measurement, 60)
                    )

                # Collect measurements at intervals
                if time.time() - last_measurement >= self.config.measurement_interval_seconds:
                    data_point = await self._collect_data_point(elapsed_hours)
                    result.data_points.append(data_point)
                    result.degradation_events.extend(data_point.degradation_events)
                    last_measurement = time.time()

                    # Check health
                    if not await self._check_health():
                        result.status = StabilityStatus.FAILED
                        result.error_messages.append(
                            f"Prometheus became unhealthy at {elapsed_hours:.2f} hours"
                        )
                        break

        self._client = None
        self._running = False
        result.end_time = datetime.utcnow()

        # Calculate stability metrics
        result.stability_metrics = self._calculate_stability_metrics(result.data_points)

        # Determine final status
        if result.stability_metrics.overall_stability_score >= 80:
            result.status = StabilityStatus.STABLE
        elif result.stability_metrics.overall_stability_score >= 50:
            result.status = StabilityStatus.DEGRADING
        else:
            result.status = StabilityStatus.UNSTABLE

        # Determine pass/fail
        result.passed = (
            result.status in (StabilityStatus.STABLE, StabilityStatus.DEGRADING)
            and result.stability_metrics.memory_growth_rate_bytes_per_hour <= (
                self.config.memory_growth_threshold_percent_per_hour *
                self._baseline_resources.memory_bytes / 100
                if self._baseline_resources else float('inf')
            )
        )

        return result

    def stop(self) -> None:
        """Stop the soak test."""
        self._running = False


def run_soak_test_sync(
    prometheus_url: str = "http://localhost:9090",
    duration_hours: float = 24.0,
    load_qps: float = 10.0,
) -> SoakTestResult:
    """Synchronous wrapper for running soak test.

    Args:
        prometheus_url: URL of the Prometheus instance
        duration_hours: Duration of the test in hours
        load_qps: Queries per second to generate

    Returns:
        SoakTestResult
    """
    config = SoakTestConfig(
        prometheus_url=prometheus_url,
        duration_seconds=int(duration_hours * 3600),
        load_queries_per_second=load_qps,
    )
    tester = SoakTester(config)
    return asyncio.run(tester.run())
