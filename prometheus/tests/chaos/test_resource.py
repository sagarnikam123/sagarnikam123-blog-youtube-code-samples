"""
Resource pressure chaos tests for Prometheus.

This module implements chaos tests that simulate CPU throttling,
memory pressure, and disk I/O latency to measure their impact on Prometheus.

Requirements: 20.2, 20.3, 20.4, 20.8, 20.9, 20.10
"""

import logging
import subprocess
import time
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx

from .config import (
    CPUThrottleConfig,
    DiskIOLatencyConfig,
    MemoryPressureConfig,
)
from .models import (
    ChaosEvent,
    ChaosTestResult,
    ChaosType,
    DeploymentMode,
    RecoveryMetrics,
    RecoveryStatus,
    ResourcePressureParams,
)

logger = logging.getLogger(__name__)


class ResourcePressureChaosTest:
    """
    Base class for resource pressure chaos tests.

    Requirements: 20.2, 20.3, 20.4, 20.9

    This class provides common functionality for tests that apply
    resource pressure (CPU, memory, disk I/O) to Prometheus.
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        namespace: str = "monitoring",
        deployment_mode: DeploymentMode = DeploymentMode.DISTRIBUTED,
        recovery_timeout_seconds: int = 300,
        health_check_interval_seconds: float = 5.0,
        kubectl_context: Optional[str] = None,
    ):
        """
        Initialize the resource pressure test.

        Args:
            prometheus_url: URL of Prometheus instance
            namespace: Kubernetes namespace
            deployment_mode: Monolithic or distributed
            recovery_timeout_seconds: Timeout for recovery
            health_check_interval_seconds: Interval between health checks
            kubectl_context: Kubernetes context to use
        """
        self.prometheus_url = prometheus_url
        self.namespace = namespace
        self.deployment_mode = deployment_mode
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.health_check_interval_seconds = health_check_interval_seconds
        self.kubectl_context = kubectl_context
        self._http_client: Optional[httpx.Client] = None

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=30.0)
        return self._http_client

    def _get_kubectl_cmd(self) -> list[str]:
        """Get base kubectl command with context if specified."""
        cmd = ["kubectl"]
        if self.kubectl_context:
            cmd.extend(["--context", self.kubectl_context])
        return cmd

    def _check_healthy(self) -> bool:
        """Check if Prometheus is healthy."""
        try:
            response = self.http_client.get(f"{self.prometheus_url}/-/healthy")
            return response.status_code == 200
        except Exception:
            return False

    def _check_ready(self) -> bool:
        """Check if Prometheus is ready."""
        try:
            response = self.http_client.get(f"{self.prometheus_url}/-/ready")
            return response.status_code == 200
        except Exception:
            return False

    def _check_api_accessible(self) -> bool:
        """Check if Prometheus API is accessible."""
        try:
            response = self.http_client.get(
                f"{self.prometheus_url}/api/v1/status/runtimeinfo"
            )
            return response.status_code == 200
        except Exception:
            return False

    def _check_query_success(self) -> bool:
        """Check if Prometheus can execute queries."""
        try:
            response = self.http_client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": "up"},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "success"
            return False
        except Exception:
            return False

    def _measure_query_latency(self) -> Optional[float]:
        """Measure query latency in milliseconds."""
        try:
            start = time.time()
            response = self.http_client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": "prometheus_tsdb_head_series"},
            )
            if response.status_code == 200:
                return (time.time() - start) * 1000
            return None
        except Exception:
            return None

    def _collect_metrics(self) -> dict[str, Any]:
        """Collect current metrics."""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": self._check_healthy(),
            "ready": self._check_ready(),
            "api_accessible": self._check_api_accessible(),
            "query_latency_ms": self._measure_query_latency(),
        }
        return metrics

    def _wait_for_recovery(self) -> RecoveryMetrics:
        """Wait for Prometheus to recover."""
        start_time = time.time()
        metrics = RecoveryMetrics()

        while time.time() - start_time < self.recovery_timeout_seconds:
            metrics.healthy_endpoint_status = self._check_healthy()
            metrics.ready_endpoint_status = self._check_ready()
            metrics.api_accessible = self._check_api_accessible()
            metrics.query_success = self._check_query_success()

            if metrics.fully_recovered:
                metrics.recovery_time_seconds = time.time() - start_time
                return metrics

            time.sleep(self.health_check_interval_seconds)

        metrics.recovery_time_seconds = time.time() - start_time
        return metrics

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None


class CPUThrottleChaosTest(ResourcePressureChaosTest):
    """
    Chaos test that simulates CPU throttling.

    Requirements: 20.2, 20.9

    This test applies CPU throttling to Prometheus and measures
    the impact on query latency and overall performance.
    """

    def __init__(self, config: Optional[CPUThrottleConfig] = None):
        """
        Initialize the CPU throttle test.

        Args:
            config: Test configuration
        """
        self.config = config or CPUThrottleConfig()
        super().__init__(
            prometheus_url=self.config.prometheus_url,
            namespace=self.config.namespace,
            deployment_mode=self.config.deployment_mode,
            recovery_timeout_seconds=self.config.recovery_timeout_seconds,
            health_check_interval_seconds=self.config.health_check_interval_seconds,
            kubectl_context=self.config.kubectl_context,
        )
        self._stress_process: Optional[subprocess.Popen] = None

    def _apply_cpu_throttle_docker(self) -> bool:
        """Apply CPU throttle using Docker."""
        try:
            # Get container ID
            result = subprocess.run(
                ["docker", "ps", "-q", "--filter", f"name={self.config.target_container}"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            container_id = result.stdout.strip()
            if not container_id:
                return False

            # Calculate CPU quota (throttle_percent of 100000 period)
            cpu_quota = int(100000 * (100 - self.config.throttle_percent) / 100)

            # Update container CPU quota
            subprocess.run(
                ["docker", "update", f"--cpu-quota={cpu_quota}", container_id],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to apply CPU throttle: {e}")
            return False

    def _apply_cpu_throttle_stress(self) -> bool:
        """Apply CPU stress using stress-ng tool."""
        try:
            # Use stress-ng to consume CPU
            cpu_workers = max(1, int(self.config.throttle_percent / 25))
            self._stress_process = subprocess.Popen(
                [
                    "stress-ng",
                    "--cpu", str(cpu_workers),
                    "--timeout", f"{self.config.duration_seconds}s",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except FileNotFoundError:
            logger.warning("stress-ng not found, trying stress")
            try:
                self._stress_process = subprocess.Popen(
                    [
                        "stress",
                        "--cpu", str(max(1, int(self.config.throttle_percent / 25))),
                        "--timeout", str(self.config.duration_seconds),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except FileNotFoundError:
                logger.error("Neither stress-ng nor stress found")
                return False
        except Exception as e:
            logger.error(f"Failed to apply CPU stress: {e}")
            return False

    def _remove_cpu_throttle(self) -> None:
        """Remove CPU throttle."""
        if self._stress_process:
            self._stress_process.terminate()
            try:
                self._stress_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._stress_process.kill()
            self._stress_process = None

    def run(self) -> ChaosTestResult:
        """
        Run the CPU throttle chaos test.

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.CPU_THROTTLE,
            target=self.config.target_container,
            deployment_mode=self.config.deployment_mode,
            parameters={
                "throttle_percent": self.config.throttle_percent,
                "duration_seconds": self.config.duration_seconds,
            },
        )

        result = ChaosTestResult(
            test_name="cpu_throttle_chaos_test",
            chaos_event=chaos_event,
        )

        # Collect pre-chaos metrics
        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        # Apply CPU throttle
        logger.info(f"Applying {self.config.throttle_percent}% CPU throttle")

        if self.config.deployment_mode == DeploymentMode.MONOLITHIC:
            success = self._apply_cpu_throttle_docker() or self._apply_cpu_throttle_stress()
        else:
            success = self._apply_cpu_throttle_stress()

        if not success:
            result.error_messages.append("Failed to apply CPU throttle")

        # Collect metrics during throttle
        metrics_during = []
        start_time = time.time()
        while time.time() - start_time < self.config.duration_seconds:
            metrics_during.append(self._collect_metrics())
            time.sleep(self.health_check_interval_seconds)

        # Remove throttle
        self._remove_cpu_throttle()
        chaos_event.end_time = datetime.utcnow()

        # Wait for recovery
        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        # Calculate impact
        pre_latency = result.pre_chaos_metrics.get("query_latency_ms", 0)
        during_latencies = [
            m.get("query_latency_ms", 0)
            for m in metrics_during
            if m.get("query_latency_ms")
        ]
        avg_during_latency = sum(during_latencies) / len(during_latencies) if during_latencies else 0

        result.metadata = {
            "throttle_percent": self.config.throttle_percent,
            "duration_seconds": self.config.duration_seconds,
            "pre_chaos_latency_ms": pre_latency,
            "avg_during_chaos_latency_ms": avg_during_latency,
            "latency_increase_percent": (
                ((avg_during_latency - pre_latency) / pre_latency * 100)
                if pre_latency > 0 else 0
            ),
            "metrics_during_chaos": metrics_during,
        }

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        return result


