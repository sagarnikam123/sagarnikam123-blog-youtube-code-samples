# =============================================================================
# grafana-amg-prod - Amazon Managed Grafana Production
# =============================================================================
# AMG uses two-plane architecture:
# - Control Plane (AWS Provider): Workspace, IAM roles
# - Data Plane (Grafana Provider): Dashboards, datasources, alerts
#
# Prerequisites:
# 1. Create AMG workspace via AWS Console or separate Terraform
# 2. Create API key: ./scripts/create-api-key.sh
# 3. Set TF_VAR_grafana_auth with the API key
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
  instance_name = "grafana-amg-prod"
  environment   = "prod"

  enable_folders     = true
  enable_datasources = true
  enable_dashboards  = true
  enable_alerting    = var.webhook_url != ""
  enable_teams       = false  # AMG uses AWS SSO for access control

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
  description = "AMG workspace endpoint (e.g., https://g-xxx.grafana-workspace.us-east-1.amazonaws.com)"
  type        = string
}

variable "grafana_auth" {
  description = "AMG API key (create via AWS CLI or Console)"
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
