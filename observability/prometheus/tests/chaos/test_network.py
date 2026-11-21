"""
Network chaos tests for Prometheus.

This module implements chaos tests that simulate network latency
and scrape target failures to measure their impact on Prometheus.

Requirements: 20.5, 20.6, 20.8, 20.9, 20.10
"""

import logging
import subprocess
import time
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx

from .config import NetworkLatencyConfig, TargetFailureConfig
from .models import (
    ChaosEvent,
    ChaosTestResult,
    ChaosType,
    DeploymentMode,
    NetworkChaosParams,
    RecoveryMetrics,
    RecoveryStatus,
)

logger = logging.getLogger(__name__)


class NetworkLatencyChaosTest:
    """
    Chaos test that simulates network latency.

    Requirements: 20.5, 20.9

    This test injects network latency to scrape targets and measures
    the impact on Prometheus scraping and query performance.
    """

    def __init__(self, config: Optional[NetworkLatencyConfig] = None):
        """
        Initialize the network latency test.

        Args:
            config: Test configuration
        """
        self.config = config or NetworkLatencyConfig()
        self._http_client: Optional[httpx.Client] = None
        self._tc_applied = False

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=30.0)
        return self._http_client

    def _get_kubectl_cmd(self) -> list[str]:
        """Get base kubectl command with context if specified."""
        cmd = ["kubectl"]
        if self.config.kubectl_context:
            cmd.extend(["--context", self.config.kubectl_context])
        return cmd

    def _check_healthy(self) -> bool:
        """Check if Prometheus is healthy."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/-/healthy"
            )
            return response.status_code == 200
        except Exception:
            return False

    def _check_ready(self) -> bool:
        """Check if Prometheus is ready."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/-/ready"
            )
            return response.status_code == 200
        except Exception:
            return False

    def _check_api_accessible(self) -> bool:
        """Check if Prometheus API is accessible."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/status/runtimeinfo"
            )
            return response.status_code == 200
        except Exception:
            return False

    def _check_query_success(self) -> bool:
        """Check if Prometheus can execute queries."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": "up"},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "success"
            return False
        except Exception:
            return False

    def _get_scrape_metrics(self) -> dict[str, Any]:
        """Get scrape-related metrics."""
        metrics = {}
        try:
            # Get scrape duration
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": "avg(scrape_duration_seconds)"},
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get("data", {}).get("result", [])
                if result:
                    metrics["avg_scrape_duration_seconds"] = float(
                        result[0].get("value", [0, 0])[1]
                    )

            # Get scrape success rate
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": "avg(up)"},
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get("data", {}).get("result", [])
                if result:
                    metrics["scrape_success_rate"] = float(
                        result[0].get("value", [0, 0])[1]
                    )
        except Exception as e:
            logger.debug(f"Failed to get scrape metrics: {e}")

        return metrics

    def _collect_metrics(self) -> dict[str, Any]:
        """Collect current metrics."""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": self._check_healthy(),
            "ready": self._check_ready(),
            "api_accessible": self._check_api_accessible(),
        }
        metrics.update(self._get_scrape_metrics())
        return metrics

    def _apply_network_latency_tc(self) -> bool:
        """
        Apply network latency using tc (traffic control).

        Note: Requires root/sudo privileges.
        """
        try:
            # Add latency to default interface
            cmd = [
                "sudo", "tc", "qdisc", "add", "dev", "eth0",
                "root", "netem", "delay",
                f"{self.config.latency_ms}ms",
                f"{self.config.jitter_ms}ms",
                f"{self.config.correlation_percent}%",
            ]

            subprocess.run(cmd, capture_output=True, check=True, timeout=30)
            self._tc_applied = True
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"tc command failed: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.warning("tc command not found")
            return False
        except Exception as e:
            logger.error(f"Failed to apply network latency: {e}")
            return False

    def _apply_network_latency_iptables(self) -> bool:
        """
        Simulate network latency using iptables with NFQUEUE.

        This is a fallback method that drops packets randomly.
        """
        # This is a simplified simulation - real implementation would
        # use more sophisticated packet manipulation
        logger.info("Network latency simulation via iptables not fully implemented")
        return False

    def _remove_network_latency(self) -> None:
        """Remove network latency."""
        if self._tc_applied:
            try:
                subprocess.run(
                    ["sudo", "tc", "qdisc", "del", "dev", "eth0", "root"],
                    capture_output=True,
                    timeout=30,
                )
                self._tc_applied = False
            except Exception as e:
                logger.warning(f"Failed to remove tc rules: {e}")

    def _wait_for_recovery(self) -> RecoveryMetrics:
        """Wait for Prometheus to recover."""
        start_time = time.time()
        metrics = RecoveryMetrics()

        while time.time() - start_time < self.config.recovery_timeout_seconds:
            metrics.healthy_endpoint_status = self._check_healthy()
            metrics.ready_endpoint_status = self._check_ready()
            metrics.api_accessible = self._check_api_accessible()
            metrics.query_success = self._check_query_success()

            if metrics.fully_recovered:
                metrics.recovery_time_seconds = time.time() - start_time
                return metrics

            time.sleep(self.config.health_check_interval_seconds)

        metrics.recovery_time_seconds = time.time() - start_time
        return metrics

    def run(self) -> ChaosTestResult:
        """
        Run the network latency chaos test.

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]

        params = NetworkChaosParams(
            latency_ms=self.config.latency_ms,
            jitter_ms=self.config.jitter_ms,
            target_endpoints=self.config.target_hosts,
            duration_seconds=self.config.duration_seconds,
        )

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.NETWORK_LATENCY,
            target="network",
            deployment_mode=self.config.deployment_mode,
            parameters=params.to_dict(),
        )

        result = ChaosTestResult(
            test_name="network_latency_chaos_test",
            chaos_event=chaos_event,
        )

        # Collect pre-chaos metrics
        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        # Apply network latency
        logger.info(
            f"Applying {self.config.latency_ms}ms network latency "
            f"(±{self.config.jitter_ms}ms)"
        )

        latency_applied = (
            self._apply_network_latency_tc() or
            self._apply_network_latency_iptables()
        )

        if not latency_applied:
            result.error_messages.append(
                "Failed to apply network latency - requires root privileges"
            )
            # Continue test to measure baseline behavior

        # Collect metrics during latency
        metrics_during = []
        start_time = time.time()
        while time.time() - start_time < self.config.duration_seconds:
            metrics_during.append(self._collect_metrics())
            time.sleep(self.config.health_check_interval_seconds)

        # Remove latency
        self._remove_network_latency()
        chaos_event.end_time = datetime.utcnow()

        # Wait for recovery
        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        # Calculate impact on scrape duration
        pre_scrape_duration = result.pre_chaos_metrics.get(
            "avg_scrape_duration_seconds", 0
        )
        during_scrape_durations = [
            m.get("avg_scrape_duration_seconds", 0)
            for m in metrics_during
            if m.get("avg_scrape_duration_seconds")
        ]
        avg_during_scrape = (
            sum(during_scrape_durations) / len(during_scrape_durations)
            if during_scrape_durations else 0
        )

        result.metadata = {
            "latency_ms": self.config.latency_ms,
            "jitter_ms": self.config.jitter_ms,
            "duration_seconds": self.config.duration_seconds,
            "latency_applied": latency_applied,
            "pre_scrape_duration_seconds": pre_scrape_duration,
            "avg_during_scrape_duration_seconds": avg_during_scrape,
            "scrape_duration_increase_percent": (
                ((avg_during_scrape - pre_scrape_duration) / pre_scrape_duration * 100)
                if pre_scrape_duration > 0 else 0
            ),
            "metrics_during_chaos": metrics_during,
        }

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        self._remove_network_latency()
        if self._http_client:
            self._http_client.close()
            self._http_client = None


class TargetFailureChaosTest:
    """
    Chaos test that simulates scrape target failures.

    Requirements: 20.6, 20.9

    This test simulates partial or complete failure of scrape targets
    and measures how Prometheus handles the failures.
    """

    def __init__(self, config: Optional[TargetFailureConfig] = None):
        """
        Initialize the target failure test.

        Args:
            config: Test configuration
        """
        self.config = config or TargetFailureConfig()
        self._http_client: Optional[httpx.Client] = None
        self._scaled_deployments: list[tuple[str, int]] = []

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=30.0)
        return self._http_client

    def _get_kubectl_cmd(self) -> list[str]:
        """Get base kubectl command with context if specified."""
        cmd = ["kubectl"]
        if self.config.kubectl_context:
            cmd.extend(["--context", self.config.kubectl_context])
        return cmd

    def _check_healthy(self) -> bool:
        """Check if Prometheus is healthy."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/-/healthy"
            )
            return response.status_code == 200
        except Exception:
            return False

    def _check_ready(self) -> bool:
        """Check if Prometheus is ready."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/-/ready"
            )
            return response.status_code == 200
        except Exception:
            return False

    def _check_api_accessible(self) -> bool:
        """Check if Prometheus API is accessible."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/status/runtimeinfo"
            )
            return response.status_code == 200
        except Exception:
            return False

    def _check_query_success(self) -> bool:
        """Check if Prometheus can execute queries."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": "up"},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "success"
            return False
        except Exception:
            return False

    def _get_targets_status(self) -> tuple[int, int, list[dict]]:
        """
        Get scrape targets status.

        Returns:
            Tuple of (targets_up, total_targets, target_details)
        """
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/targets"
            )
            if response.status_code == 200:
                data = response.json()
                targets = data.get("data", {}).get("activeTargets", [])
                total = len(targets)
                up = sum(1 for t in targets if t.get("health") == "up")
                details = [
                    {
                        "job": t.get("labels", {}).get("job", "unknown"),
                        "instance": t.get("labels", {}).get("instance", "unknown"),
                        "health": t.get("health", "unknown"),
                    }
                    for t in targets
                ]
                return up, total, details
            return 0, 0, []
        except Exception as e:
            logger.debug(f"Failed to get targets: {e}")
            return 0, 0, []

    def _collect_metrics(self) -> dict[str, Any]:
        """Collect current metrics."""
        targets_up, total_targets, target_details = self._get_targets_status()

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": self._check_healthy(),
            "ready": self._check_ready(),
            "api_accessible": self._check_api_accessible(),
            "targets_up": targets_up,
            "total_targets": total_targets,
            "target_success_rate": (
                targets_up / total_targets * 100 if total_targets > 0 else 0
            ),
        }
        return metrics

    def _get_target_deployments(self) -> list[tuple[str, str, int]]:
        """
        Get deployments matching the target selector.

        Returns:
            List of (deployment_name, namespace, replicas)
        """
        if not self.config.target_selector:
            return []

        cmd = self._get_kubectl_cmd() + [
            "get", "deployments",
            "-A",
            "-l", self.config.target_selector,
            "-o", "jsonpath={range .items[*]}{.metadata.name},{.metadata.namespace},{.spec.replicas}{\"\\n\"}{end}",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            deployments = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(',')
                    if len(parts) == 3:
                        deployments.append((parts[0], parts[1], int(parts[2])))
            return deployments
        except Exception as e:
            logger.error(f"Failed to get deployments: {e}")
            return []

    def _scale_deployment(self, name: str, namespace: str, replicas: int) -> bool:
        """Scale a deployment to specified replicas."""
        cmd = self._get_kubectl_cmd() + [
            "scale", "deployment", name,
            "-n", namespace,
            f"--replicas={replicas}",
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            return True
        except Exception as e:
            logger.error(f"Failed to scale {name}: {e}")
            return False

    def _simulate_target_failures(self) -> int:
        """
        Simulate target failures by scaling down deployments.

        Returns:
            Number of targets affected
        """
        deployments = self._get_target_deployments()
        if not deployments:
            logger.warning("No target deployments found")
            return 0

        # Calculate how many to fail
        num_to_fail = max(1, int(len(deployments) * self.config.failure_percent / 100))

        affected = 0
        for name, namespace, original_replicas in deployments[:num_to_fail]:
            self._scaled_deployments.append((name, namespace, original_replicas))

            if self.config.failure_type == "complete":
                new_replicas = 0
            else:  # partial
                new_replicas = max(0, original_replicas - 1)

            if self._scale_deployment(name, namespace, new_replicas):
                affected += original_replicas - new_replicas

        return affected

    def _restore_targets(self) -> None:
        """Restore failed targets by scaling deployments back up."""
        for name, namespace, original_replicas in self._scaled_deployments:
            self._scale_deployment(name, namespace, original_replicas)
        self._scaled_deployments = []

    def _wait_for_recovery(self) -> RecoveryMetrics:
        """Wait for Prometheus to recover."""
        start_time = time.time()
        metrics = RecoveryMetrics()

        while time.time() - start_time < self.config.recovery_timeout_seconds:
            metrics.healthy_endpoint_status = self._check_healthy()
            metrics.ready_endpoint_status = self._check_ready()
            metrics.api_accessible = self._check_api_accessible()
            metrics.query_success = self._check_query_success()

            targets_up, total_targets, _ = self._get_targets_status()
            metrics.scrape_targets_up = targets_up
            metrics.total_scrape_targets = total_targets

            if metrics.fully_recovered:
                metrics.recovery_time_seconds = time.time() - start_time
                return metrics

            time.sleep(self.config.health_check_interval_seconds)

        metrics.recovery_time_seconds = time.time() - start_time
        return metrics

    def run(self) -> ChaosTestResult:
        """
        Run the target failure chaos test.

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.TARGET_FAILURE,
            target=self.config.target_selector or "scrape_targets",
            deployment_mode=self.config.deployment_mode,
            parameters={
                "failure_percent": self.config.failure_percent,
                "failure_type": self.config.failure_type,
                "duration_seconds": self.config.duration_seconds,
            },
        )

        result = ChaosTestResult(
            test_name="target_failure_chaos_test",
            chaos_event=chaos_event,
        )

        # Collect pre-chaos metrics
        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        # Simulate target failures
        logger.info(
            f"Simulating {self.config.failure_percent}% "
            f"{self.config.failure_type} target failures"
        )

        affected_targets = self._simulate_target_failures()

        if affected_targets == 0 and self.config.target_selector:
            result.error_messages.append("No targets were affected")

        # Collect metrics during failure
        metrics_during = []
        start_time = time.time()
        while time.time() - start_time < self.config.duration_seconds:
            metrics_during.append(self._collect_metrics())
            time.sleep(self.config.health_check_interval_seconds)

        # Restore targets
        self._restore_targets()
        chaos_event.end_time = datetime.utcnow()

        # Wait for recovery
        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        # Calculate impact
        pre_success_rate = result.pre_chaos_metrics.get("target_success_rate", 100)
        during_success_rates = [
            m.get("target_success_rate", 0) for m in metrics_during
        ]
        min_during_success = min(during_success_rates) if during_success_rates else 0

        result.metadata = {
            "failure_percent": self.config.failure_percent,
            "failure_type": self.config.failure_type,
            "duration_seconds": self.config.duration_seconds,
            "affected_targets": affected_targets,
            "pre_target_success_rate": pre_success_rate,
            "min_during_target_success_rate": min_during_success,
            "metrics_during_chaos": metrics_during,
        }

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        self._restore_targets()
        if self._http_client:
            self._http_client.close()
            self._http_client = None