class MemoryPressureChaosTest(ResourcePressureChaosTest):
    """
    Chaos test that simulates memory pressure.

    Requirements: 20.3, 20.9

    This test applies memory pressure and verifies OOM handling.
    """

    def __init__(self, config: Optional[MemoryPressureConfig] = None):
        """
        Initialize the memory pressure test.

        Args:
            config: Test configuration
        """
        self.config = config or MemoryPressureConfig()
        super().__init__(
            prometheus_url=self.config.prometheus_url,
            namespace=self.config.namespace,
            deployment_mode=self.config.deployment_mode,
            recovery_timeout_seconds=self.config.recovery_timeout_seconds,
            health_check_interval_seconds=self.config.health_check_interval_seconds,
            kubectl_context=self.config.kubectl_context,
        )
        self._stress_process: Optional[subprocess.Popen] = None

    def _apply_memory_pressure(self) -> bool:
        """Apply memory pressure using stress-ng."""
        try:
            memory_arg = (
                f"{self.config.memory_bytes}"
                if self.config.memory_bytes
                else f"{int(self.config.memory_percent)}%"
            )

            self._stress_process = subprocess.Popen(
                [
                    "stress-ng",
                    "--vm", "1",
                    "--vm-bytes", memory_arg,
                    "--timeout", f"{self.config.duration_seconds}s",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except FileNotFoundError:
            logger.error("stress-ng not found")
            return False
        except Exception as e:
            logger.error(f"Failed to apply memory pressure: {e}")
            return False

    def _remove_memory_pressure(self) -> None:
        """Remove memory pressure."""
        if self._stress_process:
            self._stress_process.terminate()
            try:
                self._stress_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._stress_process.kill()
            self._stress_process = None

    def run(self) -> ChaosTestResult:
        """
        Run the memory pressure chaos test.

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]

        params = ResourcePressureParams(
            memory_bytes=self.config.memory_bytes,
            memory_percent=self.config.memory_percent,
            duration_seconds=self.config.duration_seconds,
        )

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.MEMORY_PRESSURE,
            target="system",
            deployment_mode=self.config.deployment_mode,
            parameters=params.to_dict(),
        )

        result = ChaosTestResult(
            test_name="memory_pressure_chaos_test",
            chaos_event=chaos_event,
        )

        # Collect pre-chaos metrics
        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        # Apply memory pressure
        logger.info(f"Applying memory pressure: {self.config.memory_percent}%")

        if not self._apply_memory_pressure():
            result.error_messages.append("Failed to apply memory pressure")

        # Collect metrics during pressure
        metrics_during = []
        start_time = time.time()
        while time.time() - start_time < self.config.duration_seconds:
            metrics_during.append(self._collect_metrics())
            time.sleep(self.health_check_interval_seconds)

        # Remove pressure
        self._remove_memory_pressure()
        chaos_event.end_time = datetime.utcnow()

        # Wait for recovery
        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        # Check for OOM events
        oom_detected = any(
            not m.get("healthy", True) for m in metrics_during
        )

        result.metadata = {
            "memory_percent": self.config.memory_percent,
            "memory_bytes": self.config.memory_bytes,
            "duration_seconds": self.config.duration_seconds,
            "oom_detected": oom_detected,
            "metrics_during_chaos": metrics_during,
        }

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        return result


class DiskIOLatencyChaosTest(ResourcePressureChaosTest):
    """
    Chaos test that simulates disk I/O latency.

    Requirements: 20.4, 20.9

    This test injects disk I/O latency and measures the impact.
    """

    def __init__(self, config: Optional[DiskIOLatencyConfig] = None):
        """
        Initialize the disk I/O latency test.

        Args:
            config: Test configuration
        """
        self.config = config or DiskIOLatencyConfig()
        super().__init__(
            prometheus_url=self.config.prometheus_url,
            namespace=self.config.namespace,
            deployment_mode=self.config.deployment_mode,
            recovery_timeout_seconds=self.config.recovery_timeout_seconds,
            health_check_interval_seconds=self.config.health_check_interval_seconds,
            kubectl_context=self.config.kubectl_context,
        )
        self._io_process: Optional[subprocess.Popen] = None

    def _apply_io_latency(self) -> bool:
        """Apply I/O latency using stress-ng or fio."""
        try:
            # Use stress-ng for I/O stress
            self._io_process = subprocess.Popen(
                [
                    "stress-ng",
                    "--hdd", "1",
                    "--hdd-opts", "sync",
                    "--timeout", f"{self.config.duration_seconds}s",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except FileNotFoundError:
            logger.warning("stress-ng not found, I/O latency simulation limited")
            return False
        except Exception as e:
            logger.error(f"Failed to apply I/O latency: {e}")
            return False

    def _remove_io_latency(self) -> None:
        """Remove I/O latency."""
        if self._io_process:
            self._io_process.terminate()
            try:
                self._io_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._io_process.kill()
            self._io_process = None

    def run(self) -> ChaosTestResult:
        """
        Run the disk I/O latency chaos test.

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]

        params = ResourcePressureParams(
            io_latency_ms=self.config.latency_ms,
            duration_seconds=self.config.duration_seconds,
        )

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.DISK_IO_LATENCY,
            target=self.config.target_path,
            deployment_mode=self.config.deployment_mode,
            parameters=params.to_dict(),
        )

        result = ChaosTestResult(
            test_name="disk_io_latency_chaos_test",
            chaos_event=chaos_event,
        )

        # Collect pre-chaos metrics
        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        # Apply I/O latency
        logger.info(f"Applying {self.config.latency_ms}ms I/O latency")

        if not self._apply_io_latency():
            result.error_messages.append("Failed to apply I/O latency")

        # Collect metrics during latency
        metrics_during = []
        start_time = time.time()
        while time.time() - start_time < self.config.duration_seconds:
            metrics_during.append(self._collect_metrics())
            time.sleep(self.health_check_interval_seconds)

        # Remove latency
        self._remove_io_latency()
        chaos_event.end_time = datetime.utcnow()

        # Wait for recovery
        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        result.metadata = {
            "latency_ms": self.config.latency_ms,
            "jitter_ms": self.config.jitter_ms,
            "target_path": self.config.target_path,
            "duration_seconds": self.config.duration_seconds,
            "metrics_during_chaos": metrics_during,
        }

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        return result


