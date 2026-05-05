# =============================================================================
# Module 20 — Exercise 3: Multiple Charts with for_each
# =============================================================================
# Deploy a stack of Helm charts using for_each.
# Demonstrates managing multiple third-party apps as a single Terraform config.
#
# After apply:
#   kubectl get all -n helm-stack
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
  default = "helm-stack"
}

variable "charts" {
  description = "Map of Helm charts to deploy"
  type = map(object({
    repository = string
    chart      = string
    settings   = map(string)
  }))
  default = {
    nginx = {
      repository = "https://charts.bitnami.com/bitnami"
      chart      = "nginx"
      settings = {
        "replicaCount"           = "2"
        "service.type"           = "NodePort"
        "service.nodePorts.http" = "30110"
      }
    }
    redis = {
      repository = "https://charts.bitnami.com/bitnami"
      chart      = "redis"
      settings = {
        "architecture"                = "standalone"
        "auth.enabled"                = "false"
        "master.service.type"         = "ClusterIP"
        "master.resources.limits.cpu" = "100m"
        "master.resources.limits.memory" = "128Mi"
      }
    }
  }
}

# --- Namespace ---
resource "kubernetes_namespace" "this" {
  metadata {
    name = var.namespace
    labels = {
      managed_by = "terraform"
      purpose    = "helm-stack"
    }
  }
}

# --- Deploy all charts using for_each ---
resource "helm_release" "charts" {
  for_each = var.charts

  name       = each.key
  repository = each.value.repository
  chart      = each.value.chart
  namespace  = kubernetes_namespace.this.metadata[0].name

  dynamic "set" {
    for_each = each.value.settings
    content {
      name  = set.key
      value = set.value
    }
  }

  wait            = true
  timeout         = 600
  cleanup_on_fail = true
}

# --- Outputs ---
output "namespace" {
  value = kubernetes_namespace.this.metadata[0].name
}

output "deployed_charts" {
  description = "Status of all deployed charts"
  value = {
    for name, release in helm_release.charts : name => {
      status  = release.status
      version = release.version
      chart   = release.chart
    }
  }
}

output "kubectl_commands" {
  value = <<-EOT
    kubectl get all -n ${var.namespace}
    kubectl get pods -n ${var.namespace}
    kubectl get svc -n ${var.namespace}
    minikube service nginx-nginx -n ${var.namespace} --url
  EOT
}
