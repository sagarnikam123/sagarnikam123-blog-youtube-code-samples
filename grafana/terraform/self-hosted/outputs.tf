output "folder_uid" {
  description = "UID of the Grafana folder created by Terraform"
  value       = grafana_folder.observability.uid
}

output "dashboard_url" {
  description = "URL of the Terraform-managed dashboard"
  value       = grafana_dashboard.example.url
}
