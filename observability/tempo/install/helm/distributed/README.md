# Tempo — Helm distributed

Deploy Tempo in distributed (microservices) mode using the `grafana/tempo-distributed` chart. Separate distributor, ingester, querier, and compactor components scale independently.

## Install

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install tempo grafana/tempo-distributed \
  --namespace tempo --create-namespace \
  --values values.yaml
kubectl -n tempo get pods
```

## Prerequisites

- Object storage (S3/GCS/MinIO/Azure) — local storage not supported in distributed mode.
- For Tempo 3.0+: Kafka-compatible broker (for the new architecture).

## Notes

- Each component scales independently.
- Metrics generator produces RED metrics → remote_write to Mimir/Prometheus.
- Pin chart version for reproducibility.
- For monolithic (dev/testing), use the [`../monolithic/`](../monolithic/) chart.

Official chart: [grafana/tempo-distributed](https://grafana.com/docs/tempo/latest/setup/helm-chart/).
