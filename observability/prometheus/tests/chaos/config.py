"""
Configuration for Prometheus chaos tests.

This module defines configuration classes for various chaos test types.

Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 20.9, 20.10
"""

from dataclasses import dataclass, field
from typing import Optional

from .models import ChaosTool, DeploymentMode


@dataclass
class ChaosTestConfig:
    """
    Base configuration for chaos tests.

    Attributes:
        prometheus_url: URL of the Prometheus instance
        namespace: Kubernetes namespace for Prometheus
        deployment_mode: Monolithic or distributed deployment
        chaos_tool: Chaos engineering tool to use
        recovery_timeout_seconds: Maximum time to wait for recovery
        health_check_interval_seconds: Interval between health checks
        kubectl_context: Kubernetes context to use
    """

    prometheus_url: str = "http://localhost:9090"
    namespace: str = "monitoring"
    deployment_mode: DeploymentMode = DeploymentMode.DISTRIBUTED
    chaos_tool: ChaosTool = ChaosTool.NATIVE
    recovery_timeout_seconds: int = 300
    health_check_interval_seconds: float = 5.0
    kubectl_context: Optional[str] = None


@dataclass
class PodKillConfig(ChaosTestConfig):
    """
    Configuration for pod kill chaos test.

    Requirements: 20.1, 20.8

    Attributes:
        pod_selector: Label selector for target pods
        kill_count: Number of pods to kill (for distributed)
        random_selection: Whether to randomly select pods
        grace_period_seconds: Grace period for pod termination
    """

    pod_selector: str = "app.kubernetes.io/name=prometheus"
    kill_count: int = 1
    random_selection: bool = True
    grace_period_seconds: int = 0


@dataclass
class ContainerKillConfig(ChaosTestConfig):
    """
    Configuration for container kill chaos test.

    Requirements: 20.1, 20.8

    Attributes:
        container_name: Name or ID of the container to kill
        signal: Signal to send (SIGKILL, SIGTERM, etc.)
        use_docker: Whether to use Docker commands
    """

    container_name: str = "prometheus"
    signal: str = "SIGKILL"
    use_docker: bool = True

    def __post_init__(self):
        """Set deployment mode to monolithic for container tests."""
        self.deployment_mode = DeploymentMode.MONOLITHIC


@dataclass
class CPUThrottleConfig(ChaosTestConfig):
    """
    Configuration for CPU throttle chaos test.

    Requirements: 20.2

    Attributes:
        throttle_percent: Percentage of CPU to throttle (0-100)
        duration_seconds: Duration of throttling
        target_container: Container to throttle
    """

    throttle_percent: float = 80.0
    duration_seconds: int = 60
    target_container: str = "prometheus"


@dataclass
class MemoryPressureConfig(ChaosTestConfig):
    """
    Configuration for memory pressure chaos test.

    Requirements: 20.3

    Attributes:
        memory_bytes: Amount of memory to consume
        memory_percent: Percentage of available memory to consume
        duration_seconds: Duration of memory pressure
        oom_score_adj: OOM score adjustment
    """

    memory_bytes: Optional[int] = None
    memory_percent: float = 80.0
    duration_seconds: int = 60
    oom_score_adj: int = 1000


@dataclass
class DiskIOLatencyConfig(ChaosTestConfig):
    """
    Configuration for disk I/O latency chaos test.

    Requirements: 20.4

    Attributes:
        latency_ms: Latency to inject in milliseconds
        jitter_ms: Jitter in milliseconds
        target_path: Path to inject latency on
        duration_seconds: Duration of I/O latency
    """

    latency_ms: int = 100
    jitter_ms: int = 10
    target_path: str = "/prometheus"
    duration_seconds: int = 60


@dataclass
class NetworkLatencyConfig(ChaosTestConfig):
    """
    Configuration for network latency chaos test.

    Requirements: 20.5

    Attributes:
        latency_ms: Network latency to inject in milliseconds
        jitter_ms: Latency jitter in milliseconds
        correlation_percent: Correlation percentage for latency
        target_hosts: Specific hosts to affect
        duration_seconds: Duration of network latency
    """

    latency_ms: int = 100
    jitter_ms: int = 20
    correlation_percent: float = 25.0
    target_hosts: list[str] = field(default_factory=list)
    duration_seconds: int = 60


@dataclass
class TargetFailureConfig(ChaosTestConfig):
    """
    Configuration for scrape target failure chaos test.

    Requirements: 20.6

    Attributes:
        target_selector: Label selector for target pods
        failure_percent: Percentage of targets to fail
        failure_type: Type of failure (complete, partial)
        duration_seconds: Duration of target failure
    """

    target_selector: str = ""
    failure_percent: float = 50.0
    failure_type: str = "complete"  # complete or partial
    duration_seconds: int = 60


@dataclass
class ChaosMeshConfig:
    """
    Configuration for Chaos Mesh integration.

    Requirements: 20.7

    Attributes:
        api_url: Chaos Mesh API URL
        namespace: Namespace where Chaos Mesh is installed
        experiment_namespace: Namespace for chaos experiments
    """

    api_url: str = "http://localhost:2333"
    namespace: str = "chaos-mesh"
    experiment_namespace: str = "monitoring"


@dataclass
class LitmusConfig:
    """
    Configuration for Litmus Chaos integration.

    Requirements: 20.7

    Attributes:
        api_url: Litmus API URL
        namespace: Namespace where Litmus is installed
        experiment_namespace: Namespace for chaos experiments
        service_account: Service account for experiments
    """

    api_url: str = "http://localhost:9091"
    namespace: str = "litmus"
    experiment_namespace: str = "monitoring"
    service_account: str = "litmus-admin"
