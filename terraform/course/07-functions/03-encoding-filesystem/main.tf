# =============================================================================
# Module 07 — Exercise 3: Encoding & Filesystem Functions
# =============================================================================
# JSON, YAML, base64, file(), templatefile()
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "local" {}

variable "config" {
  type = object({
    app_name    = string
    version     = string
    debug       = bool
    ports       = list(number)
    database    = map(string)
  })
  default = {
    app_name = "myapp"
    version  = "1.0.0"
    debug    = false
    ports    = [8080, 8443]
    database = {
      host = "localhost"
      port = "5432"
      name = "mydb"
    }
  }
}

locals {
  # JSON encoding/decoding
  config_json = jsonencode(var.config)
  decoded     = jsondecode(local.config_json)

  # YAML encoding
  config_yaml = yamlencode(var.config)

  # Base64
  encoded_secret = base64encode("my-secret-value")
  decoded_secret = base64decode(local.encoded_secret)

  # templatefile — render a template with variables
  nginx_config = templatefile("${path.module}/templates/nginx.conf.tftpl", {
    listen_port = 80
    server_name = "localhost"
    services = [
      { name = "web", port = 8080 },
      { name = "api", port = 3000 },
      { name = "docs", port = 4000 },
    ]
  })
}

# Write JSON config
resource "local_file" "json_config" {
  filename = "${path.module}/output/config.json"
  content  = local.config_json
}

# Write YAML config
resource "local_file" "yaml_config" {
  filename = "${path.module}/output/config.yaml"
  content  = local.config_yaml
}

# Write rendered Nginx config
resource "local_file" "nginx_config" {
  filename = "${path.module}/output/nginx.conf"
  content  = local.nginx_config
}

# Write encoding demo
resource "local_file" "encoding_demo" {
  filename = "${path.module}/output/encoding-demo.txt"
  content  = <<-EOT
    === Encoding Demo ===

    Base64 encoded: ${local.encoded_secret}
    Base64 decoded: ${local.decoded_secret}

    JSON output:    See config.json
    YAML output:    See config.yaml
    Template:       See nginx.conf
  EOT
}

output "json_preview" {
  value = local.config_json
}

output "base64_encoded" {
  value = local.encoded_secret
}
