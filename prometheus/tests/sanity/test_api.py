"""
API Accessibility Tests for Prometheus.

This module implements sanity tests to verify that the Prometheus HTTP API
is accessible and responding correctly.

Requirements: 12.1
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


class PrometheusAPIClient:
    """
    Client for interacting with the Prometheus HTTP API.

    Provides methods to check API accessibility and execute queries.
    """

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize the Prometheus API client.

        Args:
            base_url: Base URL of the Prometheus instance (e.g., http://localhost:9090)
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

    def check_api_accessible(self) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        Check if the Prometheus API is accessible.

        Verifies the /api/v1/status/config endpoint is reachable and returns
        a valid response.

        Returns:
            Tuple of (success, response_data, error_message)
        """
        url = f"{self.base_url}/api/v1/status/config"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return True, data, None
                return False, data, f"API returned non-success status: {data.get('status')}"
            return False, None, f"HTTP {response.status_code}: {response.text[:200]}"
        except httpx.TimeoutException:
            return False, None, f"Request timed out after {self.timeout}s"
        except httpx.ConnectError as e:
            return False, None, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"

    def get_status_config(self) -> dict:
        """
        Get the Prometheus configuration status.

        Returns:
            Configuration data from /api/v1/status/config

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/api/v1/status/config"
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()


def test_api_accessible(prometheus_url: str) -> TestResult:
    """
    Test that the Prometheus HTTP API is accessible.

    Requirements: 12.1

    This test verifies:
    - The /api/v1/status/config endpoint is reachable
    - The response is received within the timeout period
    - The response indicates success

    Args:
        prometheus_url: URL of the Prometheus instance

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="api_accessible",
        test_type="sanity",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    client = PrometheusAPIClient(prometheus_url, timeout=10.0)

    try:
        start = time.time()
        success, data, error_msg = client.check_api_accessible()
        duration = time.time() - start

        result.duration_seconds = duration
        result.end_time = datetime.utcnow()

        if success:
            result.status = TestStatus.PASSED
            result.message = f"API accessible at {prometheus_url} (response time: {duration:.3f}s)"
            result.metadata["response_time_seconds"] = duration
            result.metadata["config_yaml_length"] = len(data.get("data", {}).get("yaml", ""))
        else:
            result.status = TestStatus.FAILED
            result.message = f"API not accessible: {error_msg}"
            result.add_error(TestError(
                error_code="PROM_API_UNREACHABLE",
                message=error_msg or "Unknown error",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.CRITICAL,
                context={"url": prometheus_url},
                remediation="Verify Prometheus is running and accessible at the specified URL",
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


class TestAPIAccessibility:
    """
    Pytest test class for API accessibility tests.

    Requirements: 12.1
    """

    @pytest.fixture
    def api_client(self, prometheus_url: str) -> PrometheusAPIClient:
        """Create a Prometheus API client fixture."""
        client = PrometheusAPIClient(prometheus_url, timeout=10.0)
        yield client
        client.close()

    def test_status_config_endpoint_accessible(self, api_client: PrometheusAPIClient):
        """
        Test that /api/v1/status/config endpoint is accessible.

        Requirements: 12.1

        Verifies:
        - Endpoint returns HTTP 200
        - Response contains valid JSON
        - Response status is "success"
        """
        success, data, error_msg = api_client.check_api_accessible()

        assert success, f"API not accessible: {error_msg}"
        assert data is not None, "No response data received"
        assert data.get("status") == "success", f"Unexpected status: {data.get('status')}"

    def test_api_response_within_timeout(self, api_client: PrometheusAPIClient):
        """
        Test that API responds within the configured timeout.

        Requirements: 12.1

        Verifies:
        - Response is received within 10 seconds
        """
        start = time.time()
        success, _, error_msg = api_client.check_api_accessible()
        duration = time.time() - start

        # Should respond within timeout (10s) with some margin
        assert duration < 10.0, f"Response took too long: {duration:.2f}s"

        if success:
            # If successful, should be much faster
            assert duration < 5.0, f"Response slower than expected: {duration:.2f}s"

    def test_config_endpoint_returns_yaml(self, api_client: PrometheusAPIClient):
        """
        Test that the config endpoint returns YAML configuration.

        Requirements: 12.1

        Verifies:
        - Response contains configuration data
        - Configuration includes YAML content
        """
        success, data, error_msg = api_client.check_api_accessible()

        if not success:
            pytest.skip(f"API not accessible: {error_msg}")

        assert "data" in data, "Response missing 'data' field"
        assert "yaml" in data["data"], "Response missing YAML configuration"

        yaml_content = data["data"]["yaml"]
        assert len(yaml_content) > 0, "YAML configuration is empty"
        assert "global:" in yaml_content or "scrape_configs:" in yaml_content, \
            "YAML doesn't appear to be valid Prometheus configuration"
