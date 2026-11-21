# Parseable — Helm standalone

Deploy Parseable in standalone mode on Kubernetes using the official Helm chart.

## Install

```bash
helm repo add parseable https://charts.parseable.com
helm repo update
helm upgrade --install parseable parseable/parseable \
  --namespace parseable --create-namespace \
  --set parseable.store=local-store
kubectl -n parseable get pods
```

Port-forward to access the UI:

```bash
kubectl -n parseable port-forward svc/parseable 8000:80
```

Open <http://localhost:8000>.

## Notes

- Standalone: single ingest + query node with local PVC storage.
- For distributed (multi-node + object storage), see [`../distributed/`](../distributed/).
- Pin the chart version for reproducible deployments.

Official chart: [Parseable Helm chart](https://charts.parseable.com/charts/parseable/).
