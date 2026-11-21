"""
Platform deployers for the Prometheus Testing Framework.

This module provides abstract base class and concrete implementations
for deploying Prometheus across different platforms (Minikube, EKS, GKE, AKS, Docker, Binary).

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10
"""

import logging
import os
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class DeploymentMode(Enum):
    """Deployment mode for Prometheus."""

    MONOLITHIC = "monolithic"
    DISTRIBUTED = "distributed"


class Platform(Enum):
    """Supported deployment platforms."""

    MINIKUBE = "minikube"
    EKS = "eks"
    GKE = "gke"
    AKS = "aks"
    DOCKER = "docker"
    BINARY = "binary"


class DeploymentStatus(Enum):
    """Status of a deployment."""

    NOT_DEPLOYED = "not_deployed"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    TEARING_DOWN = "tearing_down"


@dataclass
class DeployConfig:
    """Configuration for Prometheus deployment."""

    version: str = "v3.5.0"
    namespace: str = "monitoring"
    release_name: str = "prometheus"
    values_files: list[str] = field(default_factory=list)
    set_values: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    wait: bool = True
    deployment_mode: DeploymentMode = DeploymentMode.MONOLITHIC
    # Docker-specific settings
    docker_compose_file: str = ""
    docker_port: int = 9090
    # Binary-specific settings
    binary_path: str = ""
    config_file: str = ""
    data_dir: str = ""


@dataclass
class DeployResult:
    """Result of a deployment operation."""

    success: bool
    status: DeploymentStatus
    prometheus_url: str = ""
    message: str = ""
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class PlatformDeployer(ABC):
    """
    Abstract base class for platform-specific deployers.

    Requirements: 9.1, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10

    This class defines the interface that all platform deployers must implement.
    Each deployer handles the specifics of deploying Prometheus to its target platform.
    """

    def __init__(self, config: Optional[DeployConfig] = None):
        """
        Initialize the deployer.

        Args:
            config: Deployment configuration
        """
        self.config = config or DeployConfig()
        self._status = DeploymentStatus.NOT_DEPLOYED
        self._prometheus_url: str = ""
        self._deployment_mode: DeploymentMode = self.config.deployment_mode

    @property
    def status(self) -> DeploymentStatus:
        """Get current deployment status."""
        return self._status

    @property
    def platform(self) -> Platform:
        """Get the platform this deployer targets."""
        raise NotImplementedError

    @abstractmethod
    def deploy(self, config: Optional[DeployConfig] = None) -> DeployResult:
        """
        Deploy Prometheus to the platform.

        Args:
            config: Optional deployment configuration override

        Returns:
            DeployResult with deployment status and details
        """

    @abstractmethod
    def teardown(self) -> bool:
        """
        Remove Prometheus deployment.

        Returns:
            True if teardown was successful
        """

    @abstractmethod
    def get_prometheus_url(self) -> str:
        """
        Get the Prometheus API URL.

        Returns:
            URL string for accessing Prometheus API
        """

    def is_healthy(self, timeout: int = 30) -> bool:
        """
        Check if Prometheus is healthy using /-/healthy endpoint.

        Args:
            timeout: Timeout in seconds for health check

        Returns:
            True if Prometheus is healthy and responding
        """
        url = self.get_prometheus_url()
        if not url:
            return False

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(f"{url}/-/healthy")
                return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning("Health check failed: %s", e)
            return False

    def is_ready(self, timeout: int = 30) -> bool:
        """
        Check if Prometheus is ready using /-/ready endpoint.

        Args:
            timeout: Timeout in seconds for readiness check

        Returns:
            True if Prometheus is ready and responding
        """
        url = self.get_prometheus_url()
        if not url:
            return False

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(f"{url}/-/ready")
                return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning("Readiness check failed: %s", e)
            return False

    def get_deployment_mode(self) -> DeploymentMode:
        """
        Get the deployment mode (monolithic or distributed).

        Returns:
            DeploymentMode enum value
        """
        return self._deployment_mode

    def wait_for_ready(self, timeout: int = 300, interval: int = 5) -> bool:
        """
        Wait for Prometheus to become ready.

        Args:
            timeout: Maximum time to wait in seconds
            interval: Time between checks in seconds

        Returns:
            True if Prometheus became ready within timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_healthy(timeout=10) and self.is_ready(timeout=10):
                return True
            time.sleep(interval)
        return False

    def _run_command(
        self,
        cmd: list[str],
        timeout: int = 300,
        capture_output: bool = True,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Run a shell command.

        Args:
            cmd: Command and arguments as list
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise on non-zero exit

        Returns:
            CompletedProcess result
        """
        logger.debug("Running command: %s", " ".join(cmd))
        return subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            check=check,
        )


