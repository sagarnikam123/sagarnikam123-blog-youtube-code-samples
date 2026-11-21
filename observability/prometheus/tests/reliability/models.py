"""
Data models for Prometheus reliability testing.

This module defines the core data structures used for reliability tests
including recovery tracking, data integrity verification, and test results.

Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ReliabilityTestType(Enum):
    """Types of reliability tests."""

    RESTART_RECOVERY = "restart_recovery"
    WAL_REPLAY = "wal_replay"
    DATA_INTEGRITY = "data_integrity"
    NETWORK_PARTITION = "network_partition"
    TARGET_REDISCOVERY = "target_rediscovery"
    ALERTING_CONTINUITY = "alerting_continuity"
    DISTRIBUTED_AVAILABILITY = "distributed_availability"


class RecoveryStatus(Enum):
    """Status of recovery after reliability event."""

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


@dataclass
class HealthCheckResult:
    """
    Result of a health check operation.

    Requirements: 19.8

    Attributes:
        healthy_endpoint: Status of /-/healthy endpoint
        ready_endpoint: Status of /-/ready endpoint
        api_accessible: Whether API is accessible
        query_success: Whether queries succeed
        timestamp: When the check was performed
    """

    healthy_endpoint: bool = False
    ready_endpoint: bool = False
    api_accessible: bool = False
    query_success: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_healthy(self) -> bool:
        """Check if Prometheus is fully healthy."""
        return (
            self.healthy_endpoint
            and self.ready_endpoint
            and self.api_accessible
            and self.query_success
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "healthy_endpoint": self.healthy_endpoint,
            "ready_endpoint": self.ready_endpoint,
            "api_accessible": self.api_accessible,
            "query_success": self.query_success,
            "is_healthy": self.is_healthy,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RecoveryMetrics:
    """
    Metrics collected during recovery verification.

    Requirements: 19.1, 19.8

    Attributes:
        recovery_time_seconds: Time taken to recover
        healthy_endpoint_status: Final status of /-/healthy
        ready_endpoint_status: Final status of /-/ready
        api_accessible: Whether API is accessible after recovery
        query_success: Whether queries succeed after recovery
        scrape_targets_up: Number of scrape targets that are up
        total_scrape_targets: Total number of scrape targets
        wal_replay_completed: Whether WAL replay completed
        data_integrity_verified: Whether data integrity was verified
    """

    recovery_time_seconds: float = 0.0
    healthy_endpoint_status: bool = False
    ready_endpoint_status: bool = False
    api_accessible: bool = False
    query_success: bool = False
    scrape_targets_up: int = 0
    total_scrape_targets: int = 0
    wal_replay_completed: bool = False
    data_integrity_verified: bool = False

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
            "recovery_time_seconds": round(self.recovery_time_seconds, 2),
            "healthy_endpoint_status": self.healthy_endpoint_status,
            "ready_endpoint_status": self.ready_endpoint_status,
            "api_accessible": self.api_accessible,
            "query_success": self.query_success,
            "scrape_targets_up": self.scrape_targets_up,
            "total_scrape_targets": self.total_scrape_targets,
            "wal_replay_completed": self.wal_replay_completed,
            "data_integrity_verified": self.data_integrity_verified,
            "fully_recovered": self.fully_recovered,
        }


@dataclass
class DataIntegrityResult:
    """
    Result of data integrity verification.

    Requirements: 19.3

    Attributes:
        samples_written: Number of samples written before shutdown
        samples_recovered: Number of samples recovered after restart
        data_loss_percent: Percentage of data lost
        integrity_verified: Whether integrity check passed
        error_message: Error message if verification failed
    """

    samples_written: int = 0
    samples_recovered: int = 0
    data_loss_percent: float = 0.0
    integrity_verified: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "samples_written": self.samples_written,
            "samples_recovered": self.samples_recovered,
            "data_loss_percent": round(self.data_loss_percent, 2),
            "integrity_verified": self.integrity_verified,
            "error_message": self.error_message,
        }


@dataclass
class WALReplayResult:
    """
    Result of WAL replay verification.

    Requirements: 19.2

    Attributes:
        replay_started: Whether WAL replay started
        replay_completed: Whether WAL replay completed
        replay_time_seconds: Time taken for WAL replay
        samples_replayed: Number of samples replayed
        error_message: Error message if replay failed
    """

    replay_started: bool = False
    replay_completed: bool = False
    replay_time_seconds: float = 0.0
    samples_replayed: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "replay_started": self.replay_started,
            "replay_completed": self.replay_completed,
            "replay_time_seconds": round(self.replay_time_seconds, 2),
            "samples_replayed": self.samples_replayed,
            "error_message": self.error_message,
        }


@dataclass
class TargetDiscoveryResult:
    """
    Result of target re-discovery verification.

    Requirements: 19.5

    Attributes:
        targets_before_restart: Number of targets before restart
        targets_after_restart: Number of targets after restart
        discovery_time_seconds: Time taken to re-discover targets
        all_targets_rediscovered: Whether all targets were re-discovered
    """

    targets_before_restart: int = 0
    targets_after_restart: int = 0
    discovery_time_seconds: float = 0.0
    all_targets_rediscovered: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "targets_before_restart": self.targets_before_restart,
            "targets_after_restart": self.targets_after_restart,
            "discovery_time_seconds": round(self.discovery_time_seconds, 2),
            "all_targets_rediscovered": self.all_targets_rediscovered,
        }


@dataclass
class AlertingContinuityResult:
    """
    Result of alerting continuity verification.

    Requirements: 19.6

    Attributes:
        alert_firing_before: Whether alert was firing before restart
        alert_firing_after: Whether alert continued firing after restart
        alert_gap_seconds: Gap in alerting during restart
        continuity_maintained: Whether alerting continuity was maintained
    """

    alert_firing_before: bool = False
    alert_firing_after: bool = False
    alert_gap_seconds: float = 0.0
    continuity_maintained: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "alert_firing_before": self.alert_firing_before,
            "alert_firing_after": self.alert_firing_after,
            "alert_gap_seconds": round(self.alert_gap_seconds, 2),
            "continuity_maintained": self.continuity_maintained,
        }


@dataclass
class ReliabilityTestResult:
    """
    Result of a reliability test execution.

    Requirements: 19.1, 19.7, 19.8

    Attributes:
        test_name: Name of the reliability test
        test_type: Type of reliability test
        deployment_mode: Monolithic or distributed
        recovery_status: Status of recovery
        recovery_metrics: Metrics from recovery verification
        pre_test_health: Health check before test
        post_test_health: Health check after test
        data_integrity: Data integrity verification result
        wal_replay: WAL replay verification result
        target_discovery: Target discovery verification result
        alerting_continuity: Alerting continuity verification result
        start_time: When the test started
        end_time: When the test ended
        error_messages: Any error messages encountered
        metadata: Additional test metadata
    """

    test_name: str
    test_type: ReliabilityTestType
    deployment_mode: DeploymentMode = DeploymentMode.MONOLITHIC
    recovery_status: RecoveryStatus = RecoveryStatus.NOT_STARTED
    recovery_metrics: RecoveryMetrics = field(default_factory=RecoveryMetrics)
    pre_test_health: Optional[HealthCheckResult] = None
    post_test_health: Optional[HealthCheckResult] = None
    data_integrity: Optional[DataIntegrityResult] = None
    wal_replay: Optional[WALReplayResult] = None
    target_discovery: Optional[TargetDiscoveryResult] = None
    alerting_continuity: Optional[AlertingContinuityResult] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    error_messages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Check if the reliability test passed."""
        return self.recovery_status == RecoveryStatus.RECOVERED

    @property
    def duration_seconds(self) -> float:
        """Get test duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.utcnow() - self.start_time).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "test_name": self.test_name,
            "test_type": self.test_type.value,
            "deployment_mode": self.deployment_mode.value,
            "recovery_status": self.recovery_status.value,
            "recovery_metrics": self.recovery_metrics.to_dict(),
            "pre_test_health": self.pre_test_health.to_dict() if self.pre_test_health else None,
            "post_test_health": self.post_test_health.to_dict() if self.post_test_health else None,
            "data_integrity": self.data_integrity.to_dict() if self.data_integrity else None,
            "wal_replay": self.wal_replay.to_dict() if self.wal_replay else None,
            "target_discovery": self.target_discovery.to_dict() if self.target_discovery else None,
            "alerting_continuity": self.alerting_continuity.to_dict() if self.alerting_continuity else None,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "error_messages": self.error_messages,
            "passed": self.passed,
            "metadata": self.metadata,
        }
