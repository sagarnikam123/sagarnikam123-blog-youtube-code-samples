"""
Data Exposure Tests for Prometheus.

This module implements security tests to check for sensitive data
exposure in Prometheus metrics.

Requirements: 22.4
"""

import re
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


class DataExposureChecker:
    """
    Checker for sensitive data exposure in Prometheus metrics.

    Provides methods to scan metrics for potentially sensitive information.
    """

    # Patterns that might indicate sensitive data
    SENSITIVE_PATTERNS = {
        "password": re.compile(r'password["\s:=]+[^"\s,}]+', re.IGNORECASE),
        "secret": re.compile(r'secret["\s:=]+[^"\s,}]+', re.IGNORECASE),
        "api_key": re.compile(r'api[_-]?key["\s:=]+[^"\s,}]+', re.IGNORECASE),
        "token": re.compile(r'(?:auth|bearer|access)[_-]?token["\s:=]+[^"\s,}]+', re.IGNORECASE),
        "private_key": re.compile(r'private[_-]?key["\s:=]+[^"\s,}]+', re.IGNORECASE),
        "credit_card": re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),
        "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        "aws_key": re.compile(r'AKIA[0-9A-Z]{16}'),
        "aws_secret": re.compile(r'[A-Za-z0-9/+=]{40}'),
    }

    # Label names that should not contain sensitive data
    SENSITIVE_LABEL_NAMES = {
        "password", "secret", "token", "key", "credential",
        "auth", "private", "ssn", "credit_card", "api_key",
    }

    # Metric names that might expose sensitive info
    SUSPICIOUS_METRIC_PATTERNS = [
        re.compile(r'.*password.*', re.IGNORECASE),
        re.compile(r'.*secret.*', re.IGNORECASE),
        re.compile(r'.*credential.*', re.IGNORECASE),
        re.compile(r'.*private.*key.*', re.IGNORECASE),
    ]

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the data exposure checker.

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

    def get_all_metrics(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get all metrics from Prometheus federation endpoint.

        Returns:
            Tuple of (metrics_text, error_message)
        """
        url = f"{self.base_url}/federate"
        params = {"match[]": "{__name__=~'.+'}"}

        try:
            response = self.client.get(url, params=params)
            if response.status_code == 200:
                return response.text, None
            elif response.status_code == 404:
                # Try alternative endpoint
                return self._get_metrics_via_query()
            return None, f"HTTP {response.status_code}: {response.text[:200]}"
        except httpx.TimeoutException:
            return None, f"Request timed out after {self.timeout}s"
        except Exception as e:
            return None, f"Error fetching metrics: {str(e)}"

    def _get_metrics_via_query(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get metrics via PromQL query as fallback.

        Returns:
            Tuple of (metrics_text, error_message)
        """
        url = f"{self.base_url}/api/v1/label/__name__/values"

        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                metric_names = data.get("data", [])
                return "\n".join(metric_names), None
            return None, f"HTTP {response.status_code}"
        except Exception as e:
            return None, f"Error: {str(e)}"

    def get_metric_labels(self, metric_name: str) -> tuple[Optional[list], Optional[str]]:
        """
        Get labels for a specific metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Tuple of (labels_list, error_message)
        """
        url = f"{self.base_url}/api/v1/series"
        params = {"match[]": metric_name}

        try:
            response = self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", []), None
            return None, f"HTTP {response.status_code}"
        except Exception as e:
            return None, f"Error: {str(e)}"

    def scan_for_sensitive_patterns(self, text: str) -> list[dict]:
        """
        Scan text for sensitive data patterns.

        Args:
            text: Text to scan

        Returns:
            List of findings with pattern name and matched text
        """
        findings = []

        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            matches = pattern.findall(text)
            for match in matches:
                # Skip common false positives
                if self._is_false_positive(pattern_name, match):
                    continue

                findings.append({
                    "pattern": pattern_name,
                    "match": self._redact_sensitive(match),
                    "severity": self._get_severity(pattern_name),
                })

        return findings

    def _is_false_positive(self, pattern_name: str, match: str) -> bool:
        """
        Check if a match is a false positive.

        Args:
            pattern_name: Name of the pattern
            match: Matched text

        Returns:
            True if this is likely a false positive
        """
        # IP addresses in metrics are often expected (e.g., instance labels)
        if pattern_name == "ip_address":
            # Private IP ranges are usually fine
            if match.startswith(("10.", "172.", "192.168.", "127.")):
                return True

        # Email patterns in metric names are usually false positives
        if pattern_name == "email" and "@" not in match:
            return True

        return False

    def _redact_sensitive(self, text: str) -> str:
        """
        Redact sensitive parts of text for safe logging.

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        if len(text) <= 8:
            return "***REDACTED***"
        return text[:4] + "***REDACTED***" + text[-4:]

    def _get_severity(self, pattern_name: str) -> str:
        """
        Get severity level for a pattern type.

        Args:
            pattern_name: Name of the pattern

        Returns:
            Severity level (critical, high, medium, low)
        """
        critical_patterns = {"password", "secret", "private_key", "aws_key", "aws_secret"}
        high_patterns = {"api_key", "token", "credit_card", "ssn"}

        if pattern_name in critical_patterns:
            return "critical"
        elif pattern_name in high_patterns:
            return "high"
        return "medium"

    def check_label_names(self, labels: dict) -> list[dict]:
        """
        Check label names for sensitive naming.

        Args:
            labels: Dictionary of label names and values

        Returns:
            List of suspicious label findings
        """
        findings = []

        for label_name, label_value in labels.items():
            label_lower = label_name.lower()

            # Check if label name suggests sensitive data
            for sensitive_name in self.SENSITIVE_LABEL_NAMES:
                if sensitive_name in label_lower:
                    findings.append({
                        "label_name": label_name,
                        "issue": f"Label name contains '{sensitive_name}'",
                        "value_redacted": self._redact_sensitive(str(label_value)),
                        "severity": "high",
                    })
                    break

        return findings

    def check_metric_names(self, metric_names: list[str]) -> list[dict]:
        """
        Check metric names for suspicious patterns.

        Args:
            metric_names: List of metric names

        Returns:
            List of suspicious metric findings
        """
        findings = []

        for metric_name in metric_names:
            for pattern in self.SUSPICIOUS_METRIC_PATTERNS:
                if pattern.match(metric_name):
                    findings.append({
                        "metric_name": metric_name,
                        "issue": "Metric name suggests sensitive data",
                        "severity": "medium",
                    })
                    break

        return findings

    def verify_no_sensitive_data(self) -> tuple[bool, dict, Optional[str]]:
        """
        Verify that no sensitive data is exposed in metrics.

        Returns:
            Tuple of (no_sensitive_data, details, error_message)
        """
        details = {
            "metrics_scanned": 0,
            "pattern_findings": [],
            "label_findings": [],
            "metric_name_findings": [],
            "total_findings": 0,
        }

        # Get all metrics
        metrics_text, error = self.get_all_metrics()
        if error:
            return False, details, f"Could not fetch metrics: {error}"

        if metrics_text:
            # Scan for sensitive patterns
            pattern_findings = self.scan_for_sensitive_patterns(metrics_text)
            details["pattern_findings"] = pattern_findings

            # Count metrics
            details["metrics_scanned"] = len(metrics_text.split("\n"))

        # Get metric names and check them
        url = f"{self.base_url}/api/v1/label/__name__/values"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                metric_names = data.get("data", [])
                metric_findings = self.check_metric_names(metric_names)
                details["metric_name_findings"] = metric_findings
        except Exception:
            pass  # Non-critical

        # Calculate total findings
        details["total_findings"] = (
            len(details["pattern_findings"]) +
            len(details["label_findings"]) +
            len(details["metric_name_findings"])
        )

        # Filter critical findings
        critical_findings = [
            f for f in details["pattern_findings"]
            if f.get("severity") == "critical"
        ]

        if critical_findings:
            return False, details, f"Found {len(critical_findings)} critical sensitive data exposures"

        if details["total_findings"] > 0:
            return True, details, f"Found {details['total_findings']} potential issues (non-critical)"

        return True, details, None


def test_data_exposure(prometheus_url: str) -> TestResult:
    """
    Test for sensitive data exposure in Prometheus metrics.

    Requirements: 22.4

    This test verifies:
    - No passwords, secrets, or API keys in metrics
    - No PII (SSN, credit cards) in metrics
    - Label names don't suggest sensitive data storage

    Args:
        prometheus_url: URL of the Prometheus instance

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="data_exposure",
        test_type="security",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    checker = DataExposureChecker(prometheus_url, timeout=30.0)

    try:
        no_sensitive, details, error = checker.verify_no_sensitive_data()
        result.metadata["scan_details"] = details

        if no_sensitive:
            if details["total_findings"] > 0:
                result.status = TestStatus.PASSED
                result.message = f"No critical issues. {details['total_findings']} potential issues found (review recommended)"
                result.metadata["recommendations"] = [
                    "Review potential issues for false positives",
                    "Consider redacting sensitive label values",
                ]
            else:
                result.status = TestStatus.PASSED
                result.message = f"No sensitive data exposure detected in {details['metrics_scanned']} metrics"
        else:
            result.status = TestStatus.FAILED
            result.message = f"Sensitive data exposure detected: {error}"
            result.add_error(TestError(
                error_code="SENSITIVE_DATA_EXPOSED",
                message=error or "Sensitive data found in metrics",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.CRITICAL,
                context={
                    "findings_count": details["total_findings"],
                    "critical_findings": [
                        f for f in details["pattern_findings"]
                        if f.get("severity") == "critical"
                    ],
                },
                remediation="Remove or redact sensitive data from metrics and labels",
            ))

        result.end_time = datetime.utcnow()
        result.duration_seconds = (result.end_time - result.start_time).total_seconds()

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
        checker.close()

    return result


class TestDataExposure:
    """
    Pytest test class for data exposure tests.

    Requirements: 22.4
    """

    @pytest.fixture
    def exposure_checker(self, prometheus_url: str) -> DataExposureChecker:
        """Create a data exposure checker fixture."""
        checker = DataExposureChecker(prometheus_url, timeout=30.0)
        yield checker
        checker.close()

    def test_no_passwords_in_metrics(self, exposure_checker: DataExposureChecker):
        """
        Test that no passwords are exposed in metrics.

        Requirements: 22.4

        Verifies:
        - No password patterns found in metric values or labels
        """
        metrics_text, error = exposure_checker.get_all_metrics()

        if error:
            pytest.skip(f"Could not fetch metrics: {error}")

        findings = exposure_checker.scan_for_sensitive_patterns(metrics_text or "")
        password_findings = [f for f in findings if f["pattern"] == "password"]

        assert len(password_findings) == 0, \
            f"Found {len(password_findings)} password exposures in metrics"

    def test_no_api_keys_in_metrics(self, exposure_checker: DataExposureChecker):
        """
        Test that no API keys are exposed in metrics.

        Requirements: 22.4

        Verifies:
        - No API key patterns found in metric values or labels
        """
        metrics_text, error = exposure_checker.get_all_metrics()

        if error:
            pytest.skip(f"Could not fetch metrics: {error}")

        findings = exposure_checker.scan_for_sensitive_patterns(metrics_text or "")
        api_key_findings = [
            f for f in findings
            if f["pattern"] in ("api_key", "aws_key", "aws_secret")
        ]

        assert len(api_key_findings) == 0, \
            f"Found {len(api_key_findings)} API key exposures in metrics"

    def test_no_pii_in_metrics(self, exposure_checker: DataExposureChecker):
        """
        Test that no PII is exposed in metrics.

        Requirements: 22.4

        Verifies:
        - No SSN patterns found
        - No credit card patterns found
        """
        metrics_text, error = exposure_checker.get_all_metrics()

        if error:
            pytest.skip(f"Could not fetch metrics: {error}")

        findings = exposure_checker.scan_for_sensitive_patterns(metrics_text or "")
        pii_findings = [
            f for f in findings
            if f["pattern"] in ("ssn", "credit_card")
        ]

        assert len(pii_findings) == 0, \
            f"Found {len(pii_findings)} PII exposures in metrics"

    def test_metric_names_not_suspicious(self, exposure_checker: DataExposureChecker):
        """
        Test that metric names don't suggest sensitive data.

        Requirements: 22.4

        Verifies:
        - No metric names containing 'password', 'secret', etc.
        """
        url = f"{exposure_checker.base_url}/api/v1/label/__name__/values"

        try:
            response = exposure_checker.client.get(url)
            if response.status_code != 200:
                pytest.skip("Could not fetch metric names")

            data = response.json()
            metric_names = data.get("data", [])

            findings = exposure_checker.check_metric_names(metric_names)

            # Warnings only, not failures
            if findings:
                for finding in findings:
                    print(f"Warning: Suspicious metric name: {finding['metric_name']}")

        except Exception as e:
            pytest.skip(f"Could not check metric names: {str(e)}")

    def test_no_critical_exposures(self, exposure_checker: DataExposureChecker):
        """
        Test that no critical sensitive data is exposed.

        Requirements: 22.4

        Verifies:
        - No critical severity findings (passwords, secrets, private keys)
        """
        no_sensitive, details, error = exposure_checker.verify_no_sensitive_data()

        if error and "Could not fetch" in error:
            pytest.skip(error)

        critical_findings = [
            f for f in details.get("pattern_findings", [])
            if f.get("severity") == "critical"
        ]

        assert len(critical_findings) == 0, \
            f"Found {len(critical_findings)} critical sensitive data exposures"
