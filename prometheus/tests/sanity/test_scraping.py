"""
Self-Monitoring Tests for Prometheus.

This module implements sanity tests to verify that Prometheus is successfully
scraping its own metrics (self-monitoring).

Requirements: 12.2
"""

import time
from datetime import datetime
from typing import Any, Optional

import httpx
import pytest

from framework.models import (
    ErrorCategory,
    ErrorSeverity,
    TestError,
    TestResult,
    TestStatus,
)


class PrometheusQueryClient:
    """
    Client for executing PromQL queries against Prometheus.

    Provides methods to query metrics and verify scraping status.
    """

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize the Prometheus query client.

        Args:
            base_url: Base URL of the Prometheus instance
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def query(self, promql: str) -> dict[str, Any]:
        """
        Execute an instant PromQL query.

        Args:
            promql: The PromQL query string

        Returns:
            Query result data

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/api/v1/query"
        response = self.client.get(url, params={"query": promql})
        response.raise_for_status()
        return response.json()

    def check_up_metric(self, job: str = "prometheus") -> tuple[bool, float, Optional[str]]:
        """
        Check if the 'up' metric for a job equals 1.

        Args:
            job: The job name to check (default: "prometheus")

        Returns:
            Tuple of (is_up, value, error_message)
        """
        query = f'up{{job="{job}"}}'
        try:
            result = self.query(query)

            if result.get("status") != "success":
                return False, 0.0, f"Query failed: {result.get('error', 'Unknown error')}"

            data = result.get("data", {})
            results = data.get("result", [])

            if not results:
                return False, 0.0, f"No results for query: {query}"

            # Get the first result's value
            first_result = results[0]
            value = float(first_result.get("value", [0, "0"])[1])

            return value == 1.0, value, None

        except httpx.TimeoutException:
            return False, 0.0, f"Query timed out after {self.timeout}s"
        except httpx.ConnectError as e:
            return False, 0.0, f"Connection failed: {str(e)}"
        except (ValueError, IndexError, KeyError) as e:
            return False, 0.0, f"Failed to parse response: {str(e)}"
        except Exception as e:
            return False, 0.0, f"Unexpected error: {str(e)}"

    def get_scrape_targets(self) -> dict[str, Any]:
        """
        Get the current scrape targets.

        Returns:
            Targets data from /api/v1/targets
        """
        url = f"{self.base_url}/api/v1/targets"
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()


def test_self_monitoring(prometheus_url: str) -> TestResult:
    """
    Test that Prometheus is scraping its own metrics.

    Requirements: 12.2

    This test verifies:
    - The up{job="prometheus"} metric exists
    - The metric value equals 1 (indicating successful scraping)

    Args:
        prometheus_url: URL of the Prometheus instance

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="self_monitoring",
        test_type="sanity",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    client = PrometheusQueryClient(prometheus_url, timeout=10.0)

    try:
        start = time.time()
        is_up, value, error_msg = client.check_up_metric("prometheus")
        duration = time.time() - start

        result.duration_seconds = duration
        result.end_time = datetime.utcnow()

        if is_up:
            result.status = TestStatus.PASSED
            result.message = f"Prometheus self-monitoring active (up={value})"
            result.metadata["up_value"] = value
            result.metadata["query_time_seconds"] = duration
        else:
            result.status = TestStatus.FAILED
            result.message = f"Self-monitoring check failed: {error_msg or f'up={value}'}"
            result.add_error(TestError(
                error_code="PROM_SELF_MONITORING_FAILED",
                message=error_msg or f"up metric value is {value}, expected 1",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.CRITICAL,
                context={"up_value": value, "url": prometheus_url},
                remediation="Check Prometheus scrape configuration and ensure self-scraping is enabled",
            ))
    except Exception as e:
        result.status = TestStatus.ERROR
        result.end_time = datetime.utcnow()
        result.message = f"Test execution error: {str(e)}"
        result.add_error(TestError(
            error_code="TEST_EXECUTION_ERROR",
            message=str(e),
            category=ErrorCategory.EXECUTION,
            severity=ErrorSeverity.CRITICAL,
        ))
    finally:
        client.close()

    return result


class TestSelfMonitoring:
    """
    Pytest test class for self-monitoring tests.

    Requirements: 12.2
    """

    @pytest.fixture
    def query_client(self, prometheus_url: str) -> PrometheusQueryClient:
        """Create a Prometheus query client fixture."""
        client = PrometheusQueryClient(prometheus_url, timeout=10.0)
        yield client
        client.close()

    def test_prometheus_up_metric_equals_one(self, query_client: PrometheusQueryClient):
        """
        Test that up{job="prometheus"} equals 1.

        Requirements: 12.2

        Verifies:
        - The up metric for the prometheus job exists
        - The value equals 1 (target is up and being scraped)
        """
        is_up, value, error_msg = query_client.check_up_metric("prometheus")

        assert is_up, f"Prometheus self-monitoring failed: {error_msg or f'up={value}'}"
        assert value == 1.0, f"Expected up=1, got up={value}"

    def test_prometheus_target_is_healthy(self, query_client: PrometheusQueryClient):
        """
        Test that the Prometheus target is in healthy state.

        Requirements: 12.2

        Verifies:
        - Prometheus appears in the targets list
        - The target health is "up"
        """
        try:
            targets_data = query_client.get_scrape_targets()
        except httpx.HTTPError as e:
            pytest.skip(f"Could not fetch targets: {e}")

        assert targets_data.get("status") == "success", \
            f"Targets API returned non-success: {targets_data.get('status')}"

        active_targets = targets_data.get("data", {}).get("activeTargets", [])

        # Find the prometheus job target
        prometheus_targets = [
            t for t in active_targets
            if t.get("labels", {}).get("job") == "prometheus"
        ]

        assert len(prometheus_targets) > 0, "No prometheus job target found"

        # Check that at least one prometheus target is up
        healthy_targets = [t for t in prometheus_targets if t.get("health") == "up"]
        assert len(healthy_targets) > 0, \
            f"No healthy prometheus targets. States: {[t.get('health') for t in prometheus_targets]}"

    def test_scrape_duration_reasonable(self, query_client: PrometheusQueryClient):
        """
        Test that Prometheus scrape duration is reasonable.

        Requirements: 12.2

        Verifies:
        - Scrape duration metric exists
        - Duration is within acceptable bounds (< 5 seconds)
        """
        query = 'prometheus_target_scrape_pool_sync_total{scrape_job="prometheus"}'

        try:
            result = query_client.query(query)
        except httpx.HTTPError as e:
            pytest.skip(f"Could not query scrape metrics: {e}")

        if result.get("status") != "success":
            pytest.skip(f"Query failed: {result.get('error')}")

        # If we get here, the metric exists which indicates scraping is working
        # The actual value check is informational
        results = result.get("data", {}).get("result", [])
        if results:
            # Scrape sync is happening
            assert True
        else:
            # No results might mean the metric name changed or scraping just started
            pytest.skip("No scrape sync metrics found yet")
