# Fluent Bit - Helm - v3.x

## Versions
- **App version**: v3.0.4
- **Chart version**: ~0.40.x
- **Docs**: https://docs.fluentbit.io/manual/v/3.0

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
helm search repo fluent/fluent-bit --versions
```

## Install

```bash
helm install fluent-bit fluent/fluent-bit \
  -f values.yaml \
  -n fluent-bit --create-namespace
```

## Upgrade

```bash
helm upgrade fluent-bit fluent/fluent-bit \
  -f values.yaml \
  -n fluent-bit
```

## Uninstall

```bash
helm uninstall fluent-bit -n fluent-bit
kubectl delete namespace fluent-bit
```

## Verify

```bash
helm status fluent-bit -n fluent-bit
kubectl get pods -n fluent-bit
kubectl logs -n fluent-bit -l app.kubernetes.io/name=fluent-bit
```
