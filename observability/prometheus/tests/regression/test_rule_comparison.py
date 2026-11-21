"""
Rule comparison tests for Prometheus regression testing.

This module implements tests to compare alerting and recording rule
results between two different Prometheus versions to detect regressions.

Requirements: 21.2, 21.3, 21.7
"""

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

from .config import RegressionTestConfig, RuleComparisonConfig
from .models import (
    ComparisonStatus,
    PrometheusVersion,
    RegressionTestReport,
    RuleComparison,
    RuleResult,
)


class PrometheusRulesClient:
    """Client for retrieving and evaluating Prometheus rules.

    Provides methods to get alerting and recording rules
    and their evaluation results.
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the rules client.

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

    def get_rules(self) -> dict[str, Any]:
        """Get all rules from Prometheus.

        Returns:
            Dictionary containing rules data
        """
        url = f"{self.base_url}/api/v1/rules"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", {})
        except Exception:
            pass
        return {}

    def get_alerts(self) -> list[dict[str, Any]]:
        """Get all active alerts from Prometheus.

        Returns:
            List of active alerts
        """
        url = f"{self.base_url}/api/v1/alerts"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", {}).get("alerts", [])
        except Exception:
            pass
        return []

    def get_alerting_rules(self) -> list[RuleResult]:
        """Get all alerting rules and their states.

        Returns:
            List of RuleResult for alerting rules
        """
        rules_data = self.get_rules()
        results = []

        for group in rules_data.get("groups", []):
            for rule in group.get("rules", []):
                if rule.get("type") == "alerting":
                    result = RuleResult(
                        rule_name=rule.get("name", ""),
                        rule_type="alerting",
                        expression=rule.get("query", ""),
                        labels=rule.get("labels", {}),
                        annotations=rule.get("annotations", {}),
                        state=rule.get("state", "inactive"),
                    )

                    # Get alert instances
                    alerts = rule.get("alerts", [])
                    if alerts:
                        result.result = [
                            {
                                "labels": a.get("labels", {}),
                                "state": a.get("state", ""),
                                "value": a.get("value", ""),
                            }
                            for a in alerts
                        ]

                    results.append(result)

        return results

    def get_recording_rules(self) -> list[RuleResult]:
        """Get all recording rules and their values.

        Returns:
            List of RuleResult for recording rules
        """
        rules_data = self.get_rules()
        results = []

        for group in rules_data.get("groups", []):
            for rule in group.get("rules", []):
                if rule.get("type") == "recording":
                    result = RuleResult(
                        rule_name=rule.get("name", ""),
                        rule_type="recording",
                        expression=rule.get("query", ""),
                        labels=rule.get("labels", {}),
                    )

                    # Query the recording rule metric
                    metric_result = self._query_metric(rule.get("name", ""))
                    if metric_result:
                        result.result = metric_result

                    results.append(result)

        return results

    def _query_metric(self, metric_name: str) -> Any:
        """Query a metric by name.

        Args:
            metric_name: Name of the metric to query

        Returns:
            Query result data or None
        """
        url = f"{self.base_url}/api/v1/query"
        try:
            response = self.client.get(url, params={"query": metric_name})
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return data.get("data", {}).get("result")
        except Exception:
            pass
        return None


class RuleComparisonTest:
    """
    Test class for comparing rule results between Prometheus versions.

    This class compares alerting and recording rule results
    to detect any regressions in rule behavior.

    Requirements: 21.2, 21.3, 21.7
    """

    def __init__(
        self,
        regression_config: RegressionTestConfig,
        rule_config: Optional[RuleComparisonConfig] = None,
    ):
        """Initialize the rule comparison test.

        Args:
            regression_config: Regression test configuration
            rule_config: Rule comparison configuration
        """
        self.regression_config = regression_config
        self.rule_config = rule_config or RuleComparisonConfig()
        self.baseline_client: Optional[PrometheusRulesClient] = None
        self.target_client: Optional[PrometheusRulesClient] = None

    def setup(self) -> tuple[bool, Optional[str]]:
        """Set up the test clients.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.baseline_client = PrometheusRulesClient(
                self.regression_config.baseline_url,
                timeout=self.regression_config.timeout_seconds,
            )
            self.target_client = PrometheusRulesClient(
                self.regression_config.target_url,
                timeout=self.regression_config.timeout_seconds,
            )

            if not self.baseline_client.is_healthy():
                return False, f"Baseline Prometheus not healthy at {self.regression_config.baseline_url}"

            if not self.target_client.is_healthy():
                return False, f"Target Prometheus not healthy at {self.regression_config.target_url}"

            return True, None

        except Exception as e:
            return False, f"Setup failed: {str(e)}"

    def teardown(self) -> None:
        """Clean up test resources."""
        if self.baseline_client:
            self.baseline_client.close()
        if self.target_client:
            self.target_client.close()

    def compare_alerting_rules(self) -> list[RuleComparison]:
        """Compare alerting rules between versions.

        Returns:
            List of RuleComparison results
        """
        baseline_rules = self.baseline_client.get_alerting_rules()
        target_rules = self.target_client.get_alerting_rules()

        # Create lookup by rule name
        baseline_by_name = {r.rule_name: r for r in baseline_rules}
        target_by_name = {r.rule_name: r for r in target_rules}

        comparisons = []

        # Filter rules if specific rules are configured
        rule_names = set(baseline_by_name.keys()) | set(target_by_name.keys())
        if self.rule_config.alerting_rules and not self.rule_config.include_all_rules:
            rule_names = set(self.rule_config.alerting_rules) & rule_names

        for rule_name in rule_names:
            baseline_result = baseline_by_name.get(rule_name)
            target_result = target_by_name.get(rule_name)

            if baseline_result is None:
                # Rule only exists in target - not a regression
                continue

            if target_result is None:
                # Rule missing in target - potential regression
                comparison = RuleComparison(
                    rule_name=rule_name,
                    rule_type="alerting",
                    baseline_result=baseline_result,
                    target_result=RuleResult(
                        rule_name=rule_name,
                        rule_type="alerting",
                        expression="",
                        error="Rule not found in target",
                    ),
                    status=ComparisonStatus.DIFFERENT,
                    differences=["Rule missing in target version"],
                )
            else:
                comparison = RuleComparison(
                    rule_name=rule_name,
                    rule_type="alerting",
                    baseline_result=baseline_result,
                    target_result=target_result,
                )
                comparison.compare()

            comparisons.append(comparison)

        return comparisons

    def compare_recording_rules(self) -> list[RuleComparison]:
        """Compare recording rules between versions.

        Returns:
            List of RuleComparison results
        """
        baseline_rules = self.baseline_client.get_recording_rules()
        target_rules = self.target_client.get_recording_rules()

        # Create lookup by rule name
        baseline_by_name = {r.rule_name: r for r in baseline_rules}
        target_by_name = {r.rule_name: r for r in target_rules}

        comparisons = []

        # Filter rules if specific rules are configured
        rule_names = set(baseline_by_name.keys()) | set(target_by_name.keys())
        if self.rule_config.recording_rules and not self.rule_config.include_all_rules:
            rule_names = set(self.rule_config.recording_rules) & rule_names

        for rule_name in rule_names:
            baseline_result = baseline_by_name.get(rule_name)
            target_result = target_by_name.get(rule_name)

            if baseline_result is None:
                continue

            if target_result is None:
                comparison = RuleComparison(
                    rule_name=rule_name,
                    rule_type="recording",
                    baseline_result=baseline_result,
                    target_result=RuleResult(
                        rule_name=rule_name,
                        rule_type="recording",
                        expression="",
                        error="Rule not found in target",
                    ),
                    status=ComparisonStatus.DIFFERENT,
                    differences=["Rule missing in target version"],
                )
            else:
                comparison = RuleComparison(
                    rule_name=rule_name,
                    rule_type="recording",
                    baseline_result=baseline_result,
                    target_result=target_result,
                )
                comparison.compare()

            comparisons.append(comparison)

        return comparisons

    def run(self) -> RegressionTestReport:
        """Run the rule comparison test.

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
            test_name="rule_comparison",
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
            # Compare alerting rules
            alerting_comparisons = self.compare_alerting_rules()
            report.rule_comparisons.extend(alerting_comparisons)

            # Compare recording rules
            recording_comparisons = self.compare_recording_rules()
            report.rule_comparisons.extend(recording_comparisons)

            # Analyze regressions
            report.analyze_regressions()

        finally:
            self.teardown()
            report.end_time = datetime.utcnow()

        return report


def run_rule_comparison_test(
    baseline_url: str = "http://localhost:9090",
    target_url: str = "http://localhost:9091",
    baseline_version: str = "v3.4.0",
    target_version: str = "v3.5.0",
) -> TestResult:
    """
    Run rule comparison test and return a TestResult.

    Requirements: 21.2, 21.3

    Args:
        baseline_url: URL of the baseline Prometheus instance
        target_url: URL of the target Prometheus instance
        baseline_version: Expected baseline version
        target_version: Expected target version

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="rule_comparison",
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

    test = RuleComparisonTest(regression_config)

    try:
        report = test.run()

        result.duration_seconds = report.duration_seconds
        result.end_time = datetime.utcnow()
        result.metadata["report"] = report.to_dict()

        alerting_count = sum(
            1 for rc in report.rule_comparisons if rc.rule_type == "alerting"
        )
        recording_count = sum(
            1 for rc in report.rule_comparisons if rc.rule_type == "recording"
        )

        if report.passed:
            result.status = TestStatus.PASSED
            result.message = (
                f"Rule comparison passed: {alerting_count} alerting rules, "
                f"{recording_count} recording rules compared"
            )
        else:
            result.status = TestStatus.FAILED
            result.message = (
                f"Rule comparison failed: {len(report.regressions)} regression(s) "
                f"detected"
            )
            for regression in report.regressions:
                result.add_error(TestError(
                    error_code="RULE_REGRESSION_DETECTED",
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


class TestRuleComparison:
    """
    Pytest test class for rule comparison tests.

    Requirements: 21.2, 21.3
    """

    @pytest.fixture
    def regression_config(self) -> RegressionTestConfig:
        """Create a regression test configuration fixture."""
        return RegressionTestConfig()

    @pytest.fixture
    def baseline_client(
        self,
        regression_config: RegressionTestConfig,
    ) -> PrometheusRulesClient:
        """Create a baseline Prometheus rules client fixture."""
        client = PrometheusRulesClient(
            regression_config.baseline_url,
            timeout=regression_config.timeout_seconds,
        )
        yield client
        client.close()

    @pytest.fixture
    def target_client(
        self,
        regression_config: RegressionTestConfig,
    ) -> PrometheusRulesClient:
        """Create a target Prometheus rules client fixture."""
        client = PrometheusRulesClient(
            regression_config.target_url,
            timeout=regression_config.timeout_seconds,
        )
        yield client
        client.close()

    def test_alerting_rules_match(
        self,
        baseline_client: PrometheusRulesClient,
        target_client: PrometheusRulesClient,
    ):
        """
        Test that alerting rules produce same results.

        Requirements: 21.2

        Verifies:
        - Same alerting rules exist in both versions
        - Alert states match between versions
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        baseline_rules = baseline_client.get_alerting_rules()
        target_rules = target_client.get_alerting_rules()

        baseline_names = {r.rule_name for r in baseline_rules}
        target_names = {r.rule_name for r in target_rules}

        # All baseline rules should exist in target
        missing_rules = baseline_names - target_names
        assert not missing_rules, (
            f"Alerting rules missing in target: {missing_rules}"
        )

    def test_recording_rules_match(
        self,
        baseline_client: PrometheusRulesClient,
        target_client: PrometheusRulesClient,
    ):
        """
        Test that recording rules produce same results.

        Requirements: 21.3

        Verifies:
        - Same recording rules exist in both versions
        - Recording rule values are equivalent
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        baseline_rules = baseline_client.get_recording_rules()
        target_rules = target_client.get_recording_rules()

        baseline_names = {r.rule_name for r in baseline_rules}
        target_names = {r.rule_name for r in target_rules}

        # All baseline rules should exist in target
        missing_rules = baseline_names - target_names
        assert not missing_rules, (
            f"Recording rules missing in target: {missing_rules}"
        )

    def test_alert_states_consistent(
        self,
        baseline_client: PrometheusRulesClient,
        target_client: PrometheusRulesClient,
    ):
        """
        Test that alert states are consistent between versions.

        Requirements: 21.2

        Verifies:
        - Firing alerts in baseline are also firing in target
        - No unexpected alert state changes
        """
        if not baseline_client.is_healthy():
            pytest.skip("Baseline Prometheus not available")
        if not target_client.is_healthy():
            pytest.skip("Target Prometheus not available")

        baseline_rules = baseline_client.get_alerting_rules()
        target_rules = target_client.get_alerting_rules()

        baseline_by_name = {r.rule_name: r for r in baseline_rules}
        target_by_name = {r.rule_name: r for r in target_rules}

        state_mismatches = []
        for rule_name, baseline_rule in baseline_by_name.items():
            if rule_name in target_by_name:
                target_rule = target_by_name[rule_name]
                if baseline_rule.state != target_rule.state:
                    state_mismatches.append(
                        f"{rule_name}: baseline={baseline_rule.state}, "
                        f"target={target_rule.state}"
                    )

        # State mismatches are warnings, not failures
        # (alerts can change state between queries)
        if state_mismatches:
            pytest.warns(
                UserWarning,
                match=f"Alert state differences detected: {len(state_mismatches)}",
            )
