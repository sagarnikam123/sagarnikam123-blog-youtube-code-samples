variable "signoz_endpoint" {
  description = "URL of the self-hosted SigNoz instance"
  type        = string
  default     = "http://localhost:8080"
}

variable "signoz_api_token" {
  description = "SigNoz API token (Settings → API Tokens)"
  type        = string
  sensitive   = true
}
