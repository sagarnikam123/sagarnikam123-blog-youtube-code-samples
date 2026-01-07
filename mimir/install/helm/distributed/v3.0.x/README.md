# Mimir Distributed Installation Guide

## Prerequisites

- Kubernetes cluster (Minikube with 3 nodes recommended)
- Helm 3.x installed
- kubectl configured

## Installation Steps

### 1. Add Grafana Helm Repository

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### 2. Create Namespace

```bash
kubectl create namespace mimir-test
```

### 3. Pre-provision PVCs (Optional but Recommended)

For production-like deployments with persistent storage, pre-provision PVCs before Helm installation:

```bash
# Apply pre-provisioned PVCs
kubectl apply -f pre-provision-pvcs.yaml

# Verify PVCs are created
kubectl get pvc -n mimir-test
```

The `pre-provision-pvcs.yaml` creates the following PVCs:
- **Kafka**: 5Gi (kafka-data-mimir-kafka-0)
- **Alertmanager**: 1Gi (storage-mimir-alertmanager-0)
- **Compactor**: 2Gi (storage-mimir-compactor-0)
- **Ingester Zone-A/B/C**: 2Gi each (storage-mimir-ingester-zone-{a,b,c}-0)
- **Store-Gateway Zone-A/B/C**: 2Gi each (storage-mimir-store-gateway-zone-{a,b,c}-0)

**Total**: 9 PVCs, 17Gi storage

#### Why PVCs for Some Components and Not Others?

**Components that NEED persistent storage (StatefulSets with data):**
- **Kafka**: Stores ingestion queue data - data loss would cause metric loss
- **Ingester**: Buffers recent metrics before flushing to object storage - needs persistence to survive restarts
- **Store-Gateway**: Caches block metadata and indexes - persistence improves query performance
- **Compactor**: Stores compaction state and temporary data - persistence prevents re-work
- **Alertmanager**: Stores alert state and silences - persistence maintains alert history

**Components that DON'T need persistent storage (Stateless or use object storage):**
- **Distributor**: Stateless proxy, no data stored
- **Querier**: Stateless, queries data from Store-Gateway and Ingester
- **Query Frontend**: Stateless, splits and caches queries in memory
- **Query Scheduler**: Stateless, manages query queue in memory
- **Ruler**: Stores rules in object storage (MinIO), not locally
- **Gateway**: Stateless nginx reverse proxy
- **MinIO**: Uses emptyDir in dev (use PVC in production for actual object storage)

### 4. Configuration Files

The mimir-distributed Helm chart includes the following example values files:

| File | Description |
|------|-------------|
| `values.yaml` | Contains default values for testing GEM in non-production environments using a test MinIO deployment for object storage |
| `values-dev.yaml` | Development config with no persistence, minimal resources, MinIO storage |
| `small.yaml` | Contains values for a higher scale than defaults, for ingestion up to approximately one million series. Not suitable for high-availability production use, due to single replicas of key components |
| `large.yaml` | Contains values for production use for ingestion up to approximately ten million series |
| `mimir-default-values.yaml` | Complete Helm chart defaults (reference only) |

### 5. Install Mimir with Custom Values

```bash
# Standard installation (custom configuration)
helm install mimir grafana/mimir-distributed -n mimir-test -f values.yaml

# Development installation (no persistence, minimal resources)
helm install mimir grafana/mimir-distributed -n mimir-test -f values-dev.yaml

# Small-scale production
helm install mimir grafana/mimir-distributed -n mimir-test -f small.yaml

# Large-scale production
helm install mimir grafana/mimir-distributed -n mimir-test -f large.yaml
```

### 6. Verify Installation

```bash
# Check pod status
kubectl get pods -n mimir-test

# Check services
kubectl get svc -n mimir-test

# Port forward to access gateway
kubectl port-forward svc/mimir-gateway 8080:80 -n mimir-test
```

### 7. Test API Endpoints

```bash
# Health check
curl http://localhost:8080/

# Build info
curl http://localhost:8080/api/v1/status/buildinfo

# Query metrics (with tenant header)
curl "http://localhost:8080/prometheus/api/v1/query?query=up" -H "X-Scope-OrgID: demo"
```

### 8. Test Write and Read Paths

```bash
# Test write path (push metrics)
cat <<EOF | curl -X POST -H "Content-Type: application/json" -H "X-Scope-OrgID: demo" --data-binary @- http://localhost:8080/api/v1/push
{
  "series": [
    {
      "labels": [
        {"name": "__name__", "value": "test_metric"},
        {"name": "job", "value": "test"}
      ],
      "samples": [
        {"value": 42, "timestamp": $(date +%s)000}
      ]
    }
  ]
}
EOF

# Test read path (query metrics)
curl "http://localhost:8080/prometheus/api/v1/query?query=test_metric" -H "X-Scope-OrgID: demo"
```