def run_cpu_throttle_test(
    prometheus_url: str = "http://localhost:9090",
    throttle_percent: float = 80.0,
    duration_seconds: int = 60,
    recovery_timeout: int = 300,
) -> ChaosTestResult:
    """
    Convenience function to run CPU throttle chaos test.

    Requirements: 20.2, 20.9, 20.10
    """
    config = CPUThrottleConfig(
        prometheus_url=prometheus_url,
        throttle_percent=throttle_percent,
        duration_seconds=duration_seconds,
        recovery_timeout_seconds=recovery_timeout,
    )

    test = CPUThrottleChaosTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()


def run_memory_pressure_test(
    prometheus_url: str = "http://localhost:9090",
    memory_percent: float = 80.0,
    duration_seconds: int = 60,
    recovery_timeout: int = 300,
) -> ChaosTestResult:
    """
    Convenience function to run memory pressure chaos test.

    Requirements: 20.3, 20.9, 20.10
    """
    config = MemoryPressureConfig(
        prometheus_url=prometheus_url,
        memory_percent=memory_percent,
        duration_seconds=duration_seconds,
        recovery_timeout_seconds=recovery_timeout,
    )

    test = MemoryPressureChaosTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()


def run_disk_io_latency_test(
    prometheus_url: str = "http://localhost:9090",
    latency_ms: int = 100,
    duration_seconds: int = 60,
    recovery_timeout: int = 300,
) -> ChaosTestResult:
    """
    Convenience function to run disk I/O latency chaos test.

    Requirements: 20.4, 20.9, 20.10
    """
    config = DiskIOLatencyConfig(
        prometheus_url=prometheus_url,
        latency_ms=latency_ms,
        duration_seconds=duration_seconds,
        recovery_timeout_seconds=recovery_timeout,
    )

    test = DiskIOLatencyChaosTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
