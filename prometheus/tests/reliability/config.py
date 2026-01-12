"""
Configuration for Prometheus reliability tests.

This module defines configuration classes for various reliability test types
including restart recovery, WAL replay, data integrity, network partition,
target re-discovery, and alerting continuity tests.

Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DeploymentMode(Enum):
    """Deployment mode for Prometheus."""

    MONOLITHIC = "monolithic"
    DISTRIBUTED = "distributed"


class RestartMethod(Enum):
    """Method used to restart Prometheus."""

    POD_DELETE = "pod_delete"
    CONTAINER_RESTART = "container_restart"
    PROCESS_RESTART = "process_restart"
    ROLLOUT_RESTART = "rollout_restart"


@dataclass
class ReliabilityTestConfig:
    """
    Base configuration for reliability tests.

    Requirements: 19.1, 19.8

    Attributes:
        prometheus_url: URL of the Prometheus instance
        namespace: Kubernetes namespace for Prometheus
        deployment_mode: Monolithic or distributed deployment
        recovery_timeout_seconds: Maximum time to wait for recovery
        health_check_interval_seconds: Interval between health checks
        kubectl_context: Kubernetes context to use
    """

    prometheus_url: str = "http://localhost:9090"
    namespace: str = "monitoring"
    deployment_mode: DeploymentMode = DeploymentMode.MONOLITHIC
    recovery_timeout_seconds: int = 300
    health_check_interval_seconds: float = 5.0
    kubectl_context: Optional[str] = None


@dataclass
class RestartRecoveryConfig(ReliabilityTestConfig):
    """
    Configuration for restart recovery test.

    Requirements: 19.1, 19.8

    Attributes:
        restart_method: Method to use for restart
        pod_selector: Label selector for Prometheus pods
        container_name: Name of the container (for Docker)
        grace_period_seconds: Grace period for termination
        verify_data_persistence: Whether to verify data after restart
    """

    restart_method: RestartMethod = RestartMethod.POD_DELETE
    pod_selector: str = "app.kubernetes.io/name=prometheus"
    container_name: str = "prometheus"
    grace_period_seconds: int = 30
    verify_data_persistence: bool = True


@dataclass
class WALReplayConfig(ReliabilityTestConfig):
    """
    Configuration for WAL replay test.

    Requirements: 19.2

    Attributes:
        simulate_crash: Whether to simulate a crash (SIGKILL)
        wal_directory: Path to WAL directory
        max_replay_time_seconds: Maximum expected WAL replay time
        verify_data_after_replay: Whether to verify data after replay
    """

    simulate_crash: bool = True
    wal_directory: str = "/prometheus/wal"
    max_replay_time_seconds: int = 300
    verify_data_after_replay: bool = True


@dataclass
class DataIntegrityConfig(ReliabilityTestConfig):
    """
    Configuration for data integrity test.

    Requirements: 19.3

    Attributes:
        test_metric_name: Name of the test metric to verify
        sample_count: Number of samples to write before shutdown
        verify_after_restart: Whether to verify data after restart
        tolerance_percent: Acceptable data loss percentage
    """

    test_metric_name: str = "reliability_test_metric"
    sample_count: int = 100
    verify_after_restart: bool = True
    tolerance_percent: float = 0.0  # No data loss expected within WAL retention


@dataclass
class NetworkPartitionConfig(ReliabilityTestConfig):
    """
    Configuration for network partition test.

    Requirements: 19.4

    Attributes:
        partition_duration_seconds: Duration of network partition
        target_endpoints: Endpoints to partition from
        verify_graceful_handling: Whether to verify graceful handling
    """

    partition_duration_seconds: int = 60
    target_endpoints: list[str] = field(default_factory=list)
    verify_graceful_handling: bool = True


@dataclass
class TargetRediscoveryConfig(ReliabilityTestConfig):
    """
    Configuration for target re-discovery test.

    Requirements: 19.5

    Attributes:
        target_selector: Label selector for scrape targets
        expected_targets: Expected number of targets after restart
        discovery_timeout_seconds: Timeout for target discovery
    """

    target_selector: str = ""
    expected_targets: int = 0
    discovery_timeout_seconds: int = 120


@dataclass
class AlertingContinuityConfig(ReliabilityTestConfig):
    """
    Configuration for alerting continuity test.

    Requirements: 19.6

    Attributes:
        alert_rule_name: Name of the alert rule to test
        alertmanager_url: URL of Alertmanager
        verify_alert_firing: Whether to verify alert continues firing
    """

    alert_rule_name: str = "TestAlert"
    alertmanager_url: str = "http://localhost:9093"
    verify_alert_firing: bool = True


@dataclass
class DistributedReliabilityConfig(ReliabilityTestConfig):
    """
    Configuration for distributed reliability tests.

    Requirements: 19.9, 19.10

    Attributes:
        replica_count: Number of Prometheus replicas
        min_available_replicas: Minimum replicas that must remain available
        test_replica_failure: Whether to test replica failure scenarios
    """

    replica_count: int = 2
    min_available_replicas: int = 1
    test_replica_failure: bool = True

    def __post_init__(self):
        """Set deployment mode to distributed."""
        self.deployment_mode = DeploymentMode.DISTRIBUTED
