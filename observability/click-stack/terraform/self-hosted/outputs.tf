output "dashboard_id" {
  description = "ID of the ClickStack dashboard managed by Terraform"
  value       = clickhouse_clickstack_dashboard.logs.id
}
