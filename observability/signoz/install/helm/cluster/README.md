# SigNoz — Helm cluster

Use the official SigNoz Helm chart for a production-oriented Kubernetes deployment. Choose ClickHouse storage, replica counts, resources, and ingress for the target cluster before installing.

```bash
helm repo add signoz https://charts.signoz.io
helm repo update
helm upgrade --install signoz signoz/signoz \
  --namespace signoz --create-namespace \
  --values values.yaml
kubectl -n signoz get pods
```

This directory is a topology starting point, not a universal capacity profile. Follow the upstream storage and sizing guidance before using it for production.

Official guide: [SigNoz Kubernetes installation](https://signoz.io/docs/install/kubernetes/others/).