class KubernetesDeployer(PlatformDeployer):
    """
    Base class for Kubernetes-based deployers.

    Provides common functionality for deploying Prometheus to Kubernetes
    clusters using Helm charts. Supports both monolithic and distributed modes.
    """

    def __init__(self, config: Optional[DeployConfig] = None):
        super().__init__(config)
        self._kubeconfig: Optional[str] = None
        self._context: Optional[str] = None

    @property
    def kubeconfig(self) -> Optional[str]:
        """Get the kubeconfig path."""
        return self._kubeconfig

    @kubeconfig.setter
    def kubeconfig(self, value: str) -> None:
        """Set the kubeconfig path."""
        self._kubeconfig = value

    @property
    def context(self) -> Optional[str]:
        """Get the Kubernetes context."""
        return self._context

    @context.setter
    def context(self, value: str) -> None:
        """Set the Kubernetes context."""
        self._context = value

    def _get_kubectl_base_cmd(self) -> list[str]:
        """Get base kubectl command with kubeconfig and context."""
        cmd = ["kubectl"]
        if self._kubeconfig:
            cmd.extend(["--kubeconfig", self._kubeconfig])
        if self._context:
            cmd.extend(["--context", self._context])
        return cmd

    def _get_helm_base_cmd(self) -> list[str]:
        """Get base helm command with kubeconfig and context."""
        cmd = ["helm"]
        if self._kubeconfig:
            cmd.extend(["--kubeconfig", self._kubeconfig])
        if self._context:
            cmd.extend(["--kube-context", self._context])
        return cmd

    def _create_namespace(self, namespace: str) -> bool:
        """Create Kubernetes namespace if it doesn't exist."""
        try:
            cmd = self._get_kubectl_base_cmd() + [
                "create", "namespace", namespace, "--dry-run=client", "-o", "yaml"
            ]
            result = self._run_command(cmd, check=False)

            cmd = self._get_kubectl_base_cmd() + [
                "apply", "-f", "-"
            ]
            subprocess.run(
                cmd,
                input=result.stdout,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create namespace: %s", e)
            return False

    def _helm_install(self, config: DeployConfig) -> DeployResult:
        """
        Install Prometheus using Helm.

        Args:
            config: Deployment configuration

        Returns:
            DeployResult with installation status
        """
        start_time = time.time()
        self._status = DeploymentStatus.DEPLOYING

        # Create namespace
        if not self._create_namespace(config.namespace):
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Failed to create namespace",
            )

        # Build helm install command
        cmd = self._get_helm_base_cmd() + [
            "upgrade", "--install",
            config.release_name,
            "prometheus-community/kube-prometheus-stack",
            "--namespace", config.namespace,
            "--timeout", f"{config.timeout_seconds}s",
        ]

        if config.wait:
            cmd.append("--wait")

        # Add values files
        for values_file in config.values_files:
            cmd.extend(["-f", values_file])

        # Add set values
        for key, value in config.set_values.items():
            cmd.extend(["--set", f"{key}={value}"])

        try:
            result = self._run_command(cmd, timeout=config.timeout_seconds + 60)
            duration = time.time() - start_time

            if result.returncode == 0:
                self._status = DeploymentStatus.DEPLOYED
                self._prometheus_url = self._discover_prometheus_url(config.namespace)
                return DeployResult(
                    success=True,
                    status=DeploymentStatus.DEPLOYED,
                    prometheus_url=self._prometheus_url,
                    message="Prometheus deployed successfully",
                    duration_seconds=duration,
                    metadata={"deployment_mode": self._deployment_mode.value},
                )

            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Helm install failed: {result.stderr}",
                duration_seconds=duration,
            )
        except subprocess.TimeoutExpired:
            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Helm install timed out",
                duration_seconds=config.timeout_seconds,
            )
        except subprocess.CalledProcessError as e:
            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Helm install failed: {e.stderr}",
                duration_seconds=time.time() - start_time,
            )

    def _helm_uninstall(self, config: DeployConfig) -> bool:
        """
        Uninstall Prometheus using Helm.

        Args:
            config: Deployment configuration

        Returns:
            True if uninstall was successful
        """
        self._status = DeploymentStatus.TEARING_DOWN

        cmd = self._get_helm_base_cmd() + [
            "uninstall",
            config.release_name,
            "--namespace", config.namespace,
        ]

        try:
            self._run_command(cmd, timeout=120)
            self._status = DeploymentStatus.NOT_DEPLOYED
            self._prometheus_url = ""
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Helm uninstall failed: %s", e)
            self._status = DeploymentStatus.FAILED
            return False

    def _discover_prometheus_url(self, namespace: str) -> str:
        """
        Discover the Prometheus service URL.

        Args:
            namespace: Kubernetes namespace

        Returns:
            Prometheus URL string
        """
        # Default to port-forward URL
        _ = namespace  # Acknowledge unused parameter
        return "http://localhost:9090"

    def _setup_port_forward(
        self,
        namespace: str,
        service_name: str = "prometheus-kube-prometheus-prometheus",
        local_port: int = 9090,
        remote_port: int = 9090,
    ) -> Optional[subprocess.Popen]:
        """
        Set up port forwarding to Prometheus service.

        Args:
            namespace: Kubernetes namespace
            service_name: Name of the Prometheus service
            local_port: Local port to forward to
            remote_port: Remote port on the service

        Returns:
            Popen process for the port-forward, or None if failed
        """
        cmd = self._get_kubectl_base_cmd() + [
            "port-forward",
            f"svc/{service_name}",
            f"{local_port}:{remote_port}",
            "-n", namespace,
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Give it a moment to establish
            time.sleep(2)
            if process.poll() is None:
                return process
            return None
        except OSError as e:
            logger.error("Failed to set up port forward: %s", e)
            return None



@dataclass
class MinikubeConfig:
    """Configuration specific to Minikube deployments."""

    profile: str = "minikube"
    driver: str = "docker"
    cpus: int = 4
    memory: str = "8192"
    disk_size: str = "20g"
    kubernetes_version: str = ""
    storage_class: str = "standard"


class MinikubeDeployer(KubernetesDeployer):
    """
    Minikube Platform Deployer.

    Requirements: 9.1, 9.8, 9.9, 9.10

    Deploys Prometheus to Minikube for local Kubernetes testing.
    Supports both monolithic and distributed deployment modes.
    """

    def __init__(
        self,
        config: Optional[DeployConfig] = None,
        minikube_config: Optional[MinikubeConfig] = None,
    ):
        super().__init__(config)
        self.minikube_config = minikube_config or MinikubeConfig()
        self._port_forward_process: Optional[subprocess.Popen] = None
        self._context = self.minikube_config.profile

    @property
    def platform(self) -> Platform:
        return Platform.MINIKUBE

    def _get_minikube_base_cmd(self) -> list[str]:
        return ["minikube", "-p", self.minikube_config.profile]

    def _is_minikube_running(self) -> bool:
        try:
            cmd = self._get_minikube_base_cmd() + ["status", "-o", "json"]
            result = self._run_command(cmd, timeout=30, check=False)
            if result.returncode == 0:
                import json
                status = json.loads(result.stdout)
                return status.get("Host", "") == "Running"
            return False
        except (subprocess.CalledProcessError, ValueError):
            return False

    def _start_minikube(self) -> bool:
        if self._is_minikube_running():
            logger.info("Minikube is already running")
            return True

        logger.info("Starting Minikube cluster...")
        cmd = self._get_minikube_base_cmd() + [
            "start",
            "--driver", self.minikube_config.driver,
            "--cpus", str(self.minikube_config.cpus),
            "--memory", self.minikube_config.memory,
            "--disk-size", self.minikube_config.disk_size,
        ]

        if self.minikube_config.kubernetes_version:
            cmd.extend(["--kubernetes-version", self.minikube_config.kubernetes_version])

        try:
            self._run_command(cmd, timeout=600)
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to start Minikube: %s", e)
            return False

    def _ensure_helm_repo(self) -> bool:
        try:
            cmd = self._get_helm_base_cmd() + [
                "repo", "add", "prometheus-community",
                "https://prometheus-community.github.io/helm-charts",
            ]
            self._run_command(cmd, timeout=60, check=False)
            cmd = self._get_helm_base_cmd() + ["repo", "update"]
            self._run_command(cmd, timeout=120)
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to setup Helm repo: %s", e)
            return False

    def _get_minikube_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName": self.minikube_config.storage_class,
            "prometheus.prometheusSpec.resources.requests.cpu": "250m",
            "prometheus.prometheusSpec.resources.requests.memory": "512Mi",
            "prometheus.prometheusSpec.resources.limits.cpu": "1",
            "prometheus.prometheusSpec.resources.limits.memory": "2Gi",
            "prometheus.prometheusSpec.securityContext.runAsNonRoot": "false",
            "prometheus.prometheusSpec.securityContext.runAsUser": "0",
        }
        if self._deployment_mode == DeploymentMode.DISTRIBUTED:
            values.update({
                "prometheus.prometheusSpec.replicas": "2",
                "prometheus.prometheusSpec.podAntiAffinity": "soft",
            })
        return values

    def deploy(self, config: Optional[DeployConfig] = None) -> DeployResult:
        deploy_config = config or self.config
        self._deployment_mode = deploy_config.deployment_mode

        if not self._start_minikube():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Failed to start Minikube cluster",
            )

        if not self._ensure_helm_repo():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Failed to setup Helm repository",
            )

        minikube_values = self._get_minikube_values()
        merged_values = {**deploy_config.set_values, **minikube_values}
        deploy_config.set_values = merged_values

        result = self._helm_install(deploy_config)
        if result.success:
            result.metadata["profile"] = self.minikube_config.profile
            result.metadata["platform"] = "minikube"
            result.metadata["deployment_mode"] = self._deployment_mode.value
        return result

    def teardown(self) -> bool:
        if self._port_forward_process:
            self._port_forward_process.terminate()
            self._port_forward_process = None
        return self._helm_uninstall(self.config)

    def get_prometheus_url(self) -> str:
        if self._prometheus_url:
            return self._prometheus_url
        return "http://localhost:9090"

    def setup_port_forward(self, local_port: int = 9090) -> bool:
        self._port_forward_process = self._setup_port_forward(
            namespace=self.config.namespace,
            service_name=f"{self.config.release_name}-kube-prometheus-prometheus",
            local_port=local_port,
        )
        if self._port_forward_process:
            self._prometheus_url = f"http://localhost:{local_port}"
            return True
        return False

    def get_minikube_ip(self) -> Optional[str]:
        try:
            cmd = self._get_minikube_base_cmd() + ["ip"]
            result = self._run_command(cmd, timeout=30)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None


