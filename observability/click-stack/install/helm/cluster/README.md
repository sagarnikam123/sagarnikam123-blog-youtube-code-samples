# ClickStack — Helm cluster

Use the official ClickStack v2 Helm chart for a Kubernetes deployment with operator-managed stateful components. Install the operators/CRDs first, then the ClickStack chart, and size ClickHouse, MongoDB, and the collector for the workload.

Follow the current two-phase commands and chart values in:

- [ClickStack Helm deployment](https://clickhouse.com/docs/clickstack/deployment/helm)
- [ClickStack Helm charts](https://github.com/ClickHouse/ClickStack-helm-charts)

Do not use the standalone Compose profile as a cluster configuration.
