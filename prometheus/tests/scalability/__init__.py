"""
Scalability tests for Prometheus scaling behavior.

This module provides comprehensive scalability testing including:
- Scaling dimension tests (targets, series, cardinality, retention, concurrency)
- Scaling curve generation and analysis
- Non-linear degradation point detection

Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7
"""

from .scaling_dimensions import (
    ScalingDimension,
    ScalingDataPoint,
    ScalingTestResult,
    ScalingTestConfig,
    ScalingDimensionTester,
)

from .scaling_curves import (
    CurveAnalysis,
    ScalingCurveReport,
    ScalingCurveConfig,
    ScalingCurveGenerator,
)

__all__ = [
    # Scaling dimensions
    "ScalingDimension",
    "ScalingDataPoint",
    "ScalingTestResult",
    "ScalingTestConfig",
    "ScalingDimensionTester",
    # Scaling curves
    "CurveAnalysis",
    "ScalingCurveReport",
    "ScalingCurveConfig",
    "ScalingCurveGenerator",
]
