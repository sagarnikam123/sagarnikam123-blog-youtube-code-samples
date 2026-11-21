"""
Integration Test: Full Deployment Workflow

This test validates the complete deployment workflow for SkyWalking cluster:
1. Deploy complete cluster
2. Verify all components healthy
3. Run connectivity tests
4. Run ingestion test
5. Verify data in UI

Feature: skywalking-cluster
Validates: All requirements
"""

import os
import subprocess
import time
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.slow
class TestFullDeploymentWorkflow:
    """Integration tests for full deployment workflow."""

    @pytest.fixture(scope="class")
    def environment(self, request):
        """Get environment from command line or default to minikube."""
        return request.config.getoption("--environment", default="minikube")

    @pytest.fixture(scope="class")
    def scripts_dir(self):
        """Return the scripts directory."""
        return Path(__file__).parent.parent / "scripts"

    @pytest.fixture(scope="class")
    def deployed_cluster(self, environment, scripts_dir):
        """Deploy SkyWalking cluster and clean up after tests."""
        print(f"\n=== Deploying SkyWalking cluster for environment: {environment} ===")

        # Deploy cluster
        deploy_script = scripts_dir / "deploy-skywalking-cluster.sh"
        result = subprocess.run(
            ["bash", str(deploy_script), environment],
            capture_output=True,
            text=True,
            timeout=1200  # 20 minutes timeout
        )

        if result.returncode != 0:
            pytest.fail(f"Deployment failed: {result.stderr}")

        print(f"Deployment output:\n{result.stdout}")

        # Wait for cluster to stabilize
        print("Waiting 60 seconds for cluster to stabilize...")
        time.sleep(60)

        yield environment

        # Cleanup after tests
        print(f"\n=== Cleaning up SkyWalking cluster ===")
        cleanup_script = scripts_dir / "cleanup-skywalking-cluster.sh"
        subprocess.run(
            ["bash", str(cleanup_script), environment, "--force"],
            capture_output=True,
            text=True,
            timeout=300
        )

    def test_01_deployment_completes_successfully(self, deployed_cluster):
        """
        Test that deployment completes without errors.

        Validates: Requirements 5.1-5.10
        """
        # If we reach here, deployment fixture succeeded
        assert deployed_cluster is not None
        print(f"✓ Deployment completed successfully for {deployed_cluster}")

    def test_02_all_components_healthy(self, deployed_cluster, scripts_dir):
        """
        Test that all components are healthy after deployment.

        Validates: Requirements 9.1-9.13
        """
        print("\n=== Running health check ===")

        health_script = scripts_dir / "test-health.sh"
        result = subprocess.run(
            ["bash", str(health_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=300
        )

        print(f"Health check output:\n{result.stdout}")

        if result.returncode != 0:
            print(f"Health check errors:\n{result.stderr}")
            pytest.fail(f"Health check failed: {result.stderr}")

        # Verify output contains success indicators
        assert "OAP Server" in result.stdout
        assert "BanyanDB" in result.stdout
        assert "Satellite" in result.stdout
        assert "UI" in result.stdout
        assert "etcd" in result.stdout

        print("✓ All components are healthy")

    def test_03_connectivity_tests_pass(self, deployed_cluster, scripts_dir):
        """
        Test that all connectivity checks pass.

        Validates: Requirements 7.1-7.10
        """
        print("\n=== Running connectivity tests ===")

        connectivity_script = scripts_dir / "test-connectivity.sh"
        result = subprocess.run(
            ["bash", str(connectivity_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=120
        )

        print(f"Connectivity test output:\n{result.stdout}")

        if result.returncode != 0:
            print(f"Connectivity test errors:\n{result.stderr}")
            pytest.fail(f"Connectivity tests failed: {result.stderr}")

        # Verify key connectivity paths
        assert "Agent → Satellite" in result.stdout or "PASS" in result.stdout
        assert "Satellite → OAP" in result.stdout or "PASS" in result.stdout
        assert "OAP → BanyanDB" in result.stdout or "PASS" in result.stdout

        print("✓ All connectivity tests passed")

    def test_04_data_ingestion_works(self, deployed_cluster, scripts_dir):
        """
        Test that data ingestion pipeline works end-to-end.

        Validates: Requirements 8.1-8.10
        """
        print("\n=== Running data ingestion test ===")

        ingestion_script = scripts_dir / "test-data-ingestion.sh"
        result = subprocess.run(
            ["bash", str(ingestion_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes
        )

        print(f"Data ingestion test output:\n{result.stdout}")

        if result.returncode != 0:
            print(f"Data ingestion test errors:\n{result.stderr}")
            pytest.fail(f"Data ingestion test failed: {result.stderr}")

        # Verify data flow through pipeline
        assert "agent" in result.stdout.lower() or "data" in result.stdout.lower()

        print("✓ Data ingestion test passed")

    def test_05_data_visible_in_ui(self, deployed_cluster, scripts_dir):
        """
        Test that ingested data is visible in SkyWalking UI.

        Validates: Requirements 14.1-14.12
        """
        print("\n=== Verifying data in UI ===")

        # Run visualization test
        viz_script = scripts_dir / "test-visualization.sh"

        if not viz_script.exists():
            pytest.skip("Visualization test script not yet implemented")

        result = subprocess.run(
            ["bash", str(viz_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=300
        )

        print(f"Visualization test output:\n{result.stdout}")

        if result.returncode != 0:
            print(f"Visualization test errors:\n{result.stderr}")
            pytest.fail(f"Visualization test failed: {result.stderr}")

        print("✓ Data is visible in UI")

    def test_06_self_observability_metrics_visible(self, deployed_cluster, scripts_dir):
        """
        Test that self-observability metrics are collected and visible.

        Validates: Requirements 10.1-10.9
        """
        print("\n=== Verifying self-observability metrics ===")

        self_obs_script = scripts_dir / "test-self-observability.sh"
        result = subprocess.run(
            ["bash", str(self_obs_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=300
        )

        print(f"Self-observability test output:\n{result.stdout}")

        if result.returncode != 0:
            print(f"Self-observability test errors:\n{result.stderr}")
            pytest.fail(f"Self-observability test failed: {result.stderr}")

        # Verify component metrics are visible
        assert "OAP" in result.stdout or "metrics" in result.stdout.lower()

        print("✓ Self-observability metrics are visible")

    def test_07_deployment_is_idempotent(self, deployed_cluster, scripts_dir):
        """
        Test that running deployment again doesn't cause errors.

        Validates: Requirements 5.3
        """
        print("\n=== Testing deployment idempotency ===")

        deploy_script = scripts_dir / "deploy-skywalking-cluster.sh"
        result = subprocess.run(
            ["bash", str(deploy_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=1200
        )

        print(f"Second deployment output:\n{result.stdout}")

        # Should succeed or indicate resources already exist
        assert result.returncode == 0 or "already exists" in result.stdout.lower()

        print("✓ Deployment is idempotent")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--environment",
        action="store",
        default="minikube",
        help="Environment to test: minikube, eks-dev, eks-prod"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
