# OneUptime — Helm standalone

OneUptime publishes an official Helm chart for Kubernetes. Use this profile for a development or small single-replica installation with a cluster-provided StorageClass.

```bash
helm repo add oneuptime https://helm-chart.oneuptime.com/
helm repo update
helm upgrade --install my-oneuptime oneuptime/oneuptime \
  --namespace oneuptime --create-namespace \
  --values values.yaml
kubectl -n oneuptime get pods
```

Set `host`, `httpProtocol`, and `global.storageClass` before installing. Review the chart's current configuration reference for database and ingress settings.

Official chart: [OneUptime Helm chart](https://github.com/OneUptime/helm-chart).
