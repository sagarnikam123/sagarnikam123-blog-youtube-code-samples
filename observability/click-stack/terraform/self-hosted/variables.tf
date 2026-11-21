variable "dashboard_name" {
  description = "Name of the ClickStack dashboard managed by Terraform"
  type        = string
  default     = "Terraform logs dashboard"
}

variable "logs_source_id" {
  description = "ClickStack logs source ID used by the dashboard"
  type        = string
}

variable "team_id" {
  description = "Optional ClickStack team ID for a non-default self-hosted team"
  type        = string
  default     = null
  nullable    = true
}
