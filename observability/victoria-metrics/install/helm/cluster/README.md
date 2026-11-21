# VictoriaMetrics stack — Helm cluster

Use the official `victoriametrics-k8s-stack` chart and enable the `VMCluster` topology for distributed metrics storage. The chart also supports VictoriaLogs and VictoriaTraces resources through the operator.

```bash
helm repo add vm https://victoriametrics.github.io/helm-charts
helm repo update
helm upgrade --install vmks vm/victoriametrics-k8s-stack \
  --namespace victoria-metrics --create-namespace \
  --values values.yaml
kubectl -n victoria-metrics get pods
```

Set storage, replicas, replication, resources, and remote-write targets in `values.yaml` for the workload. The upstream HA guide explains the cluster topology.

Official sources: [K8s Stack](https://docs.victoriametrics.com/helm/victoriametrics-k8s-stack), [HA monitoring](https://docs.victoriametrics.com/guides/k8s-ha-monitoring-via-vm-cluster/).
