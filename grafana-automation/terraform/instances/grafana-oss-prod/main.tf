# =============================================================================
# grafana-oss-prod - Production environment
# Features: Multiple datasources, many dashboards, full alerting, teams
# =============================================================================

module "grafana" {
  source = "../../modules/grafana-core"

  grafana_url   = var.grafana_url
  grafana_auth  = var.grafana_auth
  instance_name = "grafana-oss-prod"
  environment   = "prod"

  enable_folders     = true
  enable_datasources = true
  enable_dashboards  = true
  enable_alerting    = true
  enable_teams       = true  # Full access control

  folders                 = var.folders
  datasources             = var.datasources
  dashboard_folder        = "${path.module}/dashboards"
  shared_dashboard_folder = "../../shared/dashboards"

  webhook_url = var.webhook_url
  alert_rules = var.alert_rules
  teams       = var.teams
}

variable "grafana_url" { type = string }
variable "grafana_auth" { type = string; sensitive = true }
variable "folders" { type = any; default = {} }
variable "datasources" { type = any; default = {} }
variable "webhook_url" { type = string; default = "" }
variable "alert_rules" { type = any; default = {} }
variable "teams" { type = any; default = {} }

output "folder_uids" { value = module.grafana.folder_uids }
output "datasource_uids" { value = module.grafana.datasource_uids }
