# OpenObserve — Helm cluster

OpenObserve's official Kubernetes deployment is the HA Helm chart. It requires object storage and a metadata database; the chart also expects the CloudNativePG operator when using its bundled PostgreSQL cluster.

## Install

```bash
helm repo add openobserve https://charts.openobserve.ai
helm repo update
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.23/releases/cnpg-1.23.1.yaml
helm upgrade --install o2 openobserve/openobserve \
  --namespace openobserve --create-namespace \
  --values values.yaml
kubectl -n openobserve get pods
```

Set the object-store bucket, region, and credentials in `values.yaml` before installing. Do not use local disk for HA data.

Official guide: [OpenObserve HA deployment](https://openobserve.ai/docs/administration/deployment/ha-deployment/).
