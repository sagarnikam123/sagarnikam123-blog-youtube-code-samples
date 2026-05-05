# =============================================================================
# Module 24 — Exercise 4: IAM Roles & Policies with LocalStack
# =============================================================================
# Create IAM roles, policies, and attachments.
# This is the most common Terraform pattern in AWS — you'll write this daily.
#
# After apply:
#   aws --endpoint-url=http://localhost:4566 iam list-roles
#   aws --endpoint-url=http://localhost:4566 iam list-policies --scope Local
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
    iam = "http://localhost:4566"
    sts = "http://localhost:4566"
  }
}

# --- Data: Assume Role Policy Document ---
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# --- IAM Role for Lambda ---
resource "aws_iam_role" "lambda_exec" {
  name               = "lambda-execution-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json

  tags = {
    Name      = "lambda-execution-role"
    ManagedBy = "terraform"
  }
}

# --- Custom Policy: S3 Read Access ---
data "aws_iam_policy_document" "s3_read" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::my-app-*",
      "arn:aws:s3:::my-app-*/*",
    ]
  }
}

resource "aws_iam_policy" "s3_read" {
  name        = "s3-read-access"
  description = "Allow read access to app S3 buckets"
  policy      = data.aws_iam_policy_document.s3_read.json
}

# --- Custom Policy: DynamoDB Access ---
data "aws_iam_policy_document" "dynamodb_crud" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = ["arn:aws:dynamodb:us-east-1:*:table/users"]
  }
}

resource "aws_iam_policy" "dynamodb_crud" {
  name        = "dynamodb-crud-access"
  description = "CRUD access to users DynamoDB table"
  policy      = data.aws_iam_policy_document.dynamodb_crud.json
}

# --- Attach Policies to Role ---
resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.s3_read.arn
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.dynamodb_crud.arn
}

# Attach AWS managed policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Outputs ---
output "role_name" {
  value = aws_iam_role.lambda_exec.name
}

output "role_arn" {
  value = aws_iam_role.lambda_exec.arn
}

output "policies" {
  value = [
    aws_iam_policy.s3_read.name,
    aws_iam_policy.dynamodb_crud.name,
  ]
}

output "verify_commands" {
  value = <<-EOT
    aws --endpoint-url=http://localhost:4566 iam list-roles
    aws --endpoint-url=http://localhost:4566 iam list-attached-role-policies --role-name lambda-execution-role
    aws --endpoint-url=http://localhost:4566 iam get-policy --policy-arn ${aws_iam_policy.s3_read.arn}
  EOT
}
