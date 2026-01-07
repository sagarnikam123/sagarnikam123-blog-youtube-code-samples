# Prometheus Installation Guide

**TL;DR:** Use Helm for Kubernetes, Docker for local development.

## Quick Start

### Kubernetes (Recommended)
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### Local Development
```bash
docker run -d -p 9090:9090 prom/prometheus
# Open http://localhost:9090
```

## Which Method Should I Use?

| Method | Use When | Guide |
|--------|----------|-------|
| **[Helm](./helm/kube-prometheus-stack/)** | Kubernetes/EKS (production) | [→ Guide](./helm/kube-prometheus-stack/README.md) |
| **[Operator](./operator/)** | OpenShift, multi-tenant, GitOps | [→ Guide](./operator/README.md) |
| **[Docker](./docker/)** | Local dev, testing, learning | [→ Guide](./docker/README.md) |
| **[Manifests](./kubernetes/)** | Learning K8s, no Helm allowed | [→ Guide](./kubernetes/README.md) |

## Understanding the Options

```
Helm (kube-prometheus-stack)
 └── Packages kube-prometheus
      └── Uses Prometheus Operator
           └── Manages Prometheus

Most users: Start with Helm, it includes everything.
```

| | Helm | Operator | Docker |
|--|------|----------|--------|
| Prometheus | ✅ | ✅ | ✅ |
| Grafana | ✅ | ❌ | ❌ |
| Alertmanager | ✅ | ✅ | ❌ |
| Auto-discovery | ✅ | ✅ | ❌ |
| Kubernetes required | Yes | Yes | No |
| Setup time | 5 min | 15 min | 1 min |

## Resources

- [Prometheus Docs](https://prometheus.io/docs/)
- [Prometheus Operator Docs](https://prometheus-operator.dev/)
- [Prometheus Operator GitHub](https://github.com/prometheus-operator/prometheus-operator)
- [kube-prometheus GitHub](https://github.com/prometheus-operator/kube-prometheus)
- [kube-prometheus-stack Helm Chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
