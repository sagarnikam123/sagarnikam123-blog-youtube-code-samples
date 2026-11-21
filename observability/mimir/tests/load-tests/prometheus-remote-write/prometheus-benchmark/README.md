# Prometheus Benchmark for Mimir

Uses [VictoriaMetrics/prometheus-benchmark](https://github.com/VictoriaMetrics/prometheus-benchmark) to test Mimir remote write performance.

## What is prometheus-benchmark?

A Helm chart that deploys Prometheus instances configured to scrape metrics and remote write to your TSDB (Mimir).

**Key Features:**
- Configurable number of Prometheus instances
- Adjustable scrape targets and intervals
- Built-in metric generators (node-exporter, cadvisor)
- Measures write throughput and latency
- Tests multi-tenant scenarios

## Quick Start

### 1. Add Helm Repo

```bash
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update
```

### 2. Install for Mimir

```bash
# Basic test (single tenant)
helm install prom-bench vm/prometheus-benchmark \
  -n mimir-test \
  -f configs/mimir-basic.yaml

# Multi-tenant test
helm install prom-bench vm/prometheus-benchmark \
  -n mimir-test \
  -f configs/mimir-multi-tenant.yaml
```

### 3. Monitor Results

```bash
# Check Prometheus pods
kubectl get pods -n mimir-test -l app=prometheus

# View Prometheus metrics
kubectl port-forward -n mimir-test svc/prom-bench-prometheus-0 9090:9090

# Check Mimir ingestion
kubectl logs -n mimir-test -l app.kubernetes.io/component=distributor --tail=100
```

## Configuration Files

| File | Description | Use Case |
|------|-------------|----------|
| `mimir-basic.yaml` | Single tenant, 1 Prometheus, 10 targets | Basic load test |
| `mimir-multi-tenant.yaml` | 3 tenants, 3 Prometheus, 30 targets | Multi-tenancy test |
| `mimir-high-load.yaml` | 5 Prometheus, 100 targets, 15s scrape | High throughput test |

## Key Parameters

```yaml
# Number of Prometheus instances
prometheus:
  replicaCount: 3

# Scrape configuration
scrapeInterval: 30s
scrapeTargets: 10

# Remote write to Mimir
remoteWrite:
  url: http://mimir-gateway.mimir-test.svc.cluster.local/api/v1/push
  headers:
    X-Scope-OrgID: tenant-1
```

## Metrics to Monitor

- **prometheus_remote_storage_samples_total** - Total samples sent
- **prometheus_remote_storage_samples_failed_total** - Failed samples
- **prometheus_remote_storage_sent_batch_duration_seconds** - Write latency
- **prometheus_remote_storage_queue_length** - Queue backlog

## Cleanup

```bash
helm uninstall prom-bench -n mimir-test
```
