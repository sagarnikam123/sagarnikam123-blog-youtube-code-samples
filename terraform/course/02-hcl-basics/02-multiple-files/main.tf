# =============================================================================
# main.tf — Resource definitions
# =============================================================================

locals {
  content = <<-EOT
    Author: ${var.author}
    Environment: ${var.environment}
    Random ID: ${random_id.example.hex}
  EOT
}

resource "random_id" "example" {
  byte_length = 4
}

resource "local_file" "config" {
  filename = "${path.module}/output/config.txt"
  content  = local.content
}
