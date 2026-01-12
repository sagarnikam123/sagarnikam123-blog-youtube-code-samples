"""
Google GKE Platform Deployer for the Prometheus Testing Framework.

This module provides the GKE-specific implementation for deploying
Prometheus to Google Kubernetes Engine clusters.

Requirements: 9.3
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Any, Optional

from .deployer import (
    DeployConfig,
    DeployResult,
    DeploymentStatus,
    KubernetesDeployer,
    Platform,
)

logger = logging.getLogger(__name__)


@dataclass
class GKEConfig:
    """Configuration specific to Google GKE deployments."""

    project_id: str = ""
    cluster_name: str = ""
    zone: str = ""  # For zonal clusters
    region: str = ""  # For regional clusters
    # Storage class for Persistent Disks
    storage_class: str = "standard-rwo"
    # Whether to use Workload Identity
    enable_workload_identity: bool = False
    # Google Cloud Managed Prometheus integration
    enable_gmp_integration: bool = False


class GKEDeployer(KubernetesDeployer):
    """
    Google GKE Platform Deployer.

    Requirements: 9.3

    Deploys Prometheus to Google GKE clusters using Helm charts with
    GKE-specific configurations including:
    - Persistent Disk storage class configuration
    - Workload Identity integration
    - Google Cloud Managed Prometheus (GMP) integration
    - GKE-optimized resource settings
    """

    def __init__(
        self,
        config: Optional[DeployConfig] = None,
        gke_config: Optional[GKEConfig] = None,
    ):
        """
        Initialize the GKE deployer.

        Args:
            config: Base deployment configuration
            gke_config: GKE-specific configuration
        """
        super().__init__(config)
        self.gke_config = gke_config or GKEConfig()
        self._port_forward_process: Optional[subprocess.Popen] = None

    @property
    def platform(self) -> Platform:
        """Get the platform this deployer targets."""
        return Platform.GKE

    def _get_gcloud_base_cmd(self) -> list[str]:
        """Get base gcloud CLI command with project."""
        cmd = ["gcloud"]
        if self.gke_config.project_id:
            cmd.extend(["--project", self.gke_config.project_id])
        return cmd

    def _get_cluster_location(self) -> str:
        """Get the cluster location (zone or region)."""
        if self.gke_config.zone:
            return self.gke_config.zone
        return self.gke_config.region

    def _get_cluster_location_flag(self) -> list[str]:
        """Get the appropriate location flag for gcloud commands."""
        if self.gke_config.zone:
            return ["--zone", self.gke_config.zone]
        return ["--region", self.gke_config.region]

    def _update_kubeconfig(self) -> bool:
        """
        Update kubeconfig for GKE cluster access.

        Returns:
            True if kubeconfig was updated successfully
        """
        if not self.gke_config.cluster_name:
            logger.error("GKE cluster name is required")
            return False

        if not self.gke_config.zone and not self.gke_config.region:
            logger.error("GKE cluster zone or region is required")
            return False

        cmd = self._get_gcloud_base_cmd() + [
            "container", "clusters", "get-credentials",
            self.gke_config.cluster_name,
        ] + self._get_cluster_location_flag()

        try:
            result = self._run_command(cmd, timeout=60)
            if result.returncode == 0:
                logger.info(f"Updated kubeconfig for GKE cluster: {self.gke_config.cluster_name}")
                return True
            logger.error(f"Failed to update kubeconfig: {result.stderr}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update kubeconfig: {e}")
            return False

    def _verify_cluster_access(self) -> bool:
        """
        Verify access to the GKE cluster.

        Returns:
            True if cluster is accessible
        """
        cmd = self._get_kubectl_base_cmd() + ["cluster-info"]

        try:
            result = self._run_command(cmd, timeout=30, check=False)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to verify cluster access: {e}")
            return False

    def _get_cluster_info(self) -> dict[str, Any]:
        """
        Get GKE cluster information.

        Returns:
            Dictionary with cluster information
        """
        cmd = self._get_gcloud_base_cmd() + [
            "container", "clusters", "describe",
            self.gke_config.cluster_name,
            "--format", "json",
        ] + self._get_cluster_location_flag()

        try:
            result = self._run_command(cmd, timeout=30)
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Failed to get cluster info: {e}")
            return {}

    def _ensure_helm_repo(self) -> bool:
        """
        Ensure the prometheus-community Helm repo is added.

        Returns:
            True if repo is available
        """
        try:
            # Add repo
            cmd = self._get_helm_base_cmd() + [
                "repo", "add", "prometheus-community",
                "https://prometheus-community.github.io/helm-charts",
            ]
            self._run_command(cmd, timeout=60, check=False)

            # Update repos
            cmd = self._get_helm_base_cmd() + ["repo", "update"]
            self._run_command(cmd, timeout=120)
            return True
        except Exception as e:
            logger.error(f"Failed to setup Helm repo: {e}")
            return False

    def _get_gke_values(self) -> dict[str, Any]:
        """
        Get GKE-specific Helm values.

        Returns:
            Dictionary of Helm values for GKE
        """
        values = {
            # Use GKE storage class
            "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName": self.gke_config.storage_class,
            # GKE-optimized settings
            "prometheus.prometheusSpec.resources.requests.cpu": "500m",
            "prometheus.prometheusSpec.resources.requests.memory": "2Gi",
            "prometheus.prometheusSpec.resources.limits.cpu": "2",
            "prometheus.prometheusSpec.resources.limits.memory": "4Gi",
            # Alertmanager storage
            "alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.storageClassName": self.gke_config.storage_class,
            # Grafana storage
            "grafana.persistence.storageClassName": self.gke_config.storage_class,
        }

        # Add GMP integration if enabled
        if self.gke_config.enable_gmp_integration:
            values["prometheus.prometheusSpec.enableFeatures"] = ["remote-write-receiver"]

        return values

    def deploy(self, config: Optional[DeployConfig] = None) -> DeployResult:
        """
        Deploy Prometheus to GKE.

        Args:
            config: Optional deployment configuration override

        Returns:
            DeployResult with deployment status and details
        """
        deploy_config = config or self.config

        # Update kubeconfig for GKE access
        if not self._update_kubeconfig():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Failed to update kubeconfig for GKE cluster",
            )

        # Verify cluster access
        if not self._verify_cluster_access():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Cannot access GKE cluster",
            )

        # Ensure Helm repo is available
        if not self._ensure_helm_repo():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Failed to setup Helm repository",
            )

        # Merge GKE-specific values
        gke_values = self._get_gke_values()
        merged_values = {**deploy_config.set_values, **gke_values}
        deploy_config.set_values = merged_values

        # Deploy using base Helm install
        result = self._helm_install(deploy_config)

        if result.success:
            # Add GKE-specific metadata
            result.metadata["cluster_name"] = self.gke_config.cluster_name
            result.metadata["project_id"] = self.gke_config.project_id
            result.metadata["location"] = self._get_cluster_location()
            result.metadata["platform"] = "gke"

        return result

    def teardown(self) -> bool:
        """
        Remove Prometheus deployment from GKE.

        Returns:
            True if teardown was successful
        """
        # Stop port forwarding if active
        if self._port_forward_process:
            self._port_forward_process.terminate()
            self._port_forward_process = None

        return self._helm_uninstall(self.config)

    def get_prometheus_url(self) -> str:
        """
        Get the Prometheus API URL.

        For GKE, this returns the port-forwarded URL by default.
        Use setup_load_balancer() for external access.

        Returns:
            URL string for accessing Prometheus API
        """
        if self._prometheus_url:
            return self._prometheus_url
        return "http://localhost:9090"

    def setup_port_forward(self, local_port: int = 9090) -> bool:
        """
        Set up port forwarding to Prometheus service.

        Args:
            local_port: Local port to forward to

        Returns:
            True if port forwarding was set up successfully
        """
        self._port_forward_process = self._setup_port_forward(
            namespace=self.config.namespace,
            service_name=f"{self.config.release_name}-kube-prometheus-prometheus",
            local_port=local_port,
        )

        if self._port_forward_process:
            self._prometheus_url = f"http://localhost:{local_port}"
            return True
        return False

    def get_load_balancer_url(self) -> Optional[str]:
        """
        Get the Load Balancer URL if configured.

        Returns:
            Load Balancer URL or None if not configured
        """
        cmd = self._get_kubectl_base_cmd() + [
            "get", "svc",
            f"{self.config.release_name}-kube-prometheus-prometheus",
            "-n", self.config.namespace,
            "-o", "jsonpath={.status.loadBalancer.ingress[0].ip}",
        ]

        try:
            result = self._run_command(cmd, timeout=30, check=False)
            if result.returncode == 0 and result.stdout.strip():
                return f"http://{result.stdout.strip()}:9090"
            return None
        except Exception:
            return None

    def configure_workload_identity(
        self,
        service_account_name: str = "prometheus",
        gcp_service_account: Optional[str] = None,
    ) -> bool:
        """
        Configure Workload Identity for GKE.

        This allows Prometheus to use a Google Cloud service account
        for accessing GCP APIs without managing keys.

        Args:
            service_account_name: Name of the Kubernetes service account
            gcp_service_account: Email of the GCP service account

        Returns:
            True if Workload Identity was configured successfully
        """
        if not self.gke_config.enable_workload_identity:
            logger.info("Workload Identity is not enabled in configuration")
            return False

        if not gcp_service_account:
            logger.error("GCP service account email is required")
            return False

        # Annotate the Kubernetes service account
        cmd = self._get_kubectl_base_cmd() + [
            "annotate", "serviceaccount",
            service_account_name,
            "-n", self.config.namespace,
            f"iam.gke.io/gcp-service-account={gcp_service_account}",
            "--overwrite",
        ]

        try:
            result = self._run_command(cmd, timeout=30)
            if result.returncode == 0:
                logger.info(f"Configured Workload Identity for {service_account_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to configure Workload Identity: {e}")
            return False

    def enable_gmp_remote_write(self, project_id: Optional[str] = None) -> dict[str, Any]:
        """
        Get configuration for Google Cloud Managed Prometheus remote write.

        Args:
            project_id: GCP project ID (defaults to cluster project)

        Returns:
            Dictionary with remote write configuration
        """
        project = project_id or self.gke_config.project_id

        return {
            "prometheus.prometheusSpec.remoteWrite": [
                {
                    "url": f"https://monitoring.googleapis.com/v1/projects/{project}/location/global/prometheus/api/v1/write",
                    "oauth2": {
                        "clientId": "",
                        "clientSecret": "",
                        "tokenUrl": "https://oauth2.googleapis.com/token",
                        "scopes": ["https://www.googleapis.com/auth/monitoring.write"],
                    },
                }
            ]
        }

    def get_cluster_metrics(self) -> dict[str, Any]:
        """
        Get GKE cluster metrics and status.

        Returns:
            Dictionary with cluster metrics
        """
        metrics = {
            "cluster_name": self.gke_config.cluster_name,
            "project_id": self.gke_config.project_id,
            "location": self._get_cluster_location(),
            "deployment_status": self._status.value,
        }

        # Get node count
        cmd = self._get_kubectl_base_cmd() + [
            "get", "nodes", "-o", "json",
        ]

        try:
            result = self._run_command(cmd, timeout=30, check=False)
            if result.returncode == 0:
                nodes = json.loads(result.stdout)
                metrics["node_count"] = len(nodes.get("items", []))
        except Exception:
            pass

        # Get pod status
        cmd = self._get_kubectl_base_cmd() + [
            "get", "pods",
            "-n", self.config.namespace,
            "-l", f"release={self.config.release_name}",
            "-o", "json",
        ]

        try:
            result = self._run_command(cmd, timeout=30, check=False)
            if result.returncode == 0:
                pods = json.loads(result.stdout)
                pod_items = pods.get("items", [])
                metrics["pod_count"] = len(pod_items)
                metrics["pods_ready"] = sum(
                    1 for p in pod_items
                    if p.get("status", {}).get("phase") == "Running"
                )
        except Exception:
            pass

        return metrics

    def get_gke_monitoring_dashboard_url(self) -> str:
        """
        Get the URL for the GKE monitoring dashboard in Cloud Console.

        Returns:
            URL string for the GKE monitoring dashboard
        """
        return (
            f"https://console.cloud.google.com/kubernetes/workload/overview"
            f"?project={self.gke_config.project_id}"
        )
