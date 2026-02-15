# =============================================================================
# grafana-oss-staging - Staging environment
# Features: Multiple datasources, dashboards, 3 alert rules
# =============================================================================

module "grafana" {
  source = "../../modules/grafana-core"

  grafana_url   = var.grafana_url
  grafana_auth  = var.grafana_auth
  instance_name = "grafana-oss-staging"
  environment   = "staging"

  enable_folders     = true
  enable_datasources = true
  enable_dashboards  = true
  enable_alerting    = true  # Has alerts
  enable_teams       = false

  datasources             = var.datasources
  dashboard_folder        = "${path.module}/dashboards"
  shared_dashboard_folder = "../../shared/dashboards"

  webhook_url = var.webhook_url
  alert_rules = var.alert_rules
}

variable "grafana_url" { type = string }
variable "grafana_auth" { type = string; sensitive = true }
variable "datasources" { type = any; default = {} }
variable "webhook_url" { type = string; default = "" }
variable "alert_rules" { type = any; default = {} }

output "folder_uids" { value = module.grafana.folder_uids }
output "datasource_uids" { value = module.grafana.datasource_uids }
