"""
Sanity tests for quick Prometheus validation.

This module provides sanity tests to verify basic Prometheus functionality
after deployment. These tests are designed to complete within 60 seconds.

Requirements: 12.1, 12.2, 12.3, 12.4

Test modules:
- test_api: API accessibility tests (Requirement 12.1)
- test_scraping: Self-monitoring tests (Requirement 12.2)
- test_promql: PromQL query tests (Requirement 12.3)
- test_ui: Web UI accessibility tests (Requirement 12.4)
"""

from .test_api import (
    PrometheusAPIClient,
    TestAPIAccessibility,
    test_api_accessible,
)
from .test_promql import (
    PromQLTestClient,
    TestPromQL,
    test_promql_basic_queries,
)
from .test_scraping import (
    PrometheusQueryClient,
    TestSelfMonitoring,
    test_self_monitoring,
)
from .test_ui import (
    PrometheusUIClient,
    TestUIAccessibility,
    test_ui_accessible,
)

__all__ = [
    # API tests
    "PrometheusAPIClient",
    "TestAPIAccessibility",
    "test_api_accessible",
    # Scraping tests
    "PrometheusQueryClient",
    "TestSelfMonitoring",
    "test_self_monitoring",
    # PromQL tests
    "PromQLTestClient",
    "TestPromQL",
    "test_promql_basic_queries",
    # UI tests
    "PrometheusUIClient",
    "TestUIAccessibility",
    "test_ui_accessible",
]
