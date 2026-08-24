# Grafana — Kubernetes Operator

The Grafana Operator manages Grafana instances, dashboards, and datasources on Kubernetes via CRDs.

## Install the operator

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install grafana-operator grafana/grafana-operator \
  --namespace grafana-operator --create-namespace
```

## Deploy a Grafana instance

```yaml
apiVersion: grafana.integreatly.org/v1beta1
kind: Grafana
metadata:
  name: grafana
  namespace: monitoring
spec:
  config:
    server:
      root_url: http://localhost:3000
    auth.anonymous:
      enabled: "true"
```

```bash
kubectl apply -f grafana.yaml
```

## Manage dashboards as CRDs

```yaml
apiVersion: grafana.integreatly.org/v1beta1
kind: GrafanaDashboard
metadata:
  name: sample-dashboard
  namespace: monitoring
spec:
  instanceSelector:
    matchLabels:
      dashboards: "grafana"
  json: |
    { "title": "Sample", "panels": [] }
```

## Notes

- The operator syncs CRDs to the Grafana instance continuously.
- Supports `Grafana`, `GrafanaDashboard`, `GrafanaDatasource`, `GrafanaFolder` CRDs.
- Works with self-hosted Grafana instances and Grafana Cloud.
- For simple deployments without an operator, use the [Helm chart](../helm/) directly.

Official sources:
- [Grafana Operator](https://grafana.com/docs/grafana/latest/as-code/infrastructure-as-code/grafana-operator/)
- [GitHub — grafana-operator](https://github.com/grafana/grafana-operator)
