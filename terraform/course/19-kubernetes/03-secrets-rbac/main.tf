# =============================================================================
# Module 19 — Exercise 3: Secrets & RBAC
# =============================================================================
# Create Kubernetes secrets and set up role-based access control.
#
# After apply:
#   kubectl get secrets -n tf-rbac
#   kubectl get roles -n tf-rbac
#   kubectl get rolebindings -n tf-rbac
#   kubectl get serviceaccounts -n tf-rbac
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

variable "namespace" {
  type    = string
  default = "tf-rbac"
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

# --- Generate a random password ---
resource "random_password" "db_password" {
  length  = 24
  special = false
}

# --- Secret (Opaque) ---
resource "kubernetes_secret" "db_credentials" {
  metadata {
    name      = "db-credentials"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  type = "Opaque"

  data = {
    username = "app_user"
    password = random_password.db_password.result
    host     = "postgres.internal"
    port     = "5432"
    database = "myapp"
  }
}

# --- Secret (Docker Registry — example structure) ---
resource "kubernetes_secret" "registry" {
  metadata {
    name      = "registry-credentials"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "registry.example.com" = {
          username = "deploy-bot"
          password = "example-token"
          auth     = base64encode("deploy-bot:example-token")
        }
      }
    })
  }
}

# --- Service Account ---
resource "kubernetes_service_account" "app" {
  metadata {
    name      = "app-service-account"
    namespace = kubernetes_namespace.this.metadata[0].name
    labels = {
      app = "myapp"
    }
  }
}

# --- Role (namespace-scoped permissions) ---
resource "kubernetes_role" "app_reader" {
  metadata {
    name      = "app-reader"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  # Can read pods and logs
  rule {
    api_groups = [""]
    resources  = ["pods", "pods/log", "services", "configmaps"]
    verbs      = ["get", "list", "watch"]
  }

  # Can read deployments
  rule {
    api_groups = ["apps"]
    resources  = ["deployments"]
    verbs      = ["get", "list", "watch"]
  }
}

# --- Role (write permissions) ---
resource "kubernetes_role" "app_deployer" {
  metadata {
    name      = "app-deployer"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments"]
    verbs      = ["get", "list", "watch", "create", "update", "patch"]
  }

  rule {
    api_groups = [""]
    resources  = ["services", "configmaps"]
    verbs      = ["get", "list", "watch", "create", "update", "patch"]
  }
}

# --- RoleBinding (bind role to service account) ---
resource "kubernetes_role_binding" "app_reader" {
  metadata {
    name      = "app-reader-binding"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.app_reader.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.app.metadata[0].name
    namespace = kubernetes_namespace.this.metadata[0].name
  }
}

resource "kubernetes_role_binding" "app_deployer" {
  metadata {
    name      = "app-deployer-binding"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.app_deployer.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.app.metadata[0].name
    namespace = kubernetes_namespace.this.metadata[0].name
  }
}

# --- Outputs ---
output "namespace" {
  value = kubernetes_namespace.this.metadata[0].name
}

output "secret_names" {
  value = [
    kubernetes_secret.db_credentials.metadata[0].name,
    kubernetes_secret.registry.metadata[0].name,
  ]
}

output "service_account" {
  value = kubernetes_service_account.app.metadata[0].name
}

output "roles" {
  value = [
    kubernetes_role.app_reader.metadata[0].name,
    kubernetes_role.app_deployer.metadata[0].name,
  ]
}

output "kubectl_commands" {
  value = <<-EOT
    kubectl get secrets -n ${var.namespace}
    kubectl get sa -n ${var.namespace}
    kubectl get roles -n ${var.namespace}
    kubectl get rolebindings -n ${var.namespace}
    kubectl describe secret db-credentials -n ${var.namespace}
    kubectl auth can-i list pods -n ${var.namespace} --as=system:serviceaccount:${var.namespace}:app-service-account
  EOT
}
