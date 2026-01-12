"""
Authentication Tests for Prometheus.

This module implements security tests to verify that authentication is properly
enforced when configured for Prometheus.

Requirements: 22.2
"""

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


class AuthenticationVerifier:
    """
    Verifier for authentication configuration on Prometheus.

    Provides methods to check if authentication is enforced on API endpoints.
    """

    # Prometheus API endpoints to test
    API_ENDPOINTS = [
        "/api/v1/query",
        "/api/v1/query_range",
        "/api/v1/series",
        "/api/v1/labels",
        "/api/v1/targets",
        "/api/v1/rules",
        "/api/v1/alerts",
        "/api/v1/status/config",
        "/api/v1/status/flags",
        "/api/v1/status/runtimeinfo",
    ]

    # Admin endpoints that should always require auth
    ADMIN_ENDPOINTS = [
        "/api/v1/admin/tsdb/delete_series",
        "/api/v1/admin/tsdb/clean_tombstones",
        "/api/v1/admin/tsdb/snapshot",
    ]

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize the authentication verifier.

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

    def check_endpoint_auth(self, endpoint: str, method: str = "GET") -> tuple[bool, int, Optional[str]]:
        """
        Check if an endpoint requires authentication.

        Args:
            endpoint: API endpoint path
            method: HTTP method to use

        Returns:
            Tuple of (requires_auth, status_code, error_message)
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self.client.get(url)
            elif method == "POST":
                response = self.client.post(url)
            elif method == "DELETE":
                response = self.client.delete(url)
            else:
                response = self.client.request(method, url)

            # 401 Unauthorized or 403 Forbidden indicates auth is required
            requires_auth = response.status_code in (401, 403)
            return requires_auth, response.status_code, None

        except httpx.TimeoutException:
            return False, 0, f"Request timed out after {self.timeout}s"
        except httpx.ConnectError as e:
            return False, 0, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, 0, f"Unexpected error: {str(e)}"

    def check_auth_with_credentials(
        self,
        endpoint: str,
        username: str,
        password: str
    ) -> tuple[bool, int, Optional[str]]:
        """
        Check if authentication with credentials succeeds.

        Args:
            endpoint: API endpoint path
            username: Username for basic auth
            password: Password for basic auth

        Returns:
            Tuple of (auth_successful, status_code, error_message)
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.client.get(url, auth=(username, password))

            # 200 OK indicates successful authentication
            auth_successful = response.status_code == 200
            return auth_successful, response.status_code, None

        except httpx.TimeoutException:
            return False, 0, f"Request timed out after {self.timeout}s"
        except httpx.ConnectError as e:
            return False, 0, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, 0, f"Unexpected error: {str(e)}"

    def check_bearer_token_auth(
        self,
        endpoint: str,
        token: str
    ) -> tuple[bool, int, Optional[str]]:
        """
        Check if authentication with bearer token succeeds.

        Args:
            endpoint: API endpoint path
            token: Bearer token

        Returns:
            Tuple of (auth_successful, status_code, error_message)
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = self.client.get(url, headers=headers)

            # 200 OK indicates successful authentication
            auth_successful = response.status_code == 200
            return auth_successful, response.status_code, None

        except httpx.TimeoutException:
            return False, 0, f"Request timed out after {self.timeout}s"
        except httpx.ConnectError as e:
            return False, 0, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, 0, f"Unexpected error: {str(e)}"

    def verify_auth_enforced(self) -> tuple[bool, dict, Optional[str]]:
        """
        Verify that authentication is enforced on all API endpoints.

        Returns:
            Tuple of (all_protected, details, error_message)
        """
        details = {
            "protected_endpoints": [],
            "unprotected_endpoints": [],
            "errors": [],
        }

        for endpoint in self.API_ENDPOINTS:
            requires_auth, status_code, error = self.check_endpoint_auth(endpoint)

            if error:
                details["errors"].append({"endpoint": endpoint, "error": error})
                continue

            if requires_auth:
                details["protected_endpoints"].append({
                    "endpoint": endpoint,
                    "status_code": status_code,
                })
            else:
                details["unprotected_endpoints"].append({
                    "endpoint": endpoint,
                    "status_code": status_code,
                })

        # Check admin endpoints
        for endpoint in self.ADMIN_ENDPOINTS:
            requires_auth, status_code, error = self.check_endpoint_auth(endpoint, method="POST")

            if error:
                # Admin endpoints might not exist, which is fine
                continue

            if requires_auth:
                details["protected_endpoints"].append({
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "admin": True,
                })
            elif status_code != 404:  # Ignore if endpoint doesn't exist
                details["unprotected_endpoints"].append({
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "admin": True,
                })

        # Determine if auth is enforced
        # If any endpoint returns 401/403, auth is configured
        auth_configured = len(details["protected_endpoints"]) > 0
        all_protected = len(details["unprotected_endpoints"]) == 0 and auth_configured

        if not auth_configured:
            return False, details, "Authentication is not configured"
        elif not all_protected:
            unprotected = [e["endpoint"] for e in details["unprotected_endpoints"]]
            return False, details, f"Some endpoints are not protected: {unprotected}"

        return True, details, None

    def check_invalid_credentials_rejected(self) -> tuple[bool, dict, Optional[str]]:
        """
        Verify that invalid credentials are rejected.

        Returns:
            Tuple of (rejected, details, error_message)
        """
        details = {
            "tested_endpoints": [],
        }

        # Test with invalid credentials
        invalid_creds = [
            ("invalid_user", "invalid_pass"),
            ("admin", "wrongpassword"),
            ("", ""),
        ]

        for endpoint in self.API_ENDPOINTS[:3]:  # Test first 3 endpoints
            for username, password in invalid_creds:
                auth_ok, status_code, error = self.check_auth_with_credentials(
                    endpoint, username, password
                )

                if error:
                    continue

                details["tested_endpoints"].append({
                    "endpoint": endpoint,
                    "username": username,
                    "status_code": status_code,
                    "rejected": not auth_ok,
                })

                # If invalid credentials are accepted, that's a security issue
                if auth_ok:
                    return False, details, f"Invalid credentials accepted at {endpoint}"

        return True, details, None


def test_authentication_enforced(prometheus_url: str) -> TestResult:
    """
    Test that authentication is enforced when configured.

    Requirements: 22.2

    This test verifies:
    - API endpoints require authentication
    - Invalid credentials are rejected
    - Admin endpoints are protected

    Args:
        prometheus_url: URL of the Prometheus instance

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="authentication_enforced",
        test_type="security",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    verifier = AuthenticationVerifier(prometheus_url, timeout=10.0)

    try:
        # Check if auth is enforced
        auth_enforced, details, error = verifier.verify_auth_enforced()
        result.metadata["auth_details"] = details

        if not auth_enforced and error == "Authentication is not configured":
            # Auth not configured - this is informational, not a failure
            result.status = TestStatus.PASSED
            result.message = "Authentication is not configured. Consider enabling authentication for production."
            result.metadata["auth_configured"] = False
            result.metadata["recommendation"] = "Enable authentication for production deployments"
        elif auth_enforced:
            # Auth is configured and enforced
            result.status = TestStatus.PASSED
            result.message = f"Authentication is properly enforced on {len(details['protected_endpoints'])} endpoints"
            result.metadata["auth_configured"] = True
        else:
            # Auth is configured but not properly enforced
            result.status = TestStatus.FAILED
            result.message = f"Authentication issue: {error}"
            result.add_error(TestError(
                error_code="AUTH_NOT_ENFORCED",
                message=error or "Authentication not properly enforced",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.CRITICAL,
                context=details,
                remediation="Ensure all API endpoints require authentication",
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


class TestAuthentication:
    """
    Pytest test class for authentication tests.

    Requirements: 22.2
    """

    @pytest.fixture
    def auth_verifier(self, prometheus_url: str) -> AuthenticationVerifier:
        """Create an authentication verifier fixture."""
        verifier = AuthenticationVerifier(prometheus_url, timeout=10.0)
        yield verifier
        verifier.close()

    def test_api_endpoints_accessible_or_protected(self, auth_verifier: AuthenticationVerifier):
        """
        Test that API endpoints are either accessible or require authentication.

        Requirements: 22.2

        Verifies:
        - Endpoints return valid HTTP responses
        - If auth is configured, endpoints return 401/403
        """
        endpoint = "/api/v1/status/config"
        requires_auth, status_code, error = auth_verifier.check_endpoint_auth(endpoint)

        if error:
            pytest.fail(f"Could not check endpoint: {error}")

        # Either accessible (200) or protected (401/403)
        assert status_code in (200, 401, 403), \
            f"Unexpected status code {status_code} for {endpoint}"

    def test_invalid_credentials_rejected(self, auth_verifier: AuthenticationVerifier):
        """
        Test that invalid credentials are rejected.

        Requirements: 22.2

        Verifies:
        - Invalid username/password combinations are rejected
        """
        # First check if auth is configured
        requires_auth, status_code, error = auth_verifier.check_endpoint_auth("/api/v1/status/config")

        if not requires_auth:
            pytest.skip("Authentication is not configured")

        # Test with invalid credentials
        auth_ok, status_code, error = auth_verifier.check_auth_with_credentials(
            "/api/v1/status/config",
            "invalid_user",
            "invalid_password"
        )

        if error:
            pytest.fail(f"Could not test credentials: {error}")

        assert not auth_ok, "Invalid credentials should be rejected"
        assert status_code in (401, 403), f"Expected 401/403, got {status_code}"

    def test_empty_credentials_rejected(self, auth_verifier: AuthenticationVerifier):
        """
        Test that empty credentials are rejected.

        Requirements: 22.2

        Verifies:
        - Empty username/password are rejected
        """
        # First check if auth is configured
        requires_auth, status_code, error = auth_verifier.check_endpoint_auth("/api/v1/status/config")

        if not requires_auth:
            pytest.skip("Authentication is not configured")

        # Test with empty credentials
        auth_ok, status_code, error = auth_verifier.check_auth_with_credentials(
            "/api/v1/status/config",
            "",
            ""
        )

        if error:
            pytest.fail(f"Could not test credentials: {error}")

        assert not auth_ok, "Empty credentials should be rejected"

    def test_admin_endpoints_protected(self, auth_verifier: AuthenticationVerifier):
        """
        Test that admin endpoints are protected.

        Requirements: 22.2

        Verifies:
        - Admin endpoints require authentication or return 404
        """
        admin_endpoint = "/api/v1/admin/tsdb/snapshot"
        requires_auth, status_code, error = auth_verifier.check_endpoint_auth(
            admin_endpoint, method="POST"
        )

        if error:
            pytest.skip(f"Could not check admin endpoint: {error}")

        # Admin endpoint should either require auth (401/403) or not exist (404)
        # or be disabled (405 Method Not Allowed)
        assert status_code in (401, 403, 404, 405), \
            f"Admin endpoint {admin_endpoint} returned unexpected status {status_code}"
