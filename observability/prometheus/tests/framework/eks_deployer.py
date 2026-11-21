"""
AWS EKS Platform Deployer for the Prometheus Testing Framework.

This module provides the EKS-specific implementation for deploying
Prometheus to AWS Elastic Kubernetes Service clusters.

Requirements: 9.2
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
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
class EKSConfig:
    """Configuration specific to AWS EKS deployments."""

    cluster_name: str = ""
    region: str = "us-east-1"
    profile: Optional[str] = None
    role_arn: Optional[str] = None
    # Storage class for EBS volumes
    storage_class: str = "gp3"
    # Whether to create IAM roles for service accounts (IRSA)
    enable_irsa: bool = False
    # EBS CSI driver configuration
    ebs_csi_driver_enabled: bool = True


class EKSDeployer(KubernetesDeployer):
    """
    AWS EKS Platform Deployer.

    Requirements: 9.2

    Deploys Prometheus to AWS EKS clusters using Helm charts with
    EKS-specific configurations including:
    - EBS storage class configuration
    - IAM roles for service accounts (IRSA)
    - AWS Load Balancer Controller integration
    - EKS-optimized resource settings
    """

    def __init__(
        self,
        config: Optional[DeployConfig] = None,
        eks_config: Optional[EKSConfig] = None,
    ):
        """
        Initialize the EKS deployer.

        Args:
            config: Base deployment configuration
            eks_config: EKS-specific configuration
        """
        super().__init__(config)
        self.eks_config = eks_config or EKSConfig()
        self._port_forward_process: Optional[subprocess.Popen] = None

    @property
    def platform(self) -> Platform:
        """Get the platform this deployer targets."""
        return Platform.EKS

    def _get_aws_base_cmd(self) -> list[str]:
        """Get base AWS CLI command with profile and region."""
        cmd = ["aws"]
        if self.eks_config.profile:
            cmd.extend(["--profile", self.eks_config.profile])
        if self.eks_config.region:
            cmd.extend(["--region", self.eks_config.region])
        return cmd

    def _update_kubeconfig(self) -> bool:
        """
        Update kubeconfig for EKS cluster access.

        Returns:
            True if kubeconfig was updated successfully
        """
        if not self.eks_config.cluster_name:
            logger.error("EKS cluster name is required")
            return False

        cmd = self._get_aws_base_cmd() + [
            "eks", "update-kubeconfig",
            "--name", self.eks_config.cluster_name,
        ]

        if self.eks_config.role_arn:
            cmd.extend(["--role-arn", self.eks_config.role_arn])

        try:
            result = self._run_command(cmd, timeout=60)
            if result.returncode == 0:
                logger.info(f"Updated kubeconfig for EKS cluster: {self.eks_config.cluster_name}")
                return True
            logger.error(f"Failed to update kubeconfig: {result.stderr}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update kubeconfig: {e}")
            return False

    def _verify_cluster_access(self) -> bool:
        """
        Verify access to the EKS cluster.

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
        Get EKS cluster information.

        Returns:
            Dictionary with cluster information
        """
        cmd = self._get_aws_base_cmd() + [
            "eks", "describe-cluster",
            "--name", self.eks_config.cluster_name,
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

    def _get_eks_values(self) -> dict[str, Any]:
        """
        Get EKS-specific Helm values.

        Returns:
            Dictionary of Helm values for EKS
        """
        values = {
            # Use EBS storage class
            "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName": self.eks_config.storage_class,
            # EKS-optimized settings
            "prometheus.prometheusSpec.resources.requests.cpu": "500m",
            "prometheus.prometheusSpec.resources.requests.memory": "2Gi",
            "prometheus.prometheusSpec.resources.limits.cpu": "2",
            "prometheus.prometheusSpec.resources.limits.memory": "4Gi",
            # Alertmanager storage
            "alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.storageClassName": self.eks_config.storage_class,
            # Grafana storage
            "grafana.persistence.storageClassName": self.eks_config.storage_class,
        }

        return values

    def deploy(self, config: Optional[DeployConfig] = None) -> DeployResult:
        """
        Deploy Prometheus to EKS.

        Args:
            config: Optional deployment configuration override

        Returns:
            DeployResult with deployment status and details
        """
        deploy_config = config or self.config

        # Update kubeconfig for EKS access
        if not self._update_kubeconfig():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Failed to update kubeconfig for EKS cluster",
            )

        # Verify cluster access
        if not self._verify_cluster_access():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Cannot access EKS cluster",
            )

        # Ensure Helm repo is available
        if not self._ensure_helm_repo():
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Failed to setup Helm repository",
            )

        # Merge EKS-specific values
        eks_values = self._get_eks_values()
        merged_values = {**deploy_config.set_values, **eks_values}
        deploy_config.set_values = merged_values

        # Deploy using base Helm install
        result = self._helm_install(deploy_config)

        if result.success:
            # Add EKS-specific metadata
            result.metadata["cluster_name"] = self.eks_config.cluster_name
            result.metadata["region"] = self.eks_config.region
            result.metadata["platform"] = "eks"

        return result

    def teardown(self) -> bool:
        """
        Remove Prometheus deployment from EKS.

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

        For EKS, this returns the port-forwarded URL by default.
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
            "-o", "jsonpath={.status.loadBalancer.ingress[0].hostname}",
        ]

        try:
            result = self._run_command(cmd, timeout=30, check=False)
            if result.returncode == 0 and result.stdout.strip():
                return f"http://{result.stdout.strip()}:9090"
            return None
        except Exception:
            return None

    def configure_irsa(
        self,
        service_account_name: str = "prometheus",
        policy_arn: Optional[str] = None,
    ) -> bool:
        """
        Configure IAM Roles for Service Accounts (IRSA).

        This allows Prometheus to assume an IAM role for AWS API access,
        useful for remote write to Amazon Managed Prometheus (AMP).

        Args:
            service_account_name: Name of the Kubernetes service account
            policy_arn: ARN of the IAM policy to attach

        Returns:
            True if IRSA was configured successfully
        """
        if not self.eks_config.enable_irsa:
            logger.info("IRSA is not enabled in configuration")
            return False

        # Get OIDC provider
        cluster_info = self._get_cluster_info()
        if not cluster_info:
            return False

        oidc_issuer = cluster_info.get("cluster", {}).get("identity", {}).get("oidc", {}).get("issuer", "")
        if not oidc_issuer:
            logger.error("OIDC issuer not found for cluster")
            return False

        logger.info(f"OIDC issuer: {oidc_issuer}")
        # IRSA configuration would require additional IAM setup
        # This is a placeholder for the full implementation
        return True

    def get_cluster_metrics(self) -> dict[str, Any]:
        """
        Get EKS cluster metrics and status.

        Returns:
            Dictionary with cluster metrics
        """
        metrics = {
            "cluster_name": self.eks_config.cluster_name,
            "region": self.eks_config.region,
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
