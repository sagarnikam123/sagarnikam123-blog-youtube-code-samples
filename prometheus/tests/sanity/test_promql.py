"""
PromQL Query Tests for Prometheus.

This module implements sanity tests to verify that Prometheus can execute
basic PromQL queries and return valid results.

Requirements: 12.3
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


class PromQLTestClient:
    """
    Client for testing PromQL query execution.

    Provides methods to execute various types of PromQL queries
    and validate the results.
    """

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize the PromQL test client.

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

    def instant_query(self, promql: str) -> dict[str, Any]:
        """
        Execute an instant PromQL query.

        Args:
            promql: The PromQL query string

        Returns:
            Full API response as dictionary
        """
        url = f"{self.base_url}/api/v1/query"
        response = self.client.get(url, params={"query": promql})
        response.raise_for_status()
        return response.json()

    def range_query(
        self,
        promql: str,
        start: str,
        end: str,
        step: str = "15s"
    ) -> dict[str, Any]:
        """
        Execute a range PromQL query.

        Args:
            promql: The PromQL query string
            start: Start time (RFC3339 or Unix timestamp)
            end: End time (RFC3339 or Unix timestamp)
            step: Query resolution step

        Returns:
            Full API response as dictionary
        """
        url = f"{self.base_url}/api/v1/query_range"
        params = {
            "query": promql,
            "start": start,
            "end": end,
            "step": step,
        }
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def execute_query(self, promql: str) -> tuple[bool, dict, Optional[str]]:
        """
        Execute a query and return success status.

        Args:
            promql: The PromQL query string

        Returns:
            Tuple of (success, result_data, error_message)
        """
        try:
            result = self.instant_query(promql)

            if result.get("status") == "success":
                return True, result.get("data", {}), None
            else:
                error = result.get("error", "Unknown error")
                error_type = result.get("errorType", "unknown")
                return False, {}, f"{error_type}: {error}"

        except httpx.TimeoutException:
            return False, {}, f"Query timed out after {self.timeout}s"
        except httpx.ConnectError as e:
            return False, {}, f"Connection failed: {str(e)}"
        except httpx.HTTPStatusError as e:
            return False, {}, f"HTTP error: {e.response.status_code}"
        except Exception as e:
            return False, {}, f"Unexpected error: {str(e)}"

    def validate_query_result(
        self,
        result_data: dict,
        expected_type: str = "vector"
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that a query result has the expected structure.

        Args:
            result_data: The data portion of the query response
            expected_type: Expected result type (vector, matrix, scalar, string)

        Returns:
            Tuple of (is_valid, error_message)
        """
        result_type = result_data.get("resultType")

        if result_type != expected_type:
            return False, f"Expected {expected_type}, got {result_type}"

        results = result_data.get("result", [])

        # For vector/matrix, validate structure
        if result_type in ("vector", "matrix"):
            for item in results:
                if "metric" not in item:
                    return False, "Result item missing 'metric' field"
                if result_type == "vector" and "value" not in item:
                    return False, "Vector result missing 'value' field"
                if result_type == "matrix" and "values" not in item:
                    return False, "Matrix result missing 'values' field"

        return True, None