def run_network_latency_test(
    prometheus_url: str = "http://localhost:9090",
    latency_ms: int = 100,
    jitter_ms: int = 20,
    duration_seconds: int = 60,
    recovery_timeout: int = 300,
) -> ChaosTestResult:
    """
    Convenience function to run network latency chaos test.

    Requirements: 20.5, 20.9, 20.10
    """
    config = NetworkLatencyConfig(
        prometheus_url=prometheus_url,
        latency_ms=latency_ms,
        jitter_ms=jitter_ms,
        duration_seconds=duration_seconds,
        recovery_timeout_seconds=recovery_timeout,
    )

    test = NetworkLatencyChaosTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()


def run_target_failure_test(
    prometheus_url: str = "http://localhost:9090",
    target_selector: str = "",
    failure_percent: float = 50.0,
    failure_type: str = "complete",
    duration_seconds: int = 60,
    recovery_timeout: int = 300,
    namespace: str = "monitoring",
    kubectl_context: Optional[str] = None,
) -> ChaosTestResult:
    """
    Convenience function to run target failure chaos test.

    Requirements: 20.6, 20.9, 20.10
    """
    config = TargetFailureConfig(
        prometheus_url=prometheus_url,
        namespace=namespace,
        target_selector=target_selector,
        failure_percent=failure_percent,
        failure_type=failure_type,
        duration_seconds=duration_seconds,
        recovery_timeout_seconds=recovery_timeout,
        kubectl_context=kubectl_context,
    )

    test = TargetFailureChaosTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
