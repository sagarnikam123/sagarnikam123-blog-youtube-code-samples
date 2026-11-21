"""
Stability monitoring for Prometheus endurance testing.

This module implements stability monitoring that verifies compaction cycles,
monitors query performance over time, and detects gradual degradation.

Requirements: 18.4, 18.5, 18.6, 18.7, 18.10
"""

import asyncio
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

from .config import StabilityMonitorConfig
from .models import (
    CompactionInfo,
    DegradationEvent,
    DegradationType,
    PerformanceSnapshot,
    StabilityStatus,
)


@dataclass
class PerformanceBaseline:
    """
    Baseline performance measurements for comparison.

    Requirements: 18.5

    Attributes:
        query_latency_p50_ms: Baseline 50th percentile latency
        query_latency_p90_ms: Baseline 90th percentile latency
        query_latency_p99_ms: Baseline 99th percentile latency
        query_success_rate: Baseline query success rate
        scrape_duration_avg_ms: Baseline average scrape duration
        measurement_count: Number of measurements in baseline
        timestamp: When baseline was established
    """

    query_latency_p50_ms: float = 0.0
    query_latency_p90_ms: float = 0.0
    query_latency_p99_ms: float = 0.0
    query_success_rate: float = 100.0
    scrape_duration_avg_ms: float = 0.0
    measurement_count: int = 0
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query_latency_p50_ms": round(self.query_latency_p50_ms, 2),
            "query_latency_p90_ms": round(self.query_latency_p90_ms, 2),
            "query_latency_p99_ms": round(self.query_latency_p99_ms, 2),
            "query_success_rate": round(self.query_success_rate, 2),
            "scrape_duration_avg_ms": round(self.scrape_duration_avg_ms, 2),
            "measurement_count": self.measurement_count,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class CompactionCycleInfo:
    """
    Information about compaction cycles over time.

    Requirements: 18.4

    Attributes:
        total_compactions: Total compactions observed
        successful_compactions: Number of successful compactions
        failed_compactions: Number of failed compactions
        avg_duration_seconds: Average compaction duration
        max_duration_seconds: Maximum compaction duration
        compaction_timestamps: Timestamps of observed compactions
    """

    total_compactions: int = 0
    successful_compactions: int = 0
    failed_compactions: int = 0
    avg_duration_seconds: float = 0.0
    max_duration_seconds: float = 0.0
    compaction_timestamps: list[datetime] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate compaction success rate."""
        if self.total_compactions == 0:
            return 100.0
        return (self.successful_compactions / self.total_compactions) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_compactions": self.total_compactions,
            "successful_compactions": self.successful_compactions,
            "failed_compactions": self.failed_compactions,
            "success_rate": round(self.success_rate, 2),
            "avg_duration_seconds": round(self.avg_duration_seconds, 2),
            "max_duration_seconds": round(self.max_duration_seconds, 2),
        }


@dataclass
class StabilityMonitorResult:
    """
    Result of stability monitoring.

    Requirements: 18.4, 18.5, 18.6, 18.7

    Attributes:
        config: Monitor configuration
        start_time: When monitoring started
        end_time: When monitoring ended
        baseline: Established performance baseline
        performance_snapshots: Performance measurements over time
        compaction_info: Compaction cycle information
        degradation_events: Detected degradation events
        status: Overall stability status
        passed: Whether stability thresholds were met
        error_messages: Any error messages
    """

    config: Optional[StabilityMonitorConfig] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    baseline: Optional[PerformanceBaseline] = None
    performance_snapshots: list[PerformanceSnapshot] = field(default_factory=list)
    compaction_info: CompactionCycleInfo = field(default_factory=CompactionCycleInfo)
    degradation_events: list[DegradationEvent] = field(default_factory=list)
    status: StabilityStatus = StabilityStatus.STABLE
    passed: bool = True
    error_messages: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Total monitoring duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "performance_snapshots_count": len(self.performance_snapshots),
            "compaction_info": self.compaction_info.to_dict(),
            "degradation_events_count": len(self.degradation_events),
            "status": self.status.value,
            "passed": self.passed,
            "error_messages": self.error_messages,
        }


class StabilityMonitor:
    """
    Monitors Prometheus stability over time.

    This class verifies compaction cycles, monitors query performance,
    and detects gradual degradation during endurance testing.

    Requirements: 18.4, 18.5, 18.6, 18.7
    """

    # Test queries for performance monitoring
    TEST_QUERIES = [
        "up",
        "prometheus_tsdb_head_series",
        'rate(prometheus_http_requests_total[5m])',
        'sum(rate(prometheus_http_requests_total[5m])) by (handler)',
        'histogram_quantile(0.99, rate(prometheus_http_request_duration_seconds_bucket[5m]))',
    ]

    def __init__(self, config: StabilityMonitorConfig):
        """Initialize the stability monitor.

        Args:
            config: Monitor configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._baseline: Optional[PerformanceBaseline] = None
        self._last_compaction_count = 0
        self._compaction_durations: list[float] = []

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

    async def _check_ready(self) -> bool:
        """Check if Prometheus is ready.

        Requirements: 18.10

        Returns:
            True if ready, False otherwise
        """
        if not self._client:
            return False

        try:
            response = await self._client.get(
                f"{self.config.prometheus_url}/-/ready",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    async def _check_runtime_info(self) -> Optional[dict[str, Any]]:
        """Get Prometheus runtime info for stability verification.

        Requirements: 18.10

        Returns:
            Runtime info dict or None if unavailable
        """
        if not self._client:
            return None

        try:
            response = await self._client.get(
                f"{self.config.prometheus_url}/api/v1/status/runtimeinfo",
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", {})
        except Exception:
            pass
        return None

    async def _comprehensive_healthcheck(self) -> tuple[bool, dict[str, Any]]:
        """Perform comprehensive healthcheck using Prometheus API.

        Requirements: 18.10

        Returns:
            Tuple of (is_healthy, health_details)
        """
        health_details = {
            "healthy_endpoint": False,
            "ready_endpoint": False,
            "runtime_info_available": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check /-/healthy
        health_details["healthy_endpoint"] = await self._check_health()

        # Check /-/ready
        health_details["ready_endpoint"] = await self._check_ready()

        # Check runtime info
        runtime_info = await self._check_runtime_info()
        if runtime_info:
            health_details["runtime_info_available"] = True
            health_details["storage_retention"] = runtime_info.get(
                "storageRetention", "unknown"
            )
            health_details["goroutines"] = runtime_info.get("goroutineCount", 0)

        is_healthy = (
            health_details["healthy_endpoint"]
            and health_details["ready_endpoint"]
        )

        return is_healthy, health_details

    def _detect_scrape_degradation(
        self,
        current: PerformanceSnapshot,
    ) -> Optional[DegradationEvent]:
        """Detect scrape performance degradation.

        Requirements: 18.6

        Args:
            current: Current performance snapshot

        Returns:
            DegradationEvent if degradation detected, None otherwise
        """
        if not self._baseline or self._baseline.scrape_duration_avg_ms <= 0:
            return None

        scrape_increase_percent = (
            (current.scrape_duration_avg_ms - self._baseline.scrape_duration_avg_ms)
            / self._baseline.scrape_duration_avg_ms * 100
        )

        if scrape_increase_percent > self.config.degradation_threshold_percent * 2:
            return DegradationEvent(
                degradation_type=DegradationType.SCRAPE_DEGRADATION,
                severity=min(100, scrape_increase_percent),
                description=(
                    f"Scrape duration increased by {scrape_increase_percent:.1f}%, "
                    f"exceeds threshold"
                ),
                baseline_value=self._baseline.scrape_duration_avg_ms,
                current_value=current.scrape_duration_avg_ms,
                threshold=self.config.degradation_threshold_percent * 2,
            )

        return None

    def _analyze_performance_trend(
        self,
        snapshots: list[PerformanceSnapshot],
    ) -> Optional[DegradationEvent]:
        """Analyze performance trend to detect gradual degradation.

        Requirements: 18.6, 18.7

        Args:
            snapshots: List of performance snapshots over time

        Returns:
            DegradationEvent if gradual degradation detected, None otherwise
        """
        if len(snapshots) < 5:
            return None

        # Calculate trend using linear regression approximation
        latencies = [s.query_latency_p99_ms for s in snapshots]
        n = len(latencies)

        # Simple linear regression slope calculation
        x_mean = (n - 1) / 2
        y_mean = sum(latencies) / n

        numerator = sum((i - x_mean) * (latencies[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return None

        slope = numerator / denominator

        # Calculate percentage increase per measurement
        if latencies[0] > 0:
            trend_percent = (slope / latencies[0]) * 100
        else:
            trend_percent = 0

        # Detect gradual degradation (consistent upward trend)
        if trend_percent > 1.0:  # More than 1% increase per measurement
            return DegradationEvent(
                degradation_type=DegradationType.LATENCY_INCREASE,
                severity=min(100, trend_percent * 10),
                description=(
                    f"Gradual latency degradation detected: "
                    f"{trend_percent:.2f}% increase per measurement interval"
                ),
                baseline_value=latencies[0],
                current_value=latencies[-1],
                threshold=1.0,
            )

        return None

    async def _collect_performance_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance metrics.

        Requirements: 18.5

        Returns:
            PerformanceSnapshot with current metrics
        """
        latencies: list[float] = []
        successes = 0
        total = 0

        for query in self.TEST_QUERIES:
            success, latency_ms, _ = await self._query_prometheus(query)
            latencies.append(latency_ms)
            total += 1
            if success:
                successes += 1

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

        return snapshot

    async def _establish_baseline(self) -> PerformanceBaseline:
        """Establish performance baseline through multiple measurements.

        Requirements: 18.5

        Returns:
            PerformanceBaseline with averaged measurements
        """
        snapshots: list[PerformanceSnapshot] = []
        measurement_interval = 5.0  # 5 seconds between measurements
        num_measurements = max(
            3,
            int(self.config.baseline_measurement_duration_seconds / measurement_interval)
        )

        for _ in range(num_measurements):
            snapshot = await self._collect_performance_snapshot()
            snapshots.append(snapshot)
            await asyncio.sleep(measurement_interval)

        # Calculate averages
        baseline = PerformanceBaseline(
            query_latency_p50_ms=statistics.mean(
                s.query_latency_p50_ms for s in snapshots
            ),
            query_latency_p90_ms=statistics.mean(
                s.query_latency_p90_ms for s in snapshots
            ),
            query_latency_p99_ms=statistics.mean(
                s.query_latency_p99_ms for s in snapshots
            ),
            query_success_rate=statistics.mean(
                s.query_success_rate for s in snapshots
            ),
            scrape_duration_avg_ms=statistics.mean(
                s.scrape_duration_avg_ms for s in snapshots
            ),
            measurement_count=len(snapshots),
            timestamp=datetime.utcnow(),
        )

        return baseline

    async def _check_compaction(self) -> CompactionInfo:
        """Check current compaction status.

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

    def _detect_latency_degradation(
        self,
        current: PerformanceSnapshot,
    ) -> Optional[DegradationEvent]:
        """Detect query latency degradation.

        Requirements: 18.5, 18.6

        Args:
            current: Current performance snapshot

        Returns:
            DegradationEvent if degradation detected, None otherwise
        """
        if not self._baseline or self._baseline.query_latency_p99_ms <= 0:
            return None

        latency_increase_percent = (
            (current.query_latency_p99_ms - self._baseline.query_latency_p99_ms)
            / self._baseline.query_latency_p99_ms * 100
        )

        if latency_increase_percent > self.config.latency_degradation_threshold_percent:
            return DegradationEvent(
                degradation_type=DegradationType.LATENCY_INCREASE,
                severity=min(100, latency_increase_percent),
                description=(
                    f"Query latency increased by {latency_increase_percent:.1f}%, "
                    f"exceeds threshold of "
                    f"{self.config.latency_degradation_threshold_percent}%"
                ),
                baseline_value=self._baseline.query_latency_p99_ms,
                current_value=current.query_latency_p99_ms,
                threshold=self.config.latency_degradation_threshold_percent,
            )

        return None

    def _detect_query_degradation(
        self,
        current: PerformanceSnapshot,
    ) -> Optional[DegradationEvent]:
        """Detect query success rate degradation.

        Requirements: 18.6

        Args:
            current: Current performance snapshot

        Returns:
            DegradationEvent if degradation detected, None otherwise
        """
        if not self._baseline:
            return None

        success_rate_drop = self._baseline.query_success_rate - current.query_success_rate

        if success_rate_drop > self.config.degradation_threshold_percent:
            return DegradationEvent(
                degradation_type=DegradationType.QUERY_DEGRADATION,
                severity=min(100, success_rate_drop * 2),
                description=(
                    f"Query success rate dropped by {success_rate_drop:.1f}%, "
                    f"exceeds threshold of {self.config.degradation_threshold_percent}%"
                ),
                baseline_value=self._baseline.query_success_rate,
                current_value=current.query_success_rate,
                threshold=self.config.degradation_threshold_percent,
            )

        return None

    def _detect_compaction_failure(
        self,
        compaction: CompactionInfo,
    ) -> Optional[DegradationEvent]:
        """Detect compaction failures.

        Requirements: 18.4

        Args:
            compaction: Current compaction info

        Returns:
            DegradationEvent if compaction failure detected, None otherwise
        """
        if compaction.compaction_failed:
            return DegradationEvent(
                degradation_type=DegradationType.COMPACTION_FAILURE,
                severity=80,
                description="TSDB compaction failure detected",
                baseline_value=0,
                current_value=1,
                threshold=0,
            )

        return None

    async def run(self, duration_seconds: Optional[int] = None) -> StabilityMonitorResult:
        """Run stability monitoring.

        Requirements: 18.4, 18.5, 18.6, 18.7, 18.10

        Args:
            duration_seconds: Optional duration override

        Returns:
            StabilityMonitorResult with monitoring results
        """
        result = StabilityMonitorResult(config=self.config)
        result.start_time = datetime.utcnow()
        self._running = True

        test_duration = duration_seconds or 3600  # Default 1 hour
        health_check_details: list[dict[str, Any]] = []

        async with httpx.AsyncClient() as client:
            self._client = client

            # Verify Prometheus is healthy using comprehensive healthcheck
            is_healthy, health_details = await self._comprehensive_healthcheck()
            health_check_details.append(health_details)

            if not is_healthy:
                result.passed = False
                result.status = StabilityStatus.FAILED
                result.error_messages.append(
                    f"Prometheus not healthy at start: {health_details}"
                )
                result.end_time = datetime.utcnow()
                return result

            # Establish baseline
            self._baseline = await self._establish_baseline()
            result.baseline = self._baseline

            # Get initial compaction count
            initial_compaction = await self._check_compaction()
            self._last_compaction_count = initial_compaction.compactions_total

            # Run monitoring loop
            test_start = time.time()
            last_perf_check = test_start
            last_compaction_check = test_start
            last_health_check = test_start

            while self._running:
                elapsed = time.time() - test_start

                if elapsed >= test_duration:
                    break

                # Performance check
                perf_interval = self.config.query_performance_check_interval_seconds
                if time.time() - last_perf_check >= perf_interval:
                    snapshot = await self._collect_performance_snapshot()
                    result.performance_snapshots.append(snapshot)

                    # Check for degradation
                    latency_event = self._detect_latency_degradation(snapshot)
                    if latency_event:
                        result.degradation_events.append(latency_event)

                    query_event = self._detect_query_degradation(snapshot)
                    if query_event:
                        result.degradation_events.append(query_event)

                    scrape_event = self._detect_scrape_degradation(snapshot)
                    if scrape_event:
                        result.degradation_events.append(scrape_event)

                    # Check for gradual degradation trend
                    if len(result.performance_snapshots) >= 5:
                        trend_event = self._analyze_performance_trend(
                            result.performance_snapshots[-10:]
                        )
                        if trend_event:
                            result.degradation_events.append(trend_event)

                    last_perf_check = time.time()

                # Compaction check
                compact_interval = self.config.compaction_check_interval_seconds
                if time.time() - last_compaction_check >= compact_interval:
                    compaction = await self._check_compaction()

                    # Track compaction cycles
                    new_compactions = (
                        compaction.compactions_total - self._last_compaction_count
                    )
                    if new_compactions > 0:
                        result.compaction_info.total_compactions += new_compactions
                        if compaction.compaction_failed:
                            result.compaction_info.failed_compactions += new_compactions
                        else:
                            result.compaction_info.successful_compactions += (
                                new_compactions
                            )

                        result.compaction_info.compaction_timestamps.append(
                            datetime.utcnow()
                        )

                        # Track duration
                        if compaction.compaction_duration_seconds > 0:
                            self._compaction_durations.append(
                                compaction.compaction_duration_seconds
                            )

                    self._last_compaction_count = compaction.compactions_total

                    # Check for compaction failure
                    compaction_event = self._detect_compaction_failure(compaction)
                    if compaction_event:
                        result.degradation_events.append(compaction_event)

                    last_compaction_check = time.time()

                # Comprehensive health check at intervals
                health_interval = self.config.health_check_interval_seconds
                if time.time() - last_health_check >= health_interval:
                    is_healthy, health_details = await self._comprehensive_healthcheck()
                    health_check_details.append(health_details)

                    if not is_healthy:
                        result.status = StabilityStatus.FAILED
                        result.error_messages.append(
                            f"Prometheus became unhealthy at {elapsed:.0f}s: "
                            f"{health_details}"
                        )
                        break

                    last_health_check = time.time()

                await asyncio.sleep(10)  # Check every 10 seconds

        self._client = None
        self._running = False
        result.end_time = datetime.utcnow()

        # Calculate compaction statistics
        if self._compaction_durations:
            result.compaction_info.avg_duration_seconds = statistics.mean(
                self._compaction_durations
            )
            result.compaction_info.max_duration_seconds = max(
                self._compaction_durations
            )

        # Determine final status
        if result.status != StabilityStatus.FAILED:
            if len(result.degradation_events) == 0:
                result.status = StabilityStatus.STABLE
            elif len(result.degradation_events) <= 3:
                result.status = StabilityStatus.DEGRADING
            else:
                result.status = StabilityStatus.UNSTABLE

        # Check minimum compaction cycles
        min_cycles = self.config.min_compaction_cycles
        if result.compaction_info.total_compactions < min_cycles:
            result.error_messages.append(
                f"Only {result.compaction_info.total_compactions} compaction cycles "
                f"observed, minimum required: {min_cycles}"
            )

        # Determine pass/fail
        result.passed = (
            result.status in (StabilityStatus.STABLE, StabilityStatus.DEGRADING)
            and result.compaction_info.success_rate >= 90
        )

        return result

    def stop(self) -> None:
        """Stop stability monitoring."""
        self._running = False


def run_stability_monitor_sync(
    prometheus_url: str = "http://localhost:9090",
    duration_seconds: int = 3600,
) -> StabilityMonitorResult:
    """Synchronous wrapper for running stability monitoring.

    Args:
        prometheus_url: URL of the Prometheus instance
        duration_seconds: Duration of monitoring in seconds

    Returns:
        StabilityMonitorResult
    """
    config = StabilityMonitorConfig(prometheus_url=prometheus_url)
    monitor = StabilityMonitor(config)
    return asyncio.run(monitor.run(duration_seconds))
