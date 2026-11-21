"""
Security tests for Prometheus configuration validation.

This package contains security tests for verifying Prometheus security configuration:
- TLS verification (test_tls.py)
- Authentication enforcement (test_auth.py)
- Kubernetes RBAC (test_rbac.py)
- Data exposure checks (test_data_exposure.py)
- API endpoint protection (test_api_protection.py)
- Vulnerability scanning (test_vulnerabilities.py)

Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6
"""

from security.test_tls import TLSVerifier, test_tls_configuration
from security.test_auth import AuthenticationVerifier, test_authentication_enforced
from security.test_rbac import RBACVerifier, test_rbac_configuration
from security.test_data_exposure import DataExposureChecker, test_data_exposure
from security.test_api_protection import APIProtectionVerifier, test_api_protection
from security.test_vulnerabilities import VulnerabilityScanner, test_vulnerability_scan

__all__ = [
    # TLS
    "TLSVerifier",
    "test_tls_configuration",
    # Authentication
    "AuthenticationVerifier",
    "test_authentication_enforced",
    # RBAC
    "RBACVerifier",
    "test_rbac_configuration",
    # Data Exposure
    "DataExposureChecker",
    "test_data_exposure",
    # API Protection
    "APIProtectionVerifier",
    "test_api_protection",
    # Vulnerabilities
    "VulnerabilityScanner",
    "test_vulnerability_scan",
]
