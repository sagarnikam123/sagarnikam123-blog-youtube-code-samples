# Fluent Bit - Kubernetes (Raw Manifests) - v5.x

## Version
- **Image**: `fluent/fluent-bit:5.0.1`
- **Docs**: https://docs.fluentbit.io/manual

## Files
| File | Purpose |
|------|---------|
| `rbac.yaml` | ServiceAccount, ClusterRole, ClusterRoleBinding |
| `fluent-bit.yaml` | Fluent Bit config (edit this file) |
| `configmap.yaml` | Instructions to generate ConfigMap from fluent-bit.yaml |
| `kustomization.yaml` | Kustomize manifest (generates ConfigMap from fluent-bit.yaml) |
| `daemonset.yaml` | DaemonSet — references `/fluent-bit/etc/fluent-bit.yaml` |

## Deploy

### With Kustomize (recommended)
```bash
kubectl create namespace fluent-bit
kubectl apply -f rbac.yaml
kubectl apply -k .
```

### Without Kustomize
```bash
kubectl create namespace fluent-bit
kubectl apply -f rbac.yaml
kubectl create configmap fluent-bit-config \
  --from-file=fluent-bit.yaml=fluent-bit.yaml \
  -n fluent-bit
kubectl apply -f daemonset.yaml
```

## Update Config

Edit `fluent-bit.yaml`, then re-apply:
```bash
kubectl apply -k .
# or without kustomize:
kubectl create configmap fluent-bit-config \
  --from-file=fluent-bit.yaml=fluent-bit.yaml \
  -n fluent-bit --dry-run=client -o yaml | kubectl apply -f -
```

## Verify

```bash
kubectl get pods -n fluent-bit
kubectl logs -n fluent-bit -l app=fluent-bit
```

## Delete

```bash
kubectl delete -f .
kubectl delete namespace fluent-bit
```

## v5.x Notable Changes
- YAML config is the default and only recommended format
- Improved performance and plugin ecosystem
