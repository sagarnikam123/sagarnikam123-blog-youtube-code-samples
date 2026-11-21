# VictoriaMetrics stack — Helm standalone

The official `victoriametrics-k8s-stack` chart installs the operator, Grafana, and a single-node metrics/logs/traces topology when enabled in values.

```bash
helm repo add vm https://victoriametrics.github.io/helm-charts
helm repo update
helm upgrade --install vmks vm/victoriametrics-k8s-stack \
  --namespace victoria-metrics --create-namespace \
  --values values.yaml
kubectl -n victoria-metrics get pods
```

Use this for local validation or a single-node Kubernetes environment.

Official chart documentation: [VictoriaMetrics K8s Stack](https://docs.victoriametrics.com/helm/victoriametrics-k8s-stack).
