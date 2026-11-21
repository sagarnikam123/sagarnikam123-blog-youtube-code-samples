# SigNoz — Helm standalone

Installs the official SigNoz chart with the default single-release topology for development or validation.

## Prerequisites

- Kubernetes and Helm 3
- A storage class; set `global.storageClass` in `values.yaml`

## Install

```bash
helm repo add signoz https://charts.signoz.io
helm repo update
helm upgrade --install signoz signoz/signoz \
  --namespace signoz --create-namespace \
  --values values.yaml
kubectl -n signoz get pods
```

The chart installs SigNoz, its collector, ClickHouse, and ZooKeeper. This is not an HA profile.

Official guide: [Deploying with Helm directly](https://signoz.io/docs/install/kubernetes/others/).
