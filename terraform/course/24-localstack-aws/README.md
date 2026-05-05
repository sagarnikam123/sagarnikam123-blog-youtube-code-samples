# Module 24 — AWS Locally with LocalStack

## Overview

LocalStack emulates AWS services on your machine. You get to practice the `hashicorp/aws` provider — S3, DynamoDB, SQS, Lambda, IAM — without an AWS account or any billing.

This is the bridge between "I know Terraform" and "I can manage AWS infrastructure."

## Prerequisites

```bash
# Install LocalStack CLI
brew install localstack/tap/localstack-cli    # macOS
# or: pip install localstack

# Start LocalStack (uses Docker under the hood)
localstack start -d

# Verify
localstack status services

# Or run directly with Docker
docker run -d --name localstack \
  -p 4566:4566 \
  -e SERVICES=s3,dynamodb,sqs,lambda,iam \
  localstack/localstack:latest
```

## AWS Provider Configuration for LocalStack

```hcl
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3       = "http://localhost:4566"
    dynamodb = "http://localhost:4566"
    sqs      = "http://localhost:4566"
    lambda   = "http://localhost:4566"
    iam      = "http://localhost:4566"
  }
}
```

## Why LocalStack?

- **Free** — Community edition covers S3, DynamoDB, SQS, Lambda, IAM, and more
- **Fast** — No network latency, instant provisioning
- **Safe** — Can't accidentally create real resources or incur costs
- **Realistic** — Same AWS provider, same resource types, same HCL
- **Offline** — Works without internet after initial Docker pull

## Official Docs

- [LocalStack Documentation](https://docs.localstack.cloud/)
- [LocalStack Terraform Guide](https://docs.localstack.cloud/user-guide/integrations/terraform/)
- [AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [LocalStack Supported Services](https://docs.localstack.cloud/references/coverage/)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [S3 Buckets](./01-s3-buckets/) | Create buckets, upload objects, configure policies |
| 2 | [DynamoDB Tables](./02-dynamodb/) | Create tables, configure indexes, set capacity |
| 3 | [SQS Queues](./03-sqs-queues/) | Standard and FIFO queues, dead letter queues |
| 4 | [IAM Roles & Policies](./04-iam/) | Roles, policies, policy attachments |
