"""Endurance (soak) tests for long-running Prometheus stability.

This module provides endurance testing capabilities for Prometheus,
including soak tests, stability monitoring, and k6 load testing.

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9, 18.10
"""

from .config import EnduranceTestConfig, SoakTestConfig, StabilityMonitorConfig
from .models import (
    CompactionInfo,
    DegradationEvent,
    DegradationType,
    PerformanceSnapshot,
    ResourceSnapshot,
    SoakTestDataPoint,
    StabilityMetrics,
    StabilityStatus,
)
from .test_soak import SoakTestResult, SoakTester, run_soak_test_sync
from .stability_monitor import (
    CompactionCycleInfo,
    PerformanceBaseline,
    StabilityMonitor,
    StabilityMonitorResult,
    run_stability_monitor_sync,
)
from .k6_soak import (
    K6SoakConfig,
    K6SoakMetrics,
    K6SoakResult,
    K6SoakRunner,
    run_k6_soak_test,
)
from .test_deployment_modes import (
    ComparisonResult,
    DeploymentEnduranceConfig,
    DeploymentEnduranceResult,
    DeploymentEnduranceTester,
    DeploymentMode,
    MonolithicDistributedComparator,
    run_comparison_sync,
    run_deployment_endurance_test_sync,
)

__all__ = [
    # Config
    "EnduranceTestConfig",
    "SoakTestConfig",
    "StabilityMonitorConfig",
    # Models
    "CompactionInfo",
    "DegradationEvent",
    "DegradationType",
    "PerformanceSnapshot",
    "ResourceSnapshot",
    "SoakTestDataPoint",
    "StabilityMetrics",
    "StabilityStatus",
    # Soak Test
    "SoakTestResult",
    "SoakTester",
    "run_soak_test_sync",
    # Stability Monitor
    "CompactionCycleInfo",
    "PerformanceBaseline",
    "StabilityMonitor",
    "StabilityMonitorResult",
    "run_stability_monitor_sync",
    # k6 Soak Test
    "K6SoakConfig",
    "K6SoakMetrics",
    "K6SoakResult",
    "K6SoakRunner",
    "run_k6_soak_test",
    # Deployment Mode Tests
    "ComparisonResult",
    "DeploymentEnduranceConfig",
    "DeploymentEnduranceResult",
    "DeploymentEnduranceTester",
    "DeploymentMode",
    "MonolithicDistributedComparator",
    "run_comparison_sync",
    "run_deployment_endurance_test_sync",
]
