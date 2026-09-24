# Observability Installation Matrix

This matrix separates the broader installation guide from the benchmark deployment path.

- **Guide modes** document installation types the upstream project actually supports.
- **Benchmark modes** are the controlled deployments used by the open-source observability benchmark.
- `planned` means the mode still needs an implementation in this repository.
- `N/A` means the platform does not ship that mode as a platform-level installation; component-level binaries are documented separately where useful.

## Mode Definitions

| Mode | Meaning |
|:---|:---|
| Binary | Native executable or tarball installation on Linux, macOS, or Windows where upstream publishes one |
| Docker standalone | One `docker run` or one all-in-one image |
| Docker Compose standalone | Multi-container single-node deployment |
| Docker Compose cluster | Multi-node/distributed Compose deployment, only where upstream supports it |
| Kubernetes standalone | Raw manifests for one-node/dev or single-replica deployment |
| Kubernetes cluster | Raw manifests for replicated/distributed deployment |
| Helm standalone | Official chart configured for one-node/dev mode |
| Helm cluster | Official chart configured for replicated/distributed mode |
| Operator | Official Kubernetes operator or CRD-based installation |

## Platform Matrix

| Platform | Binary | Docker standalone | Compose standalone | Compose cluster | K8s standalone | K8s cluster | Helm standalone | Helm cluster | Operator | Benchmark path |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| SigNoz | existing (systemd/binary) | existing (Foundry Compose) | existing | N/A | existing (Kustomize) | existing (Kustomize) | existing | existing | N/A | Phase 1 Compose; Phase 2 Kubernetes |
| OpenObserve | existing binary | existing Docker image | existing | N/A | existing through Helm | existing through Helm | existing | existing | existing enterprise operator | Phase 1 Compose; Phase 2 Kubernetes |
| ClickStack | existing embedded | existing all-in-one | existing | N/A | N/A | N/A | existing | existing | chart-managed operators | Phase 1 Compose |
| Grafana LGTM | component-level | existing otel-lgtm image | existing | planned | component-level | component-level | component-level | component-level | component-level (Loki + Grafana operators) | Phase 1 Compose; Phase 2 component Kubernetes |
| VictoriaMetrics stack | component-level | existing through stack | existing | planned | N/A | N/A | existing | existing | existing | Phase 1 Compose; Phase 2 Kubernetes |
| Uptrace | existing | existing through stack | existing | planned | N/A | N/A | existing | existing | N/A | Phase 1 Compose; Phase 2 Kubernetes |
| Parseable | existing binary | existing Docker image | existing | existing distributed | existing through Helm | existing through Helm | existing | existing | existing operator | Phase 1 Compose; Phase 2 Kubernetes |
| Apache SkyWalking | existing | existing | existing | existing | existing | existing | existing | planned | existing SWCK | Phase 2 Kubernetes |
| Coroot | existing (systemd) | N/A | existing | N/A | existing through operator | existing through operator | existing through operator | existing through operator | existing operator | Phase 2 Compose; Phase 2 Kubernetes |
| OneUptime | N/A | N/A | existing official Compose | N/A | N/A | existing through Helm | existing | existing | chart-managed DB operators | Phase 2 Compose; Phase 2 Kubernetes |
| Highlight.io | N/A | N/A | existing hobby Compose | N/A | N/A | N/A | N/A | N/A | N/A | Phase 2 Compose only |
| Elastic Observability | existing components | existing Docker images | existing | existing multi-node | existing ECK standalone | existing ECK cluster | existing eck-stack | existing eck-stack | existing ECK | Phase 2 Compose; Phase 2 Kubernetes |
| OpenSearch Observability | existing components | existing Docker images | existing | existing multi-node | existing through Helm | existing Helm | existing | existing | existing operator | Phase 2 Compose; Phase 2 Kubernetes |
| Uptime Kuma | N/A (Node.js + PM2 from source) | existing | existing | N/A | community (via Helm) | N/A | community (HelmForge) | N/A | N/A | Uptime monitoring guide |
| Gatus | N/A (`go install` / source) | existing | existing | N/A | existing (raw manifests) | use Helm | existing (official chart) | use Helm | N/A | Uptime monitoring guide |
| OpenStatus | N/A | N/A | existing official Compose | N/A | N/A | N/A | N/A | N/A | N/A | Uptime monitoring guide |

