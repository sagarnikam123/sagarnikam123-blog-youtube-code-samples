variable "openobserve_url" {
  description = "URL of the self-hosted OpenObserve instance"
  type        = string
  default     = "http://localhost:5080"
}

variable "openobserve_username" {
  description = "OpenObserve root user email"
  type        = string
  default     = "root@example.com"
}

variable "openobserve_password" {
  description = "OpenObserve root user password"
  type        = string
  sensitive   = true
}
