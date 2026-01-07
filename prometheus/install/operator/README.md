# Prometheus Operator Installation

Deploy Prometheus using the Prometheus Operator with `Prometheus` CRD.

## Overview

The Prometheus Operator manages Prometheus deployments using Kubernetes-native Custom Resource Definitions (CRDs). It automates deployment, scaling, and lifecycle management of Prometheus clusters, along with related components like Alertmanager and ServiceMonitors.

## When to Use

| ✅ Good For | ❌ Not For |
|-------------|-----------|
| OpenShift environments | Quick local testing |
| GitOps workflows | Simple single-node setups |
| Automated lifecycle management | Learning Prometheus basics |
| Production with operator patterns | Minikube/Docker Desktop |

## Prerequisites

- Kubernetes 1.21+ or OpenShift 4.10+
- Sufficient cluster resources for Prometheus workloads
- Persistent storage (recommended for production)

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

# Install Prometheus Operator
kubectl apply -f olm/catalog-source.yaml
kubectl apply -f olm/subscription.yaml
```

### 3. Kubernetes (Direct)

```bash
# Install CRDs and operator directly
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml
```

## Deploy Prometheus

### 1. Create RBAC Resources

```bash
# Create namespace and RBAC
kubectl create namespace monitoring
kubectl apply -f prometheus/rbac.yaml
```

### 2. Apply Prometheus CR

```bash
# Choose a size: demo, small
kubectl apply -f prometheus/prometheus-demo.yaml
```

## Files

| File | Description |
|------|-------------|
| `prometheus/prometheus-demo.yaml` | Demo size (development) |
| `prometheus/prometheus-small.yaml` | Small production |
| `prometheus/rbac.yaml` | ServiceAccount and RBAC |
| `prometheus/servicemonitor.yaml` | Example ServiceMonitor |
| `openshift/subscription.yaml` | OpenShift OperatorHub |
| `olm/catalog-source.yaml` | OLM catalog source |
| `olm/subscription.yaml` | OLM subscription |

## Prometheus Sizes

| Size | Retention | Replicas | Use Case |
|------|-----------|----------|----------|
| Demo | 24h | 1 | Development |
| Small | 15d | 2 | Small production |
| Medium | 30d | 2 | Medium production |
| Large | 90d | 3 | Large production |

## Verify

```bash
# Check operator
kubectl get pods -n operators

# Check Prometheus
kubectl get prometheus -n monitoring
kubectl get pods -n monitoring

# Check status
kubectl describe prometheus prometheus-sample -n monitoring

# Check ServiceMonitors
kubectl get servicemonitors -n monitoring
```

## Uninstall

```bash
# Delete Prometheus
kubectl delete prometheus prometheus-sample -n monitoring

# Delete RBAC
kubectl delete -f prometheus/rbac.yaml

# Delete operator (OLM)
kubectl delete subscription prometheus-operator -n operators
kubectl delete csv -n operators -l operators.coreos.com/prometheus.operators

# Delete namespace
kubectl delete namespace monitoring
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

- [Prometheus Operator Docs](https://prometheus-operator.dev/)
- [Prometheus CRD Reference](https://prometheus-operator.dev/docs/api-reference/api/)
- [GitHub Repository](https://github.com/prometheus-operator/prometheus-operator)
