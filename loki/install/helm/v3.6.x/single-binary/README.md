# Loki Single Binary Mode - v3.6.x

## Overview

Loki is deployed as a single binary, useful for small installs typically without HA, up to a few tens of GB/day.

All Loki components run in one process - simplest deployment option.

## When to Use

| ✅ Good For | ❌ Not For |
|-------------|-----------|
| Development & testing | Production workloads |
| Small workloads (up to tens of GB/day) | High availability needs |
| Learning Loki | Large scale deployments |

## Files

| File | Description |
|------|-------------|
| `values-base.yaml` | Base configuration (required) |
| `values-minikube.yaml` | Minikube platform overrides |
| `values-eks.yaml` | AWS EKS platform overrides |
| `values-aks.yaml` | Azure AKS platform overrides |
| `values-minio.yaml` | MinIO S3-compatible storage |
| `values-aws-s3.yaml` | AWS S3 storage |
| `values-azure-blob.yaml` | Azure Blob storage |

## Install

```bash
cd /path/to/loki/install/helm/v3.6.x/single-binary
```

### Minikube

```bash
# Filesystem storage
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-minikube.yaml

# MinIO storage
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-minio.yaml -f values-minikube.yaml
```

### AWS EKS

```bash
# Filesystem storage (EBS)
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-eks.yaml

# MinIO storage
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-minio.yaml -f values-eks.yaml

# AWS S3 storage (recommended for production)
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-aws-s3.yaml -f values-eks.yaml
```

### Azure AKS

```bash
# Filesystem storage (Azure Disk)
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-aks.yaml

# MinIO storage
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-minio.yaml -f values-aks.yaml

# Azure Blob storage (recommended for production)
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-azure-blob.yaml -f values-aks.yaml
```

### MinIO Storage Notes

The `values-minio.yaml` uses Thanos object store client (`use_thanos_objstore: true`) which is the recommended approach for Loki 3.x. Features:

- Built-in MinIO deployment (can be disabled for external MinIO)
- S3-compatible storage with path-style access
- 7-day retention with compactor enabled
- Unified storage client across Grafana ecosystem

Default credentials (change in production):
- Access Key: `minioadmin`
- Secret Key: `minioadmin`
- Bucket: `loki-chunks`

## Upgrade

```bash
helm upgrade loki grafana/loki -n loki --version 6.49.0 \
  -f values-base.yaml -f values-<platform>.yaml
```

## Uninstall

```bash
helm uninstall loki -n loki
kubectl delete namespace loki  # Optional: remove namespace and PVCs
```

## Verify

```bash
kubectl get pods -n loki
# Should see: loki-0 (single pod)
```

## Access

```bash
kubectl port-forward svc/loki-gateway -n loki 3100:80
curl http://localhost:3100/ready
```

## Platform Differences

| Platform | Storage | Security | Service |
|----------|---------|----------|---------|
| Minikube | standard | root | ClusterIP |
| EKS | gp3 | non-root | NLB |
| AKS | managed-csi | non-root | Azure LB |

## Ring Membership

Loki uses hash rings for coordination. In single binary mode, not all components participate equally:

| Component | Uses Ring? | Purpose |
|-----------|------------|---------|
| Ingester | ✅ Yes | Data ownership, replication coordination |
| Compactor | ✅ Yes | Leader election (only one compacts at a time) |
| Index Gateway | ✅ Yes | Distributes index queries across instances |
| Ruler | ✅ Yes | Distributes rule evaluation |
| Distributor | ⚠️ Optional | Rate limiting coordination (only with `global` strategy) |
| Query Scheduler | ⚠️ Optional | Scheduler discovery (disabled in single binary) |

### Why Some Rings Appear Empty

- **Distributor ring**: Only used when `ingestion_rate_strategy: global`. With `local` strategy, ring is minimal.
- **Query Scheduler ring**: Disabled by default (`use_scheduler_ring: false`). Queriers connect directly to frontend.

### For Single-Node Deployments

Only these rings matter:
- **Ingester**: Required for data consistency
- **Compactor**: Required for leader election

Distributor and Scheduler rings are coordination-only and optional for single-node setups.
