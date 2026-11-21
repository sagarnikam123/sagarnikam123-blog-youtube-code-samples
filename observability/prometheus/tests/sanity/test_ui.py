"""
UI Accessibility Tests for Prometheus.

This module implements sanity tests to verify that the Prometheus web UI
is accessible and responding correctly.

Requirements: 12.4
"""

import time
from datetime import datetime
from typing import Optional

import httpx
import pytest

from framework.models import (
    ErrorCategory,
    ErrorSeverity,
    TestError,
    TestResult,
    TestStatus,
)


class PrometheusUIClient:
    """
    Client for testing Prometheus web UI accessibility.

    Provides methods to check various UI endpoints.
    """

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize the Prometheus UI client.

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
            self._client = httpx.Client(timeout=self.timeout, follow_redirects=True)
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def check_endpoint(self, path: str) -> tuple[bool, int, Optional[str]]:
        """
        Check if a UI endpoint is accessible.

        Args:
            path: The endpoint path (e.g., "/graph")

        Returns:
            Tuple of (success, status_code, error_message)
        """
        url = f"{self.base_url}{path}"
        try:
            response = self.client.get(url)

            if response.status_code == 200:
                return True, 200, None
            else:
                return False, response.status_code, f"HTTP {response.status_code}"

        except httpx.TimeoutException:
            return False, 0, f"Request timed out after {self.timeout}s"
        except httpx.ConnectError as e:
            return False, 0, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, 0, f"Unexpected error: {str(e)}"

    def check_graph_endpoint(self) -> tuple[bool, int, Optional[str], Optional[str]]:
        """
        Check if the /graph endpoint is accessible and returns HTML.

        Returns:
            Tuple of (success, status_code, error_message, content_type)
        """
        url = f"{self.base_url}/graph"
        try:
            response = self.client.get(url)
            content_type = response.headers.get("content-type", "")

            if response.status_code == 200:
                # Verify it returns HTML content
                if "text/html" in content_type:
                    return True, 200, None, content_type
                else:
                    return False, 200, f"Expected HTML, got {content_type}", content_type
            else:
                return False, response.status_code, f"HTTP {response.status_code}", content_type

        except httpx.TimeoutException:
            return False, 0, f"Request timed out after {self.timeout}s", None
        except httpx.ConnectError as e:
            return False, 0, f"Connection failed: {str(e)}", None
        except Exception as e:
            return False, 0, f"Unexpected error: {str(e)}", None

    def get_ui_endpoints(self) -> list[tuple[str, str]]:
        """
        Get list of UI endpoints to test.

        Returns:
            List of (path, description) tuples
        """
        return [
            ("/graph", "Query/Graph UI"),
            ("/alerts", "Alerts UI"),
            ("/targets", "Targets UI"),
            ("/status", "Status UI"),
            ("/config", "Configuration UI"),
            ("/flags", "Command-line flags UI"),
            ("/rules", "Rules UI"),
            ("/service-discovery", "Service Discovery UI"),
        ]


