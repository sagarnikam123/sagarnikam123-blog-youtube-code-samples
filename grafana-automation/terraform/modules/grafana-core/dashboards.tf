# =============================================================================
# Dashboards - Load from instance-specific and shared folders
# =============================================================================

locals {
  # Instance-specific dashboards
  instance_dashboards = var.enable_dashboards && var.dashboard_folder != "" ? fileset(var.dashboard_folder, "*.json") : toset([])

  # Shared dashboards (if path provided)
  shared_dashboards = var.enable_dashboards && var.shared_dashboard_folder != "" ? fileset(var.shared_dashboard_folder, "*.json") : toset([])
}

# Instance-specific dashboards
resource "grafana_dashboard" "instance" {
  for_each = local.instance_dashboards

  config_json = file("${var.dashboard_folder}/${each.value}")
  folder      = length(grafana_folder.this) > 0 ? values(grafana_folder.this)[0].uid : null
  overwrite   = var.dashboard_overwrite
}

# Shared dashboards
resource "grafana_dashboard" "shared" {
  for_each = local.shared_dashboards

  config_json = file("${var.shared_dashboard_folder}/${each.value}")
  folder      = length(grafana_folder.this) > 0 ? values(grafana_folder.this)[0].uid : null
  overwrite   = var.dashboard_overwrite
}
