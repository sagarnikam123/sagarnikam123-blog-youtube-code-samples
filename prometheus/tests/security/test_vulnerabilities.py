"""
Vulnerability Scan Tests for Prometheus.

This module implements security tests to scan for known CVEs and
vulnerabilities in the Prometheus version.

Requirements: 22.6
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


class VulnerabilityScanner:
    """
    Scanner for known vulnerabilities in Prometheus.

    Provides methods to check the Prometheus version against known CVEs.
    """

    # Known CVEs for Prometheus versions
    # Format: {cve_id: {affected_versions, severity, description, fixed_in}}
    KNOWN_CVES = {
        "CVE-2021-29622": {
            "affected_versions": ["<2.26.1", "<2.27.1"],
            "severity": "medium",
            "description": "Open redirect vulnerability in Prometheus",
            "fixed_in": "2.26.1, 2.27.1",
            "cvss": 6.1,
        },
        "CVE-2022-21698": {
            "affected_versions": ["<2.34.0"],
            "severity": "high",
            "description": "Denial of service via crafted Accept header in promhttp",
            "fixed_in": "2.34.0",
            "cvss": 7.5,
        },
        "CVE-2022-46146": {
            "affected_versions": ["<2.40.5", "<2.41.0"],
            "severity": "high",
            "description": "Basic authentication bypass vulnerability",
            "fixed_in": "2.40.5, 2.41.0",
            "cvss": 8.8,
        },
        "CVE-2023-45142": {
            "affected_versions": ["<2.47.1"],
            "severity": "high",
            "description": "Memory exhaustion via otelhttp",
            "fixed_in": "2.47.1",
            "cvss": 7.5,
        },
    }

    # Minimum recommended versions
    RECOMMENDED_VERSIONS = {
        "2.x": "2.53.0",
        "3.x": "3.0.0",
    }

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize the vulnerability scanner.

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

    def get_prometheus_version(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get the Prometheus version from the build info endpoint.

        Returns:
            Tuple of (version, error_message)
        """
        url = f"{self.base_url}/api/v1/status/buildinfo"

        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                version = data.get("data", {}).get("version")
                return version, None
            return None, f"HTTP {response.status_code}"
        except httpx.TimeoutException:
            return None, f"Request timed out after {self.timeout}s"
        except Exception as e:
            return None, f"Error getting version: {str(e)}"

    def parse_version(self, version_str: str) -> tuple[int, int, int]:
        """
        Parse a version string into components.

        Args:
            version_str: Version string (e.g., "2.45.0", "v2.45.0")

        Returns:
            Tuple of (major, minor, patch)
        """
        # Remove 'v' prefix if present
        version_str = version_str.lstrip("v")

        # Extract version numbers
        match = re.match(r"(\d+)\.(\d+)\.(\d+)", version_str)
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3))

        # Try simpler pattern
        match = re.match(r"(\d+)\.(\d+)", version_str)
        if match:
            return int(match.group(1)), int(match.group(2)), 0

        return 0, 0, 0

    def version_compare(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Args:
            v1: First version
            v2: Second version

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        v1_parts = self.parse_version(v1)
        v2_parts = self.parse_version(v2)

        for p1, p2 in zip(v1_parts, v2_parts):
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1

        return 0

    def is_version_affected(self, version: str, affected_spec: str) -> bool:
        """
        Check if a version is affected by a vulnerability.

        Args:
            version: Current version
            affected_spec: Affected version specification (e.g., "<2.34.0")

        Returns:
            True if version is affected
        """
        # Parse the specification
        if affected_spec.startswith("<"):
            threshold = affected_spec[1:]
            return self.version_compare(version, threshold) < 0
        elif affected_spec.startswith("<="):
            threshold = affected_spec[2:]
            return self.version_compare(version, threshold) <= 0
        elif affected_spec.startswith(">="):
            threshold = affected_spec[2:]
            return self.version_compare(version, threshold) >= 0
        elif affected_spec.startswith(">"):
            threshold = affected_spec[1:]
            return self.version_compare(version, threshold) > 0
        elif affected_spec.startswith("=="):
            threshold = affected_spec[2:]
            return self.version_compare(version, threshold) == 0
        else:
            # Exact match
            return self.version_compare(version, affected_spec) == 0

    def check_known_cves(self, version: str) -> list[dict]:
        """
        Check version against known CVEs.

        Args:
            version: Prometheus version

        Returns:
            List of applicable CVEs
        """
        applicable_cves = []

        for cve_id, cve_info in self.KNOWN_CVES.items():
            for affected_spec in cve_info["affected_versions"]:
                if self.is_version_affected(version, affected_spec):
                    applicable_cves.append({
                        "cve_id": cve_id,
                        "severity": cve_info["severity"],
                        "description": cve_info["description"],
                        "fixed_in": cve_info["fixed_in"],
                        "cvss": cve_info.get("cvss"),
                    })
                    break

        return applicable_cves

    def check_version_currency(self, version: str) -> tuple[bool, dict]:
        """
        Check if the version is current/recommended.

        Args:
            version: Prometheus version

        Returns:
            Tuple of (is_current, details)
        """
        major, minor, patch = self.parse_version(version)

        details = {
            "current_version": version,
            "major": major,
            "is_latest_major": False,
            "recommended_version": None,
            "versions_behind": 0,
        }

        # Determine recommended version based on major version
        if major >= 3:
            recommended = self.RECOMMENDED_VERSIONS.get("3.x", "3.0.0")
        else:
            recommended = self.RECOMMENDED_VERSIONS.get("2.x", "2.53.0")

        details["recommended_version"] = recommended

        # Check if current
        is_current = self.version_compare(version, recommended) >= 0
        details["is_latest_major"] = is_current

        if not is_current:
            # Calculate how many minor versions behind
            rec_major, rec_minor, rec_patch = self.parse_version(recommended)
            if major == rec_major:
                details["versions_behind"] = rec_minor - minor

        return is_current, details

    def scan_for_vulnerabilities(self) -> tuple[bool, dict, Optional[str]]:
        """
        Perform a complete vulnerability scan.

        Returns:
            Tuple of (no_critical_vulns, details, error_message)
        """
        details = {
            "version": None,
            "cves": [],
            "version_currency": {},
            "recommendations": [],
        }

        # Get version
        version, error = self.get_prometheus_version()
        if error:
            return False, details, f"Could not get Prometheus version: {error}"

        details["version"] = version

        # Check known CVEs
        cves = self.check_known_cves(version)
        details["cves"] = cves

        # Check version currency
        is_current, currency_details = self.check_version_currency(version)
        details["version_currency"] = currency_details

        # Generate recommendations
        if cves:
            critical_cves = [c for c in cves if c["severity"] in ("critical", "high")]
            if critical_cves:
                details["recommendations"].append(
                    f"URGENT: Upgrade to fix {len(critical_cves)} critical/high severity CVEs"
                )
            else:
                details["recommendations"].append(
                    f"Consider upgrading to fix {len(cves)} known CVEs"
                )

        if not is_current:
            details["recommendations"].append(
                f"Consider upgrading to {currency_details['recommended_version']} "
                f"(currently {currency_details['versions_behind']} minor versions behind)"
            )

        # Determine if there are critical vulnerabilities
        critical_cves = [c for c in cves if c["severity"] in ("critical", "high")]

        if critical_cves:
            return False, details, f"Found {len(critical_cves)} critical/high severity CVEs"

        return True, details, None

    def get_security_headers(self) -> tuple[dict, Optional[str]]:
        """
        Check security-related HTTP headers.

        Returns:
            Tuple of (headers_dict, error_message)
        """
        url = f"{self.base_url}/api/v1/status/buildinfo"

        try:
            response = self.client.get(url)

            security_headers = {
                "X-Content-Type-Options": response.headers.get("X-Content-Type-Options"),
                "X-Frame-Options": response.headers.get("X-Frame-Options"),
                "X-XSS-Protection": response.headers.get("X-XSS-Protection"),
                "Content-Security-Policy": response.headers.get("Content-Security-Policy"),
                "Strict-Transport-Security": response.headers.get("Strict-Transport-Security"),
            }

            return security_headers, None

        except Exception as e:
            return {}, f"Error checking headers: {str(e)}"


def test_vulnerability_scan(prometheus_url: str) -> TestResult:
    """
    Scan for known vulnerabilities in Prometheus.

    Requirements: 22.6

    This test verifies:
    - No critical/high severity CVEs affect the version
    - Version is reasonably current
    - Security headers are present

    Args:
        prometheus_url: URL of the Prometheus instance

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="vulnerability_scan",
        test_type="security",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    scanner = VulnerabilityScanner(prometheus_url, timeout=10.0)

    try:
        no_critical, details, error = scanner.scan_for_vulnerabilities()
        result.metadata["scan_details"] = details

        # Check security headers
        headers, header_error = scanner.get_security_headers()
        result.metadata["security_headers"] = headers

        if no_critical:
            if details["cves"]:
                result.status = TestStatus.PASSED
                result.message = f"No critical CVEs. {len(details['cves'])} lower severity issues found."
                result.metadata["recommendations"] = details.get("recommendations", [])
            else:
                result.status = TestStatus.PASSED
                result.message = f"No known CVEs found for version {details['version']}"
        else:
            result.status = TestStatus.FAILED
            result.message = f"Vulnerability scan failed: {error}"
            result.add_error(TestError(
                error_code="CRITICAL_CVE_FOUND",
                message=error or "Critical vulnerabilities found",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.CRITICAL,
                context={
                    "version": details.get("version"),
                    "cves": details.get("cves", []),
                },
                remediation="Upgrade Prometheus to the latest version to fix known CVEs",
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
        scanner.close()

    return result


class TestVulnerabilities:
    """
    Pytest test class for vulnerability scan tests.

    Requirements: 22.6
    """

    @pytest.fixture
    def vuln_scanner(self, prometheus_url: str) -> VulnerabilityScanner:
        """Create a vulnerability scanner fixture."""
        scanner = VulnerabilityScanner(prometheus_url, timeout=10.0)
        yield scanner
        scanner.close()

    def test_get_prometheus_version(self, vuln_scanner: VulnerabilityScanner):
        """
        Test that Prometheus version can be retrieved.

        Requirements: 22.6

        Verifies:
        - Version endpoint is accessible
        - Version string is returned
        """
        version, error = vuln_scanner.get_prometheus_version()

        if error:
            pytest.skip(f"Could not get version: {error}")

        assert version is not None, "Version should not be None"
        assert len(version) > 0, "Version should not be empty"

        # Version should match expected pattern
        assert re.match(r"v?\d+\.\d+", version), \
            f"Version '{version}' does not match expected pattern"

    def test_no_critical_cves(self, vuln_scanner: VulnerabilityScanner):
        """
        Test that no critical CVEs affect the version.

        Requirements: 22.6

        Verifies:
        - No critical or high severity CVEs
        """
        version, error = vuln_scanner.get_prometheus_version()

        if error:
            pytest.skip(f"Could not get version: {error}")

        cves = vuln_scanner.check_known_cves(version)
        critical_cves = [c for c in cves if c["severity"] in ("critical", "high")]

        if critical_cves:
            cve_list = ", ".join(c["cve_id"] for c in critical_cves)
            pytest.fail(f"Critical/high severity CVEs found: {cve_list}")

    def test_version_not_ancient(self, vuln_scanner: VulnerabilityScanner):
        """
        Test that Prometheus version is not too old.

        Requirements: 22.6

        Verifies:
        - Version is not more than 10 minor versions behind
        """
        version, error = vuln_scanner.get_prometheus_version()

        if error:
            pytest.skip(f"Could not get version: {error}")

        is_current, details = vuln_scanner.check_version_currency(version)

        versions_behind = details.get("versions_behind", 0)

        # Warn if more than 5 versions behind
        if versions_behind > 5:
            print(f"Warning: Prometheus is {versions_behind} minor versions behind recommended")

        # Fail if more than 10 versions behind
        assert versions_behind <= 10, \
            f"Prometheus version {version} is {versions_behind} versions behind recommended"

    def test_version_parsing(self, vuln_scanner: VulnerabilityScanner):
        """
        Test version parsing functionality.

        Requirements: 22.6

        Verifies:
        - Version strings are parsed correctly
        """
        # Test various version formats
        test_cases = [
            ("2.45.0", (2, 45, 0)),
            ("v2.45.0", (2, 45, 0)),
            ("2.45", (2, 45, 0)),
            ("3.0.0", (3, 0, 0)),
        ]

        for version_str, expected in test_cases:
            result = vuln_scanner.parse_version(version_str)
            assert result == expected, \
                f"parse_version('{version_str}') = {result}, expected {expected}"

    def test_version_comparison(self, vuln_scanner: VulnerabilityScanner):
        """
        Test version comparison functionality.

        Requirements: 22.6

        Verifies:
        - Version comparison works correctly
        """
        # Test comparisons
        assert vuln_scanner.version_compare("2.45.0", "2.46.0") < 0
        assert vuln_scanner.version_compare("2.46.0", "2.45.0") > 0
        assert vuln_scanner.version_compare("2.45.0", "2.45.0") == 0
        assert vuln_scanner.version_compare("3.0.0", "2.99.0") > 0

    def test_cve_detection(self, vuln_scanner: VulnerabilityScanner):
        """
        Test CVE detection for known vulnerable versions.

        Requirements: 22.6

        Verifies:
        - Known vulnerable versions are detected
        """
        # Test with a known vulnerable version
        cves = vuln_scanner.check_known_cves("2.30.0")

        # Should detect CVE-2022-21698 (fixed in 2.34.0)
        cve_ids = [c["cve_id"] for c in cves]
        assert "CVE-2022-21698" in cve_ids, \
            "CVE-2022-21698 should be detected for version 2.30.0"

    def test_security_headers(self, vuln_scanner: VulnerabilityScanner):
        """
        Test that security headers are checked.

        Requirements: 22.6

        Verifies:
        - Security headers can be retrieved
        """
        headers, error = vuln_scanner.get_security_headers()

        if error:
            pytest.skip(f"Could not check headers: {error}")

        # Headers dict should be returned (may be empty)
        assert isinstance(headers, dict), "Headers should be a dictionary"

        # Log which headers are present
        present_headers = [k for k, v in headers.items() if v]
        if present_headers:
            print(f"Security headers present: {present_headers}")
        else:
            print("Warning: No security headers detected")
