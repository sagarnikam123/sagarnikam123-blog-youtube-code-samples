# Mimir v2.17.x - Distributed Helm Chart

## Documentation
- https://grafana.com/docs/mimir/v2.17.x/set-up/helm-chart/

## Prerequisites

- Kubernetes cluster
- Helm 3.x installed
- kubectl configured

## Example Values Files

| File name | Description |
|-----------|-------------|
| `values.yaml` | Contains default values for testing Mimir in non-production environments using a test MinIO deployment for object storage. |
| `small.yaml` | Contains values for a higher scale than defaults, for ingestion up to approximately one million series. Not suitable for high-availability production use, due to single replicas of key components. |
| `small-dev-s3.yaml` | Contains values for small-scale development with S3 backend (~1M series). Requires AWS S3 bucket and credentials. ~28 CPU, ~51 GB. |
| `small-dev-minio.yaml` | Contains values for small-scale development with MinIO backend (~1M series). Reduced resources for local testing. ~1.5 CPU, ~8 GB. |
| `small/small-dev-s3-half.yaml` | Half-resource S3 configuration maintaining HA with same replica counts and anti-affinity. ~14 CPU, ~25.5 GB. |
| `small/small-dev-minio-half.yaml` | Half-resource MinIO configuration for minimal testing. Single replicas, no anti-affinity. ~0.5 CPU, ~3 GB. |
| `large.yaml` | Contains values for production use for ingestion up to approximately ten million series. |

## Installation Steps

### 1. Add Grafana Helm Repository

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# List all available chart versions
helm search repo grafana/mimir-distributed --versions

# Show chart info including app version (Mimir version)
helm show chart grafana/mimir-distributed --version 5.8.0
```

### 2. Create Namespace

```bash
# Create namespace (if not exists)
kubectl create namespace mimir-test

# Or check if namespace exists
kubectl get namespace mimir-test
```

### 3. Install Mimir with Custom Values

```bash
# Default installation (testing/development)
helm install mimir grafana/mimir-distributed -n mimir-test -f values/values.yaml

# Small-scale production (~1M series)
helm install mimir grafana/mimir-distributed -n mimir-test -f small/small.yaml

# Small-scale development with S3 (~1M series, ~28 CPU, ~51 GB)
helm install mimir grafana/mimir-distributed -n mimir-test -f small/small-dev-s3.yaml --version 5.8.0 --timeout=10m

# Small-scale development with MinIO (~1M series, ~1.5 CPU, ~8 GB)
helm install mimir grafana/mimir-distributed -n mimir-test -f small/small-dev-minio.yaml --version 5.8.0 --timeout=10m

# Half-resource S3 with HA (~14 CPU, ~25.5 GB)
helm install mimir grafana/mimir-distributed -n mimir-test -f small/small-dev-s3-half.yaml --version 5.8.0 --timeout=10m

# Half-resource MinIO for minimal testing (~0.5 CPU, ~3 GB)
helm install mimir grafana/mimir-distributed -n mimir-test -f small/small-dev-minio-half.yaml --version 5.8.0 --timeout=10m

# Large-scale production (~10M series)
helm install mimir grafana/mimir-distributed -n mimir-test -f large/large.yaml
```

### 4. Verify Installation

```bash
# Check pod status
kubectl get pods -n mimir-test

# Check services
kubectl get svc -n mimir-test

# Port forward to access gateway
kubectl port-forward svc/mimir-gateway 8080:80 -n mimir-test
```

### 5. Test API Endpoints

```bash
# Health check
curl http://localhost:8080/

# Build info
curl http://localhost:8080/api/v1/status/buildinfo

# Query metrics (with tenant header)
curl "http://localhost:8080/prometheus/api/v1/query?query=up" -H "X-Scope-OrgID: demo"
```

### 6. Test Write and Read Paths

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

### Standard Uninstall

```bash
# Uninstall Helm release (preserves PVCs)
helm uninstall mimir -n mimir-test

