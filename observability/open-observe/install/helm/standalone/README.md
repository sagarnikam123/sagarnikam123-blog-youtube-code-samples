# OpenObserve — Helm standalone

Deploy OpenObserve in single-node local mode on Kubernetes using the official Helm chart. This mode uses SQLite metadata and a PersistentVolumeClaim for Parquet data, with no object storage or PostgreSQL required.

## Install

```bash
helm repo add openobserve https://charts.openobserve.ai
helm repo update
helm upgrade --install o2 openobserve/openobserve \
  --namespace openobserve --create-namespace \
  --values values.yaml
kubectl -n openobserve get pods
```

Port-forward to access the UI:

```bash
kubectl -n openobserve port-forward svc/o2-openobserve-router 5080:5080
```

Open <http://localhost:5080>.

## Notes

- Single-node: `ZO_LOCAL_MODE=true`. No replication, no object store.
- For production HA, use the [cluster/HA mode](../cluster/) with object storage + PostgreSQL.
- Set a real StorageClass in `values.yaml` before deploying to a cluster without a default SC.

Official chart: [openobserve-helm-chart](https://github.com/openobserve/openobserve-helm-chart).
