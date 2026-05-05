# =============================================================================
# Module 24 — Exercise 2: DynamoDB Tables with LocalStack
# =============================================================================
# Create DynamoDB tables with indexes and capacity settings.
#
# After apply:
#   aws --endpoint-url=http://localhost:4566 dynamodb list-tables
#   aws --endpoint-url=http://localhost:4566 dynamodb describe-table --table-name users
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    dynamodb = "http://localhost:4566"
  }
}

# --- Users Table (simple primary key) ---
resource "aws_dynamodb_table" "users" {
  name         = "users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  # Global Secondary Index — query by email
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = {
    Name      = "users"
    ManagedBy = "terraform"
  }
}

# --- Orders Table (composite key: user_id + order_id) ---
resource "aws_dynamodb_table" "orders" {
  name         = "orders"
  billing_mode = "PROVISIONED"
  hash_key     = "user_id"
  range_key    = "order_id"

  read_capacity  = 5
  write_capacity = 5

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "order_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  # Local Secondary Index — query orders by date
  local_secondary_index {
    name            = "created-at-index"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  tags = {
    Name      = "orders"
    ManagedBy = "terraform"
  }
}

# --- Sessions Table (with TTL) ---
resource "aws_dynamodb_table" "sessions" {
  name         = "sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name      = "sessions"
    ManagedBy = "terraform"
  }
}

# --- Outputs ---
output "tables" {
  value = [
    aws_dynamodb_table.users.name,
    aws_dynamodb_table.orders.name,
    aws_dynamodb_table.sessions.name,
  ]
}

output "users_table_arn" {
  value = aws_dynamodb_table.users.arn
}

output "verify_commands" {
  value = <<-EOT
    aws --endpoint-url=http://localhost:4566 dynamodb list-tables
    aws --endpoint-url=http://localhost:4566 dynamodb describe-table --table-name users
    aws --endpoint-url=http://localhost:4566 dynamodb put-item --table-name users --item '{"user_id":{"S":"u1"},"email":{"S":"test@example.com"},"name":{"S":"Test User"}}'
    aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name users
  EOT
}
