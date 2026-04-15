# Fluent Bit - Kubernetes (Raw Manifests) - v3.x

## Version
- **Image**: `fluent/fluent-bit:3.0.4`
- **Docs**: https://docs.fluentbit.io/manual/v/3.0

## Files
| File | Purpose |
|------|---------|
| `rbac.yaml` | ServiceAccount, ClusterRole, ClusterRoleBinding |
| `configmap.yaml` | Fluent Bit config + parsers |
| `daemonset.yaml` | DaemonSet (runs on every node) |

## Deploy

```bash
kubectl create namespace fluent-bit
kubectl apply -f rbac.yaml
kubectl apply -f configmap.yaml
kubectl apply -f daemonset.yaml
```

## Or apply all at once

```bash
kubectl create namespace fluent-bit
kubectl apply -f .
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
