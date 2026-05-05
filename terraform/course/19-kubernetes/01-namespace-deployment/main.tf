# =============================================================================
# Module 19 — Exercise 1: Namespace & Deployment
# =============================================================================
# Create a Kubernetes namespace and deploy Nginx pods.
#
# Prerequisites:
#   minikube start --driver=docker
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply
#   kubectl get pods -n tf-learning
#   kubectl get deployments -n tf-learning
#   terraform destroy
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

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

# --- Variables ---
variable "namespace" {
  description = "Kubernetes namespace name"
  type        = string
  default     = "tf-learning"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "web"
}

variable "replicas" {
  description = "Number of pod replicas"
  type        = number
  default     = 2
}

variable "image" {
  description = "Container image"
  type        = string
  default     = "nginx:alpine"
}

# --- Namespace ---
resource "kubernetes_namespace" "app" {
  metadata {
    name = var.namespace

    labels = {
      managed_by  = "terraform"
      environment = "learning"
    }
  }
}

# --- Deployment ---
resource "kubernetes_deployment" "app" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.app.metadata[0].name

    labels = {
      app        = var.app_name
      managed_by = "terraform"
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = var.app_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.app_name
        }
      }

      spec {
        container {
          name  = var.app_name
          image = var.image

          port {
            container_port = 80
            name           = "http"
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
              port = 80
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }
        }
      }
    }
  }
}

# --- Outputs ---
output "namespace" {
  description = "Created namespace"
  value       = kubernetes_namespace.app.metadata[0].name
}

output "deployment_name" {
  description = "Deployment name"
  value       = kubernetes_deployment.app.metadata[0].name
}

output "replicas" {
  description = "Number of replicas"
  value       = var.replicas
}

output "kubectl_commands" {
  description = "Useful kubectl commands to inspect the resources"
  value = <<-EOT
    kubectl get pods -n ${var.namespace}
    kubectl get deployments -n ${var.namespace}
    kubectl describe deployment ${var.app_name} -n ${var.namespace}
    kubectl logs -l app=${var.app_name} -n ${var.namespace}
  EOT
}
