# =============================================================================
# Outputs
# =============================================================================

output "folder_uids" {
  description = "Map of folder names to UIDs"
  value       = { for k, v in grafana_folder.this : k => v.uid }
}

output "datasource_uids" {
  description = "Map of datasource names to UIDs"
  value       = { for k, v in grafana_data_source.this : k => v.uid }
}

output "dashboard_urls" {
  description = "URLs of created dashboards"
  value = merge(
    { for k, v in grafana_dashboard.instance : k => "${var.grafana_url}/d/${v.uid}" },
    { for k, v in grafana_dashboard.shared : "shared-${k}" => "${var.grafana_url}/d/${v.uid}" }
  )
}

output "contact_point_name" {
  description = "Name of the webhook contact point"
  value       = var.enable_alerting && var.webhook_url != "" ? grafana_contact_point.webhook[0].name : null
}
