# OpenSearch Observability — Helm standalone

The official Observability Stack umbrella chart installs OpenSearch, OpenSearch Dashboards, Data Prepper, OTel Collector, and Prometheus.

```bash
git clone https://github.com/opensearch-project/observability-stack.git
cd observability-stack
helm install obs charts/observability-stack \
  --namespace observability --create-namespace \
  --values /path/to/values.yaml
kubectl -n observability get pods
```

For local kind-style validation, set one OpenSearch replica, small JVM/resource limits, and a small persistence volume in `values.yaml`.

Official guide: [Observability Stack on Kubernetes](https://observability.opensearch.org/docs/deploy/kubernetes/).
