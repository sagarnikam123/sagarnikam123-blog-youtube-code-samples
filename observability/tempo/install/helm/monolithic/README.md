# Tempo — Helm monolithic

Deploy Tempo in monolithic (single-binary) mode using the `grafana/tempo` Helm chart.

## Install

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install tempo grafana/tempo \
  --namespace tempo --create-namespace \
  --values values.yaml
kubectl -n tempo get pods
```

## Access

```bash
kubectl -n tempo port-forward svc/tempo 3200:3200 4317:4317
```

## Notes

- Monolithic: all components in one process.
- Uses local PVC storage — good for dev/testing.
- For production, use the [distributed chart](../distributed/).

Official chart: [grafana/tempo](https://grafana.com/docs/tempo/latest/setup/helm-chart/).