@dataclass
class DockerConfig:
    """Configuration specific to Docker deployments."""

    compose_file: str = ""
    project_name: str = "prometheus"
    port: int = 9090
    prometheus_version: str = "v2.54.1"
    retention: str = "15d"
    memory_limit: str = "2g"


class DockerDeployer(PlatformDeployer):
    """
    Docker Platform Deployer.

    Requirements: 9.5, 9.8

    Deploys Prometheus using Docker Compose for local testing.
    Only supports monolithic deployment mode.
    """

    def __init__(
        self,
        config: Optional[DeployConfig] = None,
        docker_config: Optional[DockerConfig] = None,
    ):
        super().__init__(config)
        self.docker_config = docker_config or DockerConfig()
        self._deployment_mode = DeploymentMode.MONOLITHIC
        self._container_id: Optional[str] = None

    @property
    def platform(self) -> Platform:
        return Platform.DOCKER

    def get_deployment_mode(self) -> DeploymentMode:
        return DeploymentMode.MONOLITHIC

    def _get_docker_compose_cmd(self) -> list[str]:
        cmd = ["docker", "compose"]
        if self.docker_config.compose_file:
            cmd.extend(["-f", self.docker_config.compose_file])
        cmd.extend(["-p", self.docker_config.project_name])
        return cmd

    def _is_docker_available(self) -> bool:
        try:
            result = self._run_command(["docker", "info"], timeout=30, check=False)
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _get_container_status(self) -> Optional[str]:
        try:
            cmd = [
                "docker", "ps", "-a",
                "--filter", f"name={self.docker_config.project_name}-prometheus",
                "--format", "{{.Status}}"
            ]
            result = self._run_command(cmd, timeout=30, check=False)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except subprocess.CalledProcessError:
            return None

    def _create_default_compose_file(self) -> str:
        compose_content = f"""version: '3.8'
services:
  prometheus:
    image: prom/prometheus:{self.docker_config.prometheus_version}
    container_name: {self.docker_config.project_name}-prometheus
    restart: unless-stopped
    ports:
      - "{self.docker_config.port}:9090"
    volumes:
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time={self.docker_config.retention}'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    deploy:
      resources:
        limits:
          memory: {self.docker_config.memory_limit}
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
volumes:
  prometheus_data:
    driver: local
"""
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".yml", prefix="docker-compose-")
        with os.fdopen(fd, "w") as f:
            f.write(compose_content)
        return path

    def deploy(self, config: Optional[DeployConfig] = None) -> DeployResult:
        deploy_config = config or self.config
        start_time = time.time()
        self._status = DeploymentStatus.DEPLOYING

        if not self._is_docker_available():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Docker is not available or not running",
            )

        if deploy_config.docker_compose_file:
            self.docker_config.compose_file = deploy_config.docker_compose_file
        elif not self.docker_config.compose_file:
            self.docker_config.compose_file = self._create_default_compose_file()

        env = os.environ.copy()
        env["PROMETHEUS_VERSION"] = self.docker_config.prometheus_version
        env["PROMETHEUS_PORT"] = str(self.docker_config.port)
        env["PROMETHEUS_RETENTION"] = self.docker_config.retention
        env["PROMETHEUS_MEMORY_LIMIT"] = self.docker_config.memory_limit

        cmd = self._get_docker_compose_cmd() + ["up", "-d"]

        try:
            subprocess.run(
                cmd,
                timeout=deploy_config.timeout_seconds,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
            duration = time.time() - start_time

            if self.wait_for_ready(timeout=60):
                self._status = DeploymentStatus.DEPLOYED
                self._prometheus_url = f"http://localhost:{self.docker_config.port}"
                return DeployResult(
                    success=True,
                    status=DeploymentStatus.DEPLOYED,
                    prometheus_url=self._prometheus_url,
                    message="Prometheus deployed successfully via Docker",
                    duration_seconds=duration,
                    metadata={
                        "platform": "docker",
                        "deployment_mode": self._deployment_mode.value,
                        "container_name": f"{self.docker_config.project_name}-prometheus",
                    },
                )

            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Prometheus container started but failed health check",
                duration_seconds=duration,
            )

        except subprocess.TimeoutExpired:
            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Docker compose up timed out",
                duration_seconds=deploy_config.timeout_seconds,
            )
        except subprocess.CalledProcessError as e:
            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Docker compose up failed: {e.stderr}",
                duration_seconds=time.time() - start_time,
            )

    def teardown(self) -> bool:
        self._status = DeploymentStatus.TEARING_DOWN
        cmd = self._get_docker_compose_cmd() + ["down", "-v"]
        try:
            self._run_command(cmd, timeout=120)
            self._status = DeploymentStatus.NOT_DEPLOYED
            self._prometheus_url = ""
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Docker compose down failed: %s", e)
            self._status = DeploymentStatus.FAILED
            return False

    def get_prometheus_url(self) -> str:
        if self._prometheus_url:
            return self._prometheus_url
        return f"http://localhost:{self.docker_config.port}"

    def get_container_logs(self, lines: int = 100) -> str:
        try:
            cmd = [
                "docker", "logs",
                "--tail", str(lines),
                f"{self.docker_config.project_name}-prometheus"
            ]
            result = self._run_command(cmd, timeout=30, check=False)
            return result.stdout + result.stderr
        except subprocess.CalledProcessError:
            return ""

    def restart_container(self) -> bool:
        try:
            cmd = self._get_docker_compose_cmd() + ["restart", "prometheus"]
            self._run_command(cmd, timeout=60)
            return self.wait_for_ready(timeout=60)
        except subprocess.CalledProcessError:
            return False


