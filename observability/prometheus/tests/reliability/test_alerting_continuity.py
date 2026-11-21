"""
Alerting continuity tests for Prometheus.

This module implements reliability tests that verify alerts continue
firing after Prometheus restart.

Requirements: 19.6
"""

import logging
import subprocess
import time
from datetime import datetime
from typing import Optional

import httpx

from .config import AlertingContinuityConfig, DeploymentMode
from .models import (
    AlertingContinuityResult,
    HealthCheckResult,
    RecoveryMetrics,
    RecoveryStatus,
    ReliabilityTestResult,
    ReliabilityTestType,
)

logger = logging.getLogger(__name__)


class AlertingContinuityTest:
    """
    Reliability test that verifies alerting continuity after restart.

    Requirements: 19.6

    This test verifies that alerts that were firing before restart
    continue to fire after Prometheus recovers.
    """

    def __init__(self, config: Optional[AlertingContinuityConfig] = None):
        """
        Initialize the alerting continuity test.

        Args:
            config: Test configuration
        """
        self.config = config or AlertingContinuityConfig()
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

    def _get_firing_alerts(self) -> list[dict]:
        """
        Get list of currently firing alerts from Prometheus.

        Returns:
            List of firing alert dictionaries
        """
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/alerts"
            )
            if response.status_code == 200:
                data = response.json()
                alerts = data.get("data", {}).get("alerts", [])
                return [a for a in alerts if a.get("state") == "firing"]
            return []
        except Exception as e:
            logger.debug(f"Failed to get alerts: {e}")
            return []

    def _get_alert_rules(self) -> list[dict]:
        """
        Get list of alert rules from Prometheus.

        Returns:
            List of alert rule dictionaries
        """
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/rules"
            )
            if response.status_code == 200:
                data = response.json()
                groups = data.get("data", {}).get("groups", [])
                rules = []
                for group in groups:
                    for rule in group.get("rules", []):
                        if rule.get("type") == "alerting":
                            rules.append(rule)
                return rules
            return []
        except Exception as e:
            logger.debug(f"Failed to get rules: {e}")
            return []

    def _is_alert_firing(self, alert_name: str) -> bool:
        """
        Check if a specific alert is firing.

        Args:
            alert_name: Name of the alert to check

        Returns:
            True if the alert is firing
        """
        firing_alerts = self._get_firing_alerts()
        return any(
            a.get("labels", {}).get("alertname") == alert_name
            for a in firing_alerts
        )

    def _get_alertmanager_alerts(self) -> list[dict]:
        """
        Get alerts from Alertmanager.

        Returns:
            List of alert dictionaries from Alertmanager
        """
        try:
            response = self.http_client.get(
                f"{self.config.alertmanager_url}/api/v2/alerts"
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.debug(f"Failed to get Alertmanager alerts: {e}")
            return []

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

            if metrics.fully_recovered:
                metrics.recovery_time_seconds = time.time() - start_time
                return metrics

            time.sleep(self.config.health_check_interval_seconds)

        metrics.recovery_time_seconds = time.time() - start_time
        return metrics

    def _wait_for_alert_firing(
        self,
        alert_name: str,
        timeout: int = 120,
    ) -> tuple[bool, float]:
        """
        Wait for an alert to start firing.

        Args:
            alert_name: Name of the alert
            timeout: Timeout in seconds

        Returns:
            Tuple of (is_firing, time_to_fire)
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._is_alert_firing(alert_name):
                return True, time.time() - start_time
            time.sleep(self.config.health_check_interval_seconds)

        return False, time.time() - start_time

    def run(self) -> ReliabilityTestResult:
        """
        Run the alerting continuity test.

        Requirements: 19.6

        Returns:
            ReliabilityTestResult with test outcome
        """
        result = ReliabilityTestResult(
            test_name="alerting_continuity_test",
            test_type=ReliabilityTestType.ALERTING_CONTINUITY,
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

        # Get firing alerts before restart
        firing_alerts_before = self._get_firing_alerts()
        alert_names_before = {
            a.get("labels", {}).get("alertname")
            for a in firing_alerts_before
        }

        result.metadata["firing_alerts_before"] = list(alert_names_before)
        result.metadata["firing_count_before"] = len(firing_alerts_before)

        # Check if specific alert is firing (if configured)
        alert_to_track = self.config.alert_rule_name
        alert_firing_before = alert_to_track in alert_names_before

        # If no specific alert is configured, track any firing alert
        if not alert_firing_before and firing_alerts_before:
            alert_to_track = list(alert_names_before)[0]
            alert_firing_before = True

        result.metadata["tracked_alert"] = alert_to_track

        # Record restart time
        restart_time = datetime.utcnow()

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

        # Check alerting continuity
        recovery_time = datetime.utcnow()
        alert_gap_seconds = (recovery_time - restart_time).total_seconds()

        # Get firing alerts after restart
        firing_alerts_after = self._get_firing_alerts()
        alert_names_after = {
            a.get("labels", {}).get("alertname")
            for a in firing_alerts_after
        }

        result.metadata["firing_alerts_after"] = list(alert_names_after)
        result.metadata["firing_count_after"] = len(firing_alerts_after)

        # Check if tracked alert is still firing
        alert_firing_after = alert_to_track in alert_names_after

        # If alert wasn't firing before, wait for it to potentially fire
        if not alert_firing_before and self.config.verify_alert_firing:
            alert_firing_after, wait_time = self._wait_for_alert_firing(
                alert_to_track,
                timeout=60,
            )
            alert_gap_seconds += wait_time

        # Create alerting continuity result
        result.alerting_continuity = AlertingContinuityResult(
            alert_firing_before=alert_firing_before,
            alert_firing_after=alert_firing_after,
            alert_gap_seconds=alert_gap_seconds,
            continuity_maintained=(
                alert_firing_before == alert_firing_after
                or (not alert_firing_before and alert_firing_after)
            ),
        )

        # Perform post-test health check
        result.post_test_health = self._perform_health_check()

        # Determine recovery status
        if result.recovery_metrics.fully_recovered:
            if result.alerting_continuity.continuity_maintained:
                result.recovery_status = RecoveryStatus.RECOVERED
            else:
                result.recovery_status = RecoveryStatus.PARTIAL_RECOVERY
                result.error_messages.append(
                    f"Alert '{alert_to_track}' did not continue firing after restart"
                )
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.end_time = datetime.utcnow()

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None


def run_alerting_continuity_test(
    prometheus_url: str = "http://localhost:9090",
    alertmanager_url: str = "http://localhost:9093",
    namespace: str = "monitoring",
    alert_rule_name: str = "",
    recovery_timeout: int = 300,
    kubectl_context: Optional[str] = None,
) -> ReliabilityTestResult:
    """
    Convenience function to run alerting continuity test.

    Requirements: 19.6

    Args:
        prometheus_url: URL of Prometheus instance
        alertmanager_url: URL of Alertmanager instance
        namespace: Kubernetes namespace
        alert_rule_name: Name of alert rule to track (empty = any)
        recovery_timeout: Timeout for recovery in seconds
        kubectl_context: Kubernetes context to use

    Returns:
        ReliabilityTestResult with test outcome
    """
    config = AlertingContinuityConfig(
        prometheus_url=prometheus_url,
        alertmanager_url=alertmanager_url,
        namespace=namespace,
        alert_rule_name=alert_rule_name,
        recovery_timeout_seconds=recovery_timeout,
        kubectl_context=kubectl_context,
    )

    test = AlertingContinuityTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
