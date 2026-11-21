# VictoriaLogs — Helm cluster

The `victoria-logs-cluster` Helm chart deploys VictoriaLogs in distributed mode on Kubernetes with separate ingest and select components for horizontal scaling.

## Install

```bash
helm repo add vm https://victoriametrics.github.io/helm-charts
helm repo update
helm upgrade --install vl-cluster vm/victoria-logs-cluster \
  --namespace victoria-logs --create-namespace \
  --values values.yaml
kubectl -n victoria-logs get pods
```

## Notes

- Distributed mode: separate vlinsert + vlselect + vlstorage components.
- Requires persistent storage for vlstorage.
- For single-node deployments, use the [`helm/` (single)](../helm/) chart instead.
- Configure retention, resources, and replica counts in `values.yaml`.

Official chart: [VictoriaLogs Cluster Helm chart](https://docs.victoriametrics.com/helm/victoria-logs-cluster/).
