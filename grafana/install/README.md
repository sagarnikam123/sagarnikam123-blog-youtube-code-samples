# Grafana installation modes

This directory covers Grafana (the visualization/dashboarding component) as a standalone tool. For the full LGTM observability stack, see [`../grafana-lgtm/install/`](../../grafana-lgtm/install/).

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary/package standalone | Available | [`binary/`](binary/) | Tarball, APT, RPM, Homebrew, Windows |
| Docker standalone | Available | [`docker/`](docker/) | Single `docker run` |
| Kubernetes raw manifests | Available | [`k8s/`](k8s/) | Plain YAML Deployment + Service |
| Helm chart | Available | [`helm/standalone/`](helm/standalone/) | Official `grafana/grafana` chart |
| Grafana Operator | Available | [`operator/`](operator/) | CRD-managed instances, dashboards, datasources |

## Key facts

- Default port: 3000
- Default credentials: admin / admin
- OSS image: `grafana/grafana-oss`
- Enterprise image: `grafana/grafana` (basic features are free)

Official sources:
- [Install Grafana](https://grafana.com/docs/grafana/latest/setup-grafana/installation/)
- [Downloads](https://grafana.com/grafana/download)
- [Helm chart](https://grafana.com/docs/grafana/latest/setup-grafana/installation/helm/)
- [Kubernetes manifests](https://grafana.com/docs/grafana/latest/setup-grafana/installation/kubernetes/)
- [Grafana Operator](https://grafana.com/docs/grafana/latest/as-code/infrastructure-as-code/grafana-operator/)
- [Docker](https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/)
