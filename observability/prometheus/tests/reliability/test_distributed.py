"""
Distributed reliability tests for Prometheus.

This module implements reliability tests specific to distributed Prometheus
deployments, verifying availability when replicas fail.

Requirements: 19.9, 19.10
"""

import logging
import subprocess
import time
from datetime import datetime
from typing import Optional

import httpx

from .config import DistributedReliabilityConfig, DeploymentMode
from .models import (
    HealthCheckResult,
    RecoveryMetrics,
    RecoveryStatus,
    ReliabilityTestResult,
    ReliabilityTestType,
)

logger = logging.getLogger(__name__)


class DistributedReliabilityTest:
    """
    Reliability test for distributed Prometheus deployments.

    Requirements: 19.9, 19.10

    This test verifies that distributed Prometheus maintains availability
    when individual replicas fail.
    """

    def __init__(self, config: Optional[DistributedReliabilityConfig] = None):
        """
        Initialize the distributed reliability test.

        Args:
            config: Test configuration
        """
        self.config = config or DistributedReliabilityConfig()
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

    def _perform_health_check(self) -> HealthCheckResult:
        """Perform a complete health check."""
        return HealthCheckResult(
            healthy_endpoint=self._check_healthy(),
            ready_endpoint=self._check_ready(),
            api_accessible=self._check_api_accessible(),
            query_success=self._check_query_success(),
            timestamp=datetime.utcnow(),
        )

    def _get_prometheus_pods(self) -> list[dict]:
        """
        Get list of Prometheus pods with their status.

        Returns:
            List of pod dictionaries with name and status
        """
        cmd = self._get_kubectl_cmd() + [
            "get", "pods",
            "-n", self.config.namespace,
            "-l", "app.kubernetes.io/name=prometheus",
            "-o", "json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            import json
            data = json.loads(result.stdout)
            pods = []
            for item in data.get("items", []):
                pods.append({
                    "name": item.get("metadata", {}).get("name", ""),
                    "status": item.get("status", {}).get("phase", "Unknown"),
                    "ready": all(
                        c.get("ready", False)
                        for c in item.get("status", {}).get("containerStatuses", [])
                    ),
                })
            return pods
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []

    def _get_running_pod_count(self) -> int:
        """Get count of running Prometheus pods."""
        pods = self._get_prometheus_pods()
        return sum(1 for p in pods if p.get("status") == "Running" and p.get("ready"))

    def _kill_pod(self, pod_name: str, force: bool = False) -> bool:
        """
        Kill a specific Prometheus pod.

        Args:
            pod_name: Name of the pod to kill
            force: Whether to force delete (grace-period=0)

        Returns:
            True if pod was killed successfully
        """
        cmd = self._get_kubectl_cmd() + [
            "delete", "pod", pod_name,
            "-n", self.config.namespace,
        ]

        if force:
            cmd.extend(["--grace-period=0", "--force"])
        else:
            cmd.append("--grace-period=30")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            logger.info(f"Killed pod {pod_name}: {result.stdout}")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"Failed to kill pod {pod_name}: {e}")
            return False

    def _verify_availability_during_failure(self) -> dict:
        """
        Verify Prometheus remains available during replica failure.

        Requirements: 19.10

        Returns:
            Dictionary with availability verification results
        """
        results = {
            "healthy": self._check_healthy(),
            "ready": self._check_ready(),
            "api_accessible": self._check_api_accessible(),
            "query_success": self._check_query_success(),
            "running_pods": self._get_running_pod_count(),
            "availability_maintained": False,
        }

        # Availability is maintained if we can still query
        results["availability_maintained"] = (
            results["api_accessible"] and results["query_success"]
        )

        return results

    def _wait_for_pod_recovery(self, expected_count: int) -> tuple[bool, float]:
        """
        Wait for pods to recover to expected count.

        Args:
            expected_count: Expected number of running pods

        Returns:
            Tuple of (recovered, time_to_recover)
        """
        start_time = time.time()

        while time.time() - start_time < self.config.recovery_timeout_seconds:
            current_count = self._get_running_pod_count()
            if current_count >= expected_count:
                return True, time.time() - start_time
            time.sleep(self.config.health_check_interval_seconds)

        return False, time.time() - start_time

    def _wait_for_recovery(self) -> RecoveryMetrics:
        """Wait for Prometheus to fully recover."""
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

    def run(self) -> ReliabilityTestResult:
        """
        Run the distributed reliability test.

        Requirements: 19.9, 19.10

        Returns:
            ReliabilityTestResult with test outcome
        """
        result = ReliabilityTestResult(
            test_name="distributed_reliability_test",
            test_type=ReliabilityTestType.DISTRIBUTED_AVAILABILITY,
            deployment_mode=DeploymentMode.DISTRIBUTED,
            start_time=datetime.utcnow(),
        )

        # Perform pre-test health check
        result.pre_test_health = self._perform_health_check()

        if not result.pre_test_health.is_healthy:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before test")
            result.end_time = datetime.utcnow()
            return result

        # Get initial pod count
        pods = self._get_prometheus_pods()
        initial_pod_count = len(pods)
        running_pod_count = sum(1 for p in pods if p.get("ready"))

        result.metadata["initial_pod_count"] = initial_pod_count
        result.metadata["initial_running_pods"] = running_pod_count
        result.metadata["pod_names"] = [p.get("name") for p in pods]

        if initial_pod_count < 2:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(
                f"Not enough replicas for distributed test: {initial_pod_count}"
            )
            result.end_time = datetime.utcnow()
            return result

        # Test replica failure
        if self.config.test_replica_failure:
            # Kill one pod
            pod_to_kill = pods[0].get("name")
            logger.info(f"Killing pod {pod_to_kill} to test replica failure...")

            kill_success = self._kill_pod(pod_to_kill)

            if not kill_success:
                result.recovery_status = RecoveryStatus.FAILED
                result.error_messages.append(f"Failed to kill pod: {pod_to_kill}")
                result.end_time = datetime.utcnow()
                return result

            result.metadata["killed_pod"] = pod_to_kill

            # Wait a moment for the kill to take effect
            time.sleep(5)

            # Verify availability during failure
            availability_check = self._verify_availability_during_failure()
            result.metadata["availability_during_failure"] = availability_check

            if not availability_check.get("availability_maintained"):
                result.error_messages.append(
                    "Availability not maintained during replica failure"
                )

            # Wait for pod to recover
            recovered, recovery_time = self._wait_for_pod_recovery(initial_pod_count)
            result.metadata["pod_recovery_time"] = recovery_time
            result.metadata["pods_recovered"] = recovered

        # Wait for full recovery
        result.recovery_metrics = self._wait_for_recovery()

        # Perform post-test health check
        result.post_test_health = self._perform_health_check()

        # Get final pod count
        final_pods = self._get_prometheus_pods()
        final_running = sum(1 for p in final_pods if p.get("ready"))
        result.metadata["final_pod_count"] = len(final_pods)
        result.metadata["final_running_pods"] = final_running

        # Determine recovery status
        if result.recovery_metrics.fully_recovered:
            if result.metadata.get("availability_during_failure", {}).get("availability_maintained"):
                result.recovery_status = RecoveryStatus.RECOVERED
            else:
                result.recovery_status = RecoveryStatus.PARTIAL_RECOVERY
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.end_time = datetime.utcnow()

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None


