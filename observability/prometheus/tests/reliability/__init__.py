"""
Reliability tests for Prometheus failure and recovery behavior.

This module provides comprehensive reliability testing for Prometheus,
including restart recovery, WAL replay, data integrity, network partition,
target re-discovery, alerting continuity, and distributed availability tests.

Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10
"""

from .config import (
    AlertingContinuityConfig,
    DataIntegrityConfig,
    DeploymentMode,
    DistributedReliabilityConfig,
    NetworkPartitionConfig,
    ReliabilityTestConfig,
    RestartMethod,
    RestartRecoveryConfig,
    TargetRediscoveryConfig,
    WALReplayConfig,
)
from .models import (
    AlertingContinuityResult,
    DataIntegrityResult,
    HealthCheckResult,
    RecoveryMetrics,
    RecoveryStatus,
    ReliabilityTestResult,
    ReliabilityTestType,
    TargetDiscoveryResult,
    WALReplayResult,
)
from .test_alerting_continuity import (
    AlertingContinuityTest,
    run_alerting_continuity_test,
)
from .test_data_integrity import (
    DataIntegrityTest,
    run_data_integrity_test,
)
from .test_distributed import (
    DistributedReliabilityTest,
    MonolithicReliabilityTest,
    run_distributed_reliability_test,
    run_monolithic_reliability_test,
)
from .test_network import (
    NetworkPartitionTest,
    run_network_partition_test,
)
from .test_recovery import (
    RestartRecoveryTest,
    run_restart_recovery_test,
)
from .test_target_rediscovery import (
    TargetRediscoveryTest,
    run_target_rediscovery_test,
)
from .test_wal_replay import (
    WALReplayTest,
    run_wal_replay_test,
)

__all__ = [
    # Config classes
    "AlertingContinuityConfig",
    "DataIntegrityConfig",
    "DeploymentMode",
    "DistributedReliabilityConfig",
    "NetworkPartitionConfig",
    "ReliabilityTestConfig",
    "RestartMethod",
    "RestartRecoveryConfig",
    "TargetRediscoveryConfig",
    "WALReplayConfig",
    # Model classes
    "AlertingContinuityResult",
    "DataIntegrityResult",
    "HealthCheckResult",
    "RecoveryMetrics",
    "RecoveryStatus",
    "ReliabilityTestResult",
    "ReliabilityTestType",
    "TargetDiscoveryResult",
    "WALReplayResult",
    # Test classes
    "AlertingContinuityTest",
    "DataIntegrityTest",
    "DistributedReliabilityTest",
    "MonolithicReliabilityTest",
    "NetworkPartitionTest",
    "RestartRecoveryTest",
    "TargetRediscoveryTest",
    "WALReplayTest",
    # Convenience functions
    "run_alerting_continuity_test",
    "run_data_integrity_test",
    "run_distributed_reliability_test",
    "run_monolithic_reliability_test",
    "run_network_partition_test",
    "run_restart_recovery_test",
    "run_target_rediscovery_test",
    "run_wal_replay_test",
]
