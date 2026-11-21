# Loki Simple Scalable Mode - v3.6.x

## Overview

Loki is deployed as 3 targets: read, write, and backend. Useful for medium installs easier to manage than distributed, up to about 1TB/day.

Components grouped into 3 services:
- **Read** - query-frontend, querier
- **Write** - distributor, ingester
- **Backend** - compactor, index-gateway, query-scheduler, ruler

## When to Use

| ✅ Good For | ❌ Not For |
|-------------|-----------|
| Medium workloads (100GB-1TB/day) | Small dev/test (<100GB/day) |
| Easier ops than distributed | Maximum scalability needs |
| Production with moderate scale | Very large deployments (>1TB/day) |

## Install

```bash
cd /path/to/loki/install/helm/v3.6.x/simple-scalable

helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values.yaml
```

## Upgrade

```bash
helm upgrade loki grafana/loki -n loki --version 6.49.0 -f values.yaml
```

## Verify

```bash
kubectl get pods -n loki
# Should see: loki-read-*, loki-write-*, loki-backend-*
```

## Scaling

```bash
# Scale read for query performance
kubectl scale statefulset loki-read -n loki --replicas=3

# Scale write for ingestion throughput
kubectl scale statefulset loki-write -n loki --replicas=3
```

## References

- [Simple Scalable Mode Docs](https://grafana.com/docs/loki/latest/get-started/deployment-modes/#simple-scalable)
