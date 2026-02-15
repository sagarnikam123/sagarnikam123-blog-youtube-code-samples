# =============================================================================
# grafana-oss-local - Local development instance
# Features: Prometheus + Loki, basic dashboard, no alerting
# =============================================================================

module "grafana" {
  source = "../../modules/grafana-core"

  grafana_url   = var.grafana_url
  grafana_auth  = var.grafana_auth
  instance_name = "grafana-oss-local"
  environment   = "local"

  enable_folders     = true
  enable_datasources = true
  enable_dashboards  = true
  enable_alerting    = false
  enable_teams       = false

  datasources             = var.datasources
  dashboard_folder        = "${path.module}/dashboards"
  shared_dashboard_folder = "../../shared/dashboards"
}

variable "grafana_url" { type = string }
variable "grafana_auth" { type = string; sensitive = true }
variable "datasources" { type = any; default = {} }

output "folder_uids" { value = module.grafana.folder_uids }
output "datasource_uids" { value = module.grafana.datasource_uids }
