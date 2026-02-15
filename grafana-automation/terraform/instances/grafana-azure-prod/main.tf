# =============================================================================
# grafana-azure-prod - Azure Managed Grafana Production
# =============================================================================
# Prerequisites:
# 1. Azure Managed Grafana instance created
# 2. Service account created: ./scripts/create-service-account.sh
# 3. Set TF_VAR_grafana_auth with the token
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = ">= 2.0"
    }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth
}

module "grafana" {
  source = "../../modules/grafana-core"

  grafana_url   = var.grafana_url
  grafana_auth  = var.grafana_auth
  instance_name = "grafana-azure-prod"
  environment   = "prod"

  enable_folders     = true
  enable_datasources = true
  enable_dashboards  = true
  enable_alerting    = var.webhook_url != ""
  enable_teams       = false  # Azure uses Entra ID for access control

  datasources             = var.datasources
  dashboard_folder        = "${path.module}/dashboards"
  shared_dashboard_folder = "../../shared/dashboards"
  webhook_url             = var.webhook_url
  alert_rules             = var.alert_rules
}

# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------
variable "grafana_url" {
  description = "Azure Managed Grafana endpoint (e.g., https://my-grafana-xxxx.xxx.grafana.azure.com)"
  type        = string
}

variable "grafana_auth" {
  description = "Service account token (create via Azure CLI)"
  type        = string
  sensitive   = true
}

variable "datasources" {
  type    = any
  default = {}
}

variable "webhook_url" {
  type    = string
  default = ""
}

variable "alert_rules" {
  type    = any
  default = {}
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "folder_uids" { value = module.grafana.folder_uids }
output "datasource_uids" { value = module.grafana.datasource_uids }
