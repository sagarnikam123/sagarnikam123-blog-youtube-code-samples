# Mimir Distributed Kubernetes Manifests (v2.17.x)

Exported Kubernetes manifests from Helm deployment for microservice mode deployment.

## Directory Structure

```
.
├── deployments/          # Deployment manifests (9 components)
├── statefulsets/         # StatefulSet manifests (12 components)
├── services/             # Service manifests (26 services)
├── configmaps/           # ConfigMap manifests
├── serviceaccounts/      # ServiceAccount manifests
├── roles/                # Role manifests
├── rolebindings/         # RoleBinding manifests
├── pvcs/                 # PersistentVolumeClaim manifests (9 PVCs)
├── pdb/                  # PodDisruptionBudget manifests
└── hpa/                  # HorizontalPodAutoscaler manifests
```

## Components Exported

### Deployments (9)
- mimir-continuous-test
- mimir-distributor
- mimir-nginx
- mimir-overrides-exporter
- mimir-querier
- mimir-query-frontend
- mimir-query-scheduler
- mimir-rollout-operator
- mimir-ruler

### StatefulSets (12)
- mimir-alertmanager
- mimir-chunks-cache (3 replicas)
- mimir-compactor
- mimir-index-cache (3 replicas)
- mimir-ingester-zone-a/b/c (3 zones)
- mimir-metadata-cache (3 replicas)
- mimir-results-cache (3 replicas)
- mimir-store-gateway-zone-a/b/c (3 zones)

### Services (26)
- Component services
- Headless services for StatefulSets
- Gossip ring service
- Cache services

## Usage

### Apply All Components

```bash
# Create namespace
kubectl create namespace mimir-test

# Apply in order
kubectl apply -f serviceaccounts/
kubectl apply -f roles/
kubectl apply -f rolebindings/
kubectl apply -f configmaps/
kubectl apply -f services/
kubectl apply -f pvcs/
kubectl apply -f statefulsets/
kubectl apply -f deployments/
kubectl apply -f pdb/
kubectl apply -f hpa/
```

### Apply Individual Components

```bash
# Example: Deploy only distributor
kubectl apply -f deployments/mimir-distributor.yaml
kubectl apply -f services/mimir-distributor.yaml

# Example: Deploy ingesters
kubectl apply -f statefulsets/mimir-ingester-zone-a.yaml
kubectl apply -f statefulsets/mimir-ingester-zone-b.yaml
kubectl apply -f statefulsets/mimir-ingester-zone-c.yaml
kubectl apply -f services/mimir-ingester-zone-a.yaml
kubectl apply -f services/mimir-ingester-zone-b.yaml
kubectl apply -f services/mimir-ingester-zone-c.yaml
```

### Delete All Components

```bash
kubectl delete -f deployments/
kubectl delete -f statefulsets/
kubectl delete -f services/
kubectl delete -f pvcs/
kubectl delete -f configmaps/
kubectl delete -f rolebindings/
kubectl delete -f roles/
kubectl delete -f serviceaccounts/
```

## Important Notes

1. **Namespace**: All manifests are exported with `namespace: mimir-test`
2. **Storage**: PVCs use `efs-sc` storage class
3. **Configuration**: Mimir configuration is embedded in StatefulSet/Deployment specs
4. **Secrets**: No secrets were exported (AWS credentials need to be configured separately)
5. **Clean Manifests**: You may need to remove Helm-specific annotations and labels before applying

## Editing Manifests

Before applying, you may want to:

1. Remove Helm annotations:
   - `meta.helm.sh/release-name`
   - `meta.helm.sh/release-namespace`

2. Remove managed fields:
   - `metadata.managedFields`

3. Update resource limits/requests as needed

4. Configure AWS credentials for S3 access

## Source

Exported from Helm deployment:
- **Chart**: grafana/mimir-distributed v5.8.0
- **Mimir Version**: 2.17.0
- **Values File**: small/small-dev-s3-half.yaml
- **Export Date**: 2025-12-02
- **Cluster**: scnx-global-dev-aps1-eks