class MonolithicReliabilityTest:
    """
    Reliability test for monolithic Prometheus deployments.

    Requirements: 19.9

    This test verifies recovery behavior for single-instance Prometheus.
    """

    def __init__(self, config: Optional[DistributedReliabilityConfig] = None):
        """
        Initialize the monolithic reliability test.

        Args:
            config: Test configuration
        """
        self.config = config or DistributedReliabilityConfig()
        self.config.deployment_mode = DeploymentMode.MONOLITHIC
        self._http_client: Optional[httpx.Client] = None

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=30.0)
        return self._http_client

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

    def _perform_health_check(self) -> HealthCheckResult:
        """Perform a complete health check."""
        return HealthCheckResult(
            healthy_endpoint=self._check_healthy(),
            ready_endpoint=self._check_ready(),
            api_accessible=self._check_api_accessible(),
            query_success=self._check_query_success(),
            timestamp=datetime.utcnow(),
        )

    def _restart_prometheus(self) -> tuple[bool, str]:
        """
        Restart Prometheus container or process.

        Returns:
            Tuple of (success, target_name)
        """
        # Try Docker restart
        try:
            result = subprocess.run(
                ["docker", "restart", "prometheus"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return True, "prometheus-container"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        # Try systemctl restart
        try:
            result = subprocess.run(
                ["systemctl", "restart", "prometheus"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return True, "prometheus-service"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False, ""

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

    def run(self) -> ReliabilityTestResult:
        """
        Run the monolithic reliability test.

        Requirements: 19.9

        Returns:
            ReliabilityTestResult with test outcome
        """
        result = ReliabilityTestResult(
            test_name="monolithic_reliability_test",
            test_type=ReliabilityTestType.RESTART_RECOVERY,
            deployment_mode=DeploymentMode.MONOLITHIC,
            start_time=datetime.utcnow(),
        )

        # Perform pre-test health check
        result.pre_test_health = self._perform_health_check()

        if not result.pre_test_health.is_healthy:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before test")
            result.end_time = datetime.utcnow()
            return result

        # Restart Prometheus
        logger.info("Restarting monolithic Prometheus...")
        restart_success, target = self._restart_prometheus()

        if not restart_success:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(f"Failed to restart Prometheus: {target}")
            result.end_time = datetime.utcnow()
            return result

        result.metadata["restart_target"] = target

        # Wait for recovery
        result.recovery_metrics = self._wait_for_recovery()

        # Perform post-test health check
        result.post_test_health = self._perform_health_check()

        # Determine recovery status
        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        elif result.recovery_metrics.healthy_endpoint_status:
            result.recovery_status = RecoveryStatus.PARTIAL_RECOVERY
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.end_time = datetime.utcnow()

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None


def run_distributed_reliability_test(
    prometheus_url: str = "http://localhost:9090",
    namespace: str = "monitoring",
    replica_count: int = 2,
    recovery_timeout: int = 300,
    kubectl_context: Optional[str] = None,
) -> ReliabilityTestResult:
    """
    Convenience function to run distributed reliability test.

    Requirements: 19.9, 19.10

    Args:
        prometheus_url: URL of Prometheus instance
        namespace: Kubernetes namespace
        replica_count: Expected number of replicas
        recovery_timeout: Timeout for recovery in seconds
        kubectl_context: Kubernetes context to use

    Returns:
        ReliabilityTestResult with test outcome
    """
    config = DistributedReliabilityConfig(
        prometheus_url=prometheus_url,
        namespace=namespace,
        replica_count=replica_count,
        recovery_timeout_seconds=recovery_timeout,
        kubectl_context=kubectl_context,
    )

    test = DistributedReliabilityTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()


def run_monolithic_reliability_test(
    prometheus_url: str = "http://localhost:9090",
    recovery_timeout: int = 300,
) -> ReliabilityTestResult:
    """
    Convenience function to run monolithic reliability test.

    Requirements: 19.9

    Args:
        prometheus_url: URL of Prometheus instance
        recovery_timeout: Timeout for recovery in seconds

    Returns:
        ReliabilityTestResult with test outcome
    """
    config = DistributedReliabilityConfig(
        prometheus_url=prometheus_url,
        recovery_timeout_seconds=recovery_timeout,
    )

    test = MonolithicReliabilityTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
