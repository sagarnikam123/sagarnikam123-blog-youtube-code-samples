# PostgreSQL — Helm (Bitnami chart)

The Bitnami PostgreSQL chart deploys PostgreSQL on Kubernetes in either standalone or primary/read-replica mode.

## Prerequisites

- Kubernetes cluster with `kubectl` access
- Helm 3
- A default StorageClass (for PersistentVolumes)

## Add repo

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

## Standalone (single node)

```bash
kubectl create namespace database

helm install postgres bitnami/postgresql \
  -n database \
  --set auth.postgresPassword=changeme \
  --set auth.database=appdb \
  --set auth.username=appuser \
  --set auth.password=apppass \
  --set primary.persistence.size=8Gi
```

## Cluster (primary + read replicas)

```bash
helm install postgres bitnami/postgresql \
  -n database \
  --set architecture=replication \
  --set auth.postgresPassword=changeme \
  --set auth.replicationPassword=replpass \
  --set readReplicas.replicaCount=2 \
  --set primary.persistence.size=8Gi \
  --set readReplicas.persistence.size=8Gi
```

## Access

```bash
# Password
kubectl get secret postgres-postgresql -n database -o jsonpath='{.data.postgres-password}' | base64 -d; echo

# Port-forward and connect
kubectl port-forward svc/postgres-postgresql -n database 5432:5432 &
psql -h 127.0.0.1 -p 5432 -U postgres -d appdb
```

## Notes

- `architecture=standalone` (default) = single StatefulSet pod; `replication` = 1 primary + N streaming read replicas.
- Enable metrics with `--set metrics.enabled=true` to run postgres-exporter as a sidecar (Prometheus + Grafana).
- For automated failover/HA, prefer the CloudNativePG operator (see [`../operator/`](../operator/)); Bitnami replication has no automatic primary failover.
- Store overrides in a `values.yaml` and pass `-f values.yaml` instead of many `--set` flags.

Official source: [Bitnami PostgreSQL chart](https://github.com/bitnami/charts/tree/main/bitnami/postgresql).
