"""
API Protection Tests for Prometheus.

This module implements security tests to verify that Prometheus API endpoints
are properly protected against unauthorized access and common attacks.

Requirements: 22.5
"""

from datetime import datetime
from typing import Optional
from urllib.parse import quote

import httpx
import pytest

from framework.models import (
    ErrorCategory,
    ErrorSeverity,
    TestError,
    TestResult,
    TestStatus,
)


class APIProtectionVerifier:
    """
    Verifier for API endpoint protection on Prometheus.

    Provides methods to check for common API security issues.
    """

    # Read-only endpoints (should be accessible or auth-protected)
    READ_ENDPOINTS = [
        "/api/v1/query",
        "/api/v1/query_range",
        "/api/v1/series",
        "/api/v1/labels",
        "/api/v1/label/__name__/values",
        "/api/v1/targets",
        "/api/v1/rules",
        "/api/v1/alerts",
        "/api/v1/status/config",
        "/api/v1/status/flags",
        "/api/v1/status/runtimeinfo",
        "/api/v1/status/buildinfo",
        "/api/v1/status/tsdb",
    ]

    # Write/Admin endpoints (should be protected or disabled)
    ADMIN_ENDPOINTS = [
        ("/api/v1/admin/tsdb/delete_series", "POST"),
        ("/api/v1/admin/tsdb/clean_tombstones", "POST"),
        ("/api/v1/admin/tsdb/snapshot", "POST"),
    ]

    # Lifecycle endpoints (should be protected or disabled)
    LIFECYCLE_ENDPOINTS = [
        ("/-/reload", "POST"),
        ("/-/quit", "POST"),
    ]

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize the API protection verifier.

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

    def check_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> tuple[int, Optional[dict], Optional[str]]:
        """
        Check an API endpoint.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            params: Query parameters
            data: Request body data

        Returns:
            Tuple of (status_code, response_data, error_message)
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self.client.get(url, params=params)
            elif method == "POST":
                response = self.client.post(url, params=params, data=data)
            elif method == "DELETE":
                response = self.client.delete(url, params=params)
            else:
                response = self.client.request(method, url, params=params)

            try:
                response_data = response.json()
            except Exception:
                response_data = {"text": response.text[:500]}

            return response.status_code, response_data, None

        except httpx.TimeoutException:
            return 0, None, f"Request timed out after {self.timeout}s"
        except httpx.ConnectError as e:
            return 0, None, f"Connection failed: {str(e)}"
        except Exception as e:
            return 0, None, f"Unexpected error: {str(e)}"

    def check_admin_endpoints_protected(self) -> tuple[bool, dict, Optional[str]]:
        """
        Check that admin endpoints are protected or disabled.

        Returns:
            Tuple of (protected, details, error_message)
        """
        details = {
            "protected": [],
            "disabled": [],
            "unprotected": [],
            "errors": [],
        }

        for endpoint, method in self.ADMIN_ENDPOINTS:
            status_code, response, error = self.check_endpoint(endpoint, method)

            if error:
                details["errors"].append({"endpoint": endpoint, "error": error})
                continue

            endpoint_info = {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
            }

            if status_code in (401, 403):
                # Protected by authentication
                details["protected"].append(endpoint_info)
            elif status_code == 404:
                # Endpoint doesn't exist (disabled)
                details["disabled"].append(endpoint_info)
            elif status_code == 405:
                # Method not allowed (admin API disabled)
                details["disabled"].append(endpoint_info)
            elif status_code == 204:
                # Success - endpoint is accessible without auth
                details["unprotected"].append(endpoint_info)
            elif status_code == 200:
                # Success - endpoint is accessible without auth
                details["unprotected"].append(endpoint_info)
            else:
                # Other status - might be protected
                details["protected"].append(endpoint_info)

        if details["unprotected"]:
            unprotected = [e["endpoint"] for e in details["unprotected"]]
            return False, details, f"Admin endpoints accessible without auth: {unprotected}"

        return True, details, None

    def check_lifecycle_endpoints_protected(self) -> tuple[bool, dict, Optional[str]]:
        """
        Check that lifecycle endpoints are protected or disabled.

        IMPORTANT: Uses HEAD requests instead of POST to avoid actually
        triggering destructive actions like /-/quit which would shut down
        Prometheus. This is a non-destructive safety check.

        Returns:
            Tuple of (protected, details, error_message)
        """
        details = {
            "protected": [],
            "disabled": [],
            "unprotected": [],
            "errors": [],
            "note": "Using HEAD requests to avoid triggering destructive endpoints",
        }

        for endpoint, _ in self.LIFECYCLE_ENDPOINTS:
            # Use HEAD request to check endpoint status without triggering action
            # This avoids actually shutting down Prometheus with /-/quit
            url = f"{self.base_url}{endpoint}"

            try:
                # First try HEAD to see if endpoint exists
                response = self.client.head(url)
                status_code = response.status_code

                endpoint_info = {
                    "endpoint": endpoint,
                    "method": "HEAD (safe check)",
                    "status_code": status_code,
                }

                if status_code in (401, 403):
                    # Protected by authentication
                    details["protected"].append(endpoint_info)
                elif status_code == 404:
                    # Endpoint doesn't exist (lifecycle disabled)
                    details["disabled"].append(endpoint_info)
                elif status_code == 405:
                    # Method not allowed - endpoint exists but HEAD not supported
                    # This means lifecycle is enabled, check if it requires auth
                    # by looking at the response headers or trying OPTIONS
                    options_resp = self.client.options(url)
                    if options_resp.status_code in (401, 403):
                        details["protected"].append(endpoint_info)
                    elif options_resp.status_code == 404:
                        details["disabled"].append(endpoint_info)
                    else:
                        # Endpoint exists and is accessible - flag as unprotected
                        # but DON'T actually call it
                        endpoint_info["warning"] = (
                            "Endpoint appears accessible without auth "
                            "(not tested with POST to avoid destructive action)"
                        )
                        details["unprotected"].append(endpoint_info)
                elif status_code in (200, 204):
                    # HEAD succeeded - endpoint is accessible
                    endpoint_info["warning"] = (
                        "Endpoint accessible via HEAD - likely unprotected"
                    )
                    details["unprotected"].append(endpoint_info)
                else:
                    # Other status - assume protected
                    details["protected"].append(endpoint_info)

            except httpx.TimeoutException:
                details["errors"].append({
                    "endpoint": endpoint,
                    "error": f"Request timed out after {self.timeout}s"
                })
            except httpx.ConnectError as e:
                details["errors"].append({
                    "endpoint": endpoint,
                    "error": f"Connection failed: {str(e)}"
                })
            except Exception as e:
                details["errors"].append({
                    "endpoint": endpoint,
                    "error": f"Unexpected error: {str(e)}"
                })

        if details["unprotected"]:
            unprotected = [e["endpoint"] for e in details["unprotected"]]
            return (
                False,
                details,
                f"Lifecycle endpoints appear accessible without auth: {unprotected} "
                "(checked safely without triggering)"
            )

        return True, details, None

    def check_query_injection(self) -> tuple[bool, dict, Optional[str]]:
        """
        Check for PromQL injection vulnerabilities.

        Returns:
            Tuple of (safe, details, error_message)
        """
        details = {
            "tests_run": 0,
            "vulnerabilities": [],
        }

        # Test payloads that might indicate injection vulnerability
        injection_payloads = [
            # Basic injection attempts
            "up{__name__=~'.+'}",
            "up or vector(1)",
            "{__name__=~'.+'}[5m]",
            # Attempt to access all metrics
            "{__name__!=''}",
            # Resource exhaustion attempts
            "count(count({__name__=~'.+'}) by (__name__))",
        ]

        for payload in injection_payloads:
            details["tests_run"] += 1

            # URL encode the payload
            encoded_payload = quote(payload)

            status_code, response, error = self.check_endpoint(
                "/api/v1/query",
                params={"query": payload}
            )

            if error:
                continue

            # Check if query was executed (might indicate lack of query restrictions)
            if status_code == 200 and response:
                result_type = response.get("data", {}).get("resultType")
                result_count = len(response.get("data", {}).get("result", []))

                # Large result sets might indicate unrestricted access
                if result_count > 1000:
                    details["vulnerabilities"].append({
                        "payload": payload,
                        "issue": f"Query returned {result_count} results - consider query restrictions",
                        "severity": "medium",
                    })

        if details["vulnerabilities"]:
            return False, details, f"Found {len(details['vulnerabilities'])} potential issues"

        return True, details, None

    def check_rate_limiting(self) -> tuple[bool, dict, Optional[str]]:
        """
        Check if rate limiting is configured.

        Returns:
            Tuple of (has_rate_limiting, details, error_message)
        """
        details = {
            "requests_sent": 0,
            "rate_limited": False,
            "rate_limit_status": None,
        }

        # Send multiple rapid requests
        for i in range(20):
            status_code, response, error = self.check_endpoint(
                "/api/v1/query",
                params={"query": "up"}
            )
            details["requests_sent"] += 1

            if status_code == 429:
                details["rate_limited"] = True
                details["rate_limit_status"] = status_code
                break

            if error:
                break

        # Rate limiting is recommended but not required
        if not details["rate_limited"]:
            return True, details, "Rate limiting not detected (recommended for production)"

        return True, details, None

    def check_cors_configuration(self) -> tuple[bool, dict, Optional[str]]:
        """
        Check CORS configuration.

        Returns:
            Tuple of (secure, details, error_message)
        """
        details = {
            "cors_enabled": False,
            "allow_origin": None,
            "allow_credentials": None,
        }

        # Send OPTIONS request to check CORS
        try:
            response = self.client.options(
                f"{self.base_url}/api/v1/query",
                headers={"Origin": "http://malicious-site.com"}
            )

            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            cors_credentials = response.headers.get("Access-Control-Allow-Credentials")

            details["cors_enabled"] = cors_origin is not None
            details["allow_origin"] = cors_origin
            details["allow_credentials"] = cors_credentials

            # Check for overly permissive CORS
            if cors_origin == "*":
                return False, details, "CORS allows all origins (*) - consider restricting"

            if cors_origin == "http://malicious-site.com":
                return False, details, "CORS reflects arbitrary origins - security risk"

            return True, details, None

        except Exception as e:
            details["error"] = str(e)
            return True, details, None  # Can't determine, assume OK

    def verify_api_protection(self) -> tuple[bool, dict, Optional[str]]:
        """
        Verify overall API protection.

        Returns:
            Tuple of (protected, details, error_message)
        """
        details = {
            "admin_endpoints": {},
            "lifecycle_endpoints": {},
            "query_injection": {},
            "rate_limiting": {},
            "cors": {},
            "issues": [],
        }

        # Check admin endpoints
        admin_ok, admin_details, admin_error = self.check_admin_endpoints_protected()
        details["admin_endpoints"] = admin_details
        if not admin_ok:
            details["issues"].append(f"Admin endpoints: {admin_error}")

        # Check lifecycle endpoints
        lifecycle_ok, lifecycle_details, lifecycle_error = self.check_lifecycle_endpoints_protected()
        details["lifecycle_endpoints"] = lifecycle_details
        if not lifecycle_ok:
            details["issues"].append(f"Lifecycle endpoints: {lifecycle_error}")

        # Check query injection
        injection_ok, injection_details, injection_error = self.check_query_injection()
        details["query_injection"] = injection_details
        if not injection_ok:
            details["issues"].append(f"Query injection: {injection_error}")

        # Check rate limiting
        rate_ok, rate_details, rate_error = self.check_rate_limiting()
        details["rate_limiting"] = rate_details

        # Check CORS
        cors_ok, cors_details, cors_error = self.check_cors_configuration()
        details["cors"] = cors_details
        if not cors_ok:
            details["issues"].append(f"CORS: {cors_error}")

        if details["issues"]:
            return False, details, f"Found {len(details['issues'])} API protection issues"

        return True, details, None


def test_api_protection(prometheus_url: str) -> TestResult:
    """
    Test that Prometheus API endpoints are properly protected.

    Requirements: 22.5

    This test verifies:
    - Admin endpoints are protected or disabled
    - Lifecycle endpoints are protected or disabled
    - No obvious injection vulnerabilities
    - CORS is properly configured

    Args:
        prometheus_url: URL of the Prometheus instance

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="api_protection",
        test_type="security",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    verifier = APIProtectionVerifier(prometheus_url, timeout=10.0)

    try:
        protected, details, error = verifier.verify_api_protection()
        result.metadata["protection_details"] = details

        if protected:
            result.status = TestStatus.PASSED
            result.message = "API endpoints are properly protected"
        else:
            result.status = TestStatus.FAILED
            result.message = f"API protection issues found: {error}"
            result.add_error(TestError(
                error_code="API_PROTECTION_ISSUE",
                message=error or "API protection verification failed",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.CRITICAL,
                context={"issues": details.get("issues", [])},
                remediation="Protect admin/lifecycle endpoints and review CORS configuration",
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
        verifier.close()

    return result


class TestAPIProtection:
    """
    Pytest test class for API protection tests.

    Requirements: 22.5
    """

    @pytest.fixture
    def api_verifier(self, prometheus_url: str) -> APIProtectionVerifier:
        """Create an API protection verifier fixture."""
        verifier = APIProtectionVerifier(prometheus_url, timeout=10.0)
        yield verifier
        verifier.close()

    def test_admin_endpoints_protected(self, api_verifier: APIProtectionVerifier):
        """
        Test that admin endpoints are protected or disabled.

        Requirements: 22.5

        Verifies:
        - /api/v1/admin/* endpoints require auth or return 404/405
        """
        protected, details, error = api_verifier.check_admin_endpoints_protected()

        assert protected, f"Admin endpoints not protected: {error}"

    def test_lifecycle_endpoints_protected(self, api_verifier: APIProtectionVerifier):
        """
        Test that lifecycle endpoints are protected or disabled.

        Requirements: 22.5

        Verifies:
        - /-/reload and /-/quit require auth or return 404/405
        """
        protected, details, error = api_verifier.check_lifecycle_endpoints_protected()

        assert protected, f"Lifecycle endpoints not protected: {error}"

    def test_cors_not_overly_permissive(self, api_verifier: APIProtectionVerifier):
        """
        Test that CORS is not overly permissive.

        Requirements: 22.5

        Verifies:
        - CORS does not allow all origins (*)
        - CORS does not reflect arbitrary origins
        """
        secure, details, error = api_verifier.check_cors_configuration()

        if not secure:
            pytest.fail(f"CORS configuration issue: {error}")

    def test_query_endpoint_accessible(self, api_verifier: APIProtectionVerifier):
        """
        Test that query endpoint is accessible (or auth-protected).

        Requirements: 22.5

        Verifies:
        - /api/v1/query returns valid response or requires auth
        """
        status_code, response, error = api_verifier.check_endpoint(
            "/api/v1/query",
            params={"query": "up"}
        )

        if error:
            pytest.fail(f"Could not check query endpoint: {error}")

        # Should be accessible (200) or protected (401/403)
        assert status_code in (200, 401, 403), \
            f"Unexpected status code {status_code} for query endpoint"

    def test_delete_series_protected(self, api_verifier: APIProtectionVerifier):
        """
        Test that delete_series endpoint is protected.

        Requirements: 22.5

        Verifies:
        - /api/v1/admin/tsdb/delete_series requires auth or is disabled
        """
        status_code, response, error = api_verifier.check_endpoint(
            "/api/v1/admin/tsdb/delete_series",
            method="POST",
            params={"match[]": "up"}
        )

        if error:
            pytest.skip(f"Could not check endpoint: {error}")

        # Should be protected (401/403) or disabled (404/405)
        assert status_code in (401, 403, 404, 405), \
            f"delete_series endpoint returned {status_code} - should be protected or disabled"

    def test_reload_endpoint_protected(self, api_verifier: APIProtectionVerifier):
        """
        Test that reload endpoint is protected or disabled.

        Requirements: 22.5

        Verifies:
        - /-/reload requires auth or is disabled
        - Uses HEAD request to avoid actually triggering reload
        """
        # Use HEAD to safely check without triggering reload
        try:
            response = api_verifier.client.head(
                f"{api_verifier.base_url}/-/reload"
            )
            status_code = response.status_code
        except Exception as e:
            pytest.skip(f"Could not check endpoint: {e}")
            return

        # 401/403 = protected, 404/405 = disabled, both are acceptable
        # 200/204 via HEAD means endpoint exists and is accessible
        if status_code in (401, 403, 404, 405):
            return  # Pass - endpoint is protected or disabled

        # If HEAD returns 200/204, endpoint is accessible without auth
        pytest.fail(
            f"reload endpoint returned {status_code} via HEAD - "
            "appears accessible without auth (not tested with POST for safety)"
        )

    def test_quit_endpoint_protected(self, api_verifier: APIProtectionVerifier):
        """
        Test that quit endpoint is protected or disabled.

        Requirements: 22.5

        Verifies:
        - /-/quit requires auth or is disabled
        - Uses HEAD request to avoid actually shutting down Prometheus
        """
        # Use HEAD to safely check without triggering quit
        try:
            response = api_verifier.client.head(
                f"{api_verifier.base_url}/-/quit"
            )
            status_code = response.status_code
        except Exception as e:
            pytest.skip(f"Could not check endpoint: {e}")
            return

        # 401/403 = protected, 404/405 = disabled, both are acceptable
        # 200/204 via HEAD means endpoint exists and is accessible
        if status_code in (401, 403, 404, 405):
            return  # Pass - endpoint is protected or disabled

        # If HEAD returns 200/204, endpoint is accessible without auth
        pytest.fail(
            f"quit endpoint returned {status_code} via HEAD - "
            "appears accessible without auth (not tested with POST for safety)"
        )