@dataclass
class BinaryConfig:
    """Configuration specific to binary deployments."""

    binary_path: str = ""
    config_file: str = ""
    data_dir: str = ""
    port: int = 9090
    retention: str = "15d"
    log_level: str = "info"


class BinaryDeployer(PlatformDeployer):
    """
    Binary Platform Deployer.

    Requirements: 9.6, 9.8

    Deploys Prometheus as a binary process for bare-metal testing.
    Only supports monolithic deployment mode.
    """

    def __init__(
        self,
        config: Optional[DeployConfig] = None,
        binary_config: Optional[BinaryConfig] = None,
    ):
        super().__init__(config)
        self.binary_config = binary_config or BinaryConfig()
        self._deployment_mode = DeploymentMode.MONOLITHIC
        self._process: Optional[subprocess.Popen] = None
        self._temp_data_dir: Optional[str] = None

    @property
    def platform(self) -> Platform:
        return Platform.BINARY

    def get_deployment_mode(self) -> DeploymentMode:
        return DeploymentMode.MONOLITHIC

    def _find_prometheus_binary(self) -> Optional[str]:
        if self.binary_config.binary_path and Path(self.binary_config.binary_path).exists():
            return self.binary_config.binary_path

        common_paths = [
            "/usr/local/bin/prometheus",
            "/usr/bin/prometheus",
            str(Path.home() / ".local/bin/prometheus"),
            str(Path.home() / "bin/prometheus"),
        ]

        prometheus_in_path = shutil.which("prometheus")
        if prometheus_in_path:
            return prometheus_in_path

        for path in common_paths:
            if Path(path).exists():
                return path

        return None

    def _create_default_config(self) -> str:
        config_content = f"""global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:{self.binary_config.port}']
"""
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".yml", prefix="prometheus-")
        with os.fdopen(fd, "w") as f:
            f.write(config_content)
        return path

    def _create_data_dir(self) -> str:
        import tempfile
        return tempfile.mkdtemp(prefix="prometheus-data-")

    def deploy(self, config: Optional[DeployConfig] = None) -> DeployResult:
        _ = config  # Binary deployer uses binary_config instead
        start_time = time.time()
        self._status = DeploymentStatus.DEPLOYING

        binary_path = self._find_prometheus_binary()
        if not binary_path:
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Prometheus binary not found. Please install Prometheus or specify binary_path.",
            )

        config_file = self.binary_config.config_file
        if not config_file or not Path(config_file).exists():
            config_file = self._create_default_config()

        data_dir = self.binary_config.data_dir
        if not data_dir:
            data_dir = self._create_data_dir()
            self._temp_data_dir = data_dir

        cmd = [
            binary_path,
            f"--config.file={config_file}",
            f"--storage.tsdb.path={data_dir}",
            f"--storage.tsdb.retention.time={self.binary_config.retention}",
            f"--web.listen-address=0.0.0.0:{self.binary_config.port}",
            f"--log.level={self.binary_config.log_level}",
            "--web.enable-lifecycle",
            "--web.enable-admin-api",
        ]

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            time.sleep(3)

            if self._process.poll() is not None:
                _, stderr = self._process.communicate()
                return DeployResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    message=f"Prometheus process exited immediately: {stderr.decode()}",
                    duration_seconds=time.time() - start_time,
                )

            if self.wait_for_ready(timeout=60):
                self._status = DeploymentStatus.DEPLOYED
                self._prometheus_url = f"http://localhost:{self.binary_config.port}"
                return DeployResult(
                    success=True,
                    status=DeploymentStatus.DEPLOYED,
                    prometheus_url=self._prometheus_url,
                    message="Prometheus deployed successfully as binary",
                    duration_seconds=time.time() - start_time,
                    metadata={
                        "platform": "binary",
                        "deployment_mode": self._deployment_mode.value,
                        "binary_path": binary_path,
                        "config_file": config_file,
                        "data_dir": data_dir,
                        "pid": self._process.pid,
                    },
                )

            self._process.terminate()
            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Prometheus started but failed health check",
                duration_seconds=time.time() - start_time,
            )

        except OSError as e:
            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Failed to start Prometheus: {e}",
                duration_seconds=time.time() - start_time,
            )

    def teardown(self) -> bool:
        self._status = DeploymentStatus.TEARING_DOWN

        if self._process:
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait()
                self._process = None
            except OSError as e:
                logger.error("Failed to stop Prometheus process: %s", e)
                self._status = DeploymentStatus.FAILED
                return False

        if self._temp_data_dir and Path(self._temp_data_dir).exists():
            try:
                shutil.rmtree(self._temp_data_dir)
            except OSError as e:
                logger.warning("Failed to clean up temp data dir: %s", e)

        self._status = DeploymentStatus.NOT_DEPLOYED
        self._prometheus_url = ""
        return True

    def get_prometheus_url(self) -> str:
        if self._prometheus_url:
            return self._prometheus_url
        return f"http://localhost:{self.binary_config.port}"

    def get_process_info(self) -> dict[str, Any]:
        if not self._process:
            return {"running": False}
        return {
            "running": self._process.poll() is None,
            "pid": self._process.pid,
            "returncode": self._process.returncode,
        }

    def reload_config(self) -> bool:
        url = self.get_prometheus_url()
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(f"{url}/-/reload")
                return response.status_code == 200
        except httpx.RequestError:
            return False


