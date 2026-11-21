# Mimir Load Tests

Validate Mimir performance under **expected** traffic conditions.

## Goal
Verify system handles normal and peak loads with acceptable performance.

## Test Scenarios

### 1. Prometheus Remote Write
- Simulate Prometheus scraping and remote write
- Target: 100K-1M active series
- Rate: 1K-10K samples/sec

### 2. Grafana Alloy
- Multi-tenant metric ingestion (replaces Grafana Agent)
- Target: Multiple tenants with varying loads
- Rate: Sustained write throughput

### 3. K6 Scripts
- HTTP API load testing
- Query performance validation
- Mixed read/write workloads

### 4. Avalanche
- High-volume metric generator
- Configurable series count and churn
- Realistic label cardinality

## Tools

| Tool | Purpose | Use Case |
|------|---------|----------|
| **Prometheus Benchmark** | Remote write testing | Standard ingestion path |
| **Grafana Alloy** | Multi-tenant testing | Production-like scenarios |
| **k6** | API load testing | Query performance |
| **Avalanche** | Metric generation | High-volume ingestion |

## Success Criteria

- ✅ Write latency < 1s (p99)
- ✅ Query latency < 5s (p99)
- ✅ Error rate < 0.1%
- ✅ No pod restarts
- ✅ Resource usage within limits

## Quick Start

```bash
# Run basic load test with Prometheus Benchmark
cd prometheus-remote-write/prometheus-benchmark
helm install prom-bench vm/prometheus-benchmark -n mimir-test -f configs/mimir-basic.yaml

# Run Avalanche metric generator
cd avalanche
kubectl apply -f kubernetes/avalanche-deployment.yaml -n mimir-test

# Run Grafana Alloy
cd grafana-alloy
helm install alloy grafana/alloy -n mimir-test -f configs/alloy-mimir.yaml

# Monitor metrics
kubectl port-forward -n mimir-test svc/mimir-gateway 8080:80
```
