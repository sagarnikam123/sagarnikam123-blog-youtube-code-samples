# =============================================================================
# Grafana Core Module - Main
# =============================================================================
# Reusable module for managing any Grafana OSS instance
# Supports conditional resource creation based on feature flags
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = ">= 2.0"
    }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth
}

locals {
  # Default folder if none specified
  default_folder = {
    main = {
      title = "${title(var.environment)} Monitoring"
      uid   = "${var.instance_name}-monitoring"
    }
  }

  # Use provided folders or default
  folders = var.enable_folders ? (length(var.folders) > 0 ? var.folders : local.default_folder) : {}
}
