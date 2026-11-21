"""
Target re-discovery tests for Prometheus.

This module implements reliability tests that verify scrape targets
are re-discovered after Prometheus restart.

Requirements: 19.5
"""

import logging
import subprocess
import time
from datetime import datetime
from typing import Optional

import httpx

from .config import TargetRediscoveryConfig, DeploymentMode, RestartMethod
from .models import (
    HealthCheckResult,
    RecoveryMetrics,
    RecoveryStatus,
    ReliabilityTestResult,
    ReliabilityTestType,
    TargetDiscoveryResult,
)

logger = logging.getLogger(__name__)


class TargetRediscoveryTest:
    """
    Reliability test that verifies target re-discovery after restart.

    Requirements: 19.5

    This test records the scrape targets before restart, restarts
    Prometheus, and verifies all targets are re-discovered.
    """

    def __init__(self, config: Optional[TargetRediscoveryConfig] = None):
        """
        Initialize the target re-discovery test.

        Args:
            config: Test configuration
        """
        self.config = config or TargetRediscoveryConfig()
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

    def _get_scrape_targets(self) -> list[dict]:
        """
        Get all scrape targets from Prometheus.

        Returns:
            List of target dictionaries
        """
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/targets"
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("activeTargets", [])
            return []
        except Exception as e:
            logger.debug(f"Failed to get targets: {e}")
            return []

    def _get_target_count(self) -> tuple[int, int]:
        """
        Get count of scrape targets.

        Returns:
            Tuple of (targets_up, total_targets)
        """
        targets = self._get_scrape_targets()
        total = len(targets)
        up = sum(1 for t in targets if t.get("health") == "up")
        return up, total

    def _get_target_jobs(self) -> set[str]:
        """
        Get set of job names from targets.

        Returns:
            Set of job names
        """
        targets = self._get_scrape_targets()
        return {t.get("labels", {}).get("job", "") for t in targets if t.get("labels")}

    def _get_prometheus_pods(self) -> list[str]:
        """Get list of Prometheus pod names."""
        cmd = self._get_kubectl_cmd() + [
            "get", "pods",
            "-n", self.config.namespace,
            "-l", "app.kubernetes.io/name=prometheus",
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
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []

    def _restart_prometheus(self) -> tuple[bool, str]:
        """
        Restart Prometheus.

        Returns:
            Tuple of (success, target_name)
        """
        if self.config.deployment_mode == DeploymentMode.DISTRIBUTED:
            pods = self._get_prometheus_pods()
            if pods:
                cmd = self._get_kubectl_cmd() + [
                    "delete", "pod", pods[0],
                    "-n", self.config.namespace,
                    "--grace-period=30",
                ]
                try:
                    subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
                    return True, pods[0]
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    pass

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

            targets_up, total_targets = self._get_target_count()
            metrics.scrape_targets_up = targets_up
            metrics.total_scrape_targets = total_targets

            if metrics.fully_recovered:
                metrics.recovery_time_seconds = time.time() - start_time
                return metrics

            time.sleep(self.config.health_check_interval_seconds)

        metrics.recovery_time_seconds = time.time() - start_time
        return metrics

    def _wait_for_target_discovery(
        self,
        expected_targets: int,
        expected_jobs: set[str],
    ) -> TargetDiscoveryResult:
        """
        Wait for targets to be re-discovered.

        Requirements: 19.5

        Args:
            expected_targets: Expected number of targets
            expected_jobs: Expected set of job names

        Returns:
            TargetDiscoveryResult with discovery status
        """
        start_time = time.time()
        result = TargetDiscoveryResult(
            targets_before_restart=expected_targets,
        )

        while time.time() - start_time < self.config.discovery_timeout_seconds:
            current_up, current_total = self._get_target_count()
            current_jobs = self._get_target_jobs()

            result.targets_after_restart = current_total
            result.discovery_time_seconds = time.time() - start_time

            # Check if all targets are re-discovered
            if current_total >= expected_targets:
                # Also verify job names match
                if expected_jobs.issubset(current_jobs):
                    result.all_targets_rediscovered = True
                    logger.info(
                        f"All {current_total} targets re-discovered in "
                        f"{result.discovery_time_seconds:.2f}s"
                    )
                    return result

            time.sleep(self.config.health_check_interval_seconds)

        result.discovery_time_seconds = time.time() - start_time
        logger.warning(
            f"Target discovery timeout: {result.targets_after_restart}/{expected_targets} "
            f"targets after {result.discovery_time_seconds:.2f}s"
        )
        return result

    def run(self) -> ReliabilityTestResult:
        """
        Run the target re-discovery test.

        Requirements: 19.5

        Returns:
            ReliabilityTestResult with test outcome
        """
        result = ReliabilityTestResult(
            test_name="target_rediscovery_test",
            test_type=ReliabilityTestType.TARGET_REDISCOVERY,
            deployment_mode=DeploymentMode(self.config.deployment_mode.value),
            start_time=datetime.utcnow(),
        )

        # Perform pre-test health check
        result.pre_test_health = self._perform_health_check()

        if not result.pre_test_health.is_healthy:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before test")
            result.end_time = datetime.utcnow()
            return result

        # Record targets before restart
        targets_before_up, targets_before_total = self._get_target_count()
        jobs_before = self._get_target_jobs()

        result.metadata["targets_before_up"] = targets_before_up
        result.metadata["targets_before_total"] = targets_before_total
        result.metadata["jobs_before"] = list(jobs_before)

        if targets_before_total == 0:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("No scrape targets found before restart")
            result.end_time = datetime.utcnow()
            return result

        # Use expected_targets from config if set, otherwise use current count
        expected_targets = (
            self.config.expected_targets
            if self.config.expected_targets > 0
            else targets_before_total
        )

        # Restart Prometheus
        logger.info("Restarting Prometheus...")
        restart_success, target = self._restart_prometheus()

        if not restart_success:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(f"Failed to restart Prometheus: {target}")
            result.end_time = datetime.utcnow()
            return result

        result.metadata["restart_target"] = target

        # Wait for recovery
        result.recovery_metrics = self._wait_for_recovery()

        if not result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus did not recover after restart")
            result.end_time = datetime.utcnow()
            return result

        # Wait for target re-discovery
        result.target_discovery = self._wait_for_target_discovery(
            expected_targets=expected_targets,
            expected_jobs=jobs_before,
        )

        # Perform post-test health check
        result.post_test_health = self._perform_health_check()

        # Record final targets
        targets_after_up, targets_after_total = self._get_target_count()
        jobs_after = self._get_target_jobs()

        result.metadata["targets_after_up"] = targets_after_up
        result.metadata["targets_after_total"] = targets_after_total
        result.metadata["jobs_after"] = list(jobs_after)

        # Determine recovery status
        if result.target_discovery.all_targets_rediscovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        elif result.target_discovery.targets_after_restart > 0:
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


def run_target_rediscovery_test(
    prometheus_url: str = "http://localhost:9090",
    namespace: str = "monitoring",
    expected_targets: int = 0,
    discovery_timeout: int = 120,
    recovery_timeout: int = 300,
    kubectl_context: Optional[str] = None,
) -> ReliabilityTestResult:
    """
    Convenience function to run target re-discovery test.

    Requirements: 19.5

    Args:
        prometheus_url: URL of Prometheus instance
        namespace: Kubernetes namespace
        expected_targets: Expected number of targets (0 = use current count)
        discovery_timeout: Timeout for target discovery in seconds
        recovery_timeout: Timeout for recovery in seconds
        kubectl_context: Kubernetes context to use

    Returns:
        ReliabilityTestResult with test outcome
    """
    config = TargetRediscoveryConfig(
        prometheus_url=prometheus_url,
        namespace=namespace,
        expected_targets=expected_targets,
        discovery_timeout_seconds=discovery_timeout,
        recovery_timeout_seconds=recovery_timeout,
        kubectl_context=kubectl_context,
    )

    test = TargetRediscoveryTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