## Existing Repository Coverage

The repository already contains reusable installation patterns for individual components:

| Component | Existing modes |
|:---|:---|
| Prometheus | Binary, Docker/Compose, Helm, Operator |
| Loki | Binary, Docker (monolithic/simple-scalable/microservices), Helm, raw K8s, Operator |
| Mimir | Helm, Kubernetes |
| VictoriaLogs | Binary, Docker, Helm single, Helm cluster, Operator |
| Grafana | Binary (tarball/APT/RPM/Homebrew/Windows), Docker, Helm, Kubernetes manifests, Operator |
| Apache SkyWalking | Binary standalone, Docker standalone/cluster, Helm, SWCK |
| MySQL | Binary tarball, DEB/APT, RPM, Docker, Docker Compose (+ Adminer + exporter), Helm (Bitnami), Operator (Oracle MySQL Operator) |
| PostgreSQL | Binary (pgenv), DEB/APT (PGDG), RPM (PGDG), Docker, Docker Compose (+ Adminer + exporter), Helm (Bitnami), Operator (CloudNativePG) |

These component installations will be reused rather than duplicated inside every composite platform.

MySQL and PostgreSQL are documented as standalone SQL data stores and Grafana SQL datasources — used by application backends and analytics pipelines that visualize relational data in Grafana.

## Folder Convention

New platform-specific modes use this structure:

```text
<platform>/install/
├── binary/
│   └── standalone/
├── docker/
│   └── standalone/
├── docker-compose/
│   ├── standalone/
│   └── cluster/
├── k8s/
│   ├── standalone/
│   └── cluster/
├── helm/
│   ├── standalone/
│   └── cluster/
└── operator/
   └── cluster/
```

Existing paths remain valid until their mode is migrated and validated. Benchmark Compose files are not mixed with HA or production tuning.

## Official Sources

- [SigNoz installation](https://signoz.io/docs/install/)
- [OpenObserve installation](https://openobserve.ai/docs/)
- [ClickStack deployment](https://clickhouse.com/docs/clickstack/deployment)
- [Grafana LGTM](https://grafana.com/oss/)
- [VictoriaMetrics deployment](https://docs.victoriametrics.com/)
- [Uptrace deployment](https://uptrace.dev/get/hosted)
- [Parseable installation](https://www.parseable.com/docs/self-hosted/installation)
- [Apache SkyWalking deployment](https://skywalking.apache.org/docs/main/latest/en/setup/)
- [Coroot installation](https://docs.coroot.com/installation/)
- [Coroot Kubernetes Operator](https://docs.coroot.com/installation/k8s-operator/)
- [OneUptime Docker Compose](https://oneuptime.com/docs/installation/docker-compose)
- [OneUptime Helm chart](https://github.com/OneUptime/helm-chart)
- [Highlight.io self-hosting](https://github.com/highlight/highlight)
- [Elastic self-managed](https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html)
- [OpenSearch installation](https://opensearch.org/docs/latest/install-and-configure/)
- [OpenSearch Kubernetes Operator](https://opensearch-project.github.io/opensearch-k8s-operator/)
- [Uptime Kuma installation](https://github.com/louislam/uptime-kuma/wiki/%F0%9F%94%A7-How-to-Install)
- [Gatus configuration & deployment](https://github.com/TwiN/gatus)
- [Gatus Helm chart](https://github.com/TwiN/helm-charts/tree/master/charts/gatus)
- [OpenStatus self-hosting](https://www.openstatus.dev/docs/guides/self-hosting-openstatus)
