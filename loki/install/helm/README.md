# Loki Helm Charts

Helm chart configurations for deploying Grafana Loki on Kubernetes.

## Versions

| Directory | Chart Version | Loki Version | Status |
|-----------|---------------|--------------|--------|
| `v3.6.x/` | 6.49.0 | 3.6.3 | Current |

## Deployment Modes

| Mode | Use Case | Scale |
|------|----------|-------|
| **Single Binary** | Dev/test | <100GB/day |
| **Simple Scalable** | Medium production | 100GB-1TB/day |
| **Distributed** | Large production | >1TB/day |

## Quick Start

```bash
# Add Grafana repo
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install (choose a mode and platform)
cd v3.6.x/<mode>
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values.yaml -f values-<platform>.yaml

# Example: Single Binary on Minikube
cd v3.6.x/single-binary
helm install loki grafana/loki -n loki --create-namespace \
  --version 6.49.0 \
  -f values-base.yaml -f values-minikube.yaml
```

## Uninstall

```bash
helm uninstall loki -n loki
kubectl delete pvc --all -n loki
kubectl get pv | grep loki | awk '{print $1}' | xargs kubectl delete pv
kubectl delete namespace loki
```

## Structure

```
helm/
├── README.md                    # This file
└── v3.6.x/
    ├── README.md                # Version-specific quick reference
    ├── default-values.yaml      # Full upstream defaults (reference)
    ├── single-binary/
    │   ├── README.md
    │   ├── values-base.yaml     # Base config
    │   ├── values-minikube.yaml # Minikube overrides
    │   ├── values-docker.yaml   # Docker Desktop overrides
    │   ├── values-eks.yaml      # AWS EKS overrides
    │   └── values-aks.yaml      # Azure AKS overrides
    ├── simple-scalable/
    │   ├── README.md
    │   └── values.yaml
    └── distributed/
        ├── README.md
        └── values.yaml
```

## Key Configuration

### Storage

```yaml
# Filesystem (dev)
loki:
  storage:
    type: filesystem

# S3 (production)
loki:
  storage:
    type: s3
    s3:
      endpoint: s3.amazonaws.com
      bucketNames:
        chunks: loki-chunks
```

### Resources

```yaml
ingester:
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      memory: 4Gi
```

### Retention

```yaml
loki:
  limits_config:
    retention_period: 744h  # 31 days
```

## Troubleshooting

```bash
# Check pods
kubectl get pods -n loki

# Check logs
kubectl logs -n loki -l app.kubernetes.io/name=loki --tail=100

# Dry-run install
helm install loki grafana/loki -n loki -f values.yaml --dry-run --debug
```

## References

- [Loki Helm Chart](https://github.com/grafana/loki/tree/main/production/helm/loki)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Deployment Modes](https://grafana.com/docs/loki/latest/get-started/deployment-modes/)
