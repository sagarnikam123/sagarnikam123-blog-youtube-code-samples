# =============================================================================
# Module: docker-app — Outputs
# =============================================================================

output "container_name" {
  description = "Name of the created container"
  value       = docker_container.app.name
}

output "container_id" {
  description = "ID of the created container"
  value       = docker_container.app.id
}

output "access_url" {
  description = "URL to access the container"
  value       = "http://localhost:${var.external_port}"
}
