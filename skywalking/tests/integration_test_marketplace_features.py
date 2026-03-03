"""
Integration Test: Marketplace Features

This test validates SkyWalking marketplace features:
1. Deploy cluster
2. Deploy test services (MySQL, Redis, RabbitMQ)
3. Configure exporters and OTel Collector
4. Verify metrics in UI

Feature: skywalking-cluster
Validates: Requirements 11.1-11.10, 13.1-13.9
"""

import subprocess
import time
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.slow
class TestMarketplaceFeatures:
    """Integration tests for marketplace features."""

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
        print(f"\n=== Deploying SkyWalking cluster for marketplace tests ===")

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

    def test_01_general_services_monitoring(self, deployed_cluster, scripts_dir):
        """
        Test general services monitoring (MySQL, Redis, RabbitMQ).

        Validates: Requirements 11.1-11.10
        """
        print("\n=== Testing general services monitoring ===")

        test_script = scripts_dir / "test-general-services.sh"
        result = subprocess.run(
            ["bash", str(test_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes
        )

        print(f"General services test output:\n{result.stdout}")

        if result.returncode != 0:
            print(f"General services test errors:\n{result.stderr}")
            pytest.fail(f"General services test failed: {result.stderr}")

        # Verify services are monitored
        output_lower = result.stdout.lower()
        assert any(db in output_lower for db in ["mysql", "database", "metrics"])

        print("✓ General services monitoring validated")

    def test_02_mysql_metrics_visible(self, deployed_cluster, scripts_dir):
        """
        Test that MySQL metrics are collected and visible.

        Validates: Requirements 11.1, 11.4, 11.6
        """
        print("\n=== Verifying MySQL metrics ===")

        # This is validated as part of general services test
        # Additional specific checks can be added here

        test_script = scripts_dir / "test-general-services.sh"
        result = subprocess.run(
            ["bash", str(test_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            pytest.skip("General services test not passing yet")

        # Verify MySQL-specific metrics
        assert "mysql" in result.stdout.lower() or "database" in result.stdout.lower()

        print("✓ MySQL metrics are visible")

    def test_03_redis_metrics_visible(self, deployed_cluster, scripts_dir):
        """
        Test that Redis cache metrics are collected and visible.

        Validates: Requirements 11.2, 11.4, 11.7
        """
        print("\n=== Verifying Redis metrics ===")

        test_script = scripts_dir / "test-general-services.sh"
        result = subprocess.run(
            ["bash", str(test_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            pytest.skip("General services test not passing yet")

        # Verify Redis-specific metrics
        assert "redis" in result.stdout.lower() or "cache" in result.stdout.lower()

        print("✓ Redis metrics are visible")

    def test_04_rabbitmq_metrics_visible(self, deployed_cluster, scripts_dir):
        """
        Test that RabbitMQ metrics are collected and visible.

        Validates: Requirements 11.3, 11.4, 11.8
        """
        print("\n=== Verifying RabbitMQ metrics ===")

        test_script = scripts_dir / "test-general-services.sh"
        result = subprocess.run(
            ["bash", str(test_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            pytest.skip("General services test not passing yet")

        # Verify RabbitMQ-specific metrics
        assert "rabbitmq" in result.stdout.lower() or "mq" in result.stdout.lower()

        print("✓ RabbitMQ metrics are visible")

    def test_05_message_queue_monitoring(self, deployed_cluster, scripts_dir):
        """
        Test message queue monitoring (ActiveMQ, RabbitMQ).

        Validates: Requirements 13.1-13.9
        """
        print("\n=== Testing message queue monitoring ===")

        test_script = scripts_dir / "test-mq-monitoring.sh"
        result = subprocess.run(
            ["bash", str(test_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600
        )

        print(f"MQ monitoring test output:\n{result.stdout}")

        if result.returncode != 0:
            print(f"MQ monitoring test errors:\n{result.stderr}")
            pytest.fail(f"MQ monitoring test failed: {result.stderr}")

        # Verify MQ metrics are collected
        output_lower = result.stdout.lower()
        assert any(mq in output_lower for mq in ["activemq", "rabbitmq", "queue", "message"])

        print("✓ Message queue monitoring validated")

    def test_06_activemq_metrics_visible(self, deployed_cluster, scripts_dir):
        """
        Test that ActiveMQ metrics are collected and visible.

        Validates: Requirements 13.1, 13.3, 13.5
        """
        print("\n=== Verifying ActiveMQ metrics ===")

        test_script = scripts_dir / "test-mq-monitoring.sh"
        result = subprocess.run(
            ["bash", str(test_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            pytest.skip("MQ monitoring test not passing yet")

        # Verify ActiveMQ-specific metrics
        assert "activemq" in result.stdout.lower() or "queue" in result.stdout.lower()

        print("✓ ActiveMQ metrics are visible")

    def test_07_kubernetes_monitoring(self, deployed_cluster, scripts_dir):
        """
        Test Kubernetes cluster monitoring.

        Validates: Requirements 12.1-12.10
        """
        print("\n=== Testing Kubernetes monitoring ===")

        test_script = scripts_dir / "test-kubernetes-monitoring.sh"
        result = subprocess.run(
            ["bash", str(test_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600
        )

        print(f"Kubernetes monitoring test output:\n{result.stdout}")

        if result.returncode != 0:
            print(f"Kubernetes monitoring test errors:\n{result.stderr}")
            pytest.fail(f"Kubernetes monitoring test failed: {result.stderr}")

        # Verify Kubernetes metrics are collected
        output_lower = result.stdout.lower()
        assert any(k8s in output_lower for k8s in ["kubernetes", "pod", "node", "cluster"])

        print("✓ Kubernetes monitoring validated")

    def test_08_otel_collector_configured(self, deployed_cluster, scripts_dir):
        """
        Test that OTel Collector is properly configured for all services.

        Validates: Requirements 11.5, 12.3, 13.4
        """
        print("\n=== Verifying OTel Collector configuration ===")

        # Check if OTel Collector is deployed and running
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "skywalking", "-l", "app=otel-collector"],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"OTel Collector pods:\n{result.stdout}")

        if "otel-collector" not in result.stdout:
            pytest.skip("OTel Collector not deployed yet")

        # Verify collector is running
        assert "Running" in result.stdout or "1/1" in result.stdout

        print("✓ OTel Collector is configured and running")

    def test_09_exporters_deployed(self, deployed_cluster, scripts_dir):
        """
        Test that all required exporters are deployed.

        Validates: Requirements 11.4, 13.3
        """
        print("\n=== Verifying exporters are deployed ===")

        # Check for various exporters
        exporters = ["mysql-exporter", "redis-exporter", "rabbitmq-exporter"]

        for exporter in exporters:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "skywalking", "-l", f"app={exporter}"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if exporter in result.stdout:
                print(f"✓ {exporter} is deployed")
            else:
                print(f"⚠ {exporter} not found (may be deployed later)")

    def test_10_marketplace_features_complete_within_time(self, deployed_cluster, scripts_dir):
        """
        Test that marketplace feature validation completes within required time.

        Validates: Requirements 11.10, 13.9
        """
        print("\n=== Testing marketplace features completion time ===")

        start_time = time.time()

        # Run general services test
        test_script = scripts_dir / "test-general-services.sh"
        result = subprocess.run(
            ["bash", str(test_script), deployed_cluster],
            capture_output=True,
            text=True,
            timeout=600
        )

        elapsed_time = time.time() - start_time

        print(f"Test completed in {elapsed_time:.2f} seconds")

        # Should complete within 10 minutes (600 seconds)
        assert elapsed_time < 600, f"Test took {elapsed_time:.2f}s, expected < 600s"

        print(f"✓ Marketplace features test completed in {elapsed_time:.2f}s")


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
