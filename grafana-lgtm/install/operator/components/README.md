# Grafana LGTM — Kubernetes Operators (per-component)

Grafana Labs publishes operators for individual LGTM components. Each manages its respective component via CRDs.

## Available operators

| Component | Operator | CRDs |
|:----------|:---------|:-----|
| Loki (logs) | [Loki Operator](https://github.com/grafana/loki/tree/main/operator) | `LokiStack` |
| Grafana (UI) | [Grafana Operator](https://github.com/grafana/grafana-operator) | `Grafana`, `GrafanaDashboard`, `GrafanaDatasource` |
| Mimir | No dedicated operator | Use Helm chart |
| Tempo | No dedicated operator | Use Helm chart |

## Loki Operator example

```bash
# Install via OLM or direct manifests
kubectl apply -f https://raw.githubusercontent.com/grafana/loki/main/operator/bundle/openshift/manifests/...

# Then apply a LokiStack CR
kubectl apply -f lokistack.yaml
```

See the existing repository guide: [`../../../loki/install/operator/`](../../../loki/install/operator/).

## Grafana Operator example

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana-operator grafana/grafana-operator \
  --namespace grafana-operator --create-namespace
```

Then manage Grafana instances, dashboards, and datasources via `Grafana` CRDs.

## Notes

- There is no single "LGTM Operator" that deploys the entire stack.
- Use per-component operators for the components that have them; use Helm charts for the rest.
- Mimir and Tempo do not have dedicated operators — Helm is their production path.

Official sources:
- [Loki Operator](https://grafana.com/docs/loki/latest/setup/install/helm/)
- [Grafana Operator](https://grafana.com/docs/grafana/latest/as-code/infrastructure-as-code/grafana-operator/)
