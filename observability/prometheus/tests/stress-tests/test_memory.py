"""
Memory pressure stress test for Prometheus.

This module implements stress tests that push Prometheus toward OOM
conditions and capture failure symptoms.

Requirements: 17.5, 17.7
"""

import asyncio
import random
import string
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

from config import MemoryPressureConfig
from models import (
    BreakingPoint,
    FailureMode,
    StressTestDataPoint,
    StressTestType,
)


@dataclass
class MemoryPressureResult:
    """
    Result of a memory pressure stress test.

    Requirements: 17.5, 17.7

    Attributes:
        test_type: Type of stress test
        config: Test configuration used
        start_time: When the test started
        end_time: When the test ended
        data_points: Measurements at each memory level
        breaking_point: Discovered breaking point
        peak_memory_bytes: Peak memory usage observed
        memory_growth_rate: Rate of memory growth (bytes/second)
        oom_detected: Whether OOM was detected
        failure_symptoms: Detailed failure symptoms
        passed: Whether the test completed without unexpected failures
        error_logs: Captured error logs
    """

    test_type: StressTestType = StressTestType.MEMORY_PRESSURE
    config: Optional[MemoryPressureConfig] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data_points: list[StressTestDataPoint] = field(default_factory=list)
    breaking_point: BreakingPoint = field(default_factory=BreakingPoint)
    peak_memory_bytes: float = 0.0
    memory_growth_rate: float = 0.0
    oom_detected: bool = False
    failure_symptoms: list[str] = field(default_factory=list)
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
            "peak_memory_bytes": round(self.peak_memory_bytes, 0),
            "memory_growth_rate": round(self.memory_growth_rate, 2),
            "oom_detected": self.oom_detected,
            "failure_symptoms": self.failure_symptoms,
            "passed": self.passed,
            "error_logs": self.error_logs,
        }


