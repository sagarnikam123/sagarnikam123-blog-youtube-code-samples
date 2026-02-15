# Outputs

output "grafana_url" {
  description = "Grafana URL"
  value       = var.grafana_url
}

output "folder_uid" {
  description = "Main folder UID"
  value       = grafana_folder.main.uid
}

output "prometheus_datasource_uid" {
  description = "Prometheus datasource UID"
  value       = grafana_data_source.prometheus.uid
}

output "dashboard_url" {
  description = "Golden Signals dashboard URL"
  value       = "${var.grafana_url}/d/${grafana_dashboard.golden_signals.uid}"
}

output "loki_datasource_uid" {
  description = "Loki datasource UID (if enabled)"
  value       = var.loki_url != "" ? grafana_data_source.loki[0].uid : null
}
