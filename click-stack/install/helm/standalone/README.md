# ClickStack — Helm standalone

ClickStack's official v2 Helm chart installs the platform with operator-managed ClickHouse, MongoDB, and OpenTelemetry Collector resources.

The chart source and exact repository command are maintained by ClickHouse: [ClickStack Helm charts](https://github.com/ClickHouse/ClickStack-helm-charts). Follow the two-phase operator-then-platform installation documented in [ClickStack Helm deployment](https://clickhouse.com/docs/clickstack/deployment/helm).

Use this mode for a single-node development or validation deployment and review `values.yaml` against the chart version before installing.
