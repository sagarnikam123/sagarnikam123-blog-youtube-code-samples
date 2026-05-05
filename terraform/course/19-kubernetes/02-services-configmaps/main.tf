# =============================================================================
# Module 19 — Exercise 2: Services & ConfigMaps
# =============================================================================
# Expose a deployment via a Service and inject config via ConfigMap.
#
# After apply:
#   kubectl get svc -n tf-services
#   minikube service web -n tf-services --url    # get the NodePort URL
#   curl <url>
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

variable "namespace" {
  type    = string
  default = "tf-services"
}

variable "app_name" {
  type    = string
  default = "web"
}

variable "app_config" {
  description = "Application configuration values"
  type        = map(string)
  default = {
    LOG_LEVEL   = "info"
    APP_ENV     = "development"
    APP_VERSION = "1.0.0"
    TZ          = "Asia/Kolkata"
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

# --- ConfigMap ---
resource "kubernetes_config_map" "app" {
  metadata {
    name      = "${var.app_name}-config"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  data = var.app_config
}

# --- Deployment with ConfigMap mounted as env vars ---
resource "kubernetes_deployment" "app" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.this.metadata[0].name
    labels = {
      app = var.app_name
    }
  }

  spec {
    replicas = 2

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
          image = "nginx:alpine"

          port {
            container_port = 80
          }

          # Inject all ConfigMap keys as environment variables
          env_from {
            config_map_ref {
              name = kubernetes_config_map.app.metadata[0].name
            }
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
        }
      }
    }
  }
}

# --- Service (NodePort) ---
resource "kubernetes_service" "app" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.this.metadata[0].name
    labels = {
      app = var.app_name
    }
  }

  spec {
    type = "NodePort"

    selector = {
      app = var.app_name
    }

    port {
      port        = 80
      target_port = 80
      node_port   = 30080
    }
  }
}

# --- Outputs ---
output "namespace" {
  value = kubernetes_namespace.this.metadata[0].name
}

output "configmap_name" {
  value = kubernetes_config_map.app.metadata[0].name
}

output "service_name" {
  value = kubernetes_service.app.metadata[0].name
}

output "service_type" {
  value = kubernetes_service.app.spec[0].type
}

output "access_command" {
  description = "Run this to get the URL"
  value       = "minikube service ${var.app_name} -n ${var.namespace} --url"
}
