"""
Data models for Prometheus chaos testing.

This module defines the core data structures used for chaos tests
including chaos events, recovery tracking, and failure scenarios.

Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 20.9, 20.10
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ChaosType(Enum):
    """Types of chaos events that can be injected."""

    POD_KILL = "pod_kill"
    CONTAINER_KILL = "container_kill"
    PROCESS_KILL = "process_kill"
    CPU_THROTTLE = "cpu_throttle"
    MEMORY_PRESSURE = "memory_pressure"
    DISK_IO_LATENCY = "disk_io_latency"
    NETWORK_LATENCY = "network_latency"
    NETWORK_PARTITION = "network_partition"
    TARGET_FAILURE = "target_failure"


class RecoveryStatus(Enum):
    """Status of recovery after chaos event."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    RECOVERED = "recovered"
    PARTIAL_RECOVERY = "partial_recovery"
    FAILED = "failed"
    TIMEOUT = "timeout"


class DeploymentMode(Enum):
    """Deployment mode for Prometheus."""

    MONOLITHIC = "monolithic"
    DISTRIBUTED = "distributed"


class ChaosTool(Enum):
    """Supported chaos engineering tools."""

    NATIVE = "native"  # Built-in kubectl/docker commands
    CHAOS_MESH = "chaos_mesh"
    LITMUS = "litmus"


@dataclass
class ChaosEvent:
    """
    Represents a chaos event that was injected.

    Requirements: 20.1, 20.8

    Attributes:
        event_id: Unique identifier for the event
        chaos_type: Type of chaos injected
        target: Target of the chaos (pod name, container name, etc.)
        start_time: When the chaos was injected
        end_time: When the chaos ended (if applicable)
        parameters: Additional parameters for the chaos event
        deployment_mode: Whether targeting monolithic or distributed
    """

    event_id: str
    chaos_type: ChaosType
    target: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    parameters: dict[str, Any] = field(default_factory=dict)
    deployment_mode: DeploymentMode = DeploymentMode.DISTRIBUTED

    @property
    def duration_seconds(self) -> float:
        """Get duration of the chaos event."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.utcnow() - self.start_time).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "event_id": self.event_id,
            "chaos_type": self.chaos_type.value,
            "target": self.target,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "parameters": self.parameters,
            "deployment_mode": self.deployment_mode.value,
        }


@dataclass
class RecoveryMetrics:
    """
    Metrics collected during recovery verification.

    Requirements: 20.9

    Attributes:
        healthy_endpoint_status: Status of /-/healthy endpoint
        ready_endpoint_status: Status of /-/ready endpoint
        api_accessible: Whether API is accessible
        query_success: Whether queries succeed
        scrape_targets_up: Number of scrape targets that are up
        total_scrape_targets: Total number of scrape targets
        recovery_time_seconds: Time taken to recover
    """

    healthy_endpoint_status: bool = False
    ready_endpoint_status: bool = False
    api_accessible: bool = False
    query_success: bool = False
    scrape_targets_up: int = 0
    total_scrape_targets: int = 0
    recovery_time_seconds: float = 0.0

    @property
    def fully_recovered(self) -> bool:
        """Check if system is fully recovered."""
        return (
            self.healthy_endpoint_status
            and self.ready_endpoint_status
            and self.api_accessible
            and self.query_success
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "healthy_endpoint_status": self.healthy_endpoint_status,
            "ready_endpoint_status": self.ready_endpoint_status,
            "api_accessible": self.api_accessible,
            "query_success": self.query_success,
            "scrape_targets_up": self.scrape_targets_up,
            "total_scrape_targets": self.total_scrape_targets,
            "recovery_time_seconds": round(self.recovery_time_seconds, 2),
            "fully_recovered": self.fully_recovered,
        }


@dataclass
class ChaosTestResult:
    """
    Result of a chaos test execution.

    Requirements: 20.1, 20.8, 20.9

    Attributes:
        test_name: Name of the chaos test
        chaos_event: The chaos event that was injected
        recovery_status: Status of recovery
        recovery_metrics: Metrics from recovery verification
        pre_chaos_metrics: Metrics before chaos injection
        post_chaos_metrics: Metrics after recovery
        error_messages: Any error messages encountered
        metadata: Additional test metadata
    """

    test_name: str
    chaos_event: ChaosEvent
    recovery_status: RecoveryStatus = RecoveryStatus.NOT_STARTED
    recovery_metrics: RecoveryMetrics = field(default_factory=RecoveryMetrics)
    pre_chaos_metrics: dict[str, Any] = field(default_factory=dict)
    post_chaos_metrics: dict[str, Any] = field(default_factory=dict)
    error_messages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Check if the chaos test passed."""
        return self.recovery_status == RecoveryStatus.RECOVERED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "test_name": self.test_name,
            "chaos_event": self.chaos_event.to_dict(),
            "recovery_status": self.recovery_status.value,
            "recovery_metrics": self.recovery_metrics.to_dict(),
            "pre_chaos_metrics": self.pre_chaos_metrics,
            "post_chaos_metrics": self.post_chaos_metrics,
            "error_messages": self.error_messages,
            "passed": self.passed,
            "metadata": self.metadata,
        }


@dataclass
class ResourcePressureParams:
    """
    Parameters for resource pressure chaos tests.

    Requirements: 20.2, 20.3, 20.4

    Attributes:
        cpu_percent: CPU throttle percentage (0-100)
        memory_bytes: Memory to consume in bytes
        memory_percent: Memory pressure as percentage
        io_latency_ms: Disk I/O latency to inject in milliseconds
        duration_seconds: Duration of the pressure test
    """

    cpu_percent: Optional[float] = None
    memory_bytes: Optional[int] = None
    memory_percent: Optional[float] = None
    io_latency_ms: Optional[int] = None
    duration_seconds: int = 60

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_bytes": self.memory_bytes,
            "memory_percent": self.memory_percent,
            "io_latency_ms": self.io_latency_ms,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class NetworkChaosParams:
    """
    Parameters for network chaos tests.

    Requirements: 20.5, 20.6

    Attributes:
        latency_ms: Network latency to inject in milliseconds
        jitter_ms: Latency jitter in milliseconds
        packet_loss_percent: Percentage of packets to drop
        target_endpoints: Specific endpoints to affect
        duration_seconds: Duration of the network chaos
    """

    latency_ms: Optional[int] = None
    jitter_ms: Optional[int] = None
    packet_loss_percent: Optional[float] = None
    target_endpoints: list[str] = field(default_factory=list)
    duration_seconds: int = 60

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "latency_ms": self.latency_ms,
            "jitter_ms": self.jitter_ms,
            "packet_loss_percent": self.packet_loss_percent,
            "target_endpoints": self.target_endpoints,
            "duration_seconds": self.duration_seconds,
        }
