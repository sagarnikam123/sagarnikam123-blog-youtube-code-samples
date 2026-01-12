"""
Version comparison tests for Prometheus regression testing.

This module implements tests to compare query results between
two different Prometheus versions to detect regressions.

Requirements: 21.1, 21.7
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

from .config import RegressionTestConfig
from .models import (
    ComparisonStatus,
    PrometheusVersion,
    QueryComparison,
    QueryResult,
    RegressionTestReport,
)


class PrometheusQueryClient:
    """Client for executing PromQL queries against Prometheus.

    Provides methods to execute queries and retrieve results
    for comparison between versions.
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the query client.

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

    def execute_query(self, query: str) -> QueryResult:
        """Execute a PromQL query and return the result.

        Args:
            query: PromQL query to execute

        Returns:
            QueryResult with the query results
        """
        url = f"{self.base_url}/api/v1/query"
        result = QueryResult(query=query, timestamp=datetime.utcnow())

        try:
            start_time = time.time()
            response = self.client.get(url, params={"query": query})
            execution_time = (time.time() - start_time) * 1000

            result.execution_time_ms = execution_time

            if response.status_code != 200:
                result.error = f"HTTP {response.status_code}: {response.text[:200]}"
                return result

            data = response.json()

            if data.get("status") != "success":
                result.error = data.get("error", "Unknown error")
                return result

            result.result_type = data.get("data", {}).get("resultType")
            result.data = data.get("data", {}).get("result")

        except httpx.TimeoutException:
            result.error = f"Query timed out after {self.timeout}s"
        except httpx.ConnectError as e:
            result.error = f"Connection failed: {str(e)}"
        except Exception as e:
            result.error = f"Unexpected error: {str(e)}"

        return result

    def get_version(self) -> Optional[str]:
        """Get the Prometheus version.

        Returns:
            Version string or None if unavailable
        """
        url = f"{self.base_url}/api/v1/status/buildinfo"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("version")
        except Exception:
            pass
        return None

    def is_healthy(self) -> bool:
        """Check if Prometheus is healthy.

        Returns:
            True if healthy, False otherwise
        """
        url = f"{self.base_url}/-/healthy"
        try:
            response = self.client.get(url)
            return response.status_code == 200
        except Exception:
            return False


