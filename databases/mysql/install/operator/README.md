# MySQL — Kubernetes Operator (official)

The official [MySQL Operator for Kubernetes](https://dev.mysql.com/doc/mysql-operator/en/) (by Oracle) manages MySQL InnoDB Clusters — Group Replication with automatic failover and a MySQL Router front end — via the `InnoDBCluster` CRD.

## Install operator (Helm)

```bash
helm repo add mysql-operator https://mysql.github.io/mysql-operator/
helm repo update
helm install mysql-operator mysql-operator/mysql-operator \
  --namespace mysql-operator --create-namespace
```

Or install via kubectl:

```bash
kubectl apply -f https://raw.githubusercontent.com/mysql/mysql-operator/trunk/deploy/deploy-crds.yaml
kubectl apply -f https://raw.githubusercontent.com/mysql/mysql-operator/trunk/deploy/deploy-operator.yaml
```

## Deploy a cluster

```bash
# Root credentials secret referenced by the cluster spec
kubectl create secret generic mypwds \
  --from-literal=rootUser=root \
  --from-literal=rootHost=% \
  --from-literal=rootPassword=changeme

kubectl apply -f cluster.yaml
kubectl get innodbcluster
```

## Notes

- Manages InnoDB Cluster lifecycle: Group Replication, automatic failover, backups, upgrades.
- MySQL Router is deployed automatically to route read/write traffic.
- `spec.instances` sets replica count (3+ recommended for HA quorum).
- Connect apps to the `<cluster>` Service on port 6446 (read/write) / 6447 (read-only).

Official sources:
- [MySQL Operator docs](https://dev.mysql.com/doc/mysql-operator/en/)
- [Operator on GitHub](https://github.com/mysql/mysql-operator)
