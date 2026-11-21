"""
Azure AKS Platform Deployer for the Prometheus Testing Framework.

This module provides the AKS-specific implementation for deploying
Prometheus to Azure Kubernetes Service clusters.

Requirements: 9.4
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
class AKSConfig:
    """Configuration specific to Azure AKS deployments."""

    subscription_id: str = ""
    resource_group: str = ""
    cluster_name: str = ""
    # Storage class for Azure Disks
    storage_class: str = "managed-premium"
    # Whether to use Azure AD Pod Identity
    enable_pod_identity: bool = False
    # Whether to use Azure Workload Identity
    enable_workload_identity: bool = False
    # Azure Monitor integration
    enable_azure_monitor: bool = False


class AKSDeployer(KubernetesDeployer):
    """
    Azure AKS Platform Deployer.

    Requirements: 9.4

    Deploys Prometheus to Azure AKS clusters using Helm charts with
    AKS-specific configurations including:
    - Azure Disk storage class configuration
    - Azure AD Pod Identity / Workload Identity integration
    - Azure Monitor integration
    - AKS-optimized resource settings
    """

    def __init__(
        self,
        config: Optional[DeployConfig] = None,
        aks_config: Optional[AKSConfig] = None,
    ):
        """
        Initialize the AKS deployer.

        Args:
            config: Base deployment configuration
            aks_config: AKS-specific configuration
        """
        super().__init__(config)
        self.aks_config = aks_config or AKSConfig()
        self._port_forward_process: Optional[subprocess.Popen] = None

    @property
    def platform(self) -> Platform:
        """Get the platform this deployer targets."""
        return Platform.AKS

    def _get_az_base_cmd(self) -> list[str]:
        """Get base Azure CLI command with subscription."""
        cmd = ["az"]
        if self.aks_config.subscription_id:
            cmd.extend(["--subscription", self.aks_config.subscription_id])
        return cmd

    def _update_kubeconfig(self) -> bool:
        """
        Update kubeconfig for AKS cluster access.

        Returns:
            True if kubeconfig was updated successfully
        """
        if not self.aks_config.cluster_name:
            logger.error("AKS cluster name is required")
            return False

        if not self.aks_config.resource_group:
            logger.error("AKS resource group is required")
            return False

        cmd = self._get_az_base_cmd() + [
            "aks", "get-credentials",
            "--resource-group", self.aks_config.resource_group,
            "--name", self.aks_config.cluster_name,
            "--overwrite-existing",
        ]

        try:
            result = self._run_command(cmd, timeout=60)
            if result.returncode == 0:
                logger.info(f"Updated kubeconfig for AKS cluster: {self.aks_config.cluster_name}")
                return True
            logger.error(f"Failed to update kubeconfig: {result.stderr}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update kubeconfig: {e}")
            return False

    def _verify_cluster_access(self) -> bool:
        """
        Verify access to the AKS cluster.

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
        Get AKS cluster information.

        Returns:
            Dictionary with cluster information
        """
        cmd = self._get_az_base_cmd() + [
            "aks", "show",
            "--resource-group", self.aks_config.resource_group,
            "--name", self.aks_config.cluster_name,
            "--output", "json",
        ]

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

    def _get_aks_values(self) -> dict[str, Any]:
        """
        Get AKS-specific Helm values.

        Returns:
            Dictionary of Helm values for AKS
        """
        values = {
            # Use Azure Disk storage class
            "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName": self.aks_config.storage_class,
            # AKS-optimized settings
            "prometheus.prometheusSpec.resources.requests.cpu": "500m",
            "prometheus.prometheusSpec.resources.requests.memory": "2Gi",
            "prometheus.prometheusSpec.resources.limits.cpu": "2",
            "prometheus.prometheusSpec.resources.limits.memory": "4Gi",
            # Alertmanager storage
            "alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.storageClassName": self.aks_config.storage_class,
            # Grafana storage
            "grafana.persistence.storageClassName": self.aks_config.storage_class,
        }

        return values

    def deploy(self, config: Optional[DeployConfig] = None) -> DeployResult:
        """
        Deploy Prometheus to AKS.

        Args:
            config: Optional deployment configuration override

        Returns:
            DeployResult with deployment status and details
        """
        deploy_config = config or self.config

        # Update kubeconfig for AKS access
        if not self._update_kubeconfig():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Failed to update kubeconfig for AKS cluster",
            )

        # Verify cluster access
        if not self._verify_cluster_access():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Cannot access AKS cluster",
            )

        # Ensure Helm repo is available
        if not self._ensure_helm_repo():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Failed to setup Helm repository",
            )

        # Merge AKS-specific values
        aks_values = self._get_aks_values()
        merged_values = {**deploy_config.set_values, **aks_values}
        deploy_config.set_values = merged_values

        # Deploy using base Helm install
        result = self._helm_install(deploy_config)

        if result.success:
            # Add AKS-specific metadata
            result.metadata["cluster_name"] = self.aks_config.cluster_name
            result.metadata["resource_group"] = self.aks_config.resource_group
            result.metadata["subscription_id"] = self.aks_config.subscription_id
            result.metadata["platform"] = "aks"

        return result

    def teardown(self) -> bool:
        """
        Remove Prometheus deployment from AKS.

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

        For AKS, this returns the port-forwarded URL by default.
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
        client_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Configure Azure Workload Identity for AKS.

        This allows Prometheus to use an Azure AD identity for
        accessing Azure resources without managing credentials.

        Args:
            service_account_name: Name of the Kubernetes service account
            client_id: Azure AD application client ID
            tenant_id: Azure AD tenant ID

        Returns:
            True if Workload Identity was configured successfully
        """
        if not self.aks_config.enable_workload_identity:
            logger.info("Workload Identity is not enabled in configuration")
            return False

        if not client_id or not tenant_id:
            logger.error("Client ID and Tenant ID are required for Workload Identity")
            return False

        # Annotate the Kubernetes service account
        cmd = self._get_kubectl_base_cmd() + [
            "annotate", "serviceaccount",
            service_account_name,
            "-n", self.config.namespace,
            f"azure.workload.identity/client-id={client_id}",
            f"azure.workload.identity/tenant-id={tenant_id}",
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

    def configure_pod_identity(
        self,
        identity_name: str,
        identity_resource_id: str,
    ) -> bool:
        """
        Configure Azure AD Pod Identity for AKS.

        Args:
            identity_name: Name of the Azure identity
            identity_resource_id: Resource ID of the managed identity

        Returns:
            True if Pod Identity was configured successfully
        """
        if not self.aks_config.enable_pod_identity:
            logger.info("Pod Identity is not enabled in configuration")
            return False

        # Create AzureIdentity resource
        azure_identity = {
            "apiVersion": "aadpodidentity.k8s.io/v1",
            "kind": "AzureIdentity",
            "metadata": {
                "name": identity_name,
                "namespace": self.config.namespace,
            },
            "spec": {
                "type": 0,
                "resourceID": identity_resource_id,
                "clientID": "",  # Will be populated from the managed identity
            },
        }

        # Apply the AzureIdentity
        cmd = self._get_kubectl_base_cmd() + ["apply", "-f", "-"]

        try:
            subprocess.run(
                cmd,
                input=json.dumps(azure_identity),
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"Created AzureIdentity: {identity_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to configure Pod Identity: {e}")
            return False

    def enable_azure_monitor_remote_write(self) -> dict[str, Any]:
        """
        Get configuration for Azure Monitor remote write.

        Returns:
            Dictionary with remote write configuration for Azure Monitor
        """
        # Get the Azure Monitor workspace ingestion endpoint
        cluster_info = self._get_cluster_info()
        location = cluster_info.get("location", "eastus")

        return {
            "prometheus.prometheusSpec.remoteWrite": [
                {
                    "url": f"https://{location}.monitoring.azure.com/prometheus/v1/write",
                    "azureAd": {
                        "cloud": "AzurePublic",
                        "managedIdentity": {
                            "clientId": "",  # To be filled with managed identity client ID
                        },
                    },
                }
            ]
        }

    def get_cluster_metrics(self) -> dict[str, Any]:
        """
        Get AKS cluster metrics and status.

        Returns:
            Dictionary with cluster metrics
        """
        metrics = {
            "cluster_name": self.aks_config.cluster_name,
            "resource_group": self.aks_config.resource_group,
            "subscription_id": self.aks_config.subscription_id,
            "deployment_status": self._status.value,
        }

        # Get cluster info for additional details
        cluster_info = self._get_cluster_info()
        if cluster_info:
            metrics["location"] = cluster_info.get("location", "")
            metrics["kubernetes_version"] = cluster_info.get("kubernetesVersion", "")
            metrics["provisioning_state"] = cluster_info.get("provisioningState", "")

            # Get node pool info
            agent_pools = cluster_info.get("agentPoolProfiles", [])
            metrics["node_pools"] = len(agent_pools)
            metrics["total_nodes"] = sum(
                pool.get("count", 0) for pool in agent_pools
            )

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

    def get_azure_portal_url(self) -> str:
        """
        Get the URL for the AKS cluster in Azure Portal.

        Returns:
            URL string for the Azure Portal
        """
        return (
            f"https://portal.azure.com/#@/resource/subscriptions/"
            f"{self.aks_config.subscription_id}/resourceGroups/"
            f"{self.aks_config.resource_group}/providers/Microsoft.ContainerService/"
            f"managedClusters/{self.aks_config.cluster_name}/overview"
        )

    def get_container_insights_url(self) -> str:
        """
        Get the URL for Container Insights in Azure Portal.

        Returns:
            URL string for Container Insights
        """
        return (
            f"https://portal.azure.com/#@/resource/subscriptions/"
            f"{self.aks_config.subscription_id}/resourceGroups/"
            f"{self.aks_config.resource_group}/providers/Microsoft.ContainerService/"
            f"managedClusters/{self.aks_config.cluster_name}/containerInsights"
        )