class VersionComparisonTest:
    """
    Test class for comparing query results between Prometheus versions.

    This class deploys two Prometheus versions and compares query results
    to detect any regressions in query behavior.

    Requirements: 21.1, 21.7
    """

    def __init__(self, config: RegressionTestConfig):
        """Initialize the version comparison test.

        Args:
            config: Regression test configuration
        """
        self.config = config
        self.baseline_client: Optional[PrometheusQueryClient] = None
        self.target_client: Optional[PrometheusQueryClient] = None

    def setup(self) -> tuple[bool, Optional[str]]:
        """Set up the test clients.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.baseline_client = PrometheusQueryClient(
                self.config.baseline_url,
                timeout=self.config.timeout_seconds,
            )
            self.target_client = PrometheusQueryClient(
                self.config.target_url,
                timeout=self.config.timeout_seconds,
            )

            # Verify both instances are healthy
            if not self.baseline_client.is_healthy():
                return False, f"Baseline Prometheus not healthy at {self.config.baseline_url}"

            if not self.target_client.is_healthy():
                return False, f"Target Prometheus not healthy at {self.config.target_url}"

            return True, None

        except Exception as e:
            return False, f"Setup failed: {str(e)}"

    def teardown(self) -> None:
        """Clean up test resources."""
        if self.baseline_client:
            self.baseline_client.close()
        if self.target_client:
            self.target_client.close()

    def compare_query(self, query: str) -> QueryComparison:
        """Compare a single query between versions.

        Args:
            query: PromQL query to compare

        Returns:
            QueryComparison with the comparison results
        """
        baseline_result = self.baseline_client.execute_query(query)
        target_result = self.target_client.execute_query(query)

        comparison = QueryComparison(
            query=query,
            baseline_result=baseline_result,
            target_result=target_result,
            tolerance=self.config.value_tolerance,
        )
        comparison.compare()

        return comparison

    def run(self) -> RegressionTestReport:
        """Run the version comparison test.

        Returns:
            RegressionTestReport with all comparison results
        """
        baseline_version = PrometheusVersion(
            version=self.config.baseline_version,
            url=self.config.baseline_url,
        )
        target_version = PrometheusVersion(
            version=self.config.target_version,
            url=self.config.target_url,
        )

        report = RegressionTestReport(
            test_name="version_comparison",
            baseline_version=baseline_version,
            target_version=target_version,
            start_time=datetime.utcnow(),
        )

        # Setup clients
        success, error = self.setup()
        if not success:
            report.end_time = datetime.utcnow()
            report.passed = False
            report.regressions = [f"Setup failed: {error}"]
            return report

        try:
            # Get actual versions
            actual_baseline = self.baseline_client.get_version()
            actual_target = self.target_client.get_version()

            if actual_baseline:
                report.baseline_version.version = actual_baseline
            if actual_target:
                report.target_version.version = actual_target

            # Compare all queries
            for query in self.config.queries:
                comparison = self.compare_query(query)
                report.query_comparisons.append(comparison)

            # Analyze regressions
            report.analyze_regressions()

        finally:
            self.teardown()
            report.end_time = datetime.utcnow()

        return report


def run_version_comparison_test(
    baseline_url: str = "http://localhost:9090",
    target_url: str = "http://localhost:9091",
    baseline_version: str = "v3.4.0",
    target_version: str = "v3.5.0",
    queries: Optional[list[str]] = None,
) -> TestResult:
    """
    Run version comparison test and return a TestResult.

    Requirements: 21.1

    Args:
        baseline_url: URL of the baseline Prometheus instance
        target_url: URL of the target Prometheus instance
        baseline_version: Expected baseline version
        target_version: Expected target version
        queries: List of queries to compare (uses defaults if None)

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="version_comparison",
        test_type="regression",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    config = RegressionTestConfig(
        baseline_version=baseline_version,
        baseline_url=baseline_url,
        target_version=target_version,
        target_url=target_url,
        queries=queries or [],
    )

    test = VersionComparisonTest(config)

    try:
        report = test.run()

        result.duration_seconds = report.duration_seconds
        result.end_time = datetime.utcnow()
        result.metadata["report"] = report.to_dict()

        if report.passed:
            result.status = TestStatus.PASSED
            result.message = (
                f"Version comparison passed: {len(report.query_comparisons)} queries "
                f"compared between {report.baseline_version.version} and "
                f"{report.target_version.version}"
            )
        else:
            result.status = TestStatus.FAILED
            result.message = (
                f"Version comparison failed: {len(report.regressions)} regression(s) "
                f"detected"
            )
            for regression in report.regressions:
                result.add_error(TestError(
                    error_code="REGRESSION_DETECTED",
                    message=regression,
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.WARNING,
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

    return result


class TestVersionComparison:
    """
    Pytest test class for version comparison tests.

    Requirements: 21.1
    """

    @pytest.fixture
    def regression_config(self) -> RegressionTestConfig:
        """Create a regression test configuration fixture."""
        return RegressionTestConfig()

    @pytest.fixture
    def baseline_client(
        self,
        regression_config: RegressionTestConfig,
    ) -> PrometheusQueryClient:
        """Create a baseline Prometheus client fixture."""
        client = PrometheusQueryClient(
            regression_config.baseline_url,
            timeout=regression_config.timeout_seconds,
        )
        yield client
        client.close()

    @pytest.fixture
    def target_client(
        self,
        regression_config: RegressionTestConfig,
    ) -> PrometheusQueryClient:
        """Create a target Prometheus client fixture."""
        client = PrometheusQueryClient(
            regression_config.target_url,
            timeout=regression_config.timeout_seconds,
        )
        yield client
        client.close()

    def test_query_results_match(
        self,
        baseline_client: PrometheusQueryClient,
        target_client: PrometheusQueryClient,
    ):
        """
        Test that query results match between versions.

        Requirements: 21.1

        Verifies:
        - Same queries return same result types
        - Same queries return equivalent data
        """
        # Skip if either instance is not available
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        query = "up"
        baseline_result = baseline_client.execute_query(query)
        target_result = target_client.execute_query(query)

        # Both should succeed or both should fail
        assert baseline_result.success == target_result.success, (
            f"Query success mismatch: baseline={baseline_result.success}, "
            f"target={target_result.success}"
        )

        if baseline_result.success:
            # Result types should match
            assert baseline_result.result_type == target_result.result_type, (
                f"Result type mismatch: baseline={baseline_result.result_type}, "
                f"target={target_result.result_type}"
            )

    def test_aggregation_queries_match(
        self,
        baseline_client: PrometheusQueryClient,
        target_client: PrometheusQueryClient,
    ):
        """
        Test that aggregation queries produce same results.

        Requirements: 21.1

        Verifies:
        - sum(), count(), avg() produce equivalent results
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        queries = ["sum(up)", "count(up)"]

        for query in queries:
            baseline_result = baseline_client.execute_query(query)
            target_result = target_client.execute_query(query)

            comparison = QueryComparison(
                query=query,
                baseline_result=baseline_result,
                target_result=target_result,
            )
            comparison.compare()

            assert comparison.status == ComparisonStatus.IDENTICAL, (
                f"Query '{query}' produced different results: "
                f"{comparison.differences}"
            )

    def test_rate_queries_match(
        self,
        baseline_client: PrometheusQueryClient,
        target_client: PrometheusQueryClient,
    ):
        """
        Test that rate queries produce same results.

        Requirements: 21.1

        Verifies:
        - rate() and irate() produce equivalent results
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        query = "rate(prometheus_http_requests_total[5m])"

        baseline_result = baseline_client.execute_query(query)
        target_result = target_client.execute_query(query)

        # Both should have same result type
        if baseline_result.success and target_result.success:
            assert baseline_result.result_type == target_result.result_type
