"""
Network partition tests for Prometheus.

This module implements reliability tests that verify Prometheus handles
network partitions gracefully.

Requirements: 19.4
"""

import logging
import subprocess
import time
from datetime import datetime
from typing import Optional

import httpx

from .config import NetworkPartitionConfig, DeploymentMode
from .models import (
    HealthCheckResult,
    RecoveryMetrics,
    RecoveryStatus,
    ReliabilityTestResult,
    ReliabilityTestType,
)

logger = logging.getLogger(__name__)


class NetworkPartitionTest:
    """
    Reliability test that simulates network partitions.

    Requirements: 19.4

    This test simulates network issues between Prometheus and its
    scrape targets, then verifies graceful handling and recovery.
    """

    def __init__(self, config: Optional[NetworkPartitionConfig] = None):
        """
        Initialize the network partition test.

        Args:
            config: Test configuration
        """
        self.config = config or NetworkPartitionConfig()
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

    def _apply_network_policy(self, policy_name: str, block: bool = True) -> bool:
        """
        Apply or remove a network policy to simulate partition.

        Args:
            policy_name: Name of the network policy
            block: Whether to block (True) or allow (False) traffic

        Returns:
            True if policy was applied successfully
        """
        if block:
            # Create a network policy that blocks egress
            policy_yaml = f"""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {policy_name}
  namespace: {self.config.namespace}
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: prometheus
  policyTypes:
  - Egress
  egress: []
"""
            cmd = self._get_kubectl_cmd() + ["apply", "-f", "-"]
            try:
                result = subprocess.run(
                    cmd,
                    input=policy_yaml,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
                logger.info(f"Applied network policy: {result.stdout}")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.error(f"Failed to apply network policy: {e}")
                return False
        else:
            # Delete the network policy
            cmd = self._get_kubectl_cmd() + [
                "delete", "networkpolicy", policy_name,
                "-n", self.config.namespace,
                "--ignore-not-found",
            ]
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
                logger.info(f"Removed network policy: {result.stdout}")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.error(f"Failed to remove network policy: {e}")
                return False

    def _simulate_network_partition_iptables(self, block: bool = True) -> bool:
        """
        Simulate network partition using iptables (for Docker/binary).

        Args:
            block: Whether to block (True) or unblock (False) traffic

        Returns:
            True if partition was simulated successfully
        """
        # This requires root privileges and is platform-specific
        # For Docker, we can use docker network disconnect/connect

        try:
            if block:
                # Try to disconnect from network
                result = subprocess.run(
                    ["docker", "network", "disconnect", "bridge", "prometheus"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                return result.returncode == 0
            else:
                # Reconnect to network
                result = subprocess.run(
                    ["docker", "network", "connect", "bridge", "prometheus"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _simulate_partition(self, block: bool = True) -> tuple[bool, str]:
        """
        Simulate network partition based on deployment mode.

        Args:
            block: Whether to create (True) or remove (False) partition

        Returns:
            Tuple of (success, method_used)
        """
        policy_name = "prometheus-network-partition-test"

        if self.config.deployment_mode == DeploymentMode.DISTRIBUTED:
            success = self._apply_network_policy(policy_name, block)
            return success, "network_policy"
        else:
            success = self._simulate_network_partition_iptables(block)
            return success, "docker_network"

    def _verify_graceful_handling(self) -> dict:
        """
        Verify Prometheus handles network partition gracefully.

        Requirements: 19.4

        Returns:
            Dictionary with verification results
        """
        results = {
            "prometheus_healthy": False,
            "prometheus_ready": False,
            "api_accessible": False,
            "scrape_failures_expected": False,
            "no_crash": True,
        }

        # Check that Prometheus itself is still healthy
        results["prometheus_healthy"] = self._check_healthy()
        results["prometheus_ready"] = self._check_ready()
        results["api_accessible"] = self._check_api_accessible()

        # During partition, scrape targets should show as down
        targets_up, total_targets = self._get_scrape_targets_status()

        # If we have targets and some are down, that's expected during partition
        if total_targets > 0:
            results["scrape_failures_expected"] = targets_up < total_targets

        # Prometheus should not crash during network issues
        results["no_crash"] = results["prometheus_healthy"]

        return results

    def _wait_for_recovery(self) -> RecoveryMetrics:
        """Wait for Prometheus to recover after partition is removed."""
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
                return metrics

            time.sleep(self.config.health_check_interval_seconds)

        metrics.recovery_time_seconds = time.time() - start_time
        return metrics

    def run(self) -> ReliabilityTestResult:
        """
        Run the network partition test.

        Requirements: 19.4

        Returns:
            ReliabilityTestResult with test outcome
        """
        result = ReliabilityTestResult(
            test_name="network_partition_test",
            test_type=ReliabilityTestType.NETWORK_PARTITION,
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

        # Record initial targets status
        initial_up, initial_total = self._get_scrape_targets_status()
        result.metadata["initial_targets_up"] = initial_up
        result.metadata["initial_targets_total"] = initial_total

        # Simulate network partition
        logger.info("Simulating network partition...")
        partition_success, method = self._simulate_partition(block=True)

        if not partition_success:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(f"Failed to simulate partition using {method}")
            result.end_time = datetime.utcnow()
            return result

        result.metadata["partition_method"] = method

        try:
            # Wait for partition duration
            logger.info(f"Waiting {self.config.partition_duration_seconds}s during partition...")
            time.sleep(self.config.partition_duration_seconds)

            # Verify graceful handling during partition
            if self.config.verify_graceful_handling:
                handling_results = self._verify_graceful_handling()
                result.metadata["graceful_handling"] = handling_results

                if not handling_results.get("no_crash"):
                    result.error_messages.append("Prometheus crashed during partition")

        finally:
            # Remove network partition
            logger.info("Removing network partition...")
            self._simulate_partition(block=False)

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
        result.metadata["partition_duration"] = self.config.partition_duration_seconds

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        # Ensure network policy is removed
        self._simulate_partition(block=False)

        if self._http_client:
            self._http_client.close()
            self._http_client = None


def run_network_partition_test(
    prometheus_url: str = "http://localhost:9090",
    namespace: str = "monitoring",
    partition_duration: int = 60,
    recovery_timeout: int = 300,
    kubectl_context: Optional[str] = None,
) -> ReliabilityTestResult:
    """
    Convenience function to run network partition test.

    Requirements: 19.4

    Args:
        prometheus_url: URL of Prometheus instance
        namespace: Kubernetes namespace
        partition_duration: Duration of partition in seconds
        recovery_timeout: Timeout for recovery in seconds
        kubectl_context: Kubernetes context to use

    Returns:
        ReliabilityTestResult with test outcome
    """
    config = NetworkPartitionConfig(
        prometheus_url=prometheus_url,
        namespace=namespace,
        partition_duration_seconds=partition_duration,
        recovery_timeout_seconds=recovery_timeout,
        kubectl_context=kubectl_context,
    )

    test = NetworkPartitionTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
