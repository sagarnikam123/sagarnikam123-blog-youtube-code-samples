"""
Chaos Mesh integration for Prometheus chaos testing.

This module provides integration with Chaos Mesh for advanced chaos
engineering scenarios in Kubernetes environments.

Requirements: 20.7, 20.9, 20.10
"""

import json
import logging
import subprocess
import time
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx

from .config import ChaosMeshConfig
from .models import (
    ChaosEvent,
    ChaosTestResult,
    ChaosType,
    DeploymentMode,
    RecoveryMetrics,
    RecoveryStatus,
)

logger = logging.getLogger(__name__)


class ChaosMeshClient:
    """
    Client for interacting with Chaos Mesh.

    Requirements: 20.7

    This client provides methods to create and manage chaos experiments
    using Chaos Mesh CRDs.
    """

    def __init__(
        self,
        config: Optional[ChaosMeshConfig] = None,
        kubectl_context: Optional[str] = None,
    ):
        """
        Initialize the Chaos Mesh client.

        Args:
            config: Chaos Mesh configuration
            kubectl_context: Kubernetes context to use
        """
        self.config = config or ChaosMeshConfig()
        self.kubectl_context = kubectl_context

    def _get_kubectl_cmd(self) -> list[str]:
        """Get base kubectl command with context if specified."""
        cmd = ["kubectl"]
        if self.kubectl_context:
            cmd.extend(["--context", self.kubectl_context])
        return cmd

    def is_installed(self) -> bool:
        """
        Check if Chaos Mesh is installed in the cluster.

        Returns:
            True if Chaos Mesh is installed
        """
        cmd = self._get_kubectl_cmd() + [
            "get", "crd", "podchaos.chaos-mesh.org",
            "-o", "name",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return False

    def create_pod_chaos(
        self,
        name: str,
        namespace: str,
        target_namespace: str,
        label_selector: dict[str, str],
        action: str = "pod-kill",
        duration: str = "30s",
    ) -> bool:
        """
        Create a PodChaos experiment.

        Args:
            name: Name of the chaos experiment
            namespace: Namespace for the experiment
            target_namespace: Namespace of target pods
            label_selector: Label selector for target pods
            action: Chaos action (pod-kill, pod-failure, container-kill)
            duration: Duration of the chaos

        Returns:
            True if experiment was created successfully
        """
        experiment = {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "kind": "PodChaos",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "action": action,
                "mode": "one",
                "selector": {
                    "namespaces": [target_namespace],
                    "labelSelectors": label_selector,
                },
                "duration": duration,
            },
        }

        return self._apply_manifest(experiment)

    def create_network_chaos(
        self,
        name: str,
        namespace: str,
        target_namespace: str,
        label_selector: dict[str, str],
        action: str = "delay",
        latency: str = "100ms",
        jitter: str = "10ms",
        duration: str = "60s",
    ) -> bool:
        """
        Create a NetworkChaos experiment.

        Args:
            name: Name of the chaos experiment
            namespace: Namespace for the experiment
            target_namespace: Namespace of target pods
            label_selector: Label selector for target pods
            action: Chaos action (delay, loss, duplicate, corrupt)
            latency: Network latency to inject
            jitter: Latency jitter
            duration: Duration of the chaos

        Returns:
            True if experiment was created successfully
        """
        experiment = {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "kind": "NetworkChaos",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "action": action,
                "mode": "all",
                "selector": {
                    "namespaces": [target_namespace],
                    "labelSelectors": label_selector,
                },
                "delay": {
                    "latency": latency,
                    "jitter": jitter,
                },
                "duration": duration,
            },
        }

        return self._apply_manifest(experiment)

    def create_stress_chaos(
        self,
        name: str,
        namespace: str,
        target_namespace: str,
        label_selector: dict[str, str],
        cpu_workers: int = 1,
        memory_workers: int = 0,
        memory_size: str = "256MB",
        duration: str = "60s",
    ) -> bool:
        """
        Create a StressChaos experiment.

        Args:
            name: Name of the chaos experiment
            namespace: Namespace for the experiment
            target_namespace: Namespace of target pods
            label_selector: Label selector for target pods
            cpu_workers: Number of CPU stress workers
            memory_workers: Number of memory stress workers
            memory_size: Memory to consume per worker
            duration: Duration of the chaos

        Returns:
            True if experiment was created successfully
        """
        stressors = {}
        if cpu_workers > 0:
            stressors["cpu"] = {"workers": cpu_workers}
        if memory_workers > 0:
            stressors["memory"] = {"workers": memory_workers, "size": memory_size}

        experiment = {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "kind": "StressChaos",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "mode": "one",
                "selector": {
                    "namespaces": [target_namespace],
                    "labelSelectors": label_selector,
                },
                "stressors": stressors,
                "duration": duration,
            },
        }

        return self._apply_manifest(experiment)

    def create_io_chaos(
        self,
        name: str,
        namespace: str,
        target_namespace: str,
        label_selector: dict[str, str],
        action: str = "latency",
        latency: str = "100ms",
        path: str = "/",
        duration: str = "60s",
    ) -> bool:
        """
        Create an IOChaos experiment.

        Args:
            name: Name of the chaos experiment
            namespace: Namespace for the experiment
            target_namespace: Namespace of target pods
            label_selector: Label selector for target pods
            action: Chaos action (latency, fault, attrOverride)
            latency: I/O latency to inject
            path: Path to affect
            duration: Duration of the chaos

        Returns:
            True if experiment was created successfully
        """
        experiment = {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "kind": "IOChaos",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "action": action,
                "mode": "one",
                "selector": {
                    "namespaces": [target_namespace],
                    "labelSelectors": label_selector,
                },
                "volumePath": path,
                "delay": latency,
                "duration": duration,
            },
        }

        return self._apply_manifest(experiment)

    def delete_experiment(self, name: str, namespace: str, kind: str) -> bool:
        """
        Delete a chaos experiment.

        Args:
            name: Name of the experiment
            namespace: Namespace of the experiment
            kind: Kind of experiment (PodChaos, NetworkChaos, etc.)

        Returns:
            True if deletion was successful
        """
        cmd = self._get_kubectl_cmd() + [
            "delete", kind.lower(), name,
            "-n", namespace,
            "--ignore-not-found",
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            return True
        except Exception as e:
            logger.error(f"Failed to delete experiment: {e}")
            return False

    def get_experiment_status(
        self,
        name: str,
        namespace: str,
        kind: str,
    ) -> Optional[dict[str, Any]]:
        """
        Get the status of a chaos experiment.

        Args:
            name: Name of the experiment
            namespace: Namespace of the experiment
            kind: Kind of experiment

        Returns:
            Status dictionary or None if not found
        """
        cmd = self._get_kubectl_cmd() + [
            "get", kind.lower(), name,
            "-n", namespace,
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
            data = json.loads(result.stdout)
            return data.get("status", {})
        except Exception as e:
            logger.debug(f"Failed to get experiment status: {e}")
            return None

    def _apply_manifest(self, manifest: dict) -> bool:
        """Apply a Kubernetes manifest."""
        cmd = self._get_kubectl_cmd() + ["apply", "-f", "-"]

        try:
            result = subprocess.run(
                cmd,
                input=json.dumps(manifest),
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            logger.info(f"Applied manifest: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to apply manifest: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Failed to apply manifest: {e}")
            return False


class ChaosMeshChaosTest:
    """
    Chaos test using Chaos Mesh.

    Requirements: 20.7, 20.9

    This class provides a high-level interface for running chaos tests
    using Chaos Mesh experiments.
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        namespace: str = "monitoring",
        chaos_mesh_config: Optional[ChaosMeshConfig] = None,
        kubectl_context: Optional[str] = None,
        recovery_timeout_seconds: int = 300,
        health_check_interval_seconds: float = 5.0,
    ):
        """
        Initialize the Chaos Mesh test.

        Args:
            prometheus_url: URL of Prometheus instance
            namespace: Namespace where Prometheus is deployed
            chaos_mesh_config: Chaos Mesh configuration
            kubectl_context: Kubernetes context to use
            recovery_timeout_seconds: Timeout for recovery
            health_check_interval_seconds: Interval between health checks
        """
        self.prometheus_url = prometheus_url
        self.namespace = namespace
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.health_check_interval_seconds = health_check_interval_seconds

        self.client = ChaosMeshClient(
            config=chaos_mesh_config,
            kubectl_context=kubectl_context,
        )
        self._http_client: Optional[httpx.Client] = None
        self._active_experiments: list[tuple[str, str, str]] = []

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=30.0)
        return self._http_client

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

    def _collect_metrics(self) -> dict[str, Any]:
        """Collect current metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": self._check_healthy(),
            "ready": self._check_ready(),
            "api_accessible": self._check_api_accessible(),
        }

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

    def run_pod_chaos(
        self,
        label_selector: dict[str, str],
        action: str = "pod-kill",
        duration: str = "30s",
    ) -> ChaosTestResult:
        """
        Run a pod chaos experiment.

        Args:
            label_selector: Label selector for target pods
            action: Chaos action
            duration: Duration of chaos

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]
        experiment_name = f"prometheus-pod-chaos-{event_id}"

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.POD_KILL,
            target=str(label_selector),
            deployment_mode=DeploymentMode.DISTRIBUTED,
            parameters={
                "action": action,
                "duration": duration,
                "tool": "chaos_mesh",
            },
        )

        result = ChaosTestResult(
            test_name="chaos_mesh_pod_chaos",
            chaos_event=chaos_event,
        )

        # Check if Chaos Mesh is installed
        if not self.client.is_installed():
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Chaos Mesh is not installed")
            return result

        # Collect pre-chaos metrics
        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        # Create chaos experiment
        logger.info(f"Creating PodChaos experiment: {experiment_name}")

        success = self.client.create_pod_chaos(
            name=experiment_name,
            namespace=self.client.config.experiment_namespace,
            target_namespace=self.namespace,
            label_selector=label_selector,
            action=action,
            duration=duration,
        )

        if not success:
            result.error_messages.append("Failed to create PodChaos experiment")
        else:
            self._active_experiments.append(
                (experiment_name, self.client.config.experiment_namespace, "PodChaos")
            )

        # Wait for experiment to complete
        duration_seconds = self._parse_duration(duration)
        time.sleep(duration_seconds + 5)

        chaos_event.end_time = datetime.utcnow()

        # Wait for recovery
        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        # Clean up experiment
        self._cleanup_experiments()

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.metadata = {
            "experiment_name": experiment_name,
            "action": action,
            "duration": duration,
            "tool": "chaos_mesh",
        }

        return result

    def run_network_chaos(
        self,
        label_selector: dict[str, str],
        latency: str = "100ms",
        jitter: str = "10ms",
        duration: str = "60s",
    ) -> ChaosTestResult:
        """
        Run a network chaos experiment.

        Args:
            label_selector: Label selector for target pods
            latency: Network latency to inject
            jitter: Latency jitter
            duration: Duration of chaos

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]
        experiment_name = f"prometheus-network-chaos-{event_id}"

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.NETWORK_LATENCY,
            target=str(label_selector),
            deployment_mode=DeploymentMode.DISTRIBUTED,
            parameters={
                "latency": latency,
                "jitter": jitter,
                "duration": duration,
                "tool": "chaos_mesh",
            },
        )

        result = ChaosTestResult(
            test_name="chaos_mesh_network_chaos",
            chaos_event=chaos_event,
        )

        if not self.client.is_installed():
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Chaos Mesh is not installed")
            return result

        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        logger.info(f"Creating NetworkChaos experiment: {experiment_name}")

        success = self.client.create_network_chaos(
            name=experiment_name,
            namespace=self.client.config.experiment_namespace,
            target_namespace=self.namespace,
            label_selector=label_selector,
            latency=latency,
            jitter=jitter,
            duration=duration,
        )

        if not success:
            result.error_messages.append("Failed to create NetworkChaos experiment")
        else:
            self._active_experiments.append(
                (experiment_name, self.client.config.experiment_namespace, "NetworkChaos")
            )

        duration_seconds = self._parse_duration(duration)
        time.sleep(duration_seconds + 5)

        chaos_event.end_time = datetime.utcnow()

        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        self._cleanup_experiments()

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.metadata = {
            "experiment_name": experiment_name,
            "latency": latency,
            "jitter": jitter,
            "duration": duration,
            "tool": "chaos_mesh",
        }

        return result

    def run_stress_chaos(
        self,
        label_selector: dict[str, str],
        cpu_workers: int = 1,
        memory_workers: int = 0,
        memory_size: str = "256MB",
        duration: str = "60s",
    ) -> ChaosTestResult:
        """
        Run a stress chaos experiment.

        Args:
            label_selector: Label selector for target pods
            cpu_workers: Number of CPU stress workers
            memory_workers: Number of memory stress workers
            memory_size: Memory to consume per worker
            duration: Duration of chaos

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]
        experiment_name = f"prometheus-stress-chaos-{event_id}"

        chaos_type = (
            ChaosType.CPU_THROTTLE if cpu_workers > 0
            else ChaosType.MEMORY_PRESSURE
        )

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=chaos_type,
            target=str(label_selector),
            deployment_mode=DeploymentMode.DISTRIBUTED,
            parameters={
                "cpu_workers": cpu_workers,
                "memory_workers": memory_workers,
                "memory_size": memory_size,
                "duration": duration,
                "tool": "chaos_mesh",
            },
        )

        result = ChaosTestResult(
            test_name="chaos_mesh_stress_chaos",
            chaos_event=chaos_event,
        )

        if not self.client.is_installed():
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Chaos Mesh is not installed")
            return result

        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        logger.info(f"Creating StressChaos experiment: {experiment_name}")

        success = self.client.create_stress_chaos(
            name=experiment_name,
            namespace=self.client.config.experiment_namespace,
            target_namespace=self.namespace,
            label_selector=label_selector,
            cpu_workers=cpu_workers,
            memory_workers=memory_workers,
            memory_size=memory_size,
            duration=duration,
        )

        if not success:
            result.error_messages.append("Failed to create StressChaos experiment")
        else:
            self._active_experiments.append(
                (experiment_name, self.client.config.experiment_namespace, "StressChaos")
            )

        duration_seconds = self._parse_duration(duration)
        time.sleep(duration_seconds + 5)

        chaos_event.end_time = datetime.utcnow()

        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        self._cleanup_experiments()

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.metadata = {
            "experiment_name": experiment_name,
            "cpu_workers": cpu_workers,
            "memory_workers": memory_workers,
            "memory_size": memory_size,
            "duration": duration,
            "tool": "chaos_mesh",
        }

        return result

    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to seconds."""
        duration = duration.lower()
        if duration.endswith("s"):
            return int(duration[:-1])
        elif duration.endswith("m"):
            return int(duration[:-1]) * 60
        elif duration.endswith("h"):
            return int(duration[:-1]) * 3600
        return int(duration)

    def _cleanup_experiments(self) -> None:
        """Clean up active experiments."""
        for name, namespace, kind in self._active_experiments:
            self.client.delete_experiment(name, namespace, kind)
        self._active_experiments = []

    def cleanup(self) -> None:
        """Clean up all resources."""
        self._cleanup_experiments()
        if self._http_client:
            self._http_client.close()
            self._http_client = None