## Key Features

### Development Configuration (values-dev.yaml)
- **Hybrid Persistence**: PVCs for stateful components (Kafka, Ingester, Store-Gateway, Compactor, Alertmanager), emptyDir for MinIO
- **Minimal Resources**: Single replica for most components
- **MinIO Storage**: S3-compatible object storage backend (emptyDir in dev, use PVC in production)
- **Kafka Enabled**: Ingest-storage architecture with Kafka (5Gi persistent storage)
- **All Components Enabled**: Alertmanager, Ruler, and all core components
- **Zone-Aware Replication**: Enabled for Ingester (3 replicas across 3 zones) and Store Gateway (3 zones)

### Production Configuration (default)
- **Zone-Aware Replication**: 3 zones (a, b, c)
- **Kafka Integration**: Ingest storage architecture
- **High Availability**: Multiple replicas with proper distribution
- **Persistent Storage**: PVCs for all stateful components
- **Full Feature Set**: All components enabled

## Resource Allocation (Development)

| Component | Replicas | Memory | CPU | Persistence (with pre-provision-pvcs.yaml) |
|-----------|----------|--------|-----|--------------------------------------------|
| Ingester (3 zones) | 3 | 512Mi | 100m | 3x 2Gi PVCs (zone-a/b/c) |
| Store Gateway (3 zones) | 1 | 512Mi | 100m | 3x 2Gi PVCs (zone-a/b/c) |
| Compactor | 1 | 512Mi | 100m | 1x 2Gi PVC |
| Distributor | 1 | 512Mi | 100m | - |
| Querier | 2 | 128Mi | 100m | - |
| Query Frontend | 1 | 128Mi | 100m | - |
| Query Scheduler | 2 | 128Mi | 100m | - |
| Alertmanager | 1 | 32Mi | 10m | 1x 1Gi PVC |
| Ruler | 1 | 128Mi | 100m | - |
| Gateway | 1 | - | - | - |
| MinIO | 1 | 128Mi | 100m | emptyDir |
| Kafka | 1 | 1Gi | 1000m | 1x 5Gi PVC |
| **Total** | **15** | **~4GB** | **~2.5 CPU** | **9 PVCs (17Gi total)** |

## Troubleshooting

### Common Issues

| Issue | Quick Fix |
|-------|-----------|
| Pods not starting | Check logs: `kubectl logs -n mimir-test <pod-name>` |
| Ring not forming | Verify memberlist: `kubectl exec -n mimir-test <pod> -- wget -q -O- http://localhost:8080/memberlist` |
| Write failures | Check distributor logs: `kubectl logs -n mimir-test -l app.kubernetes.io/component=distributor` |
| Query failures | Check querier logs: `kubectl logs -n mimir-test -l app.kubernetes.io/component=querier` |
| MinIO connection issues | Ensure MinIO pod is running: `kubectl get pods -n mimir-test -l app=minio` |
| Resource constraints | Check cluster resources: `kubectl top nodes` |

### Useful Commands

```bash
# Check logs for specific component
kubectl logs -n mimir-test -l app.kubernetes.io/component=ingester --tail=50

# Describe pod for events
kubectl describe pod -n mimir-test <pod-name>

# Check all services
kubectl get svc -n mimir-test

# Get gateway service details
kubectl get svc -n mimir-test mimir-gateway

# Check MinIO storage
kubectl exec -n mimir-test <mimir-minio-pod> -- ls -lh /data

# Check resource usage (requires metrics-server)
kubectl top pods -n mimir-test
kubectl top nodes
```

### Ring Status Commands

```bash
# Ingester ring
kubectl exec -n mimir-test -l app.kubernetes.io/component=ingester -- wget -q -O- http://localhost:8080/ingester/ring

# Distributor ring
kubectl exec -n mimir-test -l app.kubernetes.io/component=distributor -- wget -q -O- http://localhost:8080/distributor/ring

# Store Gateway ring
kubectl exec -n mimir-test -l app.kubernetes.io/component=store-gateway -- wget -q -O- http://localhost:8080/store-gateway/ring

# Compactor ring
kubectl exec -n mimir-test -l app.kubernetes.io/component=compactor -- wget -q -O- http://localhost:8080/compactor/ring

# Memberlist cluster
kubectl exec -n mimir-test -l app.kubernetes.io/component=ingester -- wget -q -O- http://localhost:8080/memberlist
```

### Force Delete Pods

When pods are stuck or unresponsive:

