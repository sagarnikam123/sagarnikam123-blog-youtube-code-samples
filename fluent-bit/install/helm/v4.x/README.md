# Fluent Bit - Helm - v4.x

## Versions
- **App version**: v4.2.3.1
- **Chart version**: ~0.50.x
- **Docs**: https://docs.fluentbit.io/manual/v/4.0

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
# 1. Create namespace
kubectl create namespace fluent-bit

# 2. Apply ConfigMap from fluent-bit.yaml (before helm install)
kubectl create configmap fluent-bit-config \
  --from-file=fluent-bit.yaml=fluent-bit.yaml \
  -n fluent-bit

# 3. Install chart (uses existingConfigMap, no inline config)
helm install fluent-bit fluent/fluent-bit \
  -f values.yaml \
  -n fluent-bit
```

## Update Config (without helm upgrade)

Edit `fluent-bit.yaml`, then:
```bash
kubectl create configmap fluent-bit-config \
  --from-file=fluent-bit.yaml=fluent-bit.yaml \
  -n fluent-bit --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart daemonset/fluent-bit -n fluent-bit
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

## v4.x Notable Changes
- YAML config is now the recommended format in values.yaml
- Hot reload support
