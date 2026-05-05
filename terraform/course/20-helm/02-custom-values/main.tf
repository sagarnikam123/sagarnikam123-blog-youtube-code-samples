# =============================================================================
# Module 20 — Exercise 2: Custom Values
# =============================================================================
# Override Helm chart values using:
#   1. A values YAML file
#   2. Terraform variables passed via `set` blocks
#   3. Dynamic set blocks from a map
#
# After apply:
#   kubectl get all -n helm-custom
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

# --- Variables ---
variable "namespace" {
  type    = string
  default = "helm-custom"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "extra_settings" {
  description = "Additional Helm set values"
  type        = map(string)
  default = {
    "podAnnotations.prometheus\\.io/scrape" = "true"
    "podAnnotations.prometheus\\.io/port"   = "8080"
  }
}

# --- Namespace ---
resource "kubernetes_namespace" "this" {
  metadata {
    name = var.namespace
    labels = {
      managed_by = "terraform"
    }
  }
}

# --- Helm Release with values file + dynamic sets ---
resource "helm_release" "nginx" {
  name      = "custom-nginx"
  chart     = "nginx"
  repository = "https://charts.bitnami.com/bitnami"
  namespace = kubernetes_namespace.this.metadata[0].name

  # Method 1: Values from a YAML file
  values = [
    file("${path.module}/values/nginx.yaml")
  ]

  # Method 2: Override specific values with set blocks
  set {
    name  = "podLabels.environment"
    value = var.environment
  }

  # Method 3: Dynamic set blocks from a variable map
  dynamic "set" {
    for_each = var.extra_settings
    content {
      name  = set.key
      value = set.value
    }
  }

  wait    = true
  timeout = 300
}

# --- Outputs ---
output "release_name" {
  value = helm_release.nginx.name
}

output "release_status" {
  value = helm_release.nginx.status
}

output "namespace" {
  value = kubernetes_namespace.this.metadata[0].name
}

output "values_file_used" {
  value = "${path.module}/values/nginx.yaml"
}