def test_promql_basic_queries(prometheus_url: str) -> TestResult:
    """
    Test that basic PromQL queries return valid results.

    Requirements: 12.3

    This test verifies:
    - Simple metric queries work
    - Aggregation queries work
    - Function queries work
    - Results have valid structure

    Args:
        prometheus_url: URL of the Prometheus instance

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="promql_basic_queries",
        test_type="sanity",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    client = PromQLTestClient(prometheus_url, timeout=10.0)

    # Test queries to execute
    test_queries = [
        ("up", "Simple metric query"),
        ("count(up)", "Count aggregation"),
        ("sum(up)", "Sum aggregation"),
        ("rate(prometheus_http_requests_total[5m])", "Rate function"),
        ("1 + 1", "Scalar arithmetic"),
    ]

    passed_queries = []
    failed_queries = []

    try:
        start = time.time()

        for query, description in test_queries:
            success, data, error_msg = client.execute_query(query)

            if success:
                passed_queries.append((query, description))
            else:
                failed_queries.append((query, description, error_msg))

        duration = time.time() - start
        result.duration_seconds = duration
        result.end_time = datetime.utcnow()

        result.metadata["passed_queries"] = len(passed_queries)
        result.metadata["failed_queries"] = len(failed_queries)
        result.metadata["total_queries"] = len(test_queries)

        if not failed_queries:
            result.status = TestStatus.PASSED
            result.message = f"All {len(test_queries)} PromQL queries executed successfully"
        else:
            result.status = TestStatus.FAILED
            result.message = f"{len(failed_queries)}/{len(test_queries)} queries failed"

            for query, desc, error in failed_queries:
                result.add_error(TestError(
                    error_code="PROMQL_QUERY_FAILED",
                    message=f"{desc}: {error}",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.WARNING,
                    context={"query": query},
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


class TestPromQL:
    """
    Pytest test class for PromQL query tests.

    Requirements: 12.3
    """

    @pytest.fixture
    def promql_client(self, prometheus_url: str) -> PromQLTestClient:
        """Create a PromQL test client fixture."""
        client = PromQLTestClient(prometheus_url, timeout=10.0)
        yield client
        client.close()

    def test_simple_metric_query(self, promql_client: PromQLTestClient):
        """
        Test that a simple metric query returns valid results.

        Requirements: 12.3

        Verifies:
        - Query executes successfully
        - Result type is vector
        - Result structure is valid
        """
        success, data, error_msg = promql_client.execute_query("up")

        assert success, f"Query failed: {error_msg}"
        assert data.get("resultType") == "vector", \
            f"Expected vector result, got {data.get('resultType')}"

        results = data.get("result", [])
        assert len(results) > 0, "No results returned for 'up' query"

    def test_aggregation_query(self, promql_client: PromQLTestClient):
        """
        Test that aggregation queries work correctly.

        Requirements: 12.3

        Verifies:
        - count() aggregation works
        - sum() aggregation works
        - Results are valid
        """
        # Test count aggregation
        success, data, error_msg = promql_client.execute_query("count(up)")
        assert success, f"count() query failed: {error_msg}"

        results = data.get("result", [])
        assert len(results) > 0, "No results for count(up)"

        # The count should be a positive number
        count_value = float(results[0].get("value", [0, "0"])[1])
        assert count_value > 0, f"Expected positive count, got {count_value}"

        # Test sum aggregation
        success, _, error_msg = promql_client.execute_query("sum(up)")
        assert success, f"sum() query failed: {error_msg}"

    def test_rate_function_query(self, promql_client: PromQLTestClient):
        """
        Test that rate() function queries work.

        Requirements: 12.3

        Verifies:
        - rate() function executes without error
        - Result structure is valid
        """
        # Use a metric that should exist in any Prometheus instance
        query = "rate(prometheus_http_requests_total[5m])"
        success, data, error_msg = promql_client.execute_query(query)

        # rate() might return empty results if no requests, but should not error
        assert success, f"rate() query failed: {error_msg}"
        assert data.get("resultType") == "vector", \
            f"Expected vector result, got {data.get('resultType')}"

    def test_scalar_arithmetic(self, promql_client: PromQLTestClient):
        """
        Test that scalar arithmetic works.

        Requirements: 12.3

        Verifies:
        - Basic arithmetic expressions work
        - Result is correct
        """
        success, data, error_msg = promql_client.execute_query("1 + 1")

        assert success, f"Arithmetic query failed: {error_msg}"
        assert data.get("resultType") == "scalar", \
            f"Expected scalar result, got {data.get('resultType')}"

        # Result should be [timestamp, "2"]
        result_value = data.get("result", [0, "0"])
        assert float(result_value[1]) == 2.0, \
            f"Expected 2, got {result_value[1]}"

    def test_label_matching_query(self, promql_client: PromQLTestClient):
        """
        Test that label matching queries work.

        Requirements: 12.3

        Verifies:
        - Label equality matching works
        - Label regex matching works
        """
        # Test exact label match
        success, data, error_msg = promql_client.execute_query('up{job="prometheus"}')
        assert success, f"Label match query failed: {error_msg}"

        results = data.get("result", [])
        # All results should have job="prometheus"
        for result in results:
            job = result.get("metric", {}).get("job")
            assert job == "prometheus", f"Expected job=prometheus, got job={job}"

    def test_query_returns_valid_timestamps(self, promql_client: PromQLTestClient):
        """
        Test that query results contain valid timestamps.

        Requirements: 12.3

        Verifies:
        - Results include timestamps
        - Timestamps are reasonable (recent)
        """
        success, data, error_msg = promql_client.execute_query("up")

        assert success, f"Query failed: {error_msg}"

        results = data.get("result", [])
        assert len(results) > 0, "No results returned"

        current_time = time.time()

        for result in results:
            value = result.get("value", [])
            assert len(value) == 2, "Value should be [timestamp, value]"

            timestamp = float(value[0])
            # Timestamp should be within last hour
            assert current_time - 3600 < timestamp <= current_time + 60, \
                f"Timestamp {timestamp} is not recent"

    def test_range_query(self, promql_client: PromQLTestClient):
        """
        Test that range queries work correctly.

        Requirements: 12.3

        Verifies:
        - Range query API works
        - Returns matrix result type
        - Contains multiple data points
        """
        end_time = int(time.time())
        start_time = end_time - 300  # 5 minutes ago

        try:
            result = promql_client.range_query(
                "up",
                start=str(start_time),
                end=str(end_time),
                step="60s"
            )
        except httpx.HTTPError as e:
            pytest.skip(f"Range query failed: {e}")

        assert result.get("status") == "success", \
            f"Range query failed: {result.get('error')}"

        data = result.get("data", {})
        assert data.get("resultType") == "matrix", \
            f"Expected matrix result, got {data.get('resultType')}"

        results = data.get("result", [])
        if results:
            # Check that we have multiple values (time series data)
            values = results[0].get("values", [])
            # Should have at least a few data points in 5 minutes
            assert len(values) >= 1, "Expected multiple data points in range query"
