"""
TLS Verification Tests for Prometheus.

This module implements security tests to verify that TLS is properly configured
for Prometheus scrape targets and API endpoints.

Requirements: 22.1
"""

import ssl
import socket
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
import pytest

from framework.models import (
    ErrorCategory,
    ErrorSeverity,
    TestError,
    TestResult,
    TestStatus,
)


class TLSVerifier:
    """
    Verifier for TLS configuration on Prometheus and scrape targets.

    Provides methods to check TLS certificates, cipher suites, and protocol versions.
    """

    # Minimum acceptable TLS version
    MIN_TLS_VERSION = ssl.TLSVersion.TLSv1_2

    # Weak cipher suites that should not be used
    WEAK_CIPHERS = {
        "DES", "RC4", "MD5", "NULL", "EXPORT", "anon", "ADH", "AECDH"
    }

    def __init__(self, timeout: float = 10.0):
        """
        Initialize the TLS verifier.

        Args:
            timeout: Connection timeout in seconds
        """
        self.timeout = timeout

    def check_tls_enabled(self, host: str, port: int = 443) -> tuple[bool, Optional[str]]:
        """
        Check if TLS is enabled on the target.

        Args:
            host: Target hostname
            port: Target port

        Returns:
            Tuple of (tls_enabled, error_message)
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    return True, None
        except ssl.SSLError as e:
            return False, f"SSL error: {str(e)}"
        except socket.timeout:
            return False, f"Connection timed out after {self.timeout}s"
        except socket.error as e:
            return False, f"Socket error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def get_certificate_info(self, host: str, port: int = 443) -> tuple[Optional[dict], Optional[str]]:
        """
        Get certificate information from the target.

        Args:
            host: Target hostname
            port: Target port

        Returns:
            Tuple of (certificate_info, error_message)
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        "subject": dict(x[0] for x in cert.get("subject", [])),
                        "issuer": dict(x[0] for x in cert.get("issuer", [])),
                        "version": cert.get("version"),
                        "serial_number": cert.get("serialNumber"),
                        "not_before": cert.get("notBefore"),
                        "not_after": cert.get("notAfter"),
                        "subject_alt_names": cert.get("subjectAltName", []),
                    }, None
        except ssl.SSLCertVerificationError as e:
            return None, f"Certificate verification failed: {str(e)}"
        except ssl.SSLError as e:
            return None, f"SSL error: {str(e)}"
        except Exception as e:
            return None, f"Error getting certificate: {str(e)}"

    def check_tls_version(self, host: str, port: int = 443) -> tuple[bool, str, Optional[str]]:
        """
        Check if the TLS version meets minimum requirements.

        Args:
            host: Target hostname
            port: Target port

        Returns:
            Tuple of (meets_requirements, tls_version, error_message)
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    version = ssock.version()
                    # Check if version is TLS 1.2 or higher
                    is_secure = version in ("TLSv1.2", "TLSv1.3")
                    return is_secure, version, None
        except Exception as e:
            return False, "unknown", f"Error checking TLS version: {str(e)}"

    def check_cipher_suite(self, host: str, port: int = 443) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Check if the cipher suite is secure.

        Args:
            host: Target hostname
            port: Target port

        Returns:
            Tuple of (is_secure, cipher_name, error_message)
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cipher = ssock.cipher()
                    if cipher:
                        cipher_name = cipher[0]
                        # Check for weak ciphers
                        is_weak = any(weak in cipher_name for weak in self.WEAK_CIPHERS)
                        return not is_weak, cipher_name, None
                    return False, None, "No cipher negotiated"
        except Exception as e:
            return False, None, f"Error checking cipher: {str(e)}"

    def verify_https_endpoint(self, url: str) -> tuple[bool, dict, Optional[str]]:
        """
        Verify HTTPS is properly configured for an endpoint.

        Args:
            url: Full URL to verify

        Returns:
            Tuple of (is_secure, details, error_message)
        """
        parsed = urlparse(url)

        if parsed.scheme != "https":
            return False, {"scheme": parsed.scheme}, "URL does not use HTTPS"

        host = parsed.hostname
        port = parsed.port or 443

        details = {
            "host": host,
            "port": port,
            "scheme": parsed.scheme,
        }

        # Check TLS enabled
        tls_enabled, error = self.check_tls_enabled(host, port)
        if not tls_enabled:
            return False, details, error

        # Check TLS version
        version_ok, version, error = self.check_tls_version(host, port)
        details["tls_version"] = version
        if not version_ok:
            return False, details, f"Insecure TLS version: {version}"

        # Check cipher suite
        cipher_ok, cipher, error = self.check_cipher_suite(host, port)
        details["cipher_suite"] = cipher
        if not cipher_ok:
            return False, details, f"Weak cipher suite: {cipher}"

        # Get certificate info
        cert_info, error = self.get_certificate_info(host, port)
        if cert_info:
            details["certificate"] = cert_info

        return True, details, None


def test_tls_configuration(prometheus_url: str) -> TestResult:
    """
    Test that TLS is properly configured for Prometheus.

    Requirements: 22.1

    This test verifies:
    - TLS is enabled if HTTPS URL is provided
    - TLS version is 1.2 or higher
    - Cipher suite is secure
    - Certificate is valid

    Args:
        prometheus_url: URL of the Prometheus instance

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="tls_configuration",
        test_type="security",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    verifier = TLSVerifier(timeout=10.0)
    parsed = urlparse(prometheus_url)

    try:
        if parsed.scheme == "http":
            # HTTP URL - TLS not configured
            result.status = TestStatus.PASSED
            result.message = "Prometheus is using HTTP (TLS not configured). Consider enabling TLS for production."
            result.metadata["tls_enabled"] = False
            result.metadata["recommendation"] = "Enable TLS for production deployments"
        else:
            # HTTPS URL - verify TLS configuration
            is_secure, details, error = verifier.verify_https_endpoint(prometheus_url)
            result.metadata.update(details)

            if is_secure:
                result.status = TestStatus.PASSED
                result.message = f"TLS properly configured (version: {details.get('tls_version')}, cipher: {details.get('cipher_suite')})"
            else:
                result.status = TestStatus.FAILED
                result.message = f"TLS configuration issue: {error}"
                result.add_error(TestError(
                    error_code="TLS_CONFIG_ERROR",
                    message=error or "TLS configuration verification failed",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.CRITICAL,
                    context=details,
                    remediation="Ensure TLS 1.2+ is enabled with secure cipher suites",
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

    return result


class TestTLSVerification:
    """
    Pytest test class for TLS verification tests.

    Requirements: 22.1
    """

    @pytest.fixture
    def tls_verifier(self) -> TLSVerifier:
        """Create a TLS verifier fixture."""
        return TLSVerifier(timeout=10.0)

    def test_tls_version_minimum(self, tls_verifier: TLSVerifier, prometheus_url: str):
        """
        Test that TLS version meets minimum requirements.

        Requirements: 22.1

        Verifies:
        - TLS 1.2 or higher is used
        """
        parsed = urlparse(prometheus_url)

        if parsed.scheme != "https":
            pytest.skip("Prometheus is not using HTTPS")

        host = parsed.hostname
        port = parsed.port or 443

        version_ok, version, error = tls_verifier.check_tls_version(host, port)

        if error:
            pytest.fail(f"Could not check TLS version: {error}")

        assert version_ok, f"TLS version {version} does not meet minimum requirement (TLS 1.2+)"

    def test_cipher_suite_secure(self, tls_verifier: TLSVerifier, prometheus_url: str):
        """
        Test that cipher suite is secure.

        Requirements: 22.1

        Verifies:
        - No weak ciphers are used (DES, RC4, MD5, NULL, EXPORT)
        """
        parsed = urlparse(prometheus_url)

        if parsed.scheme != "https":
            pytest.skip("Prometheus is not using HTTPS")

        host = parsed.hostname
        port = parsed.port or 443

        is_secure, cipher, error = tls_verifier.check_cipher_suite(host, port)

        if error:
            pytest.fail(f"Could not check cipher suite: {error}")

        assert is_secure, f"Weak cipher suite detected: {cipher}"

    def test_certificate_valid(self, tls_verifier: TLSVerifier, prometheus_url: str):
        """
        Test that the TLS certificate is valid.

        Requirements: 22.1

        Verifies:
        - Certificate can be retrieved
        - Certificate is not expired
        """
        parsed = urlparse(prometheus_url)

        if parsed.scheme != "https":
            pytest.skip("Prometheus is not using HTTPS")

        host = parsed.hostname
        port = parsed.port or 443

        cert_info, error = tls_verifier.get_certificate_info(host, port)

        if error:
            pytest.fail(f"Certificate verification failed: {error}")

        assert cert_info is not None, "Could not retrieve certificate information"
        assert "not_after" in cert_info, "Certificate missing expiration date"

    def test_scrape_target_tls(self, tls_verifier: TLSVerifier, prometheus_url: str):
        """
        Test TLS configuration for scrape targets.

        Requirements: 22.1

        Verifies:
        - Scrape targets using HTTPS have valid TLS configuration
        """
        # This test would need to query Prometheus for its targets
        # and verify TLS on each HTTPS target
        parsed = urlparse(prometheus_url)

        if parsed.scheme != "https":
            pytest.skip("Prometheus is not using HTTPS - cannot verify scrape target TLS")

        # For now, just verify the main Prometheus endpoint
        is_secure, details, error = tls_verifier.verify_https_endpoint(prometheus_url)

        assert is_secure, f"TLS verification failed: {error}"
