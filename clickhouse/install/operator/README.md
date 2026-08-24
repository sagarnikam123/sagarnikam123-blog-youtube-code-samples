# ClickHouse — Kubernetes Operator (official)

The official ClickHouse Kubernetes Operator manages ClickHouse and Keeper clusters via CRDs.

## Install operator (Helm)

```bash
helm repo add clickhouse https://docs.altinity.com/clickhouse-operator/
helm repo update
helm install clickhouse-operator clickhouse/clickhouse-operator \
  --namespace clickhouse-operator --create-namespace
```

Or install via kubectl:

```bash
kubectl apply -f https://github.com/ClickHouse/clickhouse-operator/releases/latest/download/clickhouse-operator-install-bundle.yaml
```

## Deploy a cluster

```bash
kubectl apply -f cluster.yaml
kubectl get clickhouseinstallations -n clickhouse
```

## Notes

- Manages ClickHouse + Keeper lifecycle, scaling, upgrades.
- Supports sharding, replication, persistent storage, custom configs.
- The Altinity operator (`altinity/clickhouse-operator`) is the widely-used community alternative.
- For ClickStack (observability), the ClickStack Helm chart installs this operator as a dependency.

Official sources:
- [Operator install (Helm)](https://clickhouse.com/docs/products/kubernetes-operator/install/helm)
- [Operator install (kubectl)](https://clickhouse.com/docs/products/kubernetes-operator/install/kubectl)
- [Altinity operator](https://github.com/Altinity/clickhouse-operator)
