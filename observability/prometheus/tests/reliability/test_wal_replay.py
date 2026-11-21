"""
WAL replay tests for Prometheus.

This module implements reliability tests that verify Prometheus WAL
(Write-Ahead Log) replay completes successfully after a crash.

Requirements: 19.2
"""

import logging
import os
import signal
import subprocess
import time
from datetime import datetime
from typing import Optional

import httpx

from .config import WALReplayConfig, DeploymentMode
from .models import (
    HealthCheckResult,
    RecoveryMetrics,
    RecoveryStatus,
    ReliabilityTestResult,
    ReliabilityTestType,
    WALReplayResult,
)

logger = logging.getLogger(__name__)


class WALReplayTest:
    """
    Reliability test that simulates crash and verifies WAL replay.

    Requirements: 19.2

    This test simulates a Prometheus crash (using SIGKILL) and verifies
    that WAL replay completes successfully on restart.
    """

    def __init__(self, config: Optional[WALReplayConfig] = None):
        """
        Initialize the WAL replay test.

        Args:
            config: Test configuration
        """
        self.config = config or WALReplayConfig()
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
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    def _check_ready(self) -> bool:
        """Check if Prometheus is ready."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/-/ready"
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ready check failed: {e}")
            return False

    def _check_api_accessible(self) -> bool:
        """Check if Prometheus API is accessible."""
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/status/runtimeinfo"
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"API check failed: {e}")
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
        except Exception as e:
            logger.debug(f"Query check failed: {e}")
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

    def _get_container_id(self, container_name: str = "prometheus") -> Optional[str]:
        """Get Docker container ID for Prometheus."""
        cmd = ["docker", "ps", "-q", "--filter", f"name={container_name}"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            container_id = result.stdout.strip()
            if container_id:
                return container_id.split('\n')[0]
            return None
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

    def _get_process_pid(self) -> Optional[int]:
        """Get process ID for Prometheus binary."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "prometheus"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                return int(pids[0])
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
        return None

    def _simulate_crash_pod(self, pod_name: str) -> bool:
        """
        Simulate crash by killing pod with SIGKILL (grace-period=0).

        Args:
            pod_name: Name of the pod to crash

        Returns:
            True if crash was simulated successfully
        """
        cmd = self._get_kubectl_cmd() + [
            "delete", "pod", pod_name,
            "-n", self.config.namespace,
            "--grace-period=0",
            "--force",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            logger.info(f"Crashed pod {pod_name}: {result.stdout}")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"Failed to crash pod: {e}")
            return False

    def _simulate_crash_container(self, container_id: str) -> bool:
        """
        Simulate crash by sending SIGKILL to container.

        Args:
            container_id: ID of the container to crash

        Returns:
            True if crash was simulated successfully
        """
        cmd = ["docker", "kill", "--signal=KILL", container_id]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            logger.info(f"Crashed container {container_id}: {result.stdout}")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"Failed to crash container: {e}")
            return False

    def _simulate_crash_process(self, pid: int) -> bool:
        """
        Simulate crash by sending SIGKILL to process.

        Args:
            pid: Process ID to crash

        Returns:
            True if crash was simulated successfully
        """
        try:
            os.kill(pid, signal.SIGKILL)
            logger.info(f"Crashed process {pid}")
            return True
        except (ProcessLookupError, PermissionError) as e:
            logger.error(f"Failed to crash process: {e}")
            return False

    def _simulate_crash(self) -> tuple[bool, str]:
        """
        Simulate a crash based on deployment mode.

        Returns:
            Tuple of (success, target_description)
        """
        if self.config.deployment_mode == DeploymentMode.DISTRIBUTED:
            pods = self._get_prometheus_pods()
            if pods:
                success = self._simulate_crash_pod(pods[0])
                return success, f"pod:{pods[0]}"

        # Try container
        container_id = self._get_container_id()
        if container_id:
            success = self._simulate_crash_container(container_id)
            return success, f"container:{container_id}"

        # Try process
        pid = self._get_process_pid()
        if pid:
            success = self._simulate_crash_process(pid)
            return success, f"process:{pid}"

        return False, ""

    def _get_wal_replay_status(self) -> dict:
        """
        Get WAL replay status from Prometheus metrics.

        Returns:
            Dictionary with WAL replay metrics
        """
        try:
            response = self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": "prometheus_tsdb_wal_completed_pages_total"},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    result = data.get("data", {}).get("result", [])
                    if result:
                        return {
                            "wal_pages": float(result[0].get("value", [0, 0])[1]),
                            "available": True,
                        }
            return {"wal_pages": 0, "available": False}
        except Exception as e:
            logger.debug(f"Failed to get WAL status: {e}")
            return {"wal_pages": 0, "available": False}

    def _wait_for_wal_replay(self) -> WALReplayResult:
        """
        Wait for WAL replay to complete.

        Requirements: 19.2

        Returns:
            WALReplayResult with replay status
        """
        start_time = time.time()
        result = WALReplayResult()

        # Wait for Prometheus to start responding
        while time.time() - start_time < self.config.max_replay_time_seconds:
            if self._check_healthy():
                result.replay_started = True
                break
            time.sleep(self.config.health_check_interval_seconds)

        if not result.replay_started:
            result.error_message = "Prometheus did not start within timeout"
            return result

        # Wait for ready state (indicates WAL replay complete)
        while time.time() - start_time < self.config.max_replay_time_seconds:
            if self._check_ready():
                result.replay_completed = True
                result.replay_time_seconds = time.time() - start_time

                # Get WAL metrics
                wal_status = self._get_wal_replay_status()
                if wal_status.get("available"):
                    result.samples_replayed = int(wal_status.get("wal_pages", 0))

                logger.info(
                    f"WAL replay completed in {result.replay_time_seconds:.2f}s"
                )
                return result

            time.sleep(self.config.health_check_interval_seconds)

        result.replay_time_seconds = time.time() - start_time
        result.error_message = "WAL replay did not complete within timeout"
        return result

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
        Run the WAL replay test.

        Requirements: 19.2

        Returns:
            ReliabilityTestResult with test outcome
        """
        result = ReliabilityTestResult(
            test_name="wal_replay_test",
            test_type=ReliabilityTestType.WAL_REPLAY,
            deployment_mode=DeploymentMode(self.config.deployment_mode.value),
            start_time=datetime.utcnow(),
        )

        # Perform pre-test health check
        result.pre_test_health = self._perform_health_check()

        if not result.pre_test_health.is_healthy:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before crash")
            result.end_time = datetime.utcnow()
            return result

        # Simulate crash
        logger.info("Simulating Prometheus crash...")
        crash_success, target = self._simulate_crash()

        if not crash_success:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(f"Failed to simulate crash: {target}")
            result.end_time = datetime.utcnow()
            return result

        result.metadata["crash_target"] = target

        # Wait for WAL replay
        result.wal_replay = self._wait_for_wal_replay()

        if not result.wal_replay.replay_completed:
            result.recovery_status = RecoveryStatus.FAILED
            if result.wal_replay.error_message:
                result.error_messages.append(result.wal_replay.error_message)
            result.end_time = datetime.utcnow()
            return result

        # Wait for full recovery
        result.recovery_metrics = self._wait_for_recovery()
        result.recovery_metrics.wal_replay_completed = result.wal_replay.replay_completed

        # Perform post-test health check
        result.post_test_health = self._perform_health_check()

        # Determine recovery status
        if result.recovery_metrics.fully_recovered and result.wal_replay.replay_completed:
            result.recovery_status = RecoveryStatus.RECOVERED
        elif result.recovery_metrics.healthy_endpoint_status:
            result.recovery_status = RecoveryStatus.PARTIAL_RECOVERY
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.end_time = datetime.utcnow()
        result.metadata["wal_replay_time"] = result.wal_replay.replay_time_seconds

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None


def run_wal_replay_test(
    prometheus_url: str = "http://localhost:9090",
    namespace: str = "monitoring",
    max_replay_time: int = 300,
    recovery_timeout: int = 300,
    kubectl_context: Optional[str] = None,
) -> ReliabilityTestResult:
    """
    Convenience function to run WAL replay test.

    Requirements: 19.2

    Args:
        prometheus_url: URL of Prometheus instance
        namespace: Kubernetes namespace
        max_replay_time: Maximum time for WAL replay in seconds
        recovery_timeout: Timeout for recovery in seconds
        kubectl_context: Kubernetes context to use

    Returns:
        ReliabilityTestResult with test outcome
    """
    config = WALReplayConfig(
        prometheus_url=prometheus_url,
        namespace=namespace,
        max_replay_time_seconds=max_replay_time,
        recovery_timeout_seconds=recovery_timeout,
        kubectl_context=kubectl_context,
    )

    test = WALReplayTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
