# =============================================================================
# grafana-oss-dev - Development environment
# Features: Only Loki datasource, no dashboards, no alerting
# =============================================================================

module "grafana" {
  source = "../../modules/grafana-core"

  grafana_url   = var.grafana_url
  grafana_auth  = var.grafana_auth
  instance_name = "grafana-oss-dev"
  environment   = "dev"

  enable_folders     = true
  enable_datasources = true
  enable_dashboards  = false  # No dashboards for dev
  enable_alerting    = false
  enable_teams       = false

  datasources = var.datasources
}

variable "grafana_url" { type = string }
variable "grafana_auth" { type = string; sensitive = true }
variable "datasources" { type = any; default = {} }

output "folder_uids" { value = module.grafana.folder_uids }
output "datasource_uids" { value = module.grafana.datasource_uids }
