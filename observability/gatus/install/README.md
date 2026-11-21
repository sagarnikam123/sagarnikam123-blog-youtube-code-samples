# Gatus installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary standalone | Available (`go install` / source) | [`binary/standalone/`](binary/standalone/) | No prebuilt release binary; build with Go 1.21+ |
| Docker standalone | Available | [`docker/standalone/`](docker/standalone/) | `twinproduction/gatus`, listens on `:8080`, config at `/config/config.yaml` |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Gatus alone, or with PostgreSQL for persistent history |
| Docker Compose cluster | N/A | — | Scale via multiple instances / external DB, not a compose cluster mode |
| Kubernetes standalone | Available | [`k8s/standalone/`](k8s/standalone/) | Raw Deployment + Service + ConfigMap |
| Kubernetes cluster | Use Helm | [`helm/standalone/`](helm/standalone/) | Chart handles replicas/autoscaling |
| Helm standalone | Available (official) | [`helm/standalone/`](helm/standalone/) | `helm repo add twin https://twin.sh/helm-charts` |
| Operator | N/A | — | No official operator (a community `gatus-sidecar` generates configs from K8s resources) |

Config is the same `config.yaml` across every mode — only how it is delivered (bind mount, ConfigMap, Helm value) changes.

Official sources:
- [GitHub repository](https://github.com/TwiN/gatus)
- [Helm chart](https://github.com/TwiN/helm-charts/tree/master/charts/gatus)
- [gatus-sidecar (community)](https://github.com/home-operations/gatus-sidecar)
