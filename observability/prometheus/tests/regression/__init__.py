"""Regression tests for Prometheus version comparison.

This module provides regression testing capabilities for Prometheus,
including version comparison, rule comparison, configuration compatibility,
and performance comparison tests.

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7
"""

from .config import (
    ConfigCompatibilityConfig,
    PerformanceComparisonConfig,
    RegressionTestConfig,
    RuleComparisonConfig,
)
from .models import (
    ComparisonStatus,
    ConfigCompatibilityResult,
    PerformanceComparison,
    PrometheusVersion,
    QueryComparison,
    QueryResult,
    RegressionTestReport,
    RegressionType,
    RuleComparison,
    RuleResult,
)

__all__ = [
    # Config
    "RegressionTestConfig",
    "RuleComparisonConfig",
    "ConfigCompatibilityConfig",
    "PerformanceComparisonConfig",
    # Models
    "RegressionType",
    "ComparisonStatus",
    "PrometheusVersion",
    "QueryResult",
    "QueryComparison",
    "RuleResult",
    "RuleComparison",
    "PerformanceComparison",
    "ConfigCompatibilityResult",
    "RegressionTestReport",
]
