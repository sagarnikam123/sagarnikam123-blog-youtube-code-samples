# =============================================================================
# Module 29 — Exercise 2: Archive Files
# =============================================================================
# Create zip archives from source files — the pattern used for:
# - AWS Lambda deployment packages
# - Google Cloud Functions
# - Azure Functions
# - Any "upload a zip" workflow
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "archive" {}
provider "local" {}

# --- Create some source files to archive ---
resource "local_file" "app_code" {
  filename = "${path.module}/src/index.js"
  content  = <<-EOT
    exports.handler = async (event) => {
      return {
        statusCode: 200,
        body: JSON.stringify({ message: "Hello from Lambda!" }),
      };
    };
  EOT
}

resource "local_file" "package_json" {
  filename = "${path.module}/src/package.json"
  content  = jsonencode({
    name    = "lambda-function"
    version = "1.0.0"
    main    = "index.js"
  })
}

resource "local_file" "config" {
  filename = "${path.module}/src/config.json"
  content  = jsonencode({
    region      = "ap-south-1"
    environment = "production"
    log_level   = "info"
  })
}

# --- Archive: Zip from a directory ---
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/output/lambda.zip"

  depends_on = [
    local_file.app_code,
    local_file.package_json,
    local_file.config,
  ]
}

# --- Archive: Zip from a single file ---
data "archive_file" "single_file" {
  type        = "zip"
  source_file = "${path.module}/src/index.js"
  output_path = "${path.module}/output/handler.zip"

  depends_on = [local_file.app_code]
}

# --- Archive: Zip with exclusions (using source block) ---
data "archive_file" "selective" {
  type        = "zip"
  output_path = "${path.module}/output/selective.zip"

  source {
    content  = local_file.app_code.content
    filename = "index.js"
  }

  source {
    content  = local_file.config.content
    filename = "config.json"
  }
}

# --- Outputs ---
output "lambda_zip" {
  value = {
    path     = data.archive_file.lambda_package.output_path
    size     = data.archive_file.lambda_package.output_size
    hash     = data.archive_file.lambda_package.output_base64sha256
  }
}

output "single_file_zip" {
  value = data.archive_file.single_file.output_path
}

output "selective_zip" {
  value = data.archive_file.selective.output_path
}

output "usage_note" {
  value = <<-EOT
    In production, you'd use the hash to trigger Lambda updates:
      source_code_hash = data.archive_file.lambda_package.output_base64sha256
    This ensures Lambda redeploys only when code changes.
  EOT
}
