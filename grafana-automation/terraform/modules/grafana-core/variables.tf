# =============================================================================
# Grafana Core Module - Variables
# =============================================================================
# This module supports varying configurations per instance:
# - Some instances have only Loki
# - Some have multiple datasources
# - Some have only alerts, no dashboards
# - Some have many dashboards
# =============================================================================

# -----------------------------------------------------------------------------
# Connection
# -----------------------------------------------------------------------------
variable "grafana_url" {
  description = "Grafana server URL"
  type        = string
}

variable "grafana_auth" {
  description = "Grafana API key or username:password"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Instance Identity
# -----------------------------------------------------------------------------
variable "instance_name" {
  description = "Unique name for this Grafana instance (e.g., grafana-oss-dev)"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod, local)"
  type        = string
  default     = "dev"
}

# -----------------------------------------------------------------------------
# Feature Flags - Enable/disable entire feature sets
# -----------------------------------------------------------------------------
variable "enable_folders" {
  description = "Create folders"
  type        = bool
  default     = true
}

variable "enable_datasources" {
  description = "Create datasources"
  type        = bool
  default     = true
}

variable "enable_dashboards" {
  description = "Create dashboards"
  type        = bool
  default     = true
}

variable "enable_alerting" {
  description = "Create alerting resources (contact points, rules, policies)"
  type        = bool
  default     = false
}

variable "enable_teams" {
  description = "Create teams and permissions"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Folders
# -----------------------------------------------------------------------------
variable "folders" {
  description = "Map of folders to create"
  type = map(object({
    title = string
    uid   = optional(string)
  }))
  default = {}
}

# -----------------------------------------------------------------------------
# Datasources - Flexible configuration
# -----------------------------------------------------------------------------
variable "datasources" {
  description = "Map of datasources to create"
  type = map(object({
    type       = string                    # prometheus, loki, cloudwatch, etc.
    url        = optional(string, "")
    is_default = optional(bool, false)
    json_data  = optional(map(any), {})
    secure_json_data = optional(map(string), {})
  }))
  default = {}
}

# -----------------------------------------------------------------------------
# Dashboards
# -----------------------------------------------------------------------------
variable "dashboard_folder" {
  description = "Path to folder containing dashboard JSON files"
  type        = string
  default     = ""
}

variable "shared_dashboard_folder" {
  description = "Path to shared dashboards folder"
  type        = string
  default     = ""
}

variable "dashboard_overwrite" {
  description = "Overwrite existing dashboards"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Alerting
# -----------------------------------------------------------------------------
variable "webhook_url" {
  description = "Webhook URL for alerts"
  type        = string
  default     = ""
}

variable "alert_rules" {
  description = "Map of alert rules to create"
  type = map(object({
    name             = string
    folder_uid       = string
    datasource_uid   = string
    expr             = string
    threshold        = number
    for_duration     = optional(string, "5m")
    severity         = optional(string, "warning")
    summary          = optional(string, "")
  }))
  default = {}
}

# -----------------------------------------------------------------------------
# Teams
# -----------------------------------------------------------------------------
variable "teams" {
  description = "Map of teams to create"
  type = map(object({
    name  = string
    email = optional(string, "")
  }))
  default = {}
}
