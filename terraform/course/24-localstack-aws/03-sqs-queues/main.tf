# =============================================================================
# Module 24 — Exercise 3: SQS Queues with LocalStack
# =============================================================================
# Create standard and FIFO queues with dead letter queue configuration.
#
# After apply:
#   aws --endpoint-url=http://localhost:4566 sqs list-queues
#   aws --endpoint-url=http://localhost:4566 sqs send-message --queue-url <url> --message-body "hello"
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
    sqs = "http://localhost:4566"
  }
}

# --- Dead Letter Queue (receives failed messages) ---
resource "aws_sqs_queue" "dlq" {
  name                      = "orders-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Name      = "orders-dlq"
    ManagedBy = "terraform"
  }
}

# --- Standard Queue (with DLQ redrive policy) ---
resource "aws_sqs_queue" "orders" {
  name                       = "orders-queue"
  delay_seconds              = 0
  max_message_size           = 262144 # 256 KB
  message_retention_seconds  = 345600 # 4 days
  visibility_timeout_seconds = 30

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name      = "orders-queue"
    ManagedBy = "terraform"
  }
}

# --- FIFO Queue (guaranteed ordering) ---
resource "aws_sqs_queue" "notifications" {
  name                        = "notifications.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  deduplication_scope         = "messageGroup"
  fifo_throughput_limit       = "perMessageGroupId"

  tags = {
    Name      = "notifications-fifo"
    ManagedBy = "terraform"
  }
}

# --- Outputs ---
output "orders_queue_url" {
  value = aws_sqs_queue.orders.url
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.url
}

output "fifo_queue_url" {
  value = aws_sqs_queue.notifications.url
}

output "verify_commands" {
  value = <<-EOT
    aws --endpoint-url=http://localhost:4566 sqs list-queues
    aws --endpoint-url=http://localhost:4566 sqs send-message --queue-url ${aws_sqs_queue.orders.url} --message-body '{"order_id":"123"}'
    aws --endpoint-url=http://localhost:4566 sqs receive-message --queue-url ${aws_sqs_queue.orders.url}
  EOT
}
