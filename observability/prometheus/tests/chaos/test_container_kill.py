"""
Container kill chaos tests for monolithic Prometheus deployments.

This module implements chaos tests that kill Prometheus containers or processes
and verify recovery using Prometheus API healthcheck endpoints.

Requirements: 20.1, 20.8, 20.9, 20.10
"""

import logging
import os
import signal
import subprocess
import time
import uuid
from datetime import datetime
from typing import Optional

import httpx

from .config import ContainerKillConfig
from .models import (
    ChaosEvent,
    ChaosTestResult,
    ChaosType,
    DeploymentMode,
    RecoveryMetrics,
    RecoveryStatus,
)

logger = logging.getLogger(__name__)


class ContainerKillChaosTest:
    """
    Chaos test that kills Prometheus containers/processes and verifies recovery.

    Requirements: 20.1, 20.8, 20.9

    This test is designed for monolithic Prometheus deployments where
    a single container or process is running. It kills the container/process
    and verifies that Prometheus recovers using API healthcheck endpoints.
    """

    def __init__(self, config: Optional[ContainerKillConfig] = None):
        """
        Initialize the container kill chaos test.

        Args:
            config: Test configuration
        """
        self.config = config or ContainerKillConfig()
        self._http_client: Optional[httpx.Client] = None

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=30.0)
        return self._http_client

    def _get_container_id(self) -> Optional[str]:
        """
        Get the Docker container ID for Prometheus.

        Returns:
            Container ID or None if not found
        """
        cmd = [
            "docker", "ps", "-q",
            "--filter", f"name={self.config.container_name}",
        ]

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
                return container_id.split('\n')[0]  # Get first match
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get container ID: {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Timeout getting container ID")
            return None

    def _get_process_pid(self) -> Optional[int]:
        """
        Get the process ID for Prometheus binary.

        Returns:
            Process ID or None if not found
        """
        try:
            # Try pgrep first
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

        try:
            # Fallback to ps
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in result.stdout.split('\n'):
                if 'prometheus' in line.lower() and 'grep' not in line.lower():
                    parts = line.split()
                    if len(parts) > 1:
                        return int(parts[1])
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass

        return None

    def _kill_container(self, container_id: str) -> bool:
        """
        Kill a Docker container.

        Args:
            container_id: ID of the container to kill

        Returns:
            True if container was killed successfully
        """
        signal_map = {
            "SIGKILL": "KILL",
            "SIGTERM": "TERM",
            "SIGINT": "INT",
        }
        docker_signal = signal_map.get(self.config.signal, "KILL")

        cmd = ["docker", "kill", f"--signal={docker_signal}", container_id]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            logger.info(f"Killed container {container_id}: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to kill container {container_id}: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout killing container {container_id}")
            return False

    def _kill_process(self, pid: int) -> bool:
        """
        Kill a process by PID.

        Args:
            pid: Process ID to kill

        Returns:
            True if process was killed successfully
        """
        signal_map = {
            "SIGKILL": signal.SIGKILL,
            "SIGTERM": signal.SIGTERM,
            "SIGINT": signal.SIGINT,
        }
        sig = signal_map.get(self.config.signal, signal.SIGKILL)

        try:
            os.kill(pid, sig)
            logger.info(f"Sent {self.config.signal} to process {pid}")
            return True
        except ProcessLookupError:
            logger.warning(f"Process {pid} not found")
            return False
        except PermissionError:
            logger.error(f"Permission denied to kill process {pid}")
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
        Run the container kill chaos test.

        Requirements: 20.1, 20.8, 20.9

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]
        target = ""
        kill_method = ""

        # Determine target (container or process)
        if self.config.use_docker:
            container_id = self._get_container_id()
            if container_id:
                target = container_id
                kill_method = "docker"
            else:
                # Fallback to process kill
                pid = self._get_process_pid()
                if pid:
                    target = str(pid)
                    kill_method = "process"
        else:
            pid = self._get_process_pid()
            if pid:
                target = str(pid)
                kill_method = "process"

        # Create chaos event
        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.CONTAINER_KILL if kill_method == "docker" else ChaosType.PROCESS_KILL,
            target=target,
            deployment_mode=DeploymentMode.MONOLITHIC,
            parameters={
                "kill_method": kill_method,
                "signal": self.config.signal,
                "container_name": self.config.container_name,
            },
        )

        result = ChaosTestResult(
            test_name="container_kill_chaos_test",
            chaos_event=chaos_event,
        )

        if not target:
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(
                "No Prometheus container or process found"
            )
            return result

        # Collect pre-chaos metrics
        result.pre_chaos_metrics = self._collect_pre_chaos_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append(
                "Prometheus not healthy before chaos injection"
            )
            return result

        # Kill the container/process
        logger.info(f"Killing {kill_method}: {target}")

        if kill_method == "docker":
            success = self._kill_container(target)
        else:
            success = self._kill_process(int(target))

        if not success:
            result.error_messages.append(f"Failed to kill {kill_method}: {target}")

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
            "kill_method": kill_method,
            "target": target,
            "signal": self.config.signal,
            "recovery_timeout": self.config.recovery_timeout_seconds,
        }

        return result

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None


def run_container_kill_test(
    prometheus_url: str = "http://localhost:9090",
    container_name: str = "prometheus",
    signal: str = "SIGKILL",
    use_docker: bool = True,
    recovery_timeout: int = 300,
) -> ChaosTestResult:
    """
    Convenience function to run container kill chaos test.

    Requirements: 20.1, 20.8, 20.9, 20.10

    Args:
        prometheus_url: URL of Prometheus instance
        container_name: Name of the container
        signal: Signal to send (SIGKILL, SIGTERM, etc.)
        use_docker: Whether to use Docker commands
        recovery_timeout: Timeout for recovery in seconds

    Returns:
        ChaosTestResult with test outcome
    """
    config = ContainerKillConfig(
        prometheus_url=prometheus_url,
        container_name=container_name,
        signal=signal,
        use_docker=use_docker,
        recovery_timeout_seconds=recovery_timeout,
    )

    test = ContainerKillChaosTest(config)
    try:
        return test.run()
    finally:
        test.cleanup()
