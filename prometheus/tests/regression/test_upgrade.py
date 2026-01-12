"""
Unified upgrade regression tests for Prometheus.

This module provides a unified interface for running all regression tests
including version comparison, rule comparison, configuration compatibility,
and performance comparison.

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7
"""

from datetime import datetime
from typing import Optional

import pytest

from framework.models import (
    ErrorCategory,
    ErrorSeverity,
    TestError,
    TestResult,
    TestStatus,
)

from .config import (
    ConfigCompatibilityConfig,
    PerformanceComparisonConfig,
    RegressionTestConfig,
    RuleComparisonConfig,
)
from .models import (
    ComparisonStatus,
    PrometheusVersion,
    RegressionTestReport,
)
from .test_config_compatibility import ConfigCompatibilityTest
from .test_performance_comparison import PerformanceComparisonTest
from .test_rule_comparison import RuleComparisonTest
from .test_version_comparison import VersionComparisonTest


class FullRegressionTest:
    """
    Comprehensive regression test suite for Prometheus upgrades.

    This class runs all regression tests and produces a unified report
    covering query results, rules, configuration, and performance.

    Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7
    """

    def __init__(
        self,
        regression_config: RegressionTestConfig,
        rule_config: Optional[RuleComparisonConfig] = None,
        config_config: Optional[ConfigCompatibilityConfig] = None,
        perf_config: Optional[PerformanceComparisonConfig] = None,
    ):
        """Initialize the full regression test.

        Args:
            regression_config: Base regression test configuration
            rule_config: Rule comparison configuration
            config_config: Configuration compatibility settings
            perf_config: Performance comparison configuration
        """
        self.regression_config = regression_config
        self.rule_config = rule_config or RuleComparisonConfig()
        self.config_config = config_config or ConfigCompatibilityConfig()
        self.perf_config = perf_config or PerformanceComparisonConfig()

    def run(self) -> RegressionTestReport:
        """Run all regression tests.

        Returns:
            RegressionTestReport with combined results from all tests
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
            test_name="full_regression",
            baseline_version=baseline_version,
            target_version=target_version,
            start_time=datetime.utcnow(),
        )

        # Run version comparison tests
        version_test = VersionComparisonTest(self.regression_config)
        version_report = version_test.run()
        report.query_comparisons.extend(version_report.query_comparisons)

        # Run rule comparison tests
        rule_test = RuleComparisonTest(self.regression_config, self.rule_config)
        rule_report = rule_test.run()
        report.rule_comparisons.extend(rule_report.rule_comparisons)

        # Run configuration compatibility tests
        config_test = ConfigCompatibilityTest(self.regression_config, self.config_config)
        config_report = config_test.run()
        report.config_results.extend(config_report.config_results)

        # Run performance comparison tests
        perf_test = PerformanceComparisonTest(self.regression_config, self.perf_config)
        perf_report = perf_test.run()
        report.performance_comparisons.extend(perf_report.performance_comparisons)

        # Analyze all regressions
        report.analyze_regressions()
        report.end_time = datetime.utcnow()

        return report


def run_full_regression_test(
    baseline_url: str = "http://localhost:9090",
    target_url: str = "http://localhost:9091",
    baseline_version: str = "v3.4.0",
    target_version: str = "v3.5.0",
) -> TestResult:
    """
    Run full regression test suite and return a TestResult.

    Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7

    Args:
        baseline_url: URL of the baseline Prometheus instance
        target_url: URL of the target Prometheus instance
        baseline_version: Expected baseline version
        target_version: Expected target version

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="full_regression",
        test_type="regression",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    regression_config = RegressionTestConfig(
        baseline_version=baseline_version,
        baseline_url=baseline_url,
        target_version=target_version,
        target_url=target_url,
    )

    test = FullRegressionTest(regression_config)

    try:
        report = test.run()

        result.duration_seconds = report.duration_seconds
        result.end_time = datetime.utcnow()
        result.metadata["report"] = report.to_dict()

        summary = report.to_dict()["summary"]

        if report.passed:
            result.status = TestStatus.PASSED
            result.message = (
                f"Full regression test passed: "
                f"{summary['total_query_comparisons']} queries, "
                f"{summary['total_rule_comparisons']} rules, "
                f"{summary['total_config_checks']} configs, "
                f"{summary['total_performance_comparisons']} perf metrics compared"
            )
        else:
            result.status = TestStatus.FAILED
            result.message = (
                f"Full regression test failed: {len(report.regressions)} "
                f"regression(s) detected"
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


class TestUpgrade:
    """
    Pytest test class for upgrade regression tests.

    Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7
    """

    @pytest.fixture
    def regression_config(self) -> RegressionTestConfig:
        """Create a regression test configuration fixture."""
        return RegressionTestConfig()

    def test_full_regression_suite(self, regression_config: RegressionTestConfig):
        """
        Run the full regression test suite.

        Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7

        This test runs all regression checks and reports any detected
        regressions between the baseline and target versions.
        """
        test = FullRegressionTest(regression_config)
        report = test.run()

        # Report should complete without errors
        assert report.end_time is not None, "Test did not complete"

        # Check for regressions
        if not report.passed:
            regression_details = "\n".join(report.regressions)
            pytest.fail(
                f"Regressions detected:\n{regression_details}"
            )

    def test_no_query_regressions(self, regression_config: RegressionTestConfig):
        """
        Test that there are no query result regressions.

        Requirements: 21.1
        """
        test = VersionComparisonTest(regression_config)
        report = test.run()

        query_regressions = [
            qc for qc in report.query_comparisons
            if qc.status == ComparisonStatus.DIFFERENT
        ]

        assert not query_regressions, (
            f"Query regressions detected: "
            f"{[qc.query for qc in query_regressions]}"
        )

    def test_no_rule_regressions(self, regression_config: RegressionTestConfig):
        """
        Test that there are no rule regressions.

        Requirements: 21.2, 21.3
        """
        test = RuleComparisonTest(regression_config)
        report = test.run()

        rule_regressions = [
            rc for rc in report.rule_comparisons
            if rc.status == ComparisonStatus.DIFFERENT
        ]

        assert not rule_regressions, (
            f"Rule regressions detected: "
            f"{[rc.rule_name for rc in rule_regressions]}"
        )

    def test_no_config_regressions(self, regression_config: RegressionTestConfig):
        """
        Test that there are no configuration compatibility regressions.

        Requirements: 21.4, 21.5
        """
        test = ConfigCompatibilityTest(regression_config)
        report = test.run()

        config_regressions = [
            cr for cr in report.config_results
            if cr.status == ComparisonStatus.DIFFERENT
        ]

        assert not config_regressions, (
            f"Config regressions detected: "
            f"{[cr.config_name for cr in config_regressions]}"
        )

    def test_no_performance_regressions(self, regression_config: RegressionTestConfig):
        """
        Test that there are no significant performance regressions.

        Requirements: 21.6
        """
        test = PerformanceComparisonTest(regression_config)
        report = test.run()

        perf_regressions = [
            pc for pc in report.performance_comparisons
            if pc.status == ComparisonStatus.DIFFERENT
        ]

        assert not perf_regressions, (
            f"Performance regressions detected: "
            f"{[(pc.metric_name, f'{pc.difference_percent:.1f}%') for pc in perf_regressions]}"
        )
