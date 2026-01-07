# Loki Installation Methods

Choose an installation method based on your environment and requirements.

## Methods

| Method | Best For | Complexity | Production Ready |
|--------|----------|------------|------------------|
| [Helm](helm/) | Most Kubernetes clusters | Medium | ✅ Yes |
| [Operator](operator/) | OpenShift, GitOps workflows | High | ✅ Yes |
| [Local](local/) | Development, learning | Low | ❌ No |
| [Docker](docker/) | Quick testing | Low | ❌ No |
| [Tanka](tanka/) | Jsonnet-based deployments | High | ✅ Yes |
| [K8s](k8s/) | Raw Kubernetes manifests | Medium | ⚠️ Manual |

## When to Use What

### Development & Learning

| Method | When to Use |
|--------|-------------|
| **Local** | Learning Loki basics, testing configs locally |
| **Docker** | Quick experiments, CI pipelines |
| **Helm (Single Binary)** | Learning Kubernetes deployment, Minikube/Docker Desktop |

### Production

| Method | When to Use |
|--------|-------------|
| **Helm** | EKS, GKE, AKS, vanilla K8s - most flexible, widely adopted |
| **Operator** | OpenShift environments, teams using OLM/operator patterns |
| **Tanka** | Teams already using Jsonnet, Grafana Labs' internal tooling |

### Helm vs Operator (Production)

| Factor | Helm | Operator |
|--------|------|----------|
| Version control | Full - you choose exact version | Limited - operator decides |
| Flexibility | High | Opinionated |
| Community support | Large, more examples | Smaller, OpenShift-focused |
| Upgrade control | Manual, predictable | Automated |
| Best for | EKS/GKE/AKS/vanilla K8s | OpenShift, GitOps |

**Recommendation:** Use **Helm** for most production Kubernetes clusters.

## Quick Decision Guide

```
Development/Learning?
  ├── Local machine → local/ or docker/
  └── Kubernetes (Minikube) → helm/ (single-binary)

Production?
  ├── OpenShift → operator/
  ├── EKS/GKE/AKS/vanilla K8s → helm/ (recommended)
  ├── Using Jsonnet/Tanka → tanka/
  └── Need raw manifests → k8s/
```

## Deployment Modes

All Kubernetes methods support these deployment modes:

| Mode | Scale | Use Case |
|------|-------|----------|
| Single Binary | <100GB/day | Dev/test |
| Simple Scalable | 100GB-1TB/day | Medium production |
| Distributed | >1TB/day | Large production |

## Getting Started

### Helm (Recommended for K8s)

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki -n loki --create-namespace \
  -f helm/v3.6.x/single-binary/values-base.yaml \
  -f helm/v3.6.x/single-binary/values-minikube.yaml
```

### Operator (OpenShift/GitOps)

```bash
# Install operator, then apply LokiStack CR
kubectl apply -f operator/lokistack/lokistack-demo.yaml
```

### Local

```bash
./local/install.sh
```

## Resources

- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Deployment Modes](https://grafana.com/docs/loki/latest/get-started/deployment-modes/)
- [Loki Operator](https://loki-operator.dev/)
