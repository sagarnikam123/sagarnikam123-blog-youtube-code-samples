# Beyla — Helm chart (Kubernetes DaemonSet)

The official `grafana/beyla` Helm chart deploys Beyla as a DaemonSet that auto-instruments all services in your cluster.

## Install

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install beyla grafana/beyla \
  --namespace beyla --create-namespace \
  --values values.yaml
```

## Default behavior

- Exports Prometheus metrics on pod port 9090 at `/metrics`.
- Instruments all applications in the cluster.
- Application-level metrics only (network metrics disabled by default).
- Decorates metrics with Kubernetes metadata labels.

## Custom configuration

Create `values.yaml` to restrict instrumentation scope or enable OTLP export:

```yaml
config:
  data:
    discovery:
      instrument:
        - k8s_namespace: my-app
    otel_traces_export:
      endpoint: http://otel-collector.monitoring:4318
    otel_metrics_export:
      endpoint: http://otel-collector.monitoring:4318
```

Install with overrides:

```bash
helm install beyla grafana/beyla -f values.yaml --namespace beyla --create-namespace
```

## Notes

- Beyla pods run as `privileged` DaemonSet for eBPF access.
- Requires Linux nodes with kernel 5.8+ and BTF enabled.
- For Grafana Cloud integration, see the [Helm for Grafana Cloud guide](https://grafana.com/docs/beyla/latest/setup/kubernetes-helm-appolly/).
- For Alloy-bundled deployment, see [Helm Alloy guide](https://grafana.com/docs/beyla/latest/setup/helm-alloy/).

Official chart: [grafana/beyla Helm chart](https://grafana.com/docs/beyla/latest/setup/kubernetes-helm/).
