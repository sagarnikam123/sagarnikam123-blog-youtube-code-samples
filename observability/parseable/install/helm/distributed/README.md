# Parseable — Helm distributed

Deploy Parseable in distributed mode on Kubernetes. Multiple ingestor and querier pods with object storage as the backing store.

## Install

```bash
helm repo add parseable https://charts.parseable.com
helm repo update
helm upgrade --install parseable parseable/parseable \
  --namespace parseable --create-namespace \
  --values values.yaml
kubectl -n parseable get pods
```

Configure `values.yaml` with S3/MinIO/GCS bucket credentials, ingestor replica count, and querier replica count before installing.

## Notes

- Requires an S3-compatible object store.
- Ingestors and queriers scale independently.
- HA features (smart cache, anomaly detection) require Parseable Enterprise.
- For standalone (single-node, local disk), see [`../standalone/`](../standalone/).

Official guide: [Parseable distributed Kubernetes](https://www.parseable.com/docs/self-hosted/installation/distributed/k8s-helm).
