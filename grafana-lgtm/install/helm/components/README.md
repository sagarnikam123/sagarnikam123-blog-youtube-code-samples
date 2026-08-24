# Grafana LGTM — Helm per-component (Kubernetes production)

There is no single official Grafana Labs "LGTM" Helm chart. The production Kubernetes path installs each component independently using its official chart. This gives maximum control over deployment modes, scaling, and storage per signal.

## Component charts

| Component | Chart | Modes |
|:----------|:------|:------|
| Loki (logs) | `grafana/loki` | Monolithic, Simple-Scalable (deprecated), Distributed/Microservices |
| Mimir (metrics) | `grafana/mimir-distributed` | Monolithic or Microservices |
| Tempo (traces) | `grafana/tempo-distributed` or `grafana/tempo` | Monolithic or Distributed |
| Grafana (UI) | `grafana/grafana` | Single replica or HA |
| Alloy (collector) | `grafana/alloy` | DaemonSet + Deployment |

## Install example (monolithic, development)

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install loki grafana/loki -n monitoring --create-namespace \
  --set deploymentMode=Monolithic --set loki.auth_enabled=false
helm install mimir grafana/mimir-distributed -n monitoring
helm install tempo grafana/tempo -n monitoring
helm install grafana grafana/grafana -n monitoring
```

## Install example (distributed, production)

```bash
helm install loki grafana/loki -n monitoring --create-namespace \
  --set deploymentMode=Distributed -f loki-values.yaml
helm install mimir grafana/mimir-distributed -n monitoring -f mimir-values.yaml
helm install tempo grafana/tempo-distributed -n monitoring -f tempo-values.yaml
helm install grafana grafana/grafana -n monitoring -f grafana-values.yaml
```

## Notes

- Each chart has its own `values.yaml` and scaling model.
- Object storage (S3/GCS/MinIO) is required for distributed modes.
- Existing repository component guides: [`../../../loki/install/helm/`](../../../loki/install/helm/), [`../../../mimir/install/helm/`](../../../mimir/install/helm/), [`../../../grafana/install/helm/`](../../../grafana/install/helm/).

Official Helm chart docs: [grafana.com/docs/helm-charts](https://grafana.com/docs/helm-charts/).
