"""
Pod kill chaos tests for distributed Prometheus deployments.

This module implements chaos tests that randomly kill Prometheus pods
and verify recovery using Prometheus API healthcheck endpoints.

Requirements: 20.1, 20.8, 20.9, 20.10
"""

import logging
import random
import subprocess
import time
import uuid
from datetime import datetime
from typing import Optional

import httpx

from .config import PodKillConfig
from .models import (
    ChaosEvent,
    ChaosTestResult,
    ChaosType,
    DeploymentMode,
    RecoveryMetrics,
    RecoveryStatus,
)

logger = logging.getLogger(__name__)


class PodKillChaosTest:
    """
    Chaos test that kills Prometheus pods and verifies recovery.

    Requirements: 20.1, 20.8, 20.9

    This test is designed for distributed Prometheus deployments where
    multiple replicas are running. It randomly kills one or more pods
    and verifies that Prometheus recovers using API healthcheck endpoints.
    """

    def __init__(self, config: Optional[PodKillConfig] = None):
        """
        Initialize the pod kill chaos test.

        Args:
            config: Test configuration
        """
        self.config = config or PodKillConfig()
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

    def _kill_pod(self, pod_name: str) -> bool:
        """
        Kill a specific Prometheus pod.

        Args:
            pod_name: Name of the pod to kill

        Returns:
            True if pod was killed successfully
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
            logger.info(f"Killed pod {pod_name}: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to kill pod {pod_name}: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout killing pod {pod_name}")
            return False

    def _check_healthy(self) -> bool:
        """
        Check if Prometheus is healthy using /-/healthy endpoint.

        Requirements: 20.9

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

        Requirements: 20.9

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

    def _get_scrape_targets_status(self) -> tuple[int, int]:
        """
        Get scrape targets status.

        Returns:
            Tuple of (targets_up, total_targets)
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
                return up, total
            return 0, 0
        except Exception as e:
            logger.debug(f"Targets check failed: {e}")
            return 0, 0

    def _collect_pre_chaos_metrics(self) -> dict:
        """
        Collect metrics before chaos injection.

        Returns:
            Dictionary of pre-chaos metrics
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": self._check_healthy(),
            "ready": self._check_ready(),
            "api_accessible": self._check_api_accessible(),
        }

        targets_up, total_targets = self._get_scrape_targets_status()
        metrics["scrape_targets_up"] = targets_up
        metrics["total_scrape_targets"] = total_targets

        return metrics

    def _wait_for_recovery(self) -> RecoveryMetrics:
        """
        Wait for Prometheus to recover after chaos.

        Requirements: 20.9

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

            targets_up, total_targets = self._get_scrape_targets_status()
            metrics.scrape_targets_up = targets_up
            metrics.total_scrape_targets = total_targets

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

    def run(self) -> ChaosTestResult:
        """
        Run the pod kill chaos test.

        Requirements: 20.1, 20.8, 20.9

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]

        # Get available pods
        pods = self._get_prometheus_pods()
        if not pods:
            return ChaosTestResult(
                test_name="pod_kill_chaos_test",
                chaos_event=ChaosEvent(
                    event_id=event_id,
                    chaos_type=ChaosType.POD_KILL,
                    target="",
                    deployment_mode=DeploymentMode.DISTRIBUTED,
                ),
                recovery_status=RecoveryStatus.FAILED,
                error_messages=["No Prometheus pods found"],
            )

        # Select pods to kill
        if self.config.random_selection:
            kill_count = min(self.config.kill_count, len(pods))
            target_pods = random.sample(pods, kill_count)
        else:
            target_pods = pods[:self.config.kill_count]

        target_pod = target_pods[0] if target_pods else ""

        # Create chaos event
        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.POD_KILL,
            target=target_pod,
            deployment_mode=DeploymentMode.DISTRIBUTED,
            parameters={
                "pods_killed": target_pods,
                "total_pods": len(pods),
                "grace_period": self.config.grace_period_seconds,
            },
        )

        result = ChaosTestResult(
            test_name="pod_kill_chaos_test",
            chaos_event=chaos_event,
        )

        # Collect pre-chaos metrics
        result.pre_chaos_metrics = self._collect_pre_chaos_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(
                "Prometheus not healthy before chaos injection"
            )
            return result

        # Kill the pods
        logger.info(f"Killing pods: {target_pods}")
        for pod in target_pods:
            if not self._kill_pod(pod):
                result.error_messages.append(f"Failed to kill pod: {pod}")

        chaos_event.end_time = datetime.utcnow()

        # Wait for recovery
        result.recovery_metrics = self._wait_for_recovery()

        # Collect post-chaos metrics
        result.post_chaos_metrics = self._collect_pre_chaos_metrics()

        # Determine recovery status
        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        elif result.recovery_metrics.healthy_endpoint_status:
            result.recovery_status = RecoveryStatus.PARTIAL_RECOVERY
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.metadata = {
            "pods_available": len(pods),
            "pods_killed": len(target_pods),
            "recovery_timeout": self.config.recovery_timeout_seconds,
        }

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None


def run_pod_kill_test(
    prometheus_url: str = "http://localhost:9090",
    namespace: str = "monitoring",
    pod_selector: str = "app.kubernetes.io/name=prometheus",
    kill_count: int = 1,
    recovery_timeout: int = 300,
    kubectl_context: Optional[str] = None,
) -> ChaosTestResult:
    """
    Convenience function to run pod kill chaos test.

    Requirements: 20.1, 20.8, 20.9, 20.10

    Args:
        prometheus_url: URL of Prometheus instance
        namespace: Kubernetes namespace
        pod_selector: Label selector for pods
        kill_count: Number of pods to kill
        recovery_timeout: Timeout for recovery in seconds
        kubectl_context: Kubernetes context to use

    Returns:
        ChaosTestResult with test outcome
    """
    config = PodKillConfig(
        prometheus_url=prometheus_url,
        namespace=namespace,
        pod_selector=pod_selector,
        kill_count=kill_count,
        recovery_timeout_seconds=recovery_timeout,
        kubectl_context=kubectl_context,
    )

    test = PodKillChaosTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
