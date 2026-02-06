# AWS Monitoring for SkyWalking

This directory contains configurations for monitoring AWS managed services in SkyWalking.

## Supported AWS Services

| Service | Method | SkyWalking Menu | Status |
|---------|--------|-----------------|--------|
| **API Gateway** | CloudWatch via YACE | Gateway → AWS API Gateway | ✅ Ready |
| **DynamoDB** | CloudWatch via YACE | Database → DynamoDB | ✅ Ready |

## Prerequisites

1. **EKS Cluster** with IRSA (IAM Roles for Service Accounts) enabled
2. **IAM Role** with CloudWatch read permissions
3. **YACE** (Yet Another CloudWatch Exporter) deployed

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                │
│  ┌─────────────────┐           ┌─────────────────┐              │
│  │   API Gateway   │           │    DynamoDB     │              │
│  └────────┬────────┘           └────────┬────────┘              │
│           │                             │                        │
│           └──────────┬──────────────────┘                        │
│                      ▼                                           │
│           ┌─────────────────────┐                                │
│           │     CloudWatch      │                                │
│           │      Metrics        │                                │
│           └──────────┬──────────┘                                │
└──────────────────────┼──────────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────────┐
│                      ▼                    EKS Cluster            │
│           ┌─────────────────────┐                                │
│           │   YACE Exporter     │                                │
│           │  (CloudWatch → Prom)│                                │
│           └──────────┬──────────┘                                │
│                      │ :5000                                     │
│                      ▼                                           │
│           ┌─────────────────────┐                                │
│           │   OTel Collector    │                                │
│           └──────────┬──────────┘                                │
│                      │ OTLP                                      │
│                      ▼                                           │
│           ┌─────────────────────┐                                │
│           │   SkyWalking OAP    │                                │
│           └─────────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Create IAM Role for YACE

```bash
# Create IAM policy
cat > yace-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "tag:GetResources",
        "apigateway:GET",
        "dynamodb:ListTables",
        "dynamodb:DescribeTable"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name YACECloudWatchPolicy \
  --policy-document file://yace-policy.json

# Create IAM role with IRSA trust
eksctl create iamserviceaccount \
  --name yace-cloudwatch-exporter \
  --namespace skywalking \
  --cluster <your-cluster> \
  --attach-policy-arn arn:aws:iam::<account-id>:policy/YACECloudWatchPolicy \
  --approve
```

### 2. Deploy YACE

```bash
kubectl apply -f yace-exporter.yaml -n skywalking
```

### 3. Update OTel Collector

Add YACE scrape config to your OTel Collector.

### 4. Enable OAP Rules

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "...,aws-gateway,aws-dynamodb"
```

## Files

| File | Description |
|------|-------------|
| `yace-exporter.yaml` | YACE deployment with API Gateway + DynamoDB config |
| `iam-policy.json` | IAM policy for CloudWatch access |
| `otel-collector-aws.yaml` | OTel Collector scrape config for YACE |

## References

- [YACE - Yet Another CloudWatch Exporter](https://github.com/nerdswords/yet-another-cloudwatch-exporter)
- [SkyWalking AWS API Gateway Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-aws-api-gateway-monitoring/)
- [SkyWalking DynamoDB Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-aws-dynamodb-monitoring/)
- [EKS IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
