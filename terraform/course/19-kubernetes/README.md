# Module 19 — Kubernetes with Minikube

## Overview

Now that you've mastered Terraform concepts with Docker, it's time to apply them to Kubernetes — the platform you'll most likely manage as a DevOps/Platform engineer. Everything runs locally on Minikube, so it's still free.

## Prerequisites

```bash
# Install Minikube
brew install minikube    # macOS
# or: https://minikube.sigs.k8s.io/docs/start/

# Install kubectl
brew install kubectl     # macOS

# Start a local cluster
minikube start --driver=docker

# Verify
kubectl cluster-info
kubectl get nodes
```

## Kubernetes Provider

```hcl
terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}
```

## Key Resources

| Resource | What It Does |
|----------|-------------|
| `kubernetes_namespace` | Logical isolation for resources |
| `kubernetes_deployment` | Manages pods with replicas, rolling updates |
| `kubernetes_service` | Exposes pods via ClusterIP, NodePort, LoadBalancer |
| `kubernetes_config_map` | Key-value config injected into pods |
| `kubernetes_secret` | Sensitive data (base64 encoded) |
| `kubernetes_ingress_v1` | HTTP routing rules |
| `kubernetes_persistent_volume_claim` | Storage requests |
| `kubernetes_service_account` | Identity for pods |
| `kubernetes_role` / `kubernetes_role_binding` | RBAC permissions |

## Official Docs

- [Kubernetes Provider](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs)
- [Kubernetes Provider — Getting Started](https://developer.hashicorp.com/terraform/tutorials/kubernetes/kubernetes-provider)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Kubernetes Concepts](https://kubernetes.io/docs/concepts/)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Namespace & Deployment](./01-namespace-deployment/) | Create a namespace and deploy Nginx |
| 2 | [Services & ConfigMaps](./02-services-configmaps/) | Expose pods and inject configuration |
| 3 | [Secrets & RBAC](./03-secrets-rbac/) | Manage secrets and role-based access |
| 4 | [Full Stack on K8s](./04-full-stack/) | Multi-tier app with namespace, deployment, service, configmap |
