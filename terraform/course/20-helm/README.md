# Module 20 — Helm Charts with Terraform

## Overview

Helm is the package manager for Kubernetes. The Terraform Helm provider lets you deploy and manage Helm charts declaratively — combining the power of Helm's templating with Terraform's state management and lifecycle.

## Prerequisites

```bash
# Minikube must be running
minikube start --driver=docker

# Install Helm CLI (for inspecting charts, not required for Terraform)
brew install helm    # macOS

# Verify
helm version
kubectl cluster-info
```

## Helm Provider

```hcl
provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = "minikube"
  }
}
```

## Key Resource: `helm_release`

```hcl
resource "helm_release" "nginx" {
  name       = "my-nginx"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "nginx"
  version    = "18.2.4"
  namespace  = "web"

  set {
    name  = "replicaCount"
    value = "2"
  }

  values = [
    file("${path.module}/values/nginx.yaml")
  ]
}
```

## Helm vs Kubernetes Provider

| Aspect | Kubernetes Provider | Helm Provider |
|--------|-------------------|---------------|
| Granularity | Individual resources | Entire charts (bundles of resources) |
| Templating | HCL only | Helm templates + HCL |
| Community charts | Must recreate in HCL | Use as-is from registries |
| Upgrades | Resource-by-resource | `helm upgrade` semantics |
| Best for | Custom resources, fine control | Third-party apps (Nginx, Prometheus, Redis) |

## Official Docs

- [Helm Provider](https://registry.terraform.io/providers/hashicorp/helm/latest/docs)
- [helm_release Resource](https://registry.terraform.io/providers/hashicorp/helm/latest/docs/resources/release)
- [Helm Documentation](https://helm.sh/docs/)
- [Artifact Hub — Find Charts](https://artifacthub.io/)
- [Bitnami Charts](https://github.com/bitnami/charts)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Deploy Nginx Chart](./01-nginx-chart/) | Deploy Nginx from Bitnami Helm repo |
| 2 | [Custom Values](./02-custom-values/) | Override chart values with Terraform variables |
| 3 | [Multiple Charts](./03-multiple-charts/) | Deploy a stack: Nginx + Redis using for_each |
