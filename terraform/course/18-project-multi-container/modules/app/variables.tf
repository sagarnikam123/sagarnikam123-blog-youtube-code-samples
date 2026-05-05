variable "app_name" {
  description = "Name of the application container"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]+$", var.app_name))
    error_message = "App name must be lowercase alphanumeric with hyphens."
  }
}

variable "image" {
  description = "Docker image to use"
  type        = string
}

variable "internal_port" {
  description = "Container internal port"
  type        = number
  default     = 80
}

variable "external_port" {
  description = "Host port to expose"
  type        = number

  validation {
    condition     = var.external_port >= 1024 && var.external_port <= 65535
    error_message = "External port must be between 1024 and 65535."
  }
}

variable "network_id" {
  description = "Docker network ID to attach to"
  type        = string
}

variable "env_vars" {
  description = "Environment variables for the container"
  type        = map(string)
  default     = {}
}

variable "volumes" {
  description = "Volume mounts"
  type = list(object({
    host_path      = string
    container_path = string
    read_only      = optional(bool, false)
  }))
  default = []
}
