# Avalanche - Prometheus Metric Load Generator

Uses [prometheus-community/avalanche](https://github.com/prometheus-community/avalanche) to generate high-volume metrics for Mimir testing.

## What is Avalanche?

A Prometheus metric load generator that creates realistic time series data with configurable:
- Series count and cardinality
- Label combinations
- Metric churn rate
- Value patterns

**Perfect for:**
- High-volume ingestion testing
- Cardinality stress testing
- Series churn simulation
- Remote write performance validation

## Quick Start

### 1. Deploy via Kubernetes

```bash
kubectl apply -f kubernetes/avalanche-deployment.yaml -n mimir-test
```

### 2. Deploy via Docker

```bash
docker run -d --name avalanche \
  -p 9001:9001 \
  quay.io/prometheuscommunity/avalanche:latest \
  --metric-count=100 \
  --series-count=1000 \
  --remote-url=http://mimir-gateway.mimir-test.svc.cluster.local/api/v1/push \
  --remote-tenant-header=X-Scope-OrgID \
  --remote-tenant=demo
```

### 3. Configure Prometheus to Scrape

```yaml
scrape_configs:
  - job_name: 'avalanche'
    static_configs:
      - targets: ['avalanche:9001']
```

## Configuration Examples

### Basic Load (1K series)
```bash
avalanche \
  --metric-count=10 \
  --series-count=100 \
  --value-interval=30 \
  --series-interval=3600
```

### High Cardinality (100K series)
```bash
avalanche \
  --metric-count=100 \
  --series-count=1000 \
  --label-count=10 \
  --series-interval=300 \
  --metric-interval=0
```

### Series Churn Test
```bash
avalanche \
  --metric-count=50 \
  --series-count=500 \
  --series-interval=60 \
  --series-change-rate=0.5
```

### Direct Remote Write
```bash
avalanche \
  --metric-count=100 \
  --series-count=1000 \
  --remote-url=http://localhost:8080/api/v1/push \
  --remote-tenant-header=X-Scope-OrgID \
  --remote-tenant=demo \
  --remote-write-interval=30s
```

## Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--metric-count` | Number of unique metrics | 500 |
| `--series-count` | Series per metric | 10 |
| `--label-count` | Labels per series | 10 |
| `--series-interval` | Series change interval (seconds) | 60 |
| `--metric-interval` | Metric change interval (seconds) | 0 |
| `--value-interval` | Value update interval (seconds) | 30 |
| `--series-change-rate` | Percentage of series to change | 0.0 |
| `--remote-url` | Remote write endpoint | - |
| `--remote-tenant` | Tenant ID for multi-tenancy | - |

## Test Scenarios

### 1. Steady State Load
```bash
# 10K series, no churn
avalanche --metric-count=100 --series-count=100 --series-interval=0
```

### 2. High Churn
```bash
# 50% series change every minute
avalanche --metric-count=50 --series-count=200 --series-interval=60 --series-change-rate=0.5
```

### 3. Cardinality Explosion
```bash
# 1M series with high label count
avalanche --metric-count=1000 --series-count=1000 --label-count=20
```

## Monitoring Avalanche

```bash
# Check metrics endpoint
curl http://localhost:9001/metrics

# Key metrics to watch:
# - avalanche_metric_total_count
# - avalanche_series_total_count
# - avalanche_remote_write_requests_total
```

## Cleanup

```bash
# Kubernetes
kubectl delete -f kubernetes/avalanche-deployment.yaml -n mimir-test

# Docker
docker stop avalanche && docker rm avalanche
```
