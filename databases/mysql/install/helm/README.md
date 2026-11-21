# MySQL — Helm (Bitnami chart)

The Bitnami MySQL chart deploys MySQL on Kubernetes in either standalone or primary/secondary replication mode.

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

helm install mysql bitnami/mysql \
  -n database \
  --set auth.rootPassword=changeme \
  --set auth.database=appdb \
  --set auth.username=appuser \
  --set auth.password=apppass \
  --set primary.persistence.size=8Gi
```

## Cluster (primary + replicas)

```bash
helm install mysql bitnami/mysql \
  -n database \
  --set architecture=replication \
  --set auth.rootPassword=changeme \
  --set secondary.replicaCount=2 \
  --set primary.persistence.size=8Gi \
  --set secondary.persistence.size=8Gi
```

## Access

```bash
# Password
kubectl get secret mysql -n database -o jsonpath='{.data.mysql-root-password}' | base64 -d; echo

# Port-forward and connect
kubectl port-forward svc/mysql -n database 3306:3306 &
mysql -h 127.0.0.1 -P 3306 -u root -p
```

## Notes

- `architecture=standalone` (default) = single StatefulSet pod; `replication` = 1 primary + N read replicas with async replication.
- Enable metrics with `--set metrics.enabled=true` to run mysqld-exporter as a sidecar (Prometheus + Grafana).
- Store overrides in a `values.yaml` and pass `-f values.yaml` instead of many `--set` flags.

Official source: [Bitnami MySQL chart](https://github.com/bitnami/charts/tree/main/bitnami/mysql).
