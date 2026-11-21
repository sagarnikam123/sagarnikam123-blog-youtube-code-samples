# Loki v3.6.x Helm Installation

Chart version: **6.49.0** → Loki **3.6.3**

## Deployment Modes

| Mode | Directory | Use Case |
|------|-----------|----------|
| Single Binary | `single-binary/` | Dev/test, <100GB/day |
| Simple Scalable | `simple-scalable/` | Medium, 100GB-1TB/day |
| Distributed | `distributed/` | Production, >1TB/day |

## Quick Start

```bash
# Add repo (if not already added)
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Choose a mode and platform, then install
cd <mode-directory>
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values.yaml -f values-<platform>.yaml

# Example: Single Binary on Minikube
cd single-binary
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-minikube.yaml
```

## Upgrade

```bash
helm upgrade loki grafana/loki -n loki --version 6.49.0 -f values.yaml
```

## Uninstall

```bash
# Remove release
helm uninstall loki -n loki

# Delete PVCs
kubectl delete pvc --all -n loki

# Delete orphaned PVs
kubectl get pv | grep loki | awk '{print $1}' | xargs kubectl delete pv

# Delete namespace (optional)
kubectl delete namespace loki
```

## Verify

```bash
kubectl get pods -n loki
kubectl logs -n loki -l app.kubernetes.io/name=loki --tail=50
```

## Files

- `default-values.yaml` - Full upstream chart defaults (reference only)
- `<mode>/values.yaml` - Mode-specific configuration
- `distributed/README.md` - Detailed distributed mode docs
