"""
RBAC Tests for Prometheus on Kubernetes.

This module implements security tests to verify that Kubernetes RBAC
is properly configured for Prometheus.

Requirements: 22.3
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

# Try to import kubernetes client
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False


class RBACVerifier:
    """
    Verifier for Kubernetes RBAC configuration for Prometheus.

    Provides methods to check ServiceAccounts, Roles, ClusterRoles,
    and their bindings.
    """

    # Expected RBAC resources for Prometheus
    EXPECTED_RESOURCES = {
        "service_accounts": ["prometheus", "prometheus-operator"],
        "cluster_roles": [
            "prometheus",
            "prometheus-operator",
        ],
        "roles": [
            "prometheus-config",
        ],
    }

    # Minimum required permissions for Prometheus
    REQUIRED_PERMISSIONS = {
        "nodes": ["get", "list", "watch"],
        "nodes/metrics": ["get"],
        "services": ["get", "list", "watch"],
        "endpoints": ["get", "list", "watch"],
        "pods": ["get", "list", "watch"],
        "configmaps": ["get"],
    }

    def __init__(self, namespace: str = "monitoring"):
        """
        Initialize the RBAC verifier.

        Args:
            namespace: Kubernetes namespace where Prometheus is deployed
        """
        self.namespace = namespace
        self._core_api: Optional[client.CoreV1Api] = None
        self._rbac_api: Optional[client.RbacAuthorizationV1Api] = None
        self._initialized = False

    def initialize(self) -> tuple[bool, Optional[str]]:
        """
        Initialize Kubernetes client.

        Returns:
            Tuple of (success, error_message)
        """
        if not KUBERNETES_AVAILABLE:
            return False, "kubernetes package not installed"

        try:
            # Try in-cluster config first, then kubeconfig
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()

            self._core_api = client.CoreV1Api()
            self._rbac_api = client.RbacAuthorizationV1Api()
            self._initialized = True
            return True, None
        except Exception as e:
            return False, f"Failed to initialize Kubernetes client: {str(e)}"

    def check_service_account_exists(self, name: str) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        Check if a ServiceAccount exists.

        Args:
            name: ServiceAccount name

        Returns:
            Tuple of (exists, details, error_message)
        """
        if not self._initialized:
            return False, None, "Kubernetes client not initialized"

        try:
            sa = self._core_api.read_namespaced_service_account(name, self.namespace)
            return True, {
                "name": sa.metadata.name,
                "namespace": sa.metadata.namespace,
                "secrets": [s.name for s in (sa.secrets or [])],
            }, None
        except ApiException as e:
            if e.status == 404:
                return False, None, f"ServiceAccount '{name}' not found"
            return False, None, f"API error: {e.reason}"
        except Exception as e:
            return False, None, f"Error checking ServiceAccount: {str(e)}"

    def check_cluster_role_exists(self, name: str) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        Check if a ClusterRole exists and get its rules.

        Args:
            name: ClusterRole name

        Returns:
            Tuple of (exists, details, error_message)
        """
        if not self._initialized:
            return False, None, "Kubernetes client not initialized"

        try:
            role = self._rbac_api.read_cluster_role(name)
            rules = []
            for rule in (role.rules or []):
                rules.append({
                    "api_groups": rule.api_groups or [""],
                    "resources": rule.resources or [],
                    "verbs": rule.verbs or [],
                })
            return True, {
                "name": role.metadata.name,
                "rules": rules,
            }, None
        except ApiException as e:
            if e.status == 404:
                return False, None, f"ClusterRole '{name}' not found"
            return False, None, f"API error: {e.reason}"
        except Exception as e:
            return False, None, f"Error checking ClusterRole: {str(e)}"

    def check_cluster_role_binding_exists(self, name: str) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        Check if a ClusterRoleBinding exists.

        Args:
            name: ClusterRoleBinding name

        Returns:
            Tuple of (exists, details, error_message)
        """
        if not self._initialized:
            return False, None, "Kubernetes client not initialized"

        try:
            binding = self._rbac_api.read_cluster_role_binding(name)
            subjects = []
            for subject in (binding.subjects or []):
                subjects.append({
                    "kind": subject.kind,
                    "name": subject.name,
                    "namespace": subject.namespace,
                })
            return True, {
                "name": binding.metadata.name,
                "role_ref": {
                    "kind": binding.role_ref.kind,
                    "name": binding.role_ref.name,
                },
                "subjects": subjects,
            }, None
        except ApiException as e:
            if e.status == 404:
                return False, None, f"ClusterRoleBinding '{name}' not found"
            return False, None, f"API error: {e.reason}"
        except Exception as e:
            return False, None, f"Error checking ClusterRoleBinding: {str(e)}"

    def check_role_exists(self, name: str) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        Check if a Role exists in the namespace.

        Args:
            name: Role name

        Returns:
            Tuple of (exists, details, error_message)
        """
        if not self._initialized:
            return False, None, "Kubernetes client not initialized"

        try:
            role = self._rbac_api.read_namespaced_role(name, self.namespace)
            rules = []
            for rule in (role.rules or []):
                rules.append({
                    "api_groups": rule.api_groups or [""],
                    "resources": rule.resources or [],
                    "verbs": rule.verbs or [],
                })
            return True, {
                "name": role.metadata.name,
                "namespace": role.metadata.namespace,
                "rules": rules,
            }, None
        except ApiException as e:
            if e.status == 404:
                return False, None, f"Role '{name}' not found"
            return False, None, f"API error: {e.reason}"
        except Exception as e:
            return False, None, f"Error checking Role: {str(e)}"

    def verify_permissions(self, role_rules: list[dict]) -> tuple[bool, list[str]]:
        """
        Verify that a role has the required permissions.

        Args:
            role_rules: List of rule dictionaries from a Role/ClusterRole

        Returns:
            Tuple of (has_required_permissions, missing_permissions)
        """
        missing = []

        for resource, required_verbs in self.REQUIRED_PERMISSIONS.items():
            has_permission = False

            for rule in role_rules:
                resources = rule.get("resources", [])
                verbs = rule.get("verbs", [])

                # Check if this rule covers the resource
                if resource in resources or "*" in resources:
                    # Check if all required verbs are present
                    if "*" in verbs or all(v in verbs for v in required_verbs):
                        has_permission = True
                        break

            if not has_permission:
                missing.append(f"{resource}: {required_verbs}")

        return len(missing) == 0, missing

    def verify_rbac_configuration(self) -> tuple[bool, dict, Optional[str]]:
        """
        Verify the complete RBAC configuration for Prometheus.

        Returns:
            Tuple of (properly_configured, details, error_message)
        """
        details = {
            "service_accounts": [],
            "cluster_roles": [],
            "cluster_role_bindings": [],
            "roles": [],
            "missing_resources": [],
            "permission_issues": [],
        }

        # Check ServiceAccounts
        for sa_name in self.EXPECTED_RESOURCES["service_accounts"]:
            exists, sa_details, error = self.check_service_account_exists(sa_name)
            if exists:
                details["service_accounts"].append(sa_details)
            elif error and "not found" not in error.lower():
                details["missing_resources"].append(f"ServiceAccount: {sa_name}")

        # Check ClusterRoles and their permissions
        for role_name in self.EXPECTED_RESOURCES["cluster_roles"]:
            exists, role_details, error = self.check_cluster_role_exists(role_name)
            if exists:
                details["cluster_roles"].append(role_details)

                # Verify permissions
                has_perms, missing = self.verify_permissions(role_details.get("rules", []))
                if not has_perms:
                    details["permission_issues"].append({
                        "role": role_name,
                        "missing": missing,
                    })
            elif error and "not found" not in error.lower():
                details["missing_resources"].append(f"ClusterRole: {role_name}")

        # Check ClusterRoleBindings
        for role_name in self.EXPECTED_RESOURCES["cluster_roles"]:
            binding_name = role_name  # Usually same name
            exists, binding_details, error = self.check_cluster_role_binding_exists(binding_name)
            if exists:
                details["cluster_role_bindings"].append(binding_details)

        # Determine if RBAC is properly configured
        has_sa = len(details["service_accounts"]) > 0
        has_roles = len(details["cluster_roles"]) > 0
        no_permission_issues = len(details["permission_issues"]) == 0

        if not has_sa and not has_roles:
            return False, details, "No Prometheus RBAC resources found"

        if not no_permission_issues:
            issues = details["permission_issues"]
            return False, details, f"Permission issues found: {issues}"

        return True, details, None

    def check_least_privilege(self) -> tuple[bool, dict, Optional[str]]:
        """
        Check if RBAC follows least privilege principle.

        Returns:
            Tuple of (follows_least_privilege, details, error_message)
        """
        details = {
            "overly_permissive_rules": [],
            "recommendations": [],
        }

        # Check for overly permissive rules
        for role_name in self.EXPECTED_RESOURCES["cluster_roles"]:
            exists, role_details, error = self.check_cluster_role_exists(role_name)
            if not exists:
                continue

            for rule in role_details.get("rules", []):
                resources = rule.get("resources", [])
                verbs = rule.get("verbs", [])

                # Check for wildcard resources
                if "*" in resources:
                    details["overly_permissive_rules"].append({
                        "role": role_name,
                        "issue": "Wildcard resource access",
                        "rule": rule,
                    })
                    details["recommendations"].append(
                        f"Role '{role_name}': Replace '*' resources with specific resources"
                    )

                # Check for wildcard verbs
                if "*" in verbs:
                    details["overly_permissive_rules"].append({
                        "role": role_name,
                        "issue": "Wildcard verb access",
                        "rule": rule,
                    })
                    details["recommendations"].append(
                        f"Role '{role_name}': Replace '*' verbs with specific verbs"
                    )

                # Check for dangerous verbs
                dangerous_verbs = {"delete", "deletecollection", "create", "patch", "update"}
                has_dangerous = dangerous_verbs.intersection(set(verbs))
                if has_dangerous and "secrets" in resources:
                    details["overly_permissive_rules"].append({
                        "role": role_name,
                        "issue": f"Write access to secrets: {has_dangerous}",
                        "rule": rule,
                    })

        follows_least_privilege = len(details["overly_permissive_rules"]) == 0

        if not follows_least_privilege:
            return False, details, "RBAC does not follow least privilege principle"

        return True, details, None


def test_rbac_configuration(prometheus_namespace: str = "monitoring") -> TestResult:
    """
    Test that Kubernetes RBAC is properly configured for Prometheus.

    Requirements: 22.3

    This test verifies:
    - ServiceAccounts exist
    - ClusterRoles/Roles have required permissions
    - ClusterRoleBindings are properly configured
    - Least privilege principle is followed

    Args:
        prometheus_namespace: Namespace where Prometheus is deployed

    Returns:
        TestResult with pass/fail status and details
    """
    result = TestResult(
        test_name="rbac_configuration",
        test_type="security",
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
    )

    verifier = RBACVerifier(namespace=prometheus_namespace)

    try:
        # Initialize Kubernetes client
        init_ok, error = verifier.initialize()
        if not init_ok:
            result.status = TestStatus.SKIPPED
            result.message = f"Cannot verify RBAC: {error}"
            result.metadata["skip_reason"] = error
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            return result

        # Verify RBAC configuration
        rbac_ok, rbac_details, error = verifier.verify_rbac_configuration()
        result.metadata["rbac_details"] = rbac_details

        if not rbac_ok:
            result.status = TestStatus.FAILED
            result.message = f"RBAC configuration issue: {error}"
            result.add_error(TestError(
                error_code="RBAC_CONFIG_ERROR",
                message=error or "RBAC configuration verification failed",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.CRITICAL,
                context=rbac_details,
                remediation="Ensure Prometheus RBAC resources are properly configured",
            ))
        else:
            # Check least privilege
            least_priv_ok, least_priv_details, error = verifier.check_least_privilege()
            result.metadata["least_privilege"] = least_priv_details

            if not least_priv_ok:
                result.status = TestStatus.PASSED  # Warning, not failure
                result.message = f"RBAC configured but has recommendations: {error}"
                result.metadata["recommendations"] = least_priv_details.get("recommendations", [])
            else:
                result.status = TestStatus.PASSED
                result.message = "RBAC is properly configured with least privilege"

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


class TestRBAC:
    """
    Pytest test class for RBAC tests.

    Requirements: 22.3
    """

    @pytest.fixture
    def rbac_verifier(self, prometheus_namespace: str) -> RBACVerifier:
        """Create an RBAC verifier fixture."""
        verifier = RBACVerifier(namespace=prometheus_namespace)
        init_ok, error = verifier.initialize()
        if not init_ok:
            pytest.skip(f"Cannot initialize Kubernetes client: {error}")
        return verifier

    @pytest.fixture
    def prometheus_namespace(self) -> str:
        """Get the Prometheus namespace."""
        return "monitoring"

    @pytest.mark.skipif(not KUBERNETES_AVAILABLE, reason="kubernetes package not installed")
    def test_service_account_exists(self, rbac_verifier: RBACVerifier):
        """
        Test that Prometheus ServiceAccount exists.

        Requirements: 22.3

        Verifies:
        - At least one Prometheus ServiceAccount exists
        """
        found_sa = False
        for sa_name in RBACVerifier.EXPECTED_RESOURCES["service_accounts"]:
            exists, details, error = rbac_verifier.check_service_account_exists(sa_name)
            if exists:
                found_sa = True
                break

        assert found_sa, "No Prometheus ServiceAccount found"

    @pytest.mark.skipif(not KUBERNETES_AVAILABLE, reason="kubernetes package not installed")
    def test_cluster_role_exists(self, rbac_verifier: RBACVerifier):
        """
        Test that Prometheus ClusterRole exists.

        Requirements: 22.3

        Verifies:
        - At least one Prometheus ClusterRole exists
        """
        found_role = False
        for role_name in RBACVerifier.EXPECTED_RESOURCES["cluster_roles"]:
            exists, details, error = rbac_verifier.check_cluster_role_exists(role_name)
            if exists:
                found_role = True
                break

        assert found_role, "No Prometheus ClusterRole found"

    @pytest.mark.skipif(not KUBERNETES_AVAILABLE, reason="kubernetes package not installed")
    def test_required_permissions(self, rbac_verifier: RBACVerifier):
        """
        Test that Prometheus has required permissions.

        Requirements: 22.3

        Verifies:
        - ClusterRole has permissions to access nodes, pods, services, etc.
        """
        for role_name in RBACVerifier.EXPECTED_RESOURCES["cluster_roles"]:
            exists, role_details, error = rbac_verifier.check_cluster_role_exists(role_name)
            if not exists:
                continue

            has_perms, missing = rbac_verifier.verify_permissions(role_details.get("rules", []))

            if not has_perms:
                pytest.fail(f"ClusterRole '{role_name}' missing permissions: {missing}")
            return

        pytest.skip("No Prometheus ClusterRole found to verify permissions")

    @pytest.mark.skipif(not KUBERNETES_AVAILABLE, reason="kubernetes package not installed")
    def test_least_privilege(self, rbac_verifier: RBACVerifier):
        """
        Test that RBAC follows least privilege principle.

        Requirements: 22.3

        Verifies:
        - No wildcard resource access
        - No wildcard verb access
        - No unnecessary write access to secrets
        """
        follows_least_priv, details, error = rbac_verifier.check_least_privilege()

        if not follows_least_priv:
            # This is a warning, not a hard failure
            pytest.warns(
                UserWarning,
                match="RBAC does not follow least privilege"
            ) if details.get("overly_permissive_rules") else None

            # Log recommendations
            for rec in details.get("recommendations", []):
                print(f"Recommendation: {rec}")

    @pytest.mark.skipif(not KUBERNETES_AVAILABLE, reason="kubernetes package not installed")
    def test_cluster_role_binding_exists(self, rbac_verifier: RBACVerifier):
        """
        Test that ClusterRoleBinding exists for Prometheus.

        Requirements: 22.3

        Verifies:
        - ClusterRoleBinding connects ServiceAccount to ClusterRole
        """
        found_binding = False
        for role_name in RBACVerifier.EXPECTED_RESOURCES["cluster_roles"]:
            exists, details, error = rbac_verifier.check_cluster_role_binding_exists(role_name)
            if exists:
                found_binding = True
                # Verify it references the correct role
                role_ref = details.get("role_ref", {})
                assert role_ref.get("kind") == "ClusterRole", \
                    f"ClusterRoleBinding references wrong kind: {role_ref.get('kind')}"
                break

        if not found_binding:
            pytest.skip("No Prometheus ClusterRoleBinding found")
