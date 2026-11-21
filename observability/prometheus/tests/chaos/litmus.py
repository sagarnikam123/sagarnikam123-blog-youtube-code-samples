"""
Litmus Chaos integration for Prometheus chaos testing.

This module provides integration with Litmus Chaos for advanced chaos
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

from .config import LitmusConfig
from .models import (
    ChaosEvent,
    ChaosTestResult,
    ChaosType,
    DeploymentMode,
    RecoveryMetrics,
    RecoveryStatus,
)

logger = logging.getLogger(__name__)


class LitmusClient:
    """
    Client for interacting with Litmus Chaos.

    Requirements: 20.7

    This client provides methods to create and manage chaos experiments
    using Litmus CRDs.
    """

    def __init__(
        self,
        config: Optional[LitmusConfig] = None,
        kubectl_context: Optional[str] = None,
    ):
        """
        Initialize the Litmus client.

        Args:
            config: Litmus configuration
            kubectl_context: Kubernetes context to use
        """
        self.config = config or LitmusConfig()
        self.kubectl_context = kubectl_context

    def _get_kubectl_cmd(self) -> list[str]:
        """Get base kubectl command with context if specified."""
        cmd = ["kubectl"]
        if self.kubectl_context:
            cmd.extend(["--context", self.kubectl_context])
        return cmd

    def is_installed(self) -> bool:
        """
        Check if Litmus is installed in the cluster.

        Returns:
            True if Litmus is installed
        """
        cmd = self._get_kubectl_cmd() + [
            "get", "crd", "chaosengines.litmuschaos.io",
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

    def create_chaos_engine(
        self,
        name: str,
        namespace: str,
        app_namespace: str,
        app_label: str,
        app_kind: str,
        experiments: list[dict[str, Any]],
    ) -> bool:
        """
        Create a ChaosEngine to run experiments.

        Args:
            name: Name of the chaos engine
            namespace: Namespace for the engine
            app_namespace: Namespace of target application
            app_label: Label of target application
            app_kind: Kind of target application (deployment, statefulset)
            experiments: List of experiment configurations

        Returns:
            True if engine was created successfully
        """
        engine = {
            "apiVersion": "litmuschaos.io/v1alpha1",
            "kind": "ChaosEngine",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "appinfo": {
                    "appns": app_namespace,
                    "applabel": app_label,
                    "appkind": app_kind,
                },
                "engineState": "active",
                "chaosServiceAccount": self.config.service_account,
                "experiments": experiments,
            },
        }

        return self._apply_manifest(engine)

    def create_pod_delete_experiment(
        self,
        name: str,
        namespace: str,
        app_namespace: str,
        app_label: str,
        total_chaos_duration: int = 30,
        chaos_interval: int = 10,
        force: bool = True,
    ) -> bool:
        """
        Create a pod-delete chaos experiment.

        Args:
            name: Name of the chaos engine
            namespace: Namespace for the engine
            app_namespace: Namespace of target application
            app_label: Label of target application
            total_chaos_duration: Total duration of chaos in seconds
            chaos_interval: Interval between pod deletions
            force: Whether to force delete pods

        Returns:
            True if experiment was created successfully
        """
        experiments = [
            {
                "name": "pod-delete",
                "spec": {
                    "components": {
                        "env": [
                            {"name": "TOTAL_CHAOS_DURATION", "value": str(total_chaos_duration)},
                            {"name": "CHAOS_INTERVAL", "value": str(chaos_interval)},
                            {"name": "FORCE", "value": str(force).lower()},
                        ],
                    },
                },
            },
        ]

        return self.create_chaos_engine(
            name=name,
            namespace=namespace,
            app_namespace=app_namespace,
            app_label=app_label,
            app_kind="deployment",
            experiments=experiments,
        )

    def create_pod_cpu_hog_experiment(
        self,
        name: str,
        namespace: str,
        app_namespace: str,
        app_label: str,
        total_chaos_duration: int = 60,
        cpu_cores: int = 1,
    ) -> bool:
        """
        Create a pod-cpu-hog chaos experiment.

        Args:
            name: Name of the chaos engine
            namespace: Namespace for the engine
            app_namespace: Namespace of target application
            app_label: Label of target application
            total_chaos_duration: Total duration of chaos in seconds
            cpu_cores: Number of CPU cores to stress

        Returns:
            True if experiment was created successfully
        """
        experiments = [
            {
                "name": "pod-cpu-hog",
                "spec": {
                    "components": {
                        "env": [
                            {"name": "TOTAL_CHAOS_DURATION", "value": str(total_chaos_duration)},
                            {"name": "CPU_CORES", "value": str(cpu_cores)},
                        ],
                    },
                },
            },
        ]

        return self.create_chaos_engine(
            name=name,
            namespace=namespace,
            app_namespace=app_namespace,
            app_label=app_label,
            app_kind="deployment",
            experiments=experiments,
        )

    def create_pod_memory_hog_experiment(
        self,
        name: str,
        namespace: str,
        app_namespace: str,
        app_label: str,
        total_chaos_duration: int = 60,
        memory_consumption: int = 500,
    ) -> bool:
        """
        Create a pod-memory-hog chaos experiment.

        Args:
            name: Name of the chaos engine
            namespace: Namespace for the engine
            app_namespace: Namespace of target application
            app_label: Label of target application
            total_chaos_duration: Total duration of chaos in seconds
            memory_consumption: Memory to consume in MB

        Returns:
            True if experiment was created successfully
        """
        experiments = [
            {
                "name": "pod-memory-hog",
                "spec": {
                    "components": {
                        "env": [
                            {"name": "TOTAL_CHAOS_DURATION", "value": str(total_chaos_duration)},
                            {"name": "MEMORY_CONSUMPTION", "value": str(memory_consumption)},
                        ],
                    },
                },
            },
        ]

        return self.create_chaos_engine(
            name=name,
            namespace=namespace,
            app_namespace=app_namespace,
            app_label=app_label,
            app_kind="deployment",
            experiments=experiments,
        )

    def create_pod_network_latency_experiment(
        self,
        name: str,
        namespace: str,
        app_namespace: str,
        app_label: str,
        total_chaos_duration: int = 60,
        network_latency: int = 100,
    ) -> bool:
        """
        Create a pod-network-latency chaos experiment.

        Args:
            name: Name of the chaos engine
            namespace: Namespace for the engine
            app_namespace: Namespace of target application
            app_label: Label of target application
            total_chaos_duration: Total duration of chaos in seconds
            network_latency: Network latency in milliseconds

        Returns:
            True if experiment was created successfully
        """
        experiments = [
            {
                "name": "pod-network-latency",
                "spec": {
                    "components": {
                        "env": [
                            {"name": "TOTAL_CHAOS_DURATION", "value": str(total_chaos_duration)},
                            {"name": "NETWORK_LATENCY", "value": str(network_latency)},
                        ],
                    },
                },
            },
        ]

        return self.create_chaos_engine(
            name=name,
            namespace=namespace,
            app_namespace=app_namespace,
            app_label=app_label,
            app_kind="deployment",
            experiments=experiments,
        )

    def delete_chaos_engine(self, name: str, namespace: str) -> bool:
        """
        Delete a chaos engine.

        Args:
            name: Name of the engine
            namespace: Namespace of the engine

        Returns:
            True if deletion was successful
        """
        cmd = self._get_kubectl_cmd() + [
            "delete", "chaosengine", name,
            "-n", namespace,
            "--ignore-not-found",
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            return True
        except Exception as e:
            logger.error(f"Failed to delete chaos engine: {e}")
            return False

    def get_chaos_result(
        self,
        engine_name: str,
        namespace: str,
    ) -> Optional[dict[str, Any]]:
        """
        Get the result of a chaos experiment.

        Args:
            engine_name: Name of the chaos engine
            namespace: Namespace of the engine

        Returns:
            Result dictionary or None if not found
        """
        cmd = self._get_kubectl_cmd() + [
            "get", "chaosresult",
            "-n", namespace,
            "-l", f"chaosUID={engine_name}",
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
            items = data.get("items", [])
            if items:
                return items[0].get("status", {})
            return None
        except Exception as e:
            logger.debug(f"Failed to get chaos result: {e}")
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


class LitmusChaosTest:
    """
    Chaos test using Litmus Chaos.

    Requirements: 20.7, 20.9

    This class provides a high-level interface for running chaos tests
    using Litmus experiments.
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        namespace: str = "monitoring",
        litmus_config: Optional[LitmusConfig] = None,
        kubectl_context: Optional[str] = None,
        recovery_timeout_seconds: int = 300,
        health_check_interval_seconds: float = 5.0,
    ):
        """
        Initialize the Litmus test.

        Args:
            prometheus_url: URL of Prometheus instance
            namespace: Namespace where Prometheus is deployed
            litmus_config: Litmus configuration
            kubectl_context: Kubernetes context to use
            recovery_timeout_seconds: Timeout for recovery
            health_check_interval_seconds: Interval between health checks
        """
        self.prometheus_url = prometheus_url
        self.namespace = namespace
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.health_check_interval_seconds = health_check_interval_seconds

        self.client = LitmusClient(
            config=litmus_config,
            kubectl_context=kubectl_context,
        )
        self._http_client: Optional[httpx.Client] = None
        self._active_engines: list[tuple[str, str]] = []

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

    def run_pod_delete(
        self,
        app_label: str,
        duration_seconds: int = 30,
    ) -> ChaosTestResult:
        """
        Run a pod-delete chaos experiment.

        Args:
            app_label: Label of target application
            duration_seconds: Duration of chaos

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]
        engine_name = f"prometheus-pod-delete-{event_id}"

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.POD_KILL,
            target=app_label,
            deployment_mode=DeploymentMode.DISTRIBUTED,
            parameters={
                "duration_seconds": duration_seconds,
                "tool": "litmus",
            },
        )

        result = ChaosTestResult(
            test_name="litmus_pod_delete",
            chaos_event=chaos_event,
        )

        if not self.client.is_installed():
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Litmus is not installed")
            return result

        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        logger.info(f"Creating Litmus pod-delete experiment: {engine_name}")

        success = self.client.create_pod_delete_experiment(
            name=engine_name,
            namespace=self.client.config.experiment_namespace,
            app_namespace=self.namespace,
            app_label=app_label,
            total_chaos_duration=duration_seconds,
        )

        if not success:
            result.error_messages.append("Failed to create pod-delete experiment")
        else:
            self._active_engines.append(
                (engine_name, self.client.config.experiment_namespace)
            )

        # Wait for experiment to complete
        time.sleep(duration_seconds + 30)

        chaos_event.end_time = datetime.utcnow()

        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        # Get chaos result
        chaos_result = self.client.get_chaos_result(
            engine_name,
            self.client.config.experiment_namespace,
        )

        self._cleanup_engines()

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.metadata = {
            "engine_name": engine_name,
            "duration_seconds": duration_seconds,
            "tool": "litmus",
            "chaos_result": chaos_result,
        }

        return result

    def run_cpu_hog(
        self,
        app_label: str,
        duration_seconds: int = 60,
        cpu_cores: int = 1,
    ) -> ChaosTestResult:
        """
        Run a pod-cpu-hog chaos experiment.

        Args:
            app_label: Label of target application
            duration_seconds: Duration of chaos
            cpu_cores: Number of CPU cores to stress

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]
        engine_name = f"prometheus-cpu-hog-{event_id}"

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.CPU_THROTTLE,
            target=app_label,
            deployment_mode=DeploymentMode.DISTRIBUTED,
            parameters={
                "duration_seconds": duration_seconds,
                "cpu_cores": cpu_cores,
                "tool": "litmus",
            },
        )

        result = ChaosTestResult(
            test_name="litmus_cpu_hog",
            chaos_event=chaos_event,
        )

        if not self.client.is_installed():
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Litmus is not installed")
            return result

        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        logger.info(f"Creating Litmus cpu-hog experiment: {engine_name}")

        success = self.client.create_pod_cpu_hog_experiment(
            name=engine_name,
            namespace=self.client.config.experiment_namespace,
            app_namespace=self.namespace,
            app_label=app_label,
            total_chaos_duration=duration_seconds,
            cpu_cores=cpu_cores,
        )

        if not success:
            result.error_messages.append("Failed to create cpu-hog experiment")
        else:
            self._active_engines.append(
                (engine_name, self.client.config.experiment_namespace)
            )

        time.sleep(duration_seconds + 30)

        chaos_event.end_time = datetime.utcnow()

        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        self._cleanup_engines()

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.metadata = {
            "engine_name": engine_name,
            "duration_seconds": duration_seconds,
            "cpu_cores": cpu_cores,
            "tool": "litmus",
        }

        return result

    def run_memory_hog(
        self,
        app_label: str,
        duration_seconds: int = 60,
        memory_mb: int = 500,
    ) -> ChaosTestResult:
        """
        Run a pod-memory-hog chaos experiment.

        Args:
            app_label: Label of target application
            duration_seconds: Duration of chaos
            memory_mb: Memory to consume in MB

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]
        engine_name = f"prometheus-memory-hog-{event_id}"

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.MEMORY_PRESSURE,
            target=app_label,
            deployment_mode=DeploymentMode.DISTRIBUTED,
            parameters={
                "duration_seconds": duration_seconds,
                "memory_mb": memory_mb,
                "tool": "litmus",
            },
        )

        result = ChaosTestResult(
            test_name="litmus_memory_hog",
            chaos_event=chaos_event,
        )

        if not self.client.is_installed():
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Litmus is not installed")
            return result

        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        logger.info(f"Creating Litmus memory-hog experiment: {engine_name}")

        success = self.client.create_pod_memory_hog_experiment(
            name=engine_name,
            namespace=self.client.config.experiment_namespace,
            app_namespace=self.namespace,
            app_label=app_label,
            total_chaos_duration=duration_seconds,
            memory_consumption=memory_mb,
        )

        if not success:
            result.error_messages.append("Failed to create memory-hog experiment")
        else:
            self._active_engines.append(
                (engine_name, self.client.config.experiment_namespace)
            )

        time.sleep(duration_seconds + 30)

        chaos_event.end_time = datetime.utcnow()

        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        self._cleanup_engines()

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.metadata = {
            "engine_name": engine_name,
            "duration_seconds": duration_seconds,
            "memory_mb": memory_mb,
            "tool": "litmus",
        }

        return result

    def run_network_latency(
        self,
        app_label: str,
        duration_seconds: int = 60,
        latency_ms: int = 100,
    ) -> ChaosTestResult:
        """
        Run a pod-network-latency chaos experiment.

        Args:
            app_label: Label of target application
            duration_seconds: Duration of chaos
            latency_ms: Network latency in milliseconds

        Returns:
            ChaosTestResult with test outcome
        """
        event_id = str(uuid.uuid4())[:8]
        engine_name = f"prometheus-network-latency-{event_id}"

        chaos_event = ChaosEvent(
            event_id=event_id,
            chaos_type=ChaosType.NETWORK_LATENCY,
            target=app_label,
            deployment_mode=DeploymentMode.DISTRIBUTED,
            parameters={
                "duration_seconds": duration_seconds,
                "latency_ms": latency_ms,
                "tool": "litmus",
            },
        )

        result = ChaosTestResult(
            test_name="litmus_network_latency",
            chaos_event=chaos_event,
        )

        if not self.client.is_installed():
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Litmus is not installed")
            return result

        result.pre_chaos_metrics = self._collect_metrics()

        if not result.pre_chaos_metrics.get("healthy"):
            result.recovery_status = RecoveryStatus.FAILED
            result.error_messages.append("Prometheus not healthy before chaos")
            return result

        logger.info(f"Creating Litmus network-latency experiment: {engine_name}")

        success = self.client.create_pod_network_latency_experiment(
            name=engine_name,
            namespace=self.client.config.experiment_namespace,
            app_namespace=self.namespace,
            app_label=app_label,
            total_chaos_duration=duration_seconds,
            network_latency=latency_ms,
        )

        if not success:
            result.error_messages.append("Failed to create network-latency experiment")
        else:
            self._active_engines.append(
                (engine_name, self.client.config.experiment_namespace)
            )

        time.sleep(duration_seconds + 30)

        chaos_event.end_time = datetime.utcnow()

        result.recovery_metrics = self._wait_for_recovery()
        result.post_chaos_metrics = self._collect_metrics()

        self._cleanup_engines()

        if result.recovery_metrics.fully_recovered:
            result.recovery_status = RecoveryStatus.RECOVERED
        else:
            result.recovery_status = RecoveryStatus.FAILED

        result.metadata = {
            "engine_name": engine_name,
            "duration_seconds": duration_seconds,
            "latency_ms": latency_ms,
            "tool": "litmus",
        }

        return result

    def _cleanup_engines(self) -> None:
        """Clean up active chaos engines."""
        for name, namespace in self._active_engines:
            self.client.delete_chaos_engine(name, namespace)
        self._active_engines = []

    def cleanup(self) -> None:
        """Clean up all resources."""
        self._cleanup_engines()
        if self._http_client:
            self._http_client.close()
            self._http_client = None
