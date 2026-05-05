# =============================================================================
# Module 04 — Exercise 2: Data Sources
# =============================================================================
# Data sources READ information — they don't create infrastructure.
# Uses: http (fetch a URL), local_file (read a file), external (run a script).
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    http = {
      source  = "hashicorp/http"
      version = "~> 3.4"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.3"
    }
  }
}

provider "http" {}
provider "local" {}
provider "external" {}

# --- Data Source 1: HTTP request ---
# Fetch your public IP address from a free API
data "http" "my_ip" {
  url = "https://api.ipify.org?format=json"

  request_headers = {
    Accept = "application/json"
  }
}

# --- Data Source 2: External script ---
# Run a local script and consume its JSON output
data "external" "system_info" {
  program = ["bash", "${path.module}/scripts/system-info.sh"]
}

# --- Data Source 3: Read a local file ---
# First create a file, then read it back via data source
resource "local_file" "sample" {
  filename = "${path.module}/output/sample.txt"
  content  = "This file was created by Terraform at ${timestamp()}"
}

data "local_file" "read_sample" {
  filename = local_file.sample.filename

  depends_on = [local_file.sample]
}

# --- Outputs ---
output "public_ip_response" {
  description = "Response from the IP API"
  value       = data.http.my_ip.response_body
}

output "system_hostname" {
  description = "Hostname from the external script"
  value       = data.external.system_info.result.hostname
}

output "system_os" {
  description = "OS from the external script"
  value       = data.external.system_info.result.os
}

output "file_content" {
  description = "Content read back from the local file"
  value       = data.local_file.read_sample.content
}
