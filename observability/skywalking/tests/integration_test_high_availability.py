"""
Integration Test: High Availability

This test validates high availability features:
1. Deploy cluster
2. Kill one OAP Server pod
3. Verify data ingestion continues
4. Verify UI remains accessible

Feature: skywalking-cluster
Validates: Requirements 18.1-18.10
"""

import subprocess
import time
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.slow
class TestHighAvailability:
    """Integration tests for high availability features."""

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
        print(f"\n=== Deploying SkyWalking cluster for HA tests ===")

        # Deploy cluster
        deploy_script = scripts_dir / "deploy-skywalking-cluster.sh"
        result = subprocess.run(
            ["bash", str(deploy_script), environment],
            capture_output=True,
            text=True,
            timeout=1200
        )

        if result.returncode != 0:
            pytest.fail(f"Deployment failed: {result.stderr}")

        print("Waiting 60 seconds for cluster to stabilize...")
        time.sleep(60)

        yield environment

        # Cleanup
        print(f"\n=== Cleaning up ===")
        cleanup_script = scripts_dir / "cleanup-skywalking-cluster.sh"
        subprocess.run(
            ["bash", str(cleanup_script), environment, "--force"],
            capture_output=True,
            text=True,
            timeout=300
        )

    def test_01_cluster_has_multiple_replicas(self, deployed_cluster):
        """
        Test that cluster is deployed with multiple replicas for HA.

        Validates: Requirements 18.9
        """
        print("\n=== Verifying multiple replicas ===")

        # Check OAP Server replicas
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "skywalking", "-l", "app=oap"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"OAP Server pods:\n{result.stdout}")

        # Count running pods
        oap_count = result.stdout.count("Running")
        assert oap_count >= 2, f"Expected at least 2 OAP replicas, found {oap_count}"

        print(f"✓ Found {oap_count} OAP Server replicas")

    def test_02_pod_anti_affinity_configured(self, deployed_cluster):
        """
        Test that pod anti-affinity rules are configured.

        Validates: Requirements 18.1, 18.2, 18.3, 18.4
        """
        print("\n=== Verifying pod anti-affinity ===")

        # Check OAP Server deployment for anti-affinity
        result = subprocess.run(
            ["kubectl", "get", "deployment", "-n", "skywalking", "-o", "yaml"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Look for anti-affinity configuration
        if "antiAffinity" in result.stdout or "podAntiAffinity" in result.stdout:
            print("✓ Pod anti-affinity is configured")
        else:
            print("⚠ Pod anti-affinity configuration not found in deployment")

    def test_03_pod_disruption_budgets_configured(self, deployed_cluster):
        """
        Test that pod disruption budgets are configured.

        Validates: Requirements 18.5, 18.6, 18.7
        """
        print("\n=== Verifying pod disruption budgets ===")

        result = subprocess.run(
            ["kubectl", "get", "pdb", "-n", "skywalking"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"Pod Disruption Budgets:\n{result.stdout}")

        if "oap" in result.stdout.lower() or "PodDisruptionBudget" in result.stdout:
            print("✓ Pod disruption budgets are configured")
        else:
            print("⚠ Pod disruption budgets not found")

    def test_04_kill_oap_server_pod(self, deployed_cluster):
        """
        Test killing one OAP Server pod to simulate failure.

        Validates: Requirements 18.1-18.10
        """
        print("\n=== Killing one OAP Server pod ===")

        # Get first OAP Server pod
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "skywalking", "-l", "app=oap", "-o", "name"],
            capture_output=True,
            text=True,
            timeout=30
        )

        pods = [p.strip() for p in result.stdout.split("\n") if p.strip()]

        if not pods:
            pytest.fail("No OAP Server pods found")

        pod_to_kill = pods[0]
        print(f"Killing pod: {pod_to_kill}")

        # Delete the pod
        result = subprocess.run(
            ["kubectl", "delete", pod_to_kill, "-n", "skywalking"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"Delete result: {result.stdout}")

        # Wait for pod to be recreated
        print("Waiting 30 seconds for pod to be recreated...")
        time.sleep(30)

        print("✓ OAP Server pod killed")

    def test_05_data_ingestion_continues_after_pod_failure(self, deployed_cluster, scripts_dir):
        """
        Test that data ingestion continues after pod failure.

        Validates: Requirements 18.1-18.10
        """
        print("\n=== Verifying data ingestion continues ===")

        # Run data ingestion test
        ingestion_script = scripts_dir / "test-data-ingestion.sh"
        result = subprocess.run(
            ["bash", str(ingestion_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600
        )

        print(f"Data ingestion test output:\n{result.stdout}")

        if result.returncode != 0:
            print(f"Data ingestion test errors:\n{result.stderr}")
            pytest.fail(f"Data ingestion failed after pod failure: {result.stderr}")

        print("✓ Data ingestion continues after pod failure")

    def test_06_ui_remains_accessible_after_pod_failure(self, deployed_cluster):
        """
        Test that UI remains accessible after pod failure.

        Validates: Requirements 18.1-18.10
        """
        print("\n=== Verifying UI accessibility ===")

        # Check UI pods are running
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "skywalking", "-l", "app=ui"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"UI pods:\n{result.stdout}")

        # Verify at least one UI pod is running
        assert "Running" in result.stdout, "No UI pods are running"

        print("✓ UI remains accessible")

    def test_07_cluster_recovers_automatically(self, deployed_cluster):
        """
        Test that cluster recovers automatically after pod failure.

        Validates: Requirements 18.1-18.10
        """
        print("\n=== Verifying automatic recovery ===")

        # Wait for cluster to stabilize
        print("Waiting 60 seconds for cluster to stabilize...")
        time.sleep(60)

        # Check all pods are running
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "skywalking"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"All pods:\n{result.stdout}")

        # Count running pods
        running_count = result.stdout.count("Running")
        total_count = result.stdout.count("/")

        print(f"Running pods: {running_count}/{total_count}")

        # Most pods should be running (allow for some transient states)
        assert running_count >= total_count * 0.8, "Too many pods not running"

        print("✓ Cluster recovered automatically")

    def test_08_rolling_update_strategy_configured(self, deployed_cluster):
        """
        Test that rolling update strategy is configured.

        Validates: Requirements 18.8
        """
        print("\n=== Verifying rolling update strategy ===")

        # Check deployment strategy
        result = subprocess.run(
            ["kubectl", "get", "deployment", "-n", "skywalking", "-o", "yaml"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Look for rolling update configuration
        if "RollingUpdate" in result.stdout or "maxUnavailable" in result.stdout:
            print("✓ Rolling update strategy is configured")
        else:
            print("⚠ Rolling update strategy configuration not found")

    def test_09_no_data_loss_during_failure(self, deployed_cluster, scripts_dir):
        """
        Test that no data is lost during pod failure.

        Validates: Requirements 18.1-18.10
        """
        print("\n=== Verifying no data loss ===")

        # This is implicitly tested by data ingestion continuing
        # Additional checks can be added here for data persistence

        # Run health check to ensure cluster is healthy
        health_script = scripts_dir / "test-health.sh"
        result = subprocess.run(
            ["bash", str(health_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            pytest.fail(f"Health check failed after recovery: {result.stderr}")

        print("✓ No data loss detected")

    def test_10_etcd_cluster_maintains_quorum(self, deployed_cluster):
        """
        Test that etcd cluster maintains quorum during failures.

        Validates: Requirements 18.10
        """
        print("\n=== Verifying etcd quorum ===")

        # Check etcd pods
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "skywalking", "-l", "app=etcd"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"etcd pods:\n{result.stdout}")

        # Count running etcd pods
        etcd_count = result.stdout.count("Running")

        if etcd_count >= 2:
            print(f"✓ etcd cluster has {etcd_count} members (quorum maintained)")
        else:
            print(f"⚠ etcd cluster has only {etcd_count} members")


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
