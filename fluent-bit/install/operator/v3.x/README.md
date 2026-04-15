# Fluent Operator - v3.x

## Versions
- **Operator version**: v3.7.0
- **Helm chart**: fluent-operator-3.5.0
- **Docs**: https://fluent-operator.netlify.app/

## Prerequisites
- Kubernetes cluster
- Helm 3.x
- kubectl configured

## Add Helm Repo

```bash
helm repo add fluent https://fluent.github.io/helm-charts
helm repo update
```

## Search Chart Versions

```bash
helm search repo fluent/fluent-operator --versions
```

## Install

```bash
helm install fluent-operator fluent/fluent-operator \
  -f values.yaml \
  -n fluent-operator --create-namespace
```

## Verify

```bash
# Check operator pod is running
kubectl get pods -n fluent-operator

# Check CRDs are installed
kubectl get crds | grep fluentbit

# Check FluentBit DaemonSet created by operator
kubectl get fluentbit -n fluent-operator
kubectl get pods -n fluent-operator -l app.kubernetes.io/name=fluent-bit
```

## Apply Example CRs

```bash
# Deploy ClusterInput, ClusterFilter, ClusterOutput
kubectl apply -f fluent-bit-cr.yaml
```

## Upgrade

### Helm Upgrade
```bash
helm repo update

# Check available versions
helm search repo fluent/fluent-operator --versions

helm upgrade fluent-operator fluent/fluent-operator \
  -f values.yaml \
  -n fluent-operator
```

### macOS (if installed via brew for CLI tools only)
```bash
# Note: brew only installs fluent-bit binary, not the operator
# Operator is Kubernetes-only, upgrade via Helm above
brew upgrade fluent-bit   # upgrades the CLI binary only
```

## Uninstall

```bash
helm uninstall fluent-operator -n fluent-operator

# Remove CRDs (caution: deletes all CR resources)
kubectl get crds | grep fluent | awk '{print $1}' | xargs kubectl delete crd

kubectl delete namespace fluent-operator
```

## v3.x Notable Changes
- Supports Fluent Bit v3.x and v4.x images
- Improved CRD schema validation
- Multi-tenant namespace-scoped CRDs (Input, Filter, Output)
