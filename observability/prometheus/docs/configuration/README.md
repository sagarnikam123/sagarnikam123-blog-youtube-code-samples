# Prometheus Configuration Guide

This guide covers scrape configuration for various targets including custom applications, infrastructure exporters, Kubernetes service discovery, and observability stack components.

## Overview

Prometheus collects metrics by scraping HTTP endpoints. Configuration defines:
- **What** to scrape (targets)
- **How** to scrape (intervals, timeouts, authentication)
- **How** to process (relabeling, filtering)

## Configuration Methods

| Method | Use Case | Documentation |
|--------|----------|---------------|
| Static Config | Known, fixed targets | [Custom Metrics Guide](./custom-metrics.md) |
| File SD | Dynamic targets from files | [Custom Metrics Guide](./custom-metrics.md) |
| Kubernetes SD | Auto-discover K8s workloads | [Kubernetes Discovery](./kubernetes-discovery.md) |
| ServiceMonitor | K8s with Prometheus Operator | [Kubernetes Discovery](./kubernetes-discovery.md) |

## Quick Reference

### Static Target

```yaml
scrape_configs:
  - job_name: 'my-app'
    static_configs:
      - targets: ['app1:8080', 'app2:8080']
```

### Kubernetes Pod Discovery

```yaml
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### ServiceMonitor (Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
spec:
  selector:
    matchLabels:
      app: my-app
  endpoints:
    - port: metrics
```

## Configuration Files

This repository provides ready-to-use configurations:

```
conf/
├── scrape-configs/
│   ├── static/              # Static target configs
│   │   └── custom-apps.yml
│   ├── file-sd/             # File-based discovery
│   │   └── targets.json
│   ├── kubernetes/          # K8s service discovery
│   │   ├── pods.yml
│   │   └── services.yml
│   ├── exporters/           # Infrastructure exporters
│   │   ├── node-exporter.yml
│   │   ├── kube-state-metrics.yml
│   │   └── ...
│   └── observability/       # Observability stack
│       ├── grafana.yml
│       ├── mimir.yml
│       └── ...
├── servicemonitors/         # K8s ServiceMonitor CRDs
│   ├── exporters/
│   └── observability/
└── podmonitors/             # K8s PodMonitor CRDs
```

## Documentation Index

| Document | Description |
|----------|-------------|
| [Kubernetes Discovery](./kubernetes-discovery.md) | Auto-discover K8s pods and services |
| [Custom Metrics](./custom-metrics.md) | Scrape custom application metrics |
| [Exporters Guide](./exporters.md) | Infrastructure exporter configurations |
| [Observability Stack](./observability-stack.md) | Grafana, Mimir, Loki, etc. |

## Common Configuration Patterns

### Scrape Interval

```yaml
global:
  scrape_interval: 15s      # Default for all jobs
  scrape_timeout: 10s       # Must be <= scrape_interval

scrape_configs:
  - job_name: 'fast-metrics'
    scrape_interval: 5s     # Override for this job

  - job_name: 'slow-metrics'
    scrape_interval: 60s
```

### Authentication

```yaml
scrape_configs:
  - job_name: 'authenticated'
    basic_auth:
      username: prometheus
      password_file: /etc/prometheus/secrets/password

  - job_name: 'bearer-token'
    bearer_token_file: /etc/prometheus/secrets/token
```

### TLS Configuration

```yaml
scrape_configs:
  - job_name: 'https-target'
    scheme: https
    tls_config:
      ca_file: /etc/prometheus/certs/ca.crt
      cert_file: /etc/prometheus/certs/client.crt
      key_file: /etc/prometheus/certs/client.key
```

### Relabeling

```yaml
relabel_configs:
  # Keep only targets with specific label
  - source_labels: [__meta_kubernetes_pod_label_app]
    action: keep
    regex: my-app

  # Add custom label
  - target_label: environment
    replacement: production

  # Extract value from existing label
  - source_labels: [__address__]
    target_label: instance
    regex: '([^:]+):\d+'
    replacement: '${1}'
```

### Metric Filtering

```yaml
metric_relabel_configs:
  # Drop unwanted metrics
  - source_labels: [__name__]
    regex: 'go_gc_.*'
    action: drop

  # Keep only specific metrics
  - source_labels: [__name__]
    regex: 'http_requests_total|http_request_duration_.*'
    action: keep
```

## Validate Configuration

Always validate before applying:

```bash
# Using promtool
promtool check config prometheus.yml

# Docker
docker run --rm -v $(pwd):/config prom/prometheus \
  promtool check config /config/prometheus.yml
```

## Apply Configuration

### Binary/Docker

```bash
# Reload via API (if --web.enable-lifecycle is set)
curl -X POST http://localhost:9090/-/reload

# Or send SIGHUP
kill -HUP $(pgrep prometheus)
```

### Kubernetes (Helm)

```bash
# Update ConfigMap and restart
kubectl create configmap prometheus-config \
  --from-file=prometheus.yml -n monitoring --dry-run=client -o yaml | \
  kubectl apply -f -

# Prometheus Operator auto-reloads on ConfigMap changes
```

### Kubernetes (Operator)

ServiceMonitors and PodMonitors are automatically discovered:

```bash
kubectl apply -f servicemonitor.yaml
# Prometheus discovers new targets within ~30 seconds
```

## Best Practices

1. **Use meaningful job names** - They appear in metrics and alerts
2. **Set appropriate intervals** - Balance freshness vs load
3. **Add labels** - Environment, team, service for filtering
4. **Filter metrics** - Drop high-cardinality or unused metrics
5. **Use relabeling** - Normalize labels across targets
6. **Validate configs** - Always test before applying
7. **Document custom configs** - Future you will thank you

## Next Steps

1. [Configure Kubernetes discovery](./kubernetes-discovery.md)
2. [Set up custom application metrics](./custom-metrics.md)
3. [Configure infrastructure exporters](./exporters.md)
4. [Monitor observability stack](./observability-stack.md)
