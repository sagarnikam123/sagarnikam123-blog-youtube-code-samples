# Step 9: Additional Resources (Optional)
# These are less commonly used but available in the provider
#
# References:
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/mute_timing
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/annotation
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/playlist
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/library_panel
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/organization

# =============================================================================
# MUTE TIMING - Silence alerts during maintenance windows
# =============================================================================
# Command: terraform apply -target=grafana_mute_timing.weekends
# Destroy: terraform destroy -target=grafana_mute_timing.weekends

resource "grafana_mute_timing" "weekends" {
  count = var.alerting_enabled ? 1 : 0

  name = "Weekend Mute"

  intervals {
    weekdays = ["saturday", "sunday"]
  }
}

resource "grafana_mute_timing" "maintenance" {
  count = var.alerting_enabled ? 1 : 0

  name = "Maintenance Window"

  intervals {
    times {
      start = "02:00"
      end   = "04:00"
    }
    weekdays = ["sunday"]
  }
}

# =============================================================================
# ANNOTATION - Add annotations to dashboards programmatically
# =============================================================================
# Command: terraform apply -target=grafana_annotation.deployment
# Destroy: terraform destroy -target=grafana_annotation.deployment
#
# Useful for marking deployments, incidents, etc.

# resource "grafana_annotation" "deployment" {
#   text = "Deployment v1.2.3"
#   tags = ["deployment", var.environment]
#
#   # Optional: link to specific dashboard
#   # dashboard_uid = grafana_dashboard.system_overview.uid
# }

# =============================================================================
# PLAYLIST - Auto-rotate through dashboards
# =============================================================================
# Command: terraform apply -target=grafana_playlist.monitoring
# Destroy: terraform destroy -target=grafana_playlist.monitoring

# resource "grafana_playlist" "monitoring" {
#   name     = "Monitoring Rotation"
#   interval = "5m"
#
#   item {
#     order = 1
#     title = "System Overview"
#     type  = "dashboard_by_uid"
#     value = grafana_dashboard.system_overview.uid
#   }
# }

# =============================================================================
# LIBRARY PANEL - Reusable panel across dashboards
# =============================================================================
# Command: terraform apply -target=grafana_library_panel.cpu_gauge
# Destroy: terraform destroy -target=grafana_library_panel.cpu_gauge

# resource "grafana_library_panel" "cpu_gauge" {
#   name       = "CPU Usage Gauge"
#   folder_uid = grafana_folder.main.uid
#
#   model_json = jsonencode({
#     title = "CPU Usage"
#     type  = "gauge"
#     datasource = { type = "prometheus", uid = grafana_data_source.prometheus.uid }
#     targets = [{
#       expr  = "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
#       refId = "A"
#     }]
#     fieldConfig = {
#       defaults = { unit = "percent", min = 0, max = 100 }
#     }
#   })
# }

# =============================================================================
# ORGANIZATION - Multi-tenant Grafana (OSS only, not AMG/Azure)
# =============================================================================
# Command: terraform apply -target=grafana_organization.tenant
# Destroy: terraform destroy -target=grafana_organization.tenant
#
# Note: Organizations are for multi-tenant setups. Most single-tenant
# deployments don't need this.

# resource "grafana_organization" "tenant" {
#   name = "Tenant A"
#
#   admin_user = "admin"
#   admins     = ["admin@example.com"]
#   editors    = ["editor@example.com"]
#   viewers    = ["viewer@example.com"]
# }
