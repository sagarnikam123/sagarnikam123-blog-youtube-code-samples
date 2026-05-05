output "container_name" {
  description = "Name of the container"
  value       = docker_container.this.name
}

output "container_id" {
  description = "ID of the container"
  value       = docker_container.this.id
}

output "access_url" {
  description = "URL to access the container"
  value       = "http://localhost:${var.external_port}"
}

output "ip_address" {
  description = "Container IP on the Docker network"
  value       = docker_container.this.network_data[0].ip_address
}
