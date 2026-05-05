# =============================================================================
# Module 20 — Exercise 1: Deploy Nginx Helm Chart
# =============================================================================
# Deploy Nginx from the Bitnami Helm repository using Terraform.
#
# Prerequisites:
#   minikube start --driver=docker
#
# After apply:
#   kubectl get all -n helm-nginx
#   minikube service helm-nginx-nginx -n helm-nginx --url
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
  }
}

provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = "minikube"
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}

# --- Create a namespace first ---
resource "kubernetes_namespace" "nginx" {
  metadata {
    name = "helm-nginx"
    labels = {
      managed_by = "terraform"
    }
  }
}

# --- Deploy Nginx via Helm ---
resource "helm_release" "nginx" {
  name       = "helm-nginx"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "nginx"
  namespace  = kubernetes_namespace.nginx.metadata[0].name

  # Use set blocks for simple overrides
  set {
    name  = "replicaCount"
    value = "2"
  }

  set {
    name  = "service.type"
    value = "NodePort"
  }

  set {
    name  = "service.nodePorts.http"
    value = "30100"
  }

  # Wait for pods to be ready
  wait    = true
  timeout = 300

  # Cleanup on destroy
  cleanup_on_fail = true
}

# --- Outputs ---
output "release_name" {
  description = "Helm release name"
  value       = helm_release.nginx.name
}

output "release_status" {
  description = "Helm release status"
  value       = helm_release.nginx.status
}

output "chart_version" {
  description = "Deployed chart version"
  value       = helm_release.nginx.version
}

output "namespace" {
  value = kubernetes_namespace.nginx.metadata[0].name
}

output "access_command" {
  value = "minikube service helm-nginx-nginx -n helm-nginx --url"
}
