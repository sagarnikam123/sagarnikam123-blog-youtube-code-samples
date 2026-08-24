# Parseable — Kubernetes Operator

The official Parseable Kubernetes Operator manages Parseable clusters using CRDs.

## Install the operator

```bash
helm repo add parseable https://charts.parseable.com
helm repo update
helm install parseable-operator parseable/parseable-operator \
  --namespace parseable-operator --create-namespace
```

## Deploy a Parseable cluster

After the operator is running, apply a `ParseableCluster` custom resource:

```bash
kubectl apply -f cluster.yaml
kubectl get parseableclusters -n parseable
```

## Notes

- The operator manages lifecycle, scaling, and upgrades of Parseable clusters.
- Requires object storage for distributed mode.
- For simpler deployments without an operator, use the [Helm charts](../../helm/).

Official source: [Parseable Kubernetes Operator](https://github.com/parseablehq/operator).