def get_deployer(
    platform: str | Platform,
    config: Optional[DeployConfig] = None,
    **kwargs: Any,
) -> PlatformDeployer:
    """
    Factory function to get the appropriate deployer for a platform.

    Args:
        platform: Target platform (string or Platform enum)
        config: Base deployment configuration
        **kwargs: Platform-specific configuration options

    Returns:
        PlatformDeployer instance for the specified platform

    Raises:
        ValueError: If platform is not supported
    """
    # Import here to avoid circular imports
    from .eks_deployer import EKSDeployer, EKSConfig
    from .gke_deployer import GKEDeployer, GKEConfig
    from .aks_deployer import AKSDeployer, AKSConfig

    if isinstance(platform, str):
        platform = Platform(platform.lower())

    if platform == Platform.EKS:
        eks_config = EKSConfig(
            cluster_name=kwargs.get("cluster_name", ""),
            region=kwargs.get("region", "us-east-1"),
            profile=kwargs.get("profile"),
            role_arn=kwargs.get("role_arn"),
            storage_class=kwargs.get("storage_class", "gp3"),
            enable_irsa=kwargs.get("enable_irsa", False),
        )
        return EKSDeployer(config=config, eks_config=eks_config)

    if platform == Platform.GKE:
        gke_config = GKEConfig(
            project_id=kwargs.get("project_id", ""),
            cluster_name=kwargs.get("cluster_name", ""),
            zone=kwargs.get("zone", ""),
            region=kwargs.get("region", ""),
            storage_class=kwargs.get("storage_class", "standard-rwo"),
            enable_workload_identity=kwargs.get("enable_workload_identity", False),
            enable_gmp_integration=kwargs.get("enable_gmp_integration", False),
        )
        return GKEDeployer(config=config, gke_config=gke_config)

    if platform == Platform.AKS:
        aks_config = AKSConfig(
            subscription_id=kwargs.get("subscription_id", ""),
            resource_group=kwargs.get("resource_group", ""),
            cluster_name=kwargs.get("cluster_name", ""),
            storage_class=kwargs.get("storage_class", "managed-premium"),
            enable_pod_identity=kwargs.get("enable_pod_identity", False),
            enable_workload_identity=kwargs.get("enable_workload_identity", False),
            enable_azure_monitor=kwargs.get("enable_azure_monitor", False),
        )
        return AKSDeployer(config=config, aks_config=aks_config)

    if platform == Platform.MINIKUBE:
        minikube_config = MinikubeConfig(
            profile=kwargs.get("profile", "minikube"),
            driver=kwargs.get("driver", "docker"),
            cpus=kwargs.get("cpus", 4),
            memory=kwargs.get("memory", "8192"),
            disk_size=kwargs.get("disk_size", "20g"),
            kubernetes_version=kwargs.get("kubernetes_version", ""),
            storage_class=kwargs.get("storage_class", "standard"),
        )
        return MinikubeDeployer(config=config, minikube_config=minikube_config)

    if platform == Platform.DOCKER:
        docker_config = DockerConfig(
            compose_file=kwargs.get("compose_file", ""),
            project_name=kwargs.get("project_name", "prometheus"),
            port=kwargs.get("port", 9090),
            prometheus_version=kwargs.get("prometheus_version", "v2.54.1"),
            retention=kwargs.get("retention", "15d"),
            memory_limit=kwargs.get("memory_limit", "2g"),
        )
        return DockerDeployer(config=config, docker_config=docker_config)

    if platform == Platform.BINARY:
        binary_config = BinaryConfig(
            binary_path=kwargs.get("binary_path", ""),
            config_file=kwargs.get("config_file", ""),
            data_dir=kwargs.get("data_dir", ""),
            port=kwargs.get("port", 9090),
            retention=kwargs.get("retention", "15d"),
            log_level=kwargs.get("log_level", "info"),
        )
        return BinaryDeployer(config=config, binary_config=binary_config)

    raise ValueError(f"Unsupported platform: {platform}")
