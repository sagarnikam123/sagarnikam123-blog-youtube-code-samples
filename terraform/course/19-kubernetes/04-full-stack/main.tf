# =============================================================================
# Module 19 — Exercise 4: Full Stack on Kubernetes
# =============================================================================
# Deploy a multi-tier application: frontend + backend + shared config.
# Demonstrates modules, for_each, configmaps, services — all on K8s.
#
# After apply:
#   kubectl get all -n tf-fullstack
#   minikube service frontend -n tf-fullstack --url
#   minikube service backend -n tf-fullstack --url
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}

provider "random" {}

# --- Variables ---
variable "namespace" {
  type    = string
  default = "tf-fullstack"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "services" {
  description = "Map of services to deploy"
  type = map(object({
    image     = string
    replicas  = number
    port      = number
    node_port = number
  }))
  default = {
    frontend = {
      image     = "nginx:alpine"
      replicas  = 2
      port      = 80
      node_port = 30090
    }
    backend = {
      image     = "httpd:alpine"
      replicas  = 2
      port      = 80
      node_port = 30091
    }
  }
}

# --- Locals ---
locals {
  common_labels = {
    managed_by  = "terraform"
    environment = var.environment
    project     = "tf-fullstack"
  }
}

resource "random_pet" "release" {
  length = 1
}

# --- Namespace ---
resource "kubernetes_namespace" "this" {
  metadata {
    name   = var.namespace
    labels = local.common_labels
  }
}

# --- Shared ConfigMap ---
resource "kubernetes_config_map" "shared" {
  metadata {
    name      = "shared-config"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  data = {
    ENVIRONMENT = var.environment
    RELEASE     = random_pet.release.id
    LOG_LEVEL   = var.environment == "prod" ? "warn" : "debug"
    TZ          = "Asia/Kolkata"
  }
}

# --- Deployments (one per service using for_each) ---
resource "kubernetes_deployment" "services" {
  for_each = var.services

  metadata {
    name      = each.key
    namespace = kubernetes_namespace.this.metadata[0].name
    labels    = merge(local.common_labels, { app = each.key })
  }

  spec {
    replicas = each.value.replicas

    selector {
      match_labels = {
        app = each.key
      }
    }

    template {
      metadata {
        labels = merge(local.common_labels, { app = each.key })
      }

      spec {
        container {
          name  = each.key
          image = each.value.image

          port {
            container_port = each.value.port
            name           = "http"
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.shared.metadata[0].name
            }
          }

          env {
            name  = "SERVICE_NAME"
            value = each.key
          }

          resources {
            limits = {
              cpu    = "100m"
              memory = "64Mi"
            }
            requests = {
              cpu    = "50m"
              memory = "32Mi"
            }
          }

          liveness_probe {
            http_get {
              path = "/"
              port = each.value.port
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }
        }
      }
    }
  }
}

# --- Services (one per deployment using for_each) ---
resource "kubernetes_service" "services" {
  for_each = var.services

  metadata {
    name      = each.key
    namespace = kubernetes_namespace.this.metadata[0].name
    labels    = merge(local.common_labels, { app = each.key })
  }

  spec {
    type = "NodePort"

    selector = {
      app = each.key
    }

    port {
      port        = each.value.port
      target_port = each.value.port
      node_port   = each.value.node_port
    }
  }
}

# --- Outputs ---
output "namespace" {
  value = kubernetes_namespace.this.metadata[0].name
}

output "release" {
  value = random_pet.release.id
}

output "service_urls" {
  description = "Run 'minikube service <name> -n tf-fullstack --url' to get actual URLs"
  value = {
    for name, svc in kubernetes_service.services :
    name => "NodePort: ${var.services[name].node_port}"
  }
}

output "deployment_replicas" {
  value = {
    for name, dep in kubernetes_deployment.services :
    name => dep.spec[0].replicas
  }
}

output "kubectl_commands" {
  value = <<-EOT
    kubectl get all -n ${var.namespace}
    kubectl get configmap shared-config -n ${var.namespace} -o yaml
    %{for name in keys(var.services)~}
    minikube service ${name} -n ${var.namespace} --url
    %{endfor~}
  EOT
}
