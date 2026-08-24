# VictoriaMetrics installation modes

This directory covers all officially supported deployment methods for VictoriaMetrics (single-node and cluster).

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary single-node (systemd) | Available | [`binary/standalone/`](binary/standalone/) | Self-contained binary, no deps |
| Binary cluster (systemd) | Available | [`binary/cluster/`](binary/cluster/) | vmstorage + vminsert + vmselect on bare-metal |
| Docker single-node | Available | [`docker/standalone/`](docker/standalone/) | Single `docker run` |
| Docker cluster | Available | [`docker/cluster/`](docker/cluster/) | Official multi-container cluster compose |
| Docker Compose standalone (full stack) | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 1 benchmark (VM + VL + VT + Grafana) |
| Ansible Roles | Available | [`ansible/`](ansible/) | Official Ansible Galaxy roles for all components |
| Helm standalone | Available | [`helm/standalone/`](helm/standalone/) | K8s Stack chart, single-node |
| Helm cluster | Available | [`helm/cluster/`](helm/cluster/) | K8s Stack chart, distributed |
| Kubernetes Operator | Available | [`operator/cluster/`](operator/cluster/) | CRD-managed VMCluster, VMAgent, VMAlert |

## Architecture modes

- **Single-node**: One `victoria-metrics-prod` binary handles ingestion, storage, and queries. Scales vertically to millions of metrics/s.
- **Cluster**: Separate vmstorage, vminsert, vmselect components. Scales horizontally by adding nodes.

Official sources:
- [Quick Start](https://docs.victoriametrics.com/victoriametrics/quick-start/)
- [Helm Charts](https://docs.victoriametrics.com/helm/victoriametrics-k8s-stack)
- [Kubernetes Operator](https://docs.victoriametrics.com/operator/setup/)
- [Docker Hub](https://hub.docker.com/u/victoriametrics)
- [GitHub Releases](https://github.com/VictoriaMetrics/VictoriaMetrics/releases)