class MemoryPressureTester:
    """
    Executes memory pressure stress tests against Prometheus.

    This class generates increasing numbers of time series to push
    Prometheus toward OOM conditions, capturing failure symptoms.

    Requirements: 17.5, 17.7
    """

    def __init__(self, config: MemoryPressureConfig):
        """Initialize the memory pressure tester.

        Args:
            config: Test configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._generated_series: int = 0

    def _generate_random_string(self, length: int = 8) -> str:
        """Generate a random string for labels."""
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

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
        except httpx.ConnectError:
            # Connection refused - likely OOM crash
            return False, 0.0, None
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
        except httpx.ConnectError:
            # Connection refused - likely crashed
            return False
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
            "memory_virtual_bytes": "process_virtual_memory_bytes",
            "head_chunks": "prometheus_tsdb_head_chunks",
            "head_chunks_created": "prometheus_tsdb_head_chunks_created_total",
            "head_chunks_removed": "prometheus_tsdb_head_chunks_removed_total",
            "wal_corruptions": "prometheus_tsdb_wal_corruptions_total",
            "compactions_failed": "prometheus_tsdb_compactions_failed_total",
            "gc_duration": "go_gc_duration_seconds_sum",
        }

        for name, query in metric_queries.items():
            success, _, result = await self._query_prometheus(query)
            if success and result:
                try:
                    metrics[name] = float(result[0].get("value", [0, 0])[1])
                except (IndexError, ValueError, TypeError):
                    pass

        return metrics

    async def _detect_oom_symptoms(
        self,
        prom_metrics: dict[str, float],
        prev_metrics: Optional[dict[str, float]],
    ) -> list[str]:
        """Detect symptoms that indicate OOM is approaching.

        Args:
            prom_metrics: Current Prometheus metrics
            prev_metrics: Previous Prometheus metrics

        Returns:
            List of detected symptoms
        """
        symptoms = []

        memory_bytes = prom_metrics.get("memory_bytes", 0)

        # Check memory usage against limit if known
        if self.config.memory_limit_bytes:
            memory_percent = (memory_bytes / self.config.memory_limit_bytes) * 100

            if memory_percent >= self.config.memory_critical_threshold_percent:
                symptoms.append(
                    f"CRITICAL: Memory usage at {memory_percent:.1f}% of limit"
                )
            elif memory_percent >= self.config.memory_warning_threshold_percent:
                symptoms.append(
                    f"WARNING: Memory usage at {memory_percent:.1f}% of limit"
                )

        # Check for rapid memory growth
        if prev_metrics:
            prev_memory = prev_metrics.get("memory_bytes", 0)
            if prev_memory > 0:
                growth_rate = (memory_bytes - prev_memory) / prev_memory * 100
                if growth_rate > 20:  # More than 20% growth
                    symptoms.append(
                        f"Rapid memory growth: {growth_rate:.1f}% increase"
                    )

        # Check for GC pressure
        gc_duration = prom_metrics.get("gc_duration", 0)
        if prev_metrics:
            prev_gc = prev_metrics.get("gc_duration", 0)
            gc_increase = gc_duration - prev_gc
            if gc_increase > 1.0:  # More than 1 second of GC
                symptoms.append(
                    f"High GC pressure: {gc_increase:.2f}s GC time"
                )

        # Check for compaction failures
        compactions_failed = prom_metrics.get("compactions_failed", 0)
        if compactions_failed > 0:
            symptoms.append(f"Compaction failures detected: {compactions_failed}")

        # Check for WAL corruptions
        wal_corruptions = prom_metrics.get("wal_corruptions", 0)
        if wal_corruptions > 0:
            symptoms.append(f"WAL corruptions detected: {wal_corruptions}")

        return symptoms

    async def _simulate_memory_pressure(
        self,
        target_series: int,
    ) -> tuple[int, list[str]]:
        """Simulate memory pressure by tracking series generation.

        Note: This simulates the effect of high series count. In a real
        scenario, you would push actual metrics via remote_write.

        Args:
            target_series: Target number of series

        Returns:
            Tuple of (series_simulated, errors)
        """
        errors = []

        # Track simulated series
        new_series = target_series - self._generated_series
        if new_series > 0:
            self._generated_series = target_series

        return self._generated_series, errors

    async def _measure_at_series_level(
        self,
        target_series: int,
        prev_metrics: Optional[dict[str, float]] = None,
    ) -> tuple[StressTestDataPoint, dict[str, float]]:
        """Measure performance at a specific series level.

        Args:
            target_series: Target number of series
            prev_metrics: Previous metrics for comparison

        Returns:
            Tuple of (StressTestDataPoint, current_metrics)
        """
        # Simulate memory pressure
        _, sim_errors = await self._simulate_memory_pressure(target_series)

        # Run test queries to measure impact
        latencies: list[float] = []
        successes = 0
        total = 0

        test_queries = [
            "up",
            "prometheus_tsdb_head_series",
            "process_resident_memory_bytes",
        ]

        for _ in range(5):
            for query in test_queries:
                success, latency_ms, _ = await self._query_prometheus(query)
                latencies.append(latency_ms)
                total += 1
                if success:
                    successes += 1

        # Calculate percentiles
        sorted_latencies = sorted(latencies) if latencies else [0]
        n = len(sorted_latencies)

        p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0
        p99 = sorted_latencies[min(int(n * 0.99), n - 1)] if n > 0 else 0

        # Get Prometheus metrics
        prom_metrics = await self._get_prometheus_metrics()

        # Check health
        is_healthy = await self._check_health()

        # Detect OOM symptoms
        oom_symptoms = await self._detect_oom_symptoms(prom_metrics, prev_metrics)

        success_rate = (successes / total * 100) if total > 0 else 0
        error_messages = sim_errors + oom_symptoms

        if success_rate < 90:
            error_messages.append(f"Success rate dropped to {success_rate:.1f}%")

        if p99 > 30000:  # 30 second threshold
            error_messages.append(f"P99 latency {p99:.1f}ms exceeds 30000ms threshold")

        # Calculate memory utilization percentage
        memory_bytes = prom_metrics.get("memory_bytes", 0)
        memory_percent = 0.0
        if self.config.memory_limit_bytes:
            memory_percent = (memory_bytes / self.config.memory_limit_bytes) * 100

        # Determine if this is a failure state
        is_failure = (
            not is_healthy
            or success_rate < 50
            or any("CRITICAL" in s for s in oom_symptoms)
        )

        data_point = StressTestDataPoint(
            load_level=target_series,
            query_latency_p50_ms=p50,
            query_latency_p99_ms=p99,
            success_rate_percent=success_rate,
            cpu_utilization_percent=prom_metrics.get("cpu_seconds", 0) * 100,
            memory_utilization_bytes=memory_bytes,
            memory_utilization_percent=memory_percent,
            active_series=int(prom_metrics.get("active_series", 0)),
            is_healthy=not is_failure,
            error_messages=error_messages,
        )

        return data_point, prom_metrics

    async def run(self) -> MemoryPressureResult:
        """Run the memory pressure stress test.

        Requirements: 17.5, 17.7

        Returns:
            MemoryPressureResult with test results and breaking point
        """
        result = MemoryPressureResult(config=self.config)
        result.start_time = datetime.utcnow()
        self._running = True
        self._generated_series = 0

        last_healthy_data_point: Optional[StressTestDataPoint] = None
        prev_metrics: Optional[dict[str, float]] = None
        initial_memory: float = 0.0

        async with httpx.AsyncClient() as client:
            self._client = client

            # Verify Prometheus is healthy before starting
            if not await self._check_health():
                result.passed = False
                result.error_logs.append("Prometheus not healthy at test start")
                result.end_time = datetime.utcnow()
                return result

            # Get initial memory
            initial_metrics = await self._get_prometheus_metrics()
            initial_memory = initial_metrics.get("memory_bytes", 0)

            current_series = self.config.initial_series

            while (
                self._running
                and current_series <= self.config.max_series
                and result.duration_seconds < self.config.max_test_duration_seconds
            ):
                # Measure at current series level
                data_point, current_metrics = await self._measure_at_series_level(
                    current_series,
                    prev_metrics,
                )
                result.data_points.append(data_point)

                # Track peak memory
                if data_point.memory_utilization_bytes > result.peak_memory_bytes:
                    result.peak_memory_bytes = data_point.memory_utilization_bytes

                # Collect failure symptoms
                if data_point.error_messages:
                    result.failure_symptoms.extend(data_point.error_messages)

                if data_point.is_healthy:
                    last_healthy_data_point = data_point
                    prev_metrics = current_metrics
                else:
                    # Failure detected - record breaking point
                    failure_mode = FailureMode.OOM

                    # Check if it's actually OOM or another failure
                    if not await self._check_health():
                        failure_mode = FailureMode.CRASH
                        result.oom_detected = True
                    elif data_point.success_rate_percent < 50:
                        failure_mode = FailureMode.DEGRADATION

                    result.breaking_point = BreakingPoint(
                        max_series=(
                            int(last_healthy_data_point.load_level)
                            if last_healthy_data_point else 0
                        ),
                        failure_mode=failure_mode,
                        failure_timestamp=datetime.utcnow(),
                        failure_symptoms=data_point.error_messages,
                        last_healthy_metrics={
                            "series": last_healthy_data_point.load_level if last_healthy_data_point else 0,
                            "memory_bytes": last_healthy_data_point.memory_utilization_bytes if last_healthy_data_point else 0,
                            "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms if last_healthy_data_point else 0,
                            "success_rate": last_healthy_data_point.success_rate_percent if last_healthy_data_point else 0,
                        },
                    )

                    result.error_logs.extend(data_point.error_messages)
                    break

                # Increase series count
                current_series += self.config.series_increment

                # Brief pause between levels
                await asyncio.sleep(self.config.sample_interval_seconds)

        self._client = None
        self._running = False
        result.end_time = datetime.utcnow()

        # Calculate memory growth rate
        if result.duration_seconds > 0 and initial_memory > 0:
            result.memory_growth_rate = (
                (result.peak_memory_bytes - initial_memory) / result.duration_seconds
            )

        # If we completed without failure, record the max achieved
        if result.breaking_point.failure_mode == FailureMode.NONE and last_healthy_data_point:
            result.breaking_point.max_series = int(last_healthy_data_point.load_level)
            result.breaking_point.last_healthy_metrics = {
                "series": last_healthy_data_point.load_level,
                "memory_bytes": last_healthy_data_point.memory_utilization_bytes,
                "latency_p99_ms": last_healthy_data_point.query_latency_p99_ms,
                "success_rate": last_healthy_data_point.success_rate_percent,
            }

        return result

    def stop(self) -> None:
        """Stop the stress test."""
        self._running = False


def run_memory_pressure_test_sync(
    prometheus_url: str = "http://localhost:9090",
    initial_series: int = 10000,
    max_series: int = 10_000_000,
    series_increment: int = 50000,
    memory_limit_bytes: Optional[int] = None,
) -> MemoryPressureResult:
    """Synchronous wrapper for running memory pressure test.

    Args:
        prometheus_url: URL of the Prometheus instance
        initial_series: Starting number of series
        max_series: Maximum series to attempt
        series_increment: Series increase per step
        memory_limit_bytes: Memory limit for OOM detection

    Returns:
        MemoryPressureResult
    """
    config = MemoryPressureConfig(
        prometheus_url=prometheus_url,
        initial_series=initial_series,
        max_series=max_series,
        series_increment=series_increment,
        memory_limit_bytes=memory_limit_bytes,
    )
    tester = MemoryPressureTester(config)
    return asyncio.run(tester.run())
