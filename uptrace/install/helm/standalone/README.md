# Uptrace — Helm standalone

Uptrace provides an official Kubernetes Helm chart. Use this mode for a single Uptrace release backed by the chart's configured dependencies.

```bash
helm repo add uptrace https://uptrace.github.io/helm-charts
helm repo update
helm upgrade --install uptrace uptrace/uptrace \
  --namespace uptrace --create-namespace \
  --values values.yaml
kubectl -n uptrace get pods
```

Review the chart's current values for ClickHouse, PostgreSQL, Redis, persistence, and the project DSN before installing.

Official deployment overview: [Self-hosting Uptrace](https://uptrace.dev/get/hosted).
