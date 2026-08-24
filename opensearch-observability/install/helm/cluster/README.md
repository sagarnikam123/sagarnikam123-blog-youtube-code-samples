# OpenSearch Observability — Helm cluster

Install the official Observability Stack umbrella chart with the default distributed topology, then tune OpenSearch, Data Prepper, OTel Collector, and persistence for the target workload.

```bash
git clone https://github.com/opensearch-project/observability-stack.git
cd observability-stack
helm install obs charts/observability-stack \
  --namespace observability --create-namespace \
  --values /path/to/values.yaml
kubectl -n observability get pods
```

Do not use the single-node values from the standalone mode for production. Configure credentials through the chart's Kubernetes Secret flow.

Official guide: [Observability Stack on Kubernetes](https://observability.opensearch.org/docs/deploy/kubernetes/).
