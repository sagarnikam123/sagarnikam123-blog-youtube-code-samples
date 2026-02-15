# =============================================================================
# Instance Template - Copy this folder for new instances
# =============================================================================
# Usage:
#   1. cp -r _template grafana-oss-new
#   2. Update terraform.tfvars
#   3. terraform init && terraform apply
# =============================================================================

module "grafana" {
  source = "../../modules/grafana-core"

  # Connection
  grafana_url  = var.grafana_url
  grafana_auth = var.grafana_auth

  # Identity
  instance_name = var.instance_name
  environment   = var.environment

  # Feature flags
  enable_folders     = var.enable_folders
  enable_datasources = var.enable_datasources
  enable_dashboards  = var.enable_dashboards
  enable_alerting    = var.enable_alerting
  enable_teams       = var.enable_teams

  # Resources
  folders     = var.folders
  datasources = var.datasources

  # Dashboards
  dashboard_folder        = var.dashboard_folder
  shared_dashboard_folder = var.shared_dashboard_folder

  # Alerting
  webhook_url = var.webhook_url
  alert_rules = var.alert_rules

  # Teams
  teams = var.teams
}

# -----------------------------------------------------------------------------
# Variables (passed from terraform.tfvars)
# -----------------------------------------------------------------------------
variable "grafana_url" { type = string }
variable "grafana_auth" { type = string; sensitive = true }
variable "instance_name" { type = string }
variable "environment" { type = string; default = "dev" }

variable "enable_folders" { type = bool; default = true }
variable "enable_datasources" { type = bool; default = true }
variable "enable_dashboards" { type = bool; default = false }
variable "enable_alerting" { type = bool; default = false }
variable "enable_teams" { type = bool; default = false }

variable "folders" { type = any; default = {} }
variable "datasources" { type = any; default = {} }
variable "dashboard_folder" { type = string; default = "" }
variable "shared_dashboard_folder" { type = string; default = "" }
variable "webhook_url" { type = string; default = "" }
variable "alert_rules" { type = any; default = {} }
variable "teams" { type = any; default = {} }

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "folder_uids" { value = module.grafana.folder_uids }
output "datasource_uids" { value = module.grafana.datasource_uids }
output "dashboard_urls" { value = module.grafana.dashboard_urls }
