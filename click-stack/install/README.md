# ClickStack installation modes

ClickStack has several upstream deployment modes. The repository keeps the benchmark Compose stack separate from the simpler demo modes and Kubernetes production path.

| Mode | Status | Path | Use |
|:-----|:-------|:-----|:----|
| ClickHouse-embedded binary | Available | [`binary/standalone/`](binary/standalone/) | Demo/evaluation against the ClickHouse binary |
| Docker all-in-one | Available | [`docker/standalone/`](docker/standalone/) | Local demo; all components in one container |
| Docker HyperDX-only | Available | [`docker/hyperdx-only/`](docker/hyperdx-only/) | Existing ClickHouse plus MongoDB |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 1 benchmark and single-server deployments |
| Docker Compose cluster | Not documented by upstream | — | Use Helm or managed ClickHouse instead |
| Browser local mode | Available | [`browser/local-mode/`](browser/local-mode/) | Ephemeral demo/debugging only |
| Helm standalone | Available | [`helm/standalone/`](helm/standalone/) | Kubernetes development/validation |
| Helm cluster | Available | [`helm/cluster/`](helm/cluster/) | Kubernetes production scaling |
| Raw Kubernetes manifests | Not maintained separately | — | Helm is the official Kubernetes path |
| Operators | Included by the Helm installation | — | Helm installs the required operators/CRDs |

Official overview: [ClickStack deployment options](https://clickhouse.com/docs/clickstack/deployment/overview).

## Terraform configuration management

Terraform does not provision the ClickStack platform itself. After installing ClickStack with Docker Compose or Helm, use the [self-hosted Terraform example](../terraform/self-hosted/) to manage dashboards and other supported ClickStack configuration resources.

Official source: [ClickStack Terraform provider](https://clickhouse.com/blog/clickstack-terraform-provider).
