# Elastic Observability installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Native packages/binaries | Available | [`binary/standalone/`](binary/standalone/) | Elasticsearch, Kibana, APM Server installed separately |
| Docker standalone | Available | [`docker/standalone/`](docker/standalone/) | Individual containers on a Docker network |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 2 benchmark (single-node, security disabled) |
| Docker Compose cluster | Available | [`docker-compose/cluster/`](docker-compose/cluster/) | Official three-node Elasticsearch example |
| ECK operator standalone | Available | [`operator/standalone/`](operator/standalone/) | Single-replica Kubernetes deployment via YAML |
| ECK operator cluster | Available | [`operator/cluster/`](operator/cluster/) | Multi-node Kubernetes deployment via YAML |
| Helm standalone (eck-stack) | Available | [`helm/standalone/`](helm/standalone/) | ECK operator + eck-stack chart, single-node |
| Helm cluster (eck-stack) | Available | [`helm/cluster/`](helm/cluster/) | ECK operator + eck-stack chart, multi-node |

Official sources:
- [Install Elasticsearch](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/installing-elasticsearch)
- [Docker Compose multi-node](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-elasticsearch-docker-compose)
- [Install ECK (YAML)](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/install-using-yaml-manifest-quickstart)
- [Install ECK (Helm)](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/install-using-helm-chart)
- [eck-stack chart](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/managing-deployments-using-helm-chart)
