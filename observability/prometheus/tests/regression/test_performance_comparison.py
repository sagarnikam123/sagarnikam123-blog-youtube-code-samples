"""
Performance comparison tests for Prometheus regression testing.

This module implements tests to compare performance metrics between
two different Prometheus versions to detect performance regressions.

Requirements: 21.6, 21.7
"""

import statistics
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

from .config import PerformanceComparisonConfig, RegressionTestConfig
from .models import (
    ComparisonStatus,
    PerformanceComparison,
    PrometheusVersion,
    RegressionTestReport,
)


class PrometheusPerformanceClient:
    """Client for measuring Prometheus performance metrics.

    Provides methods to measure query latency, resource usage,
    and other performance indicators.
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the performance client.

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

    def is_healthy(self) -> bool:
        """Check if Prometheus is healthy."""
        url = f"{self.base_url}/-/healthy"
        try:
            response = self.client.get(url)
            return response.status_code == 200
        except Exception:
            return False

    def measure_query_latency(
        self,
        query: str,
        iterations: int = 10,
    ) -> dict[str, float]:
        """Measure query latency over multiple iterations.

        Args:
            query: PromQL query to execute
            iterations: Number of iterations

        Returns:
            Dictionary with latency statistics (p50, p90, p99, avg)
        """
        url = f"{self.base_url}/api/v1/query"
        latencies = []

        for _ in range(iterations):
            try:
                start = time.time()
                response = self.client.get(url, params={"query": query})
                latency = (time.time() - start) * 1000  # Convert to ms

                if response.status_code == 200:
                    latencies.append(latency)
            except Exception:
                pass

        if not latencies:
            return {"p50": 0, "p90": 0, "p99": 0, "avg": 0, "min": 0, "max": 0}

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        return {
            "p50": sorted_latencies[int(n * 0.50)],
            "p90": sorted_latencies[int(n * 0.90)] if n > 1 else sorted_latencies[0],
            "p99": sorted_latencies[min(int(n * 0.99), n - 1)],
            "avg": statistics.mean(latencies),
            "min": min(latencies),
            "max": max(latencies),
        }

    def get_scrape_duration(self) -> Optional[float]:
        """Get average scrape duration.

        Returns:
            Average scrape duration in seconds or None
        """
        url = f"{self.base_url}/api/v1/query"
        try:
            response = self.client.get(
                url,
                params={"query": "avg(scrape_duration_seconds)"},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])
                    if results:
                        return float(results[0].get("value", [0, 0])[1])
        except Exception:
            pass
        return None

    def get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in bytes.

        Returns:
            Memory usage in bytes or None
        """
        url = f"{self.base_url}/api/v1/query"
        try:
            response = self.client.get(
                url,
                params={"query": "process_resident_memory_bytes"},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])
                    if results:
                        return float(results[0].get("value", [0, 0])[1])
        except Exception:
            pass
        return None

    def get_cpu_usage(self) -> Optional[float]:
        """Get CPU usage percentage.

        Returns:
            CPU usage percentage or None
        """
        url = f"{self.base_url}/api/v1/query"
        try:
            response = self.client.get(
                url,
                params={"query": "rate(process_cpu_seconds_total[1m]) * 100"},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])
                    if results:
                        return float(results[0].get("value", [0, 0])[1])
        except Exception:
            pass
        return None

    def get_head_series_count(self) -> Optional[int]:
        """Get the number of head series.

        Returns:
            Number of head series or None
        """
        url = f"{self.base_url}/api/v1/query"
        try:
            response = self.client.get(
                url,
                params={"query": "prometheus_tsdb_head_series"},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])
                    if results:
                        return int(float(results[0].get("value", [0, 0])[1]))
        except Exception:
            pass
        return None

    def collect_all_metrics(self, iterations: int = 10) -> dict[str, float]:
        """Collect all performance metrics.

        Args:
            iterations: Number of iterations for latency measurements

        Returns:
            Dictionary of all performance metrics
        """
        metrics = {}

        # Query latency for simple query
        simple_latency = self.measure_query_latency("up", iterations)
        metrics["query_latency_simple_p50"] = simple_latency["p50"]
        metrics["query_latency_simple_p90"] = simple_latency["p90"]
        metrics["query_latency_simple_p99"] = simple_latency["p99"]

        # Query latency for complex query
        complex_latency = self.measure_query_latency(
            "sum by (job) (rate(prometheus_http_requests_total[5m]))",
            iterations,
        )
        metrics["query_latency_complex_p50"] = complex_latency["p50"]
        metrics["query_latency_complex_p90"] = complex_latency["p90"]
        metrics["query_latency_complex_p99"] = complex_latency["p99"]

        # Resource metrics
        scrape_duration = self.get_scrape_duration()
        if scrape_duration is not None:
            metrics["scrape_duration_avg"] = scrape_duration * 1000  # Convert to ms

        memory_usage = self.get_memory_usage()
        if memory_usage is not None:
            metrics["memory_usage_bytes"] = memory_usage

        cpu_usage = self.get_cpu_usage()
        if cpu_usage is not None:
            metrics["cpu_usage_percent"] = cpu_usage

        head_series = self.get_head_series_count()
        if head_series is not None:
            metrics["head_series_count"] = float(head_series)

        return metrics


