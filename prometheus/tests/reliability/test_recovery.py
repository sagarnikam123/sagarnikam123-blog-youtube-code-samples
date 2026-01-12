"""
Restart recovery tests for Prometheus.

This module implements reliability tests that verify Prometheus recovers
correctly after pod/container restart using /-/healthy and /-/ready endpoints.

Requirements: 19.1, 19.8
"""

import logging
import subprocess
import time
from datetime import datetime
from typing import Optional

import httpx

from .config import RestartRecoveryConfig, RestartMethod, DeploymentMode
from .models import (
    HealthCheckResult,
    RecoveryMetrics,
    RecoveryStatus,
    ReliabilityTestResult,
    ReliabilityTestType,
)

logger = logging.getLogger(__name__)


class RestartRecoveryTest:
    """
    Reliability test that restarts Prometheus and verifies recovery.

    Requirements: 19.1, 19.8

    This test restarts Prometheus (pod, container, or process) and verifies
    that it recovers correctly using the /-/healthy and /-/ready endpoints.
    """

    def __init__(self, config: Optional[RestartRecoveryConfig] = None):
        """
        Initialize the restart recovery test.

        Args:
            config: Test configuration
        """
        self.config = config or RestartRecoveryConfig()
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
        """
        Check if Prometheus is healthy using /-/healthy endpoint.

        Requirements: 19.8

        Returns:
            True if healthy endpoint returns 200
        """
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/-/healthy"
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    def _check_ready(self) -> bool:
        """
        Check if Prometheus is ready using /-/ready endpoint.

        Requirements: 19.8

        Returns:
            True if ready endpoint returns 200
        """
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/-/ready"
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ready check failed: {e}")
            return False

    def _check_api_accessible(self) -> bool:
        """
        Check if Prometheus API is accessible.

        Returns:
            True if API responds to queries
        """
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/status/runtimeinfo"
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"API check failed: {e}")
            return False

    def _check_query_success(self) -> bool:
        """
        Check if Prometheus can execute queries.

        Returns:
            True if a simple query succeeds
        """
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": "up"},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "success"
            return False
        except Exception as e:
            logger.debug(f"Query check failed: {e}")
            return False

    def _perform_health_check(self) -> HealthCheckResult:
        """
        Perform a complete health check.

        Requirements: 19.8

        Returns:
            HealthCheckResult with all health statuses
        """
        return HealthCheckResult(
            healthy_endpoint=self._check_healthy(),
            ready_endpoint=self._check_ready(),
            api_accessible=self._check_api_accessible(),
            query_success=self._check_query_success(),
            timestamp=datetime.utcnow(),
        )

    def _get_prometheus_pods(self) -> list[str]:
        """
        Get list of Prometheus pod names.

        Returns:
            List of pod names matching the selector
        """
        cmd = self._get_kubectl_cmd() + [
            "get", "pods",
            "-n", self.config.namespace,
            "-l", self.config.pod_selector,
            "-o", "jsonpath={.items[*].metadata.name}",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            pods = result.stdout.strip().split()
            return [p for p in pods if p]
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get pods: {e.stderr}")
            return []
        except subprocess.TimeoutExpired:
            logger.error("Timeout getting pods")
            return []

    def _restart_pod(self, pod_name: str) -> bool:
        """
        Restart a Kubernetes pod by deleting it.

        Args:
            pod_name: Name of the pod to restart

        Returns:
            True if pod was deleted successfully
        """
        cmd = self._get_kubectl_cmd() + [
            "delete", "pod", pod_name,
            "-n", self.config.namespace,
            f"--grace-period={self.config.grace_period_seconds}",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            logger.info(f"Deleted pod {pod_name}: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete pod {pod_name}: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout deleting pod {pod_name}")
            return False

    def _rollout_restart(self) -> bool:
        """
        Perform a rollout restart of the Prometheus deployment.

        Returns:
            True if rollout restart was initiated successfully
        """
        # Try StatefulSet first, then Deployment
        for resource_type in ["statefulset", "deployment"]:
            cmd = self._get_kubectl_cmd() + [
                "rollout", "restart",
                f"{resource_type}/prometheus-kube-prometheus-prometheus",
                "-n", self.config.namespace,
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode == 0:
                    logger.info(f"Rollout restart initiated: {result.stdout}")
                    return True
            except subprocess.TimeoutExpired:
                continue

        logger.error("Failed to initiate rollout restart")
        return False

    def _restart_container(self) -> bool:
        """
        Restart a Docker container.

        Returns:
            True if container was restarted successfully
        """
        cmd = ["docker", "restart", self.config.container_name]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            logger.info(f"Restarted container: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart container: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout restarting container")
            return False

    def _restart_process(self) -> bool:
        """
        Restart Prometheus process using systemctl or launchctl.

        Returns:
            True if process was restarted successfully
        """
        # Try systemctl first (Linux)
        try:
            result = subprocess.run(
                ["systemctl", "restart", "prometheus"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                logger.info("Restarted prometheus via systemctl")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Try launchctl (macOS)
        try:
            subprocess.run(
                ["launchctl", "stop", "prometheus"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            time.sleep(2)
            result = subprocess.run(
                ["launchctl", "start", "prometheus"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                logger.info("Restarted prometheus via launchctl")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        logger.error("Failed to restart prometheus process")
        return False

    def _perform_restart(self) -> tuple[bool, str]:
        """
        Perform the restart based on configuration.

        Returns:
            Tuple of (success, target_name)
        """
        if self.config.restart_method == RestartMethod.POD_DELETE:
            pods = self._get_prometheus_pods()
            if not pods:
                return False, ""
            target_pod = pods[0]
            success = self._restart_pod(target_pod)
            return success, target_pod

        elif self.config.restart_method == RestartMethod.ROLLOUT_RESTART:
            success = self._rollout_restart()
            return success, "prometheus-deployment"

        elif self.config.restart_method == RestartMethod.CONTAINER_RESTART:
            success = self._restart_container()
            return success, self.config.container_name

        elif self.config.restart_method == RestartMethod.PROCESS_RESTART:
            success = self._restart_process()
            return success, "prometheus-process"

        return False, ""

    def _wait_for_recovery(self) -> RecoveryMetrics:
        """
        Wait for Prometheus to recover after restart.

        Requirements: 19.1, 19.8

        Returns:
            RecoveryMetrics with recovery status
        """
        start_time = time.time()
        metrics = RecoveryMetrics()

        while time.time() - start_time < self.config.recovery_timeout_seconds:
            metrics.healthy_endpoint_status = self._check_healthy()
            metrics.ready_endpoint_status = self._check_ready()
            metrics.api_accessible = self._check_api_accessible()
            metrics.query_success = self._check_query_success()

            if metrics.fully_recovered:
                metrics.recovery_time_seconds = time.time() - start_time
                logger.info(
                    f"Prometheus recovered in {metrics.recovery_time_seconds:.2f}s"
                )
                return metrics

            time.sleep(self.config.health_check_interval_seconds)

        metrics.recovery_time_seconds = time.time() - start_time
        logger.warning(
            f"Recovery timeout after {metrics.recovery_time_seconds:.2f}s"
        )
        return metrics

    def run(self) -> ReliabilityTestResult:
        """
        Run the restart recovery test.

        Requirements: 19.1, 19.8

        Returns:
            ReliabilityTestResult with test outcome
        """
        result = ReliabilityTestResult(
            test_name="restart_recovery_test",
            test_type=ReliabilityTestType.RESTART_RECOVERY,
            deployment_mode=DeploymentMode(self.config.deployment_mode.value),
            start_time=datetime.utcnow(),
        )

        # Perform pre-test health check
        result.pre_test_health = self._perform_health_check()

        if not result.pre_test_health.is_healthy:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(
                "Prometheus not healthy before restart"
            )
            result.end_time = datetime.utcnow()
            return result

        # Perform restart
        logger.info(f"Restarting Prometheus using method: {self.config.restart_method.value}")
        restart_success, target = self._perform_restart()

        if not restart_success:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(f"Failed to restart: {target}")
            result.end_time = datetime.utcnow()
            return result

        result.metadata["restart_target"] = target
        result.metadata["restart_method"] = self.config.restart_method.value

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
        result.metadata["recovery_timeout"] = self.config.recovery_timeout_seconds

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None


def run_restart_recovery_test(
    prometheus_url: str = "http://localhost:9090",
    namespace: str = "monitoring",
    restart_method: str = "pod_delete",
    pod_selector: str = "app.kubernetes.io/name=prometheus",
    container_name: str = "prometheus",
    recovery_timeout: int = 300,
    kubectl_context: Optional[str] = None,
) -> ReliabilityTestResult:
    """
    Convenience function to run restart recovery test.

    Requirements: 19.1, 19.8

    Args:
        prometheus_url: URL of Prometheus instance
        namespace: Kubernetes namespace
        restart_method: Method to use for restart
        pod_selector: Label selector for pods
        container_name: Name of the container
        recovery_timeout: Timeout for recovery in seconds
        kubectl_context: Kubernetes context to use

    Returns:
        ReliabilityTestResult with test outcome
    """
    method_map = {
        "pod_delete": RestartMethod.POD_DELETE,
        "container_restart": RestartMethod.CONTAINER_RESTART,
        "process_restart": RestartMethod.PROCESS_RESTART,
        "rollout_restart": RestartMethod.ROLLOUT_RESTART,
    }

    config = RestartRecoveryConfig(
        prometheus_url=prometheus_url,
        namespace=namespace,
        restart_method=method_map.get(restart_method, RestartMethod.POD_DELETE),
        pod_selector=pod_selector,
        container_name=container_name,
        recovery_timeout_seconds=recovery_timeout,
        kubectl_context=kubectl_context,
    )

    test = RestartRecoveryTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