```bash
# Force delete single pod
kubectl delete pod <pod-name> --force --grace-period=0 -n mimir-test

# Force delete all Mimir pods
kubectl delete pods -l app.kubernetes.io/name=mimir --force --grace-period=0 -n mimir-test

# Force delete specific component pods
kubectl delete pods -l app.kubernetes.io/component=ingester --force --grace-period=0 -n mimir-test

# For stuck/terminating pods - remove finalizers first
kubectl patch pod <pod-name> -p '{"metadata":{"finalizers":null}}' -n mimir-test
kubectl delete pod <pod-name> --force --grace-period=0 -n mimir-test
```

**Warning**: Force deletion bypasses graceful shutdown and may cause data loss. Use only when pods are unresponsive.

## Cleanup Commands

### Remove All PVCs and PVs

When you need to completely clean up persistent storage:

```bash
# 1. List all PVCs in mimir-test namespace
kubectl get pvc -n mimir-test

# 2. Delete all PVCs in mimir-test namespace
kubectl delete pvc --all -n mimir-test

# 3. List PVs that might be related to mimir (check CLAIM column)
kubectl get pv

# 4. Delete all PV in mimir-test namespace
kubectl delete pv --all -n mimir-test

# 5. Delete specific mimir-related PVs (replace with actual PV names)
kubectl delete pv <pv-name-1> <pv-name-2>

# 6. Force delete stuck PVCs (if needed)
kubectl patch pvc <pvc-name> -p '{"metadata":{"finalizers":null}}' -n mimir-test
kubectl delete pvc <pvc-name> --force --grace-period=0 -n mimir-test

# 7. Alternative: Delete all PVCs with specific labels
kubectl delete pvc -l app.kubernetes.io/name=mimir -n mimir-test
```

### Complete Cleanup Script

```bash
#!/bin/bash
# Complete Mimir cleanup script

echo "Uninstalling Mimir Helm release..."
helm uninstall mimir -n mimir-test

echo "Waiting for pods to terminate..."
sleep 10

echo "Deleting all PVCs in mimir-test namespace..."
kubectl delete pvc --all -n mimir-test --timeout=60s

echo "Force deleting any stuck PVCs..."
for pvc in $(kubectl get pvc -n mimir-test -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
  echo "Force deleting PVC: $pvc"
  kubectl patch pvc $pvc -p '{"metadata":{"finalizers":null}}' -n mimir-test 2>/dev/null
  kubectl delete pvc $pvc --force --grace-period=0 -n mimir-test 2>/dev/null
done

echo "Checking for mimir-related PVs..."
kubectl get pv | grep mimir

echo "Deleting namespace..."
kubectl delete namespace mimir-test

echo "Cleanup completed!"
```

**Usage**: Save as `cleanup-mimir.sh`, make executable with `chmod +x cleanup-mimir.sh`, then run `./cleanup-mimir.sh`

### Selective Cleanup

```bash
# Delete only ingester PVCs (preserves other data)
kubectl delete pvc -l app.kubernetes.io/component=ingester -n mimir-test

# Delete only store-gateway PVCs
kubectl delete pvc -l app.kubernetes.io/component=store-gateway -n mimir-test

# Delete MinIO data (if using persistent storage)
kubectl delete pvc -l app=minio -n mimir-test
```

## Uninstall

```bash
# Standard uninstall (preserves PVCs if any)
helm uninstall mimir -n mimir-test
kubectl delete namespace mimir-test

# Complete uninstall (removes everything including persistent data)
helm uninstall mimir -n mimir-test
kubectl delete pvc --all -n mimir-test
kubectl delete namespace mimir-test
```

## Upgrade

```bash
# Upgrade with main values file
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f values.yaml

# Upgrade with development values
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f values-dev.yaml

# Upgrade to specific version
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f values.yaml --version 5.5.0
```

## Architecture

### Development Setup (values-dev.yaml)
```
┌─────────────────────────────────────────────────────────┐
│                    Mimir Gateway                        │
│                   (nginx reverse proxy)                 │
└────────────┬────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼─────┐
│Distrib │      │  Query   │
│ utor   │      │ Frontend │
└───┬────┘      └────┬─────┘
    │                │
┌───▼────┐      ┌────▼─────┐      ┌──────────┐
│Ingester│◄─────┤  Querier │◄─────┤  Store   │
│        │      │          │      │ Gateway  │
└───┬────┘      └──────────┘      └────┬─────┘
    │                                   │
    │           ┌──────────┐            │
    └──────────►│  MinIO   │◄───────────┘
                │ (S3 API) │
                └──────────┘
```

## References

- [Mimir Documentation](https://grafana.com/docs/mimir/latest/)
- [Mimir Helm Chart](https://github.com/grafana/mimir/tree/main/operations/helm/charts/mimir-distributed)
- [Mimir Architecture](https://grafana.com/docs/mimir/latest/references/architecture/)
