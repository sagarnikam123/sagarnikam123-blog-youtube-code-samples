# Loki Operator Installation

Deploy Loki using the Loki Operator with `LokiStack` CRD.

## Overview

The Loki Operator manages Loki deployments using Kubernetes-native Custom Resource Definitions (CRDs). It automates deployment, scaling, and lifecycle management of Loki clusters.

## When to Use

| ✅ Good For | ❌ Not For |
|-------------|-----------|
| OpenShift environments | Quick local testing |
| GitOps workflows | Simple single-node setups |
| Automated lifecycle management | Learning Loki basics |
| Production with operator patterns | Minikube/Docker Desktop |

## Prerequisites

- Kubernetes 1.21+ or OpenShift 4.10+
- cert-manager (for webhook certificates)
- Object storage (S3, GCS, Azure Blob, or MinIO)

## Installation Methods

### 1. OpenShift (OperatorHub)

```bash
# Install via OperatorHub UI or CLI
oc apply -f openshift/subscription.yaml
```

### 2. Kubernetes (OLM)

```bash
# Install OLM first
curl -sL https://github.com/operator-framework/operator-lifecycle-manager/releases/download/v0.28.0/install.sh | bash -s v0.28.0

# Install Loki Operator
kubectl apply -f olm/catalog-source.yaml
kubectl apply -f olm/subscription.yaml
```

### 3. Kubernetes (Direct)

```bash
# Install CRDs and operator directly
kubectl apply -f https://raw.githubusercontent.com/grafana/loki/main/operator/bundle/manifests/loki-operator.clusterserviceversion.yaml
```

## Deploy LokiStack

### 1. Create Object Storage Secret

```bash
# For MinIO/S3
kubectl create secret generic lokistack-storage \
  -n loki \
  --from-literal=endpoint=http://minio:9000 \
  --from-literal=bucketnames=loki-chunks \
  --from-literal=access_key_id=loki \
  --from-literal=access_key_secret=supersecret
```

### 2. Apply LokiStack CR

```bash
# Choose a size: 1x.demo, 1x.extra-small, 1x.small, 1x.medium
kubectl apply -f lokistack/lokistack-demo.yaml
```

## Files

| File | Description |
|------|-------------|
| `lokistack/lokistack-demo.yaml` | Demo size (development) |
| `lokistack/lokistack-small.yaml` | Small production |
| `lokistack/storage-secret.yaml` | Object storage credentials |
| `openshift/subscription.yaml` | OpenShift OperatorHub |
| `olm/catalog-source.yaml` | OLM catalog source |
| `olm/subscription.yaml` | OLM subscription |

## LokiStack Sizes

| Size | Ingestion | Query | Use Case |
|------|-----------|-------|----------|
| `1x.demo` | ~20GB/day | Light | Development |
| `1x.extra-small` | ~100GB/day | Moderate | Small production |
| `1x.small` | ~500GB/day | Heavy | Medium production |
| `1x.medium` | ~2TB/day | Heavy | Large production |

## Verify

```bash
# Check operator
kubectl get pods -n loki-operator

# Check LokiStack
kubectl get lokistack -n loki
kubectl get pods -n loki

# Check status
kubectl describe lokistack lokistack-sample -n loki
```

## Uninstall

```bash
# Delete LokiStack
kubectl delete lokistack lokistack-sample -n loki

# Delete storage secret
kubectl delete secret lokistack-storage -n loki

# Delete operator (OLM)
kubectl delete subscription loki-operator -n loki-operator
kubectl delete csv -n loki-operator -l operators.coreos.com/loki-operator.loki-operator

# Delete namespace
kubectl delete namespace loki
```

## Helm vs Operator

| Aspect | Helm | Operator |
|--------|------|----------|
| Complexity | Lower | Higher |
| Automation | Manual upgrades | Automated lifecycle |
| Best for | Most K8s clusters | OpenShift, GitOps |
| Learning curve | Easier | Steeper |
| Flexibility | High | Opinionated |

## Resources

- [Loki Operator Docs](https://loki-operator.dev/)
- [LokiStack API Reference](https://loki-operator.dev/docs/api.md/)
- [GitHub Repository](https://github.com/grafana/loki/tree/main/operator)
