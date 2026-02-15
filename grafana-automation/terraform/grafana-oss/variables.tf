# Variables for Grafana OSS

variable "grafana_url" {
  description = "Grafana server URL"
  type        = string
  default     = "http://localhost:3000"
}

variable "grafana_auth" {
  description = "Grafana API key or username:password"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

# Data source URLs
variable "prometheus_url" {
  description = "Prometheus server URL"
  type        = string
  default     = "http://localhost:9090"
}

variable "loki_url" {
  description = "Loki server URL (leave empty to skip)"
  type        = string
  default     = "http://localhost:3100"
}

# Feature flags
variable "alerting_enabled" {
  description = "Enable alerting resources"
  type        = bool
  default     = false
}

variable "webhook_url" {
  description = "Webhook URL for alerts (e.g., webhook.site, custom endpoint)"
  type        = string
  sensitive   = true
  default     = ""
}
