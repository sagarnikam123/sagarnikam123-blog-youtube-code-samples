# =============================================================================
# Module 24 — Exercise 1: S3 Buckets with LocalStack
# =============================================================================
# Create S3 buckets locally using LocalStack.
#
# Prerequisites:
#   localstack start -d
#   # or: docker run -d -p 4566:4566 localstack/localstack
#
# Usage:
#   terraform init
#   terraform apply
#   aws --endpoint-url=http://localhost:4566 s3 ls
#   aws --endpoint-url=http://localhost:4566 s3 ls s3://my-app-assets/
#   terraform destroy
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# --- LocalStack AWS Provider ---
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3 = "http://localhost:4566"
  }
}

provider "random" {}

# --- Variables ---
variable "environment" {
  type    = string
  default = "dev"
}

variable "project" {
  type    = string
  default = "my-app"
}

# --- Random suffix for unique bucket names ---
resource "random_id" "suffix" {
  byte_length = 4
}

# --- S3 Bucket: Application Assets ---
resource "aws_s3_bucket" "assets" {
  bucket = "${var.project}-assets-${random_id.suffix.hex}"

  tags = {
    Name        = "${var.project}-assets"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# --- S3 Bucket: Logs ---
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project}-logs-${random_id.suffix.hex}"

  tags = {
    Name        = "${var.project}-logs"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# --- Bucket Versioning ---
resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id

  versioning_configuration {
    status = "Enabled"
  }
}

# --- Bucket Lifecycle Rule ---
resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    expiration {
      days = 30
    }

    filter {
      prefix = "logs/"
    }
  }
}

# --- Upload a sample object ---
resource "aws_s3_object" "readme" {
  bucket  = aws_s3_bucket.assets.id
  key     = "README.txt"
  content = "This bucket is managed by Terraform via LocalStack."

  content_type = "text/plain"
}

# --- Outputs ---
output "assets_bucket" {
  value = aws_s3_bucket.assets.bucket
}

output "logs_bucket" {
  value = aws_s3_bucket.logs.bucket
}

output "verify_commands" {
  value = <<-EOT
    aws --endpoint-url=http://localhost:4566 s3 ls
    aws --endpoint-url=http://localhost:4566 s3 ls s3://${aws_s3_bucket.assets.bucket}/
    aws --endpoint-url=http://localhost:4566 s3 cp s3://${aws_s3_bucket.assets.bucket}/README.txt -
  EOT
}