# Delete namespace (removes all resources)
kubectl delete namespace mimir-test
```

### Complete Uninstall (with data cleanup)

```bash
# Delete persistent data first
kubectl delete pvc --all -n mimir-test

# Uninstall Helm release
helm uninstall mimir -n mimir-test

# Delete namespace
kubectl delete namespace mimir-test
```

### Faster Cleanup Options

When `helm uninstall` takes too long:

```bash
# Option 1: Force delete namespace (fastest - immediate cleanup)
kubectl delete namespace mimir-test --grace-period=0 --force

# Option 2: Non-blocking helm uninstall
helm uninstall mimir -n mimir-test --wait=false

# Option 3: Background helm uninstall
helm uninstall mimir -n mimir-test --wait=false &

# Option 4: Complete force cleanup (nuclear option)
kubectl delete pvc --all -n mimir-test --grace-period=0 --force
kubectl delete namespace mimir-test --grace-period=0 --force
```

**Warning**: Force deletion bypasses graceful shutdown. Resources may continue running briefly. Use when standard uninstall hangs or takes excessive time.

## Upgrade

```bash
# Upgrade with default values
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f values.yaml

# Upgrade with small-dev-s3 configuration
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f small/small-dev-s3.yaml --version 5.8.0 --timeout=10m

# Upgrade with small-dev-minio configuration
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f small/small-dev-minio.yaml --version 5.8.0 --timeout=10m

# Upgrade with half-resource S3 configuration
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f small/small-dev-s3-half.yaml --version 5.8.0 --timeout=10m

# Upgrade with half-resource MinIO configuration
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f small/small-dev-minio-half.yaml --version 5.8.0 --timeout=10m

# Upgrade with small configuration
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f small.yaml

# Upgrade with large configuration
helm upgrade mimir grafana/mimir-distributed -n mimir-test -f large.yaml


```

## S3 Bucket Operations

### Verify S3 Bucket Access

```bash
# List S3 bucket contents
aws s3 ls s3://scnx-global-dev-aps1-metrics/ --profile 073885930324_eks_devenv_devops

# List with details
aws s3 ls s3://scnx-global-dev-aps1-metrics/ --recursive --human-readable --summarize --profile 073885930324_eks_devenv_devops

# Check bucket exists and is accessible
aws s3 ls s3://scnx-global-dev-aps1-metrics/ --region ap-south-1 --profile 073885930324_eks_devenv_devops

# List specific tenant data
aws s3 ls s3://scnx-global-dev-aps1-metrics/<tenant-id>/ --profile 073885930324_eks_devenv_devops
```

### Delete S3 Bucket Data

```bash
# Delete specific tenant data
aws s3 rm s3://scnx-global-dev-aps1-metrics/<tenant-id>/ --recursive --profile 073885930324_eks_devenv_devops

# Delete specific folder
aws s3 rm s3://scnx-global-dev-aps1-metrics/<folder-name>/ --recursive --profile 073885930324_eks_devenv_devops

# Delete specific file
aws s3 rm s3://scnx-global-dev-aps1-metrics/<path-to-file> --profile 073885930324_eks_devenv_devops

# Delete all contents (keep bucket)
aws s3 rm s3://scnx-global-dev-aps1-metrics/ --recursive --profile 073885930324_eks_devenv_devops

# Delete bucket and all contents (complete cleanup)
aws s3 rb s3://scnx-global-dev-aps1-metrics/ --force --profile 073885930324_eks_devenv_devops

# Dry-run deletion (preview what would be deleted)
aws s3 rm s3://scnx-global-dev-aps1-metrics/<tenant-id>/ --recursive --dryrun --profile 073885930324_eks_devenv_devops
```

**Warning**: S3 deletions are permanent and cannot be undone. Always verify the path before deletion. Use `--dryrun` to preview deletions.

## References

- [Mimir v2.17.x Documentation](https://grafana.com/docs/mimir/v2.17.x/)
- [Mimir Helm Chart](https://github.com/grafana/mimir/tree/main/operations/helm/charts/mimir-distributed)
- [Mimir Architecture](https://grafana.com/docs/mimir/latest/references/architecture/)