class PerformanceComparisonTest:
    """
    Test class for comparing performance metrics between Prometheus versions.

    This class measures and compares performance metrics to detect
    any performance regressions after upgrades.

    Requirements: 21.6, 21.7
    """

    def __init__(
        self,
        regression_config: RegressionTestConfig,
        perf_config: Optional[PerformanceComparisonConfig] = None,
    ):
        """Initialize the performance comparison test.

        Args:
            regression_config: Regression test configuration
            perf_config: Performance comparison configuration
        """
        self.regression_config = regression_config
        self.perf_config = perf_config or PerformanceComparisonConfig()
        self.baseline_client: Optional[PrometheusPerformanceClient] = None
        self.target_client: Optional[PrometheusPerformanceClient] = None

    def setup(self) -> tuple[bool, Optional[str]]:
        """Set up the test clients.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.baseline_client = PrometheusPerformanceClient(
                self.regression_config.baseline_url,
                timeout=self.regression_config.timeout_seconds,
            )
            self.target_client = PrometheusPerformanceClient(
                self.regression_config.target_url,
                timeout=self.regression_config.timeout_seconds,
            )

            if not self.baseline_client.is_healthy():
                return False, f"Baseline Prometheus not healthy"

            if not self.target_client.is_healthy():
                return False, f"Target Prometheus not healthy"

            return True, None

        except Exception as e:
            return False, f"Setup failed: {str(e)}"

    def teardown(self) -> None:
        """Clean up test resources."""
        if self.baseline_client:
            self.baseline_client.close()
        if self.target_client:
            self.target_client.close()

    def compare_metrics(self) -> list[PerformanceComparison]:
        """Compare performance metrics between versions.

        Returns:
            List of PerformanceComparison results
        """
        comparisons = []

        # Collect metrics from both instances
        baseline_metrics = self.baseline_client.collect_all_metrics(
            iterations=self.perf_config.iterations
        )
        target_metrics = self.target_client.collect_all_metrics(
            iterations=self.perf_config.iterations
        )

        # Determine which metrics to compare
        metric_names = set(baseline_metrics.keys()) & set(target_metrics.keys())
        if self.perf_config.metrics:
            metric_names = set(self.perf_config.metrics) & metric_names

        # Define units for metrics
        units = {
            "query_latency_simple_p50": "ms",
            "query_latency_simple_p90": "ms",
            "query_latency_simple_p99": "ms",
            "query_latency_complex_p50": "ms",
            "query_latency_complex_p90": "ms",
            "query_latency_complex_p99": "ms",
            "scrape_duration_avg": "ms",
            "memory_usage_bytes": "bytes",
            "cpu_usage_percent": "%",
            "head_series_count": "count",
        }

        for metric_name in metric_names:
            baseline_value = baseline_metrics.get(metric_name, 0)
            target_value = target_metrics.get(metric_name, 0)

            comparison = PerformanceComparison(
                metric_name=metric_name,
                baseline_value=baseline_value,
                target_value=target_value,
                unit=units.get(metric_name, ""),
                threshold_percent=self.perf_config.threshold_percent,
            )
            comparison.compare()

            comparisons.append(comparison)

        return comparisons

    def run(self) -> RegressionTestReport:
        """Run the performance comparison test.

        Returns:
            RegressionTestReport with all comparison results
        """
        baseline_version = PrometheusVersion(
            version=self.regression_config.baseline_version,
            url=self.regression_config.baseline_url,
        )
        target_version = PrometheusVersion(
            version=self.regression_config.target_version,
            url=self.regression_config.target_url,
        )

        report = RegressionTestReport(
            test_name="performance_comparison",
            baseline_version=baseline_version,
            target_version=target_version,
            start_time=datetime.utcnow(),
        )

        success, error = self.setup()
        if not success:
            report.end_time = datetime.utcnow()
            report.passed = False
            report.regressions = [f"Setup failed: {error}"]
            return report

        try:
            # Compare performance metrics
            comparisons = self.compare_metrics()
            report.performance_comparisons = comparisons

            # Analyze regressions
            report.analyze_regressions()

        finally:
            self.teardown()
            report.end_time = datetime.utcnow()

        return report


def run_performance_comparison_test(
    baseline_url: str = "http://localhost:9090",
    target_url: str = "http://localhost:9091",
    baseline_version: str = "v3.4.0",
    target_version: str = "v3.5.0",
    threshold_percent: float = 10.0,
    iterations: int = 10,
) -> TestResult:
    """
    Run performance comparison test and return a TestResult.

    Requirements: 21.6

    Args:
        baseline_url: URL of the baseline Prometheus instance
        target_url: URL of the target Prometheus instance
        baseline_version: Expected baseline version
        target_version: Expected target version
        threshold_percent: Acceptable performance difference threshold
        iterations: Number of iterations for latency measurements

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="performance_comparison",
        test_type="regression",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    regression_config = RegressionTestConfig(
        baseline_version=baseline_version,
        baseline_url=baseline_url,
        target_version=target_version,
        target_url=target_url,
        performance_threshold_percent=threshold_percent,
    )

    perf_config = PerformanceComparisonConfig(
        threshold_percent=threshold_percent,
        iterations=iterations,
    )

    test = PerformanceComparisonTest(regression_config, perf_config)

    try:
        report = test.run()

        result.duration_seconds = report.duration_seconds
        result.end_time = datetime.utcnow()
        result.metadata["report"] = report.to_dict()

        if report.passed:
            result.status = TestStatus.PASSED
            result.message = (
                f"Performance comparison passed: "
                f"{len(report.performance_comparisons)} metrics compared"
            )
        else:
            result.status = TestStatus.FAILED
            result.message = (
                f"Performance comparison failed: {len(report.regressions)} "
                f"regression(s) detected"
            )
            for regression in report.regressions:
                result.add_error(TestError(
                    error_code="PERFORMANCE_REGRESSION_DETECTED",
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


class TestPerformanceComparison:
    """
    Pytest test class for performance comparison tests.

    Requirements: 21.6
    """

    @pytest.fixture
    def regression_config(self) -> RegressionTestConfig:
        """Create a regression test configuration fixture."""
        return RegressionTestConfig()

    @pytest.fixture
    def baseline_client(
        self,
        regression_config: RegressionTestConfig,
    ) -> PrometheusPerformanceClient:
        """Create a baseline Prometheus performance client fixture."""
        client = PrometheusPerformanceClient(
            regression_config.baseline_url,
            timeout=regression_config.timeout_seconds,
        )
        yield client
        client.close()

    @pytest.fixture
    def target_client(
        self,
        regression_config: RegressionTestConfig,
    ) -> PrometheusPerformanceClient:
        """Create a target Prometheus performance client fixture."""
        client = PrometheusPerformanceClient(
            regression_config.target_url,
            timeout=regression_config.timeout_seconds,
        )
        yield client
        client.close()

    def test_query_latency_not_degraded(
        self,
        baseline_client: PrometheusPerformanceClient,
        target_client: PrometheusPerformanceClient,
    ):
        """
        Test that query latency has not degraded after upgrade.

        Requirements: 21.6

        Verifies:
        - Query latency p99 is within acceptable threshold
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        query = "up"
        iterations = 10
        threshold_percent = 20.0  # Allow 20% degradation

        baseline_latency = baseline_client.measure_query_latency(query, iterations)
        target_latency = target_client.measure_query_latency(query, iterations)

        if baseline_latency["p99"] > 0:
            degradation = (
                (target_latency["p99"] - baseline_latency["p99"]) /
                baseline_latency["p99"] * 100
            )

            assert degradation < threshold_percent, (
                f"Query latency degraded by {degradation:.1f}% "
                f"(baseline p99: {baseline_latency['p99']:.2f}ms, "
                f"target p99: {target_latency['p99']:.2f}ms)"
            )

    def test_memory_usage_not_increased_significantly(
        self,
        baseline_client: PrometheusPerformanceClient,
        target_client: PrometheusPerformanceClient,
    ):
        """
        Test that memory usage has not increased significantly.

        Requirements: 21.6

        Verifies:
        - Memory usage is within acceptable threshold
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        threshold_percent = 25.0  # Allow 25% increase

        baseline_memory = baseline_client.get_memory_usage()
        target_memory = target_client.get_memory_usage()

        if baseline_memory is None or target_memory is None:
            pytest.skip("Memory metrics not available")

        if baseline_memory > 0:
            increase = (target_memory - baseline_memory) / baseline_memory * 100

            assert increase < threshold_percent, (
                f"Memory usage increased by {increase:.1f}% "
                f"(baseline: {baseline_memory / 1024 / 1024:.1f}MB, "
                f"target: {target_memory / 1024 / 1024:.1f}MB)"
            )

    def test_scrape_duration_not_degraded(
        self,
        baseline_client: PrometheusPerformanceClient,
        target_client: PrometheusPerformanceClient,
    ):
        """
        Test that scrape duration has not degraded.

        Requirements: 21.6

        Verifies:
        - Average scrape duration is within acceptable threshold
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        threshold_percent = 20.0

        baseline_duration = baseline_client.get_scrape_duration()
        target_duration = target_client.get_scrape_duration()

        if baseline_duration is None or target_duration is None:
            pytest.skip("Scrape duration metrics not available")

        if baseline_duration > 0:
            degradation = (target_duration - baseline_duration) / baseline_duration * 100

            assert degradation < threshold_percent, (
                f"Scrape duration degraded by {degradation:.1f}% "
                f"(baseline: {baseline_duration * 1000:.2f}ms, "
                f"target: {target_duration * 1000:.2f}ms)"
            )

    def test_complex_query_performance(
        self,
        baseline_client: PrometheusPerformanceClient,
        target_client: PrometheusPerformanceClient,
    ):
        """
        Test that complex query performance has not degraded.

        Requirements: 21.6

        Verifies:
        - Complex query latency is within acceptable threshold
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        query = "sum by (job) (rate(prometheus_http_requests_total[5m]))"
        iterations = 10
        threshold_percent = 25.0

        baseline_latency = baseline_client.measure_query_latency(query, iterations)
        target_latency = target_client.measure_query_latency(query, iterations)

        if baseline_latency["p99"] > 0:
            degradation = (
                (target_latency["p99"] - baseline_latency["p99"]) /
                baseline_latency["p99"] * 100
            )

            assert degradation < threshold_percent, (
                f"Complex query latency degraded by {degradation:.1f}% "
                f"(baseline p99: {baseline_latency['p99']:.2f}ms, "
                f"target p99: {target_latency['p99']:.2f}ms)"
            )
