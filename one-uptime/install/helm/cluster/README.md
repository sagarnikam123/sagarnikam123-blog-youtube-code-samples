# OneUptime — Helm cluster

Use the official OneUptime Helm chart for a Kubernetes deployment with production-oriented replica, persistence, ingress, and database settings.

```bash
helm repo add oneuptime https://helm-chart.oneuptime.com/
helm repo update
helm upgrade --install my-oneuptime oneuptime/oneuptime \
  --namespace oneuptime --create-namespace \
  --values values.yaml
kubectl -n oneuptime get pods
```

Configure a real hostname, TLS, StorageClass, resource requests, persistence, and the desired PostgreSQL, Redis, and ClickHouse topology before using this profile in production. The chart supports bundled and external database/operator configurations; follow the upstream database guide for the selected topology.

Official sources: [OneUptime Helm chart](https://github.com/OneUptime/helm-chart), [sizing and capacity](https://oneuptime.com/docs/en/installation/sizing).
