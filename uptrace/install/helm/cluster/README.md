# Uptrace — Helm cluster

Use the official Uptrace Helm chart with external or clustered ClickHouse, PostgreSQL, and Redis for a distributed deployment.

```bash
helm repo add uptrace https://uptrace.github.io/helm-charts
helm repo update
helm upgrade --install uptrace uptrace/uptrace \
  --namespace uptrace --create-namespace \
  --values values.yaml
kubectl -n uptrace get pods
```

Configure the chart to point at production database services and size the Uptrace replicas and persistence for the workload. Run the Uptrace database migrations/seed procedure required by the selected chart version.

Official deployment overview: [Self-hosting Uptrace](https://uptrace.dev/get/hosted).
