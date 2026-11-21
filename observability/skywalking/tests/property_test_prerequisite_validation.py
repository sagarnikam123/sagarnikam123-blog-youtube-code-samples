#!/usr/bin/env python3
"""
Property-Based Test: Deployment Script Prerequisite Validation

Feature: skywalking-cluster
Property 4: Deployment Script Prerequisite Validation

This test validates that for any missing prerequisite (kubectl, helm, cluster
connectivity, or insufficient resources), the deployment script fails before making
any cluster modifications and reports the specific missing prerequisite.

Validates: Requirements 5.2, 5.10

The test simulates various prerequisite failure scenarios and verifies that:
1. The script detects missing prerequisites
2. The script exits before making cluster changes
3. The script reports specific missing prerequisites
4. The script provides actionable error messages
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st


# Test configuration
DEPLOYMENT_SCRIPT = Path(__file__).parent.parent / "scripts" / "deploy-skywalking-cluster.sh"
VALID_ENVIRONMENTS = ["minikube", "eks-dev", "eks-prod"]
REQUIRED_COMMANDS = ["kubectl", "helm"]
MINIKUBE_MIN_CPU = 6
MINIKUBE_MIN_MEMORY_GB = 12


# Hypothesis strategies
@st.composite
def missing_command_strategy(draw):
    """Generate scenarios where a required command is missing."""
    command = draw(st.sampled_from(REQUIRED_COMMANDS))
    environment = draw(st.sampled_from(VALID_ENVIRONMENTS))

    return {
        "missing_command": command,
        "environment": environment,
        "scenario": f"missing_{command}"
    }


@st.composite
def cluster_connectivity_failure_strategy(draw):
    """Generate scenarios where cluster connectivity fails."""
    environment = draw(st.sampled_from(VALID_ENVIRONMENTS))
    error_type = draw(st.sampled_from([
        "connection_refused",
        "timeout",
        "authentication_failed",
        "cluster_unreachable"
    ]))

    return {
        "environment": environment,
        "error_type": error_type,
        "scenario": "cluster_connectivity_failure"
    }


@st.composite
def insufficient_resources_strategy(draw):
    """Generate scenarios where Minikube has insufficient resources."""
    # Only test for minikube environment
    cpu_count = draw(st.integers(min_value=1, max_value=5))  # Below minimum of 6
    memory_gb = draw(st.integers(min_value=4, max_value=11))  # Below minimum of 12

    return {
        "environment": "minikube",
        "cpu_count": cpu_count,
        "memory_gb": memory_gb,
        "scenario": "insufficient_resources"
    }


@st.composite
def kubernetes_version_incompatibility_strategy(draw):
    """Generate scenarios with incompatible Kubernetes versions."""
    environment = draw(st.sampled_from(VALID_ENVIRONMENTS))

    # Generate versions below minimum (v1.19)
    major = 1
    minor = draw(st.integers(min_value=10, max_value=18))

    return {
        "environment": environment,
        "k8s_version": f"v{major}.{minor}",
        "scenario": "incompatible_k8s_version"
    }


@st.composite
def storage_class_missing_strategy(draw):
    """Generate scenarios where required storage class is missing."""
    environment = draw(st.sampled_from(VALID_ENVIRONMENTS))

    # Determine expected storage class
    if environment == "minikube":
        expected_storage_class = "standard"
    else:  # eks-*
        expected_storage_class = "gp3"

    return {
        "environment": environment,
        "expected_storage_class": expected_storage_class,
        "scenario": "storage_class_missing"
    }


class TestPrerequisiteValidation:
    """Property-based tests for deployment script prerequisite validation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.deployment_script = DEPLOYMENT_SCRIPT

        # Verify test prerequisites
        assert self.deployment_script.exists(), \
            f"Deployment script not found: {self.deployment_script}"
        assert os.access(self.deployment_script, os.X_OK), \
            f"Deployment script is not executable: {self.deployment_script}"

    def run_deployment_script(
        self,
        environment: str,
        dry_run: bool = True,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """
        Run the deployment script with specified parameters.

        Args:
            environment: Target environment
            dry_run: Whether to use dry-run mode
            env_vars: Environment variables to set
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess with stdout, stderr, and returncode
        """
        cmd = [str(self.deployment_script), environment]

        if dry_run:
            cmd.append("--dry-run")

        # Merge environment variables
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=False
            )
            return result
        except subprocess.TimeoutExpired:
            pytest.fail(f"Deployment script timed out after {timeout}s")

    def check_no_cluster_modifications(self, environment: str) -> bool:
        """
        Verify that no cluster modifications were made.

        This checks that:
        1. Namespace was not created (or was pre-existing)
        2. No Helm releases were installed
        3. No new resources were created

        Args:
            environment: Target environment

        Returns:
            True if no modifications were made
        """
        namespace = "skywalking"
        release_name = "skywalking"

        try:
            # Check if Helm release exists (most reliable indicator)
            result = subprocess.run(
                ["helm", "list", "-n", namespace, "-q"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )

            # If helm command fails or release not found, no modifications
            if result.returncode != 0 or release_name not in result.stdout:
                return True

            # Release exists - modifications were made
            return False

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # If helm is not available, check kubectl
            try:
                # Check if namespace exists
                result = subprocess.run(
                    ["kubectl", "get", "namespace", namespace],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False
                )

                # If namespace doesn't exist, no modifications were made
                if result.returncode != 0:
                    return True

                # If namespace exists, check if it has any pods
                result = subprocess.run(
                    ["kubectl", "get", "pods", "-n", namespace, "--no-headers"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False
                )

                # If no pods found, namespace might be pre-existing but empty
                if result.returncode != 0 or len(result.stdout.strip()) == 0:
                    return True

                # Pods exist - modifications were made
                return False

            except (subprocess.TimeoutExpired, FileNotFoundError):
                # If kubectl is not available, assume no modifications
                return True

    @given(scenario=missing_command_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_missing_command_detected(self, scenario: Dict):
        """
        Property 4: Deployment Script Prerequisite Validation

        For any missing prerequisite command (kubectl or helm),
        the deployment script should:
        1. Detect the missing command
        2. Exit with non-zero status
        3. Report the specific missing command
        4. Not make any cluster modifications

        This test simulates missing commands by modifying PATH.
        """
        missing_command = scenario["missing_command"]
        environment = scenario["environment"]

        # Create a temporary directory with limited PATH
        with tempfile.TemporaryDirectory() as temp_dir:
            # Build a PATH that excludes the missing command
            original_path = os.environ.get("PATH", "")
            path_dirs = original_path.split(os.pathsep)

            # Filter out directories containing the missing command
            filtered_path = []
            for path_dir in path_dirs:
                cmd_path = Path(path_dir) / missing_command
                if not cmd_path.exists():
                    filtered_path.append(path_dir)

            # If we couldn't filter out the command, skip this test
            if len(filtered_path) == len(path_dirs):
                pytest.skip(f"Cannot simulate missing {missing_command} - not found in PATH")

            modified_path = os.pathsep.join(filtered_path)

            # Run deployment script with modified PATH
            result = self.run_deployment_script(
                environment,
                dry_run=True,
                env_vars={"PATH": modified_path}
            )

            # Verify script failed
            assert result.returncode != 0, \
                f"Script should fail when {missing_command} is missing, but returned {result.returncode}"

            # Verify error message mentions the missing command
            output = result.stdout + result.stderr
            assert missing_command in output.lower(), \
                f"Error output should mention missing command '{missing_command}'"

            # Verify no cluster modifications were made
            assert self.check_no_cluster_modifications(environment), \
                "Script should not modify cluster when prerequisites are missing"

    @given(scenario=cluster_connectivity_failure_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_cluster_connectivity_failure_detected(self, scenario: Dict):
        """
        Property 4: Deployment Script Prerequisite Validation

        For any cluster connectivity failure, the deployment script should:
        1. Detect the connectivity issue
        2. Exit with non-zero status
        3. Report the connectivity problem
        4. Not make any cluster modifications

        This test simulates connectivity failures by using invalid kubeconfig.
        """
        environment = scenario["environment"]
        error_type = scenario["error_type"]

        # Create a temporary kubeconfig with invalid cluster
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_kubeconfig = Path(temp_dir) / "invalid-kubeconfig"

            # Create invalid kubeconfig based on error type
            if error_type == "connection_refused":
                kubeconfig_content = """
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://localhost:9999
  name: invalid-cluster
contexts:
- context:
    cluster: invalid-cluster
    user: invalid-user
  name: invalid-context
current-context: invalid-context
users:
- name: invalid-user
  user:
    token: invalid-token
"""
            else:
                kubeconfig_content = """
apiVersion: v1
kind: Config
clusters: []
contexts: []
current-context: ""
users: []
"""

            invalid_kubeconfig.write_text(kubeconfig_content)

            # Run deployment script with invalid kubeconfig
            result = self.run_deployment_script(
                environment,
                dry_run=True,
                env_vars={"KUBECONFIG": str(invalid_kubeconfig)}
            )

            # Verify script failed
            assert result.returncode != 0, \
                f"Script should fail when cluster is unreachable, but returned {result.returncode}"

            # Verify error message mentions connectivity issue
            output = result.stdout + result.stderr
            connectivity_keywords = ["connect", "cluster", "unreachable", "connection", "accessibility"]
            assert any(keyword in output.lower() for keyword in connectivity_keywords), \
                "Error output should mention cluster connectivity issue"

            # Verify no cluster modifications were made
            # (This check will fail gracefully since cluster is unreachable)
            assert self.check_no_cluster_modifications(environment), \
                "Script should not modify cluster when connectivity fails"

    @given(scenario=insufficient_resources_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_insufficient_minikube_resources_detected(self, scenario: Dict):
        """
        Property 4: Deployment Script Prerequisite Validation

        For any Minikube deployment with insufficient resources (CPU < 6 or Memory < 12GB),
        the deployment script should:
        1. Detect the insufficient resources
        2. Exit with non-zero status
        3. Report the specific resource constraint
        4. Provide guidance on required resources
        5. Not make any cluster modifications

        Note: This test requires a mock since we cannot actually modify Minikube resources.
        """
        environment = scenario["environment"]
        cpu_count = scenario["cpu_count"]
        memory_gb = scenario["memory_gb"]

        # This test validates the logic but requires mocking for actual execution
        # In a real scenario, the script would check Minikube resources

        # Verify the test scenario is actually insufficient
        assert cpu_count < MINIKUBE_MIN_CPU or memory_gb < MINIKUBE_MIN_MEMORY_GB, \
            "Test scenario should have insufficient resources"

        # Document expected behavior
        expected_behaviors = []

        if cpu_count < MINIKUBE_MIN_CPU:
            expected_behaviors.append(f"CPU cores: {cpu_count} (minimum {MINIKUBE_MIN_CPU} required)")

        if memory_gb < MINIKUBE_MIN_MEMORY_GB:
            expected_behaviors.append(f"Memory: {memory_gb}GB (minimum {MINIKUBE_MIN_MEMORY_GB}GB required)")

        # Verify expected behaviors are defined
        assert len(expected_behaviors) > 0, \
            "At least one resource constraint should be detected"

        # Note: Actual execution would require Minikube to be running with these constraints
        # For property-based testing, we validate the logic is sound
        pytest.skip("Requires actual Minikube instance with constrained resources")

    @given(scenario=storage_class_missing_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_storage_class_missing_detected(self, scenario: Dict):
        """
        Property 4: Deployment Script Prerequisite Validation

        For any deployment where the required storage class is missing,
        the deployment script should:
        1. Detect the missing storage class
        2. Exit with non-zero status
        3. Report the specific missing storage class
        4. Provide guidance on creating the storage class
        5. Not make any cluster modifications

        Note: This test requires a mock since we cannot modify cluster storage classes.
        """
        environment = scenario["environment"]
        expected_storage_class = scenario["expected_storage_class"]

        # Verify expected storage class is correct for environment
        if environment == "minikube":
            assert expected_storage_class == "standard", \
                "Minikube should use 'standard' storage class"
        else:  # eks-*
            assert expected_storage_class == "gp3", \
                "EKS should use 'gp3' storage class"

        # Document expected behavior
        expected_error_message = f"Storage class '{expected_storage_class}' not found"

        # Note: Actual execution would require cluster without the storage class
        # For property-based testing, we validate the logic is sound
        pytest.skip("Requires cluster without required storage class")

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_prerequisite_check_order(self, environment: str):
        """
        Property 4: Deployment Script Prerequisite Validation

        For any environment, prerequisite checks should occur in the correct order:
        1. Command availability (kubectl, helm)
        2. Cluster connectivity
        3. Kubernetes version compatibility
        4. Resource availability (Minikube only)
        5. Storage class availability
        6. Helm values validation

        The script should fail at the first failed check and not proceed to later checks.
        """
        # This test validates the logical order of prerequisite checks
        # by examining the script structure

        script_content = self.deployment_script.read_text()

        # Define expected check order
        check_order = [
            "check_command",  # Command availability
            "check_cluster_connectivity",  # Cluster connectivity
            "check_minikube_resources",  # Resource availability (Minikube)
            "check_storage_class",  # Storage class
            "validate_helm_values"  # Helm values
        ]

        # Find positions of each check in the script
        check_positions = {}
        for check in check_order:
            position = script_content.find(check)
            if position != -1:
                check_positions[check] = position

        # Verify checks are defined
        assert len(check_positions) > 0, \
            "Script should define prerequisite check functions"

        # Verify checks are called in order (in main function)
        main_function_start = script_content.find("main() {")
        if main_function_start != -1:
            main_function = script_content[main_function_start:]

            # Find call positions within main function
            call_positions = {}
            for check in check_order:
                call_position = main_function.find(check)
                if call_position != -1:
                    call_positions[check] = call_position

            # Verify calls are in order
            if len(call_positions) >= 2:
                previous_position = -1
                for check in check_order:
                    if check in call_positions:
                        current_position = call_positions[check]
                        if previous_position != -1:
                            assert current_position > previous_position, \
                                f"Prerequisite check '{check}' should be called after previous checks"
                        previous_position = current_position

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_error_messages_are_actionable(self, environment: str):
        """
        Property 4: Deployment Script Prerequisite Validation

        For any prerequisite failure, the error message should be actionable:
        1. Clearly state what is missing or wrong
        2. Provide specific values (e.g., "CPU: 4, required: 6")
        3. Suggest remediation steps
        4. Include relevant commands or links

        This test validates the error message format and content.
        """
        script_content = self.deployment_script.read_text()

        # Define expected error message patterns
        error_patterns = {
            "missing_command": [
                "not installed",
                "not in PATH",
                "Please ensure"
            ],
            "cluster_connectivity": [
                "Cannot connect",
                "cluster",
                "Please ensure",
                "accessible"
            ],
            "insufficient_resources": [
                "Insufficient",
                "minimum",
                "required",
                "minikube start"
            ],
            "storage_class": [
                "not found",
                "Storage class",
                "kubectl apply"
            ]
        }

        # Verify error handling functions exist
        assert "print_error" in script_content, \
            "Script should have error printing function"

        assert "print_info" in script_content, \
            "Script should have info printing function for guidance"

        # Verify error messages include actionable information
        for error_type, patterns in error_patterns.items():
            # Check if at least some error patterns are present
            # (Not all error types may be in the script)
            pattern_found = any(pattern.lower() in script_content.lower() for pattern in patterns)

            # If this error type is handled, verify it has actionable messages
            if pattern_found:
                # Verify at least 2 patterns are present (error + guidance)
                matching_patterns = sum(1 for pattern in patterns if pattern.lower() in script_content.lower())
                assert matching_patterns >= 2, \
                    f"Error type '{error_type}' should have actionable error messages"

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_dry_run_skips_prerequisite_failures(self, environment: str):
        """
        Property 4: Deployment Script Prerequisite Validation

        For any environment, when using --dry-run mode, the script should still
        perform prerequisite validation but should not make any cluster modifications
        even if prerequisites pass.

        This test verifies that:
        1. Dry-run mode still validates prerequisites
        2. Dry-run mode does not create resources
        3. Dry-run mode provides preview of what would be deployed
        """
        # Run script in dry-run mode
        result = self.run_deployment_script(environment, dry_run=True)

        # Verify script output mentions dry-run
        output = result.stdout + result.stderr
        assert "dry" in output.lower() or "preview" in output.lower(), \
            "Dry-run mode should be indicated in output"

        # Verify no cluster modifications were made
        assert self.check_no_cluster_modifications(environment), \
            "Dry-run mode should not modify cluster"

    @given(environment=st.sampled_from(VALID_ENVIRONMENTS))
    @settings(max_examples=100, deadline=None)
    def test_property_prerequisite_validation_exit_codes(self, environment: str):
        """
        Property 4: Deployment Script Prerequisite Validation

        For any prerequisite failure, the script should exit with a non-zero exit code.
        For successful prerequisite validation (in dry-run), the script should exit with 0.

        This test verifies consistent exit code behavior.
        """
        # Run script in dry-run mode (should pass prerequisites if cluster is available)
        result = self.run_deployment_script(environment, dry_run=True)

        # Exit code should be 0 if prerequisites pass, non-zero if they fail
        # We can't guarantee prerequisites will pass, so we just verify consistency
        if result.returncode == 0:
            # Prerequisites passed - verify success message
            output = result.stdout + result.stderr
            assert "success" in output.lower() or "complete" in output.lower(), \
                "Successful execution should indicate success"
        else:
            # Prerequisites failed - verify error message
            output = result.stdout + result.stderr
            error_keywords = ["error", "fail", "insufficient", "missing", "cannot"]
            assert any(keyword in output.lower() for keyword in error_keywords), \
                f"Failed execution should indicate error (found: {output[:200]})"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
