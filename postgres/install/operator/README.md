# PostgreSQL — Kubernetes Operator (CloudNativePG)

[CloudNativePG](https://cloudnative-pg.io/) is a CNCF operator that manages PostgreSQL HA clusters via the `Cluster` CRD — streaming replication, automatic failover, backups, and rolling upgrades. (Alternatives: Zalando postgres-operator, Crunchy PGO.)

## Install operator (Helm)

```bash
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo update
helm install cnpg cnpg/cloudnative-pg \
  --namespace cnpg-system --create-namespace
```

Or install via kubectl:

```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.1.yaml
```

## Deploy a cluster

```bash
kubectl apply -f cluster.yaml
kubectl get clusters
kubectl cnpg status pg-cluster      # requires the cnpg kubectl plugin
```

## Access

```bash
# Operator generates a secret <cluster>-app with the app-user credentials
kubectl get secret pg-cluster-app -o jsonpath='{.data.password}' | base64 -d; echo

# Read/write service: <cluster>-rw ; read-only: <cluster>-ro
kubectl port-forward svc/pg-cluster-rw 5432:5432
```

## Notes

- Manages full cluster lifecycle: streaming replication, automatic failover, PITR backups to object storage, rolling minor/major upgrades.
- `spec.instances` sets replica count (3 recommended for HA quorum).
- Apps connect to `<cluster>-rw` (primary, read/write) or `<cluster>-ro` (replicas, read-only).
- Built-in Prometheus metrics endpoint — enable a PodMonitor for Grafana.

Official sources:
- [CloudNativePG docs](https://cloudnative-pg.io/documentation/current/)
- [CloudNativePG on GitHub](https://github.com/cloudnative-pg/cloudnative-pg)
