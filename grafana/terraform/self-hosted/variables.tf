variable "grafana_url" {
  description = "URL of the self-hosted Grafana instance"
  type        = string
  default     = "http://localhost:3000"
}

variable "grafana_auth" {
  description = "Grafana service account token (Administration → Service Accounts → Add token)"
  type        = string
  sensitive   = true
}
