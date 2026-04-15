# Fluent Operator - v2.x

## Versions
- **Operator version**: v2.9.0
- **Helm chart**: fluent-operator-2.x
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
  --version <chart-version> \
  -n fluent-operator --create-namespace
```

## Verify

```bash
kubectl get pods -n fluent-operator
kubectl get crds | grep fluentbit
kubectl get fluentbit -n fluent-operator
```

## Apply Example CRs

```bash
kubectl apply -f fluent-bit-cr.yaml
```

## Upgrade

### Helm Upgrade
```bash
helm repo update

helm upgrade fluent-operator fluent/fluent-operator \
  -f values.yaml \
  -n fluent-operator
```

### macOS (brew - binary only, not operator)
```bash
# brew only manages the fluent-bit binary, not the operator
brew upgrade fluent-bit   # upgrades CLI binary only
```

## Uninstall

```bash
helm uninstall fluent-operator -n fluent-operator

# Remove CRDs (caution: deletes all CR resources)
kubectl get crds | grep fluent | awk '{print $1}' | xargs kubectl delete crd

kubectl delete namespace fluent-operator
```