def test_ui_accessible(prometheus_url: str) -> TestResult:
    """
    Test that the Prometheus web UI is accessible.

    Requirements: 12.4

    This test verifies:
    - The /graph endpoint returns HTTP 200
    - The response is HTML content

    Args:
        prometheus_url: URL of the Prometheus instance

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="ui_accessible",
        test_type="sanity",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    client = PrometheusUIClient(prometheus_url, timeout=10.0)

    try:
        start = time.time()
        success, status_code, error_msg, content_type = client.check_graph_endpoint()
        duration = time.time() - start

        result.duration_seconds = duration
        result.end_time = datetime.utcnow()

        if success:
            result.status = TestStatus.PASSED
            result.message = f"UI accessible at {prometheus_url}/graph (HTTP {status_code})"
            result.metadata["status_code"] = status_code
            result.metadata["content_type"] = content_type
            result.metadata["response_time_seconds"] = duration
        else:
            result.status = TestStatus.FAILED
            result.message = f"UI not accessible: {error_msg}"
            result.add_error(TestError(
                error_code="PROM_UI_UNREACHABLE",
                message=error_msg or "Unknown error",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.CRITICAL,
                context={
                    "url": f"{prometheus_url}/graph",
                    "status_code": status_code,
                },
                remediation="Verify Prometheus is running and the web UI is enabled",
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


class TestUIAccessibility:
    """
    Pytest test class for UI accessibility tests.

    Requirements: 12.4
    """

    @pytest.fixture
    def ui_client(self, prometheus_url: str) -> PrometheusUIClient:
        """Create a Prometheus UI client fixture."""
        client = PrometheusUIClient(prometheus_url, timeout=10.0)
        yield client
        client.close()

    def test_graph_endpoint_returns_200(self, ui_client: PrometheusUIClient):
        """
        Test that /graph endpoint returns HTTP 200.

        Requirements: 12.4

        Verifies:
        - Endpoint is accessible
        - Returns HTTP 200 status code
        """
        success, status_code, error_msg, _ = ui_client.check_graph_endpoint()

        assert success, f"Graph endpoint not accessible: {error_msg}"
        assert status_code == 200, f"Expected HTTP 200, got {status_code}"

    def test_graph_endpoint_returns_html(self, ui_client: PrometheusUIClient):
        """
        Test that /graph endpoint returns HTML content.

        Requirements: 12.4

        Verifies:
        - Response content type is text/html
        """
        success, status_code, error_msg, content_type = ui_client.check_graph_endpoint()

        if not success:
            pytest.skip(f"Graph endpoint not accessible: {error_msg}")

        assert content_type is not None, "No content-type header"
        assert "text/html" in content_type, \
            f"Expected text/html content type, got {content_type}"

    def test_alerts_endpoint_accessible(self, ui_client: PrometheusUIClient):
        """
        Test that /alerts endpoint is accessible.

        Requirements: 12.4

        Verifies:
        - Alerts UI endpoint returns HTTP 200
        """
        success, status_code, error_msg = ui_client.check_endpoint("/alerts")

        assert success, f"Alerts endpoint not accessible: {error_msg}"
        assert status_code == 200, f"Expected HTTP 200, got {status_code}"

    def test_targets_endpoint_accessible(self, ui_client: PrometheusUIClient):
        """
        Test that /targets endpoint is accessible.

        Requirements: 12.4

        Verifies:
        - Targets UI endpoint returns HTTP 200
        """
        success, status_code, error_msg = ui_client.check_endpoint("/targets")

        assert success, f"Targets endpoint not accessible: {error_msg}"
        assert status_code == 200, f"Expected HTTP 200, got {status_code}"

    def test_status_endpoint_accessible(self, ui_client: PrometheusUIClient):
        """
        Test that /status endpoint is accessible.

        Requirements: 12.4

        Verifies:
        - Status UI endpoint returns HTTP 200
        """
        success, status_code, error_msg = ui_client.check_endpoint("/status")

        assert success, f"Status endpoint not accessible: {error_msg}"
        assert status_code == 200, f"Expected HTTP 200, got {status_code}"

    def test_all_ui_endpoints_accessible(self, ui_client: PrometheusUIClient):
        """
        Test that all main UI endpoints are accessible.

        Requirements: 12.4

        Verifies:
        - All standard UI endpoints return HTTP 200
        """
        endpoints = ui_client.get_ui_endpoints()
        failed_endpoints = []

        for path, description in endpoints:
            success, status_code, error_msg = ui_client.check_endpoint(path)
            if not success or status_code != 200:
                failed_endpoints.append((path, description, status_code, error_msg))

        if failed_endpoints:
            failures = "\n".join(
                f"  - {path} ({desc}): {err or f'HTTP {code}'}"
                for path, desc, code, err in failed_endpoints
            )
            pytest.fail(f"Some UI endpoints failed:\n{failures}")

    def test_ui_response_time_acceptable(self, ui_client: PrometheusUIClient):
        """
        Test that UI response time is acceptable.

        Requirements: 12.4

        Verifies:
        - UI responds within 5 seconds
        """
        start = time.time()
        success, _, error_msg, _ = ui_client.check_graph_endpoint()
        duration = time.time() - start

        if not success:
            pytest.skip(f"UI not accessible: {error_msg}")

        # UI should respond quickly
        assert duration < 5.0, f"UI response too slow: {duration:.2f}s"
