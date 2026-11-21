# Kubernetes Service Discovery Guide

Configure Prometheus to automatically discover and scrape Kubernetes workloads.

## Overview

Prometheus supports native Kubernetes service discovery through `kubernetes_sd_config`. This enables automatic discovery of:
- Pods
- Services
- Endpoints
- Nodes
- Ingresses

## Discovery Methods

| Method | Use Case | Configuration |
|--------|----------|---------------|
| Pod Annotations | Any pod with annotations | `kubernetes_sd_config` + relabeling |
| ServiceMonitor | Prometheus Operator | CRD-based |
| PodMonitor | Direct pod scraping | CRD-based |
| Service Discovery | Service **Use annotations** for simple cases without Operator
3. **Filter namespaces** to reduce discovery load
4. **Add meaningful labels** for filtering and grouping
5. **Set appropriate intervals** based on metric importance
6. **Use relabeling** to normalize labels across services
7. **Drop unnecessary metrics** to reduce storage

## Next Steps

1. [Configure custom application metrics](./custom-metrics.md)
2. [Set up infrastructure exporters](./exporters.md)
3. [Monitor observability stack](./observability-stack.md)


# Check ServiceAccount
kubectl get serviceaccount prometheus -n monitoring
```

## Configuration Files

Pre-built configurations are available:

| File | Description |
|------|-------------|
| `conf/scrape-configs/kubernetes/pods.yml` | Pod annotation discovery |
| `conf/scrape-configs/kubernetes/services.yml` | Service discovery |
| `conf/servicemonitors/` | ServiceMonitor examples |
| `conf/podmonitors/` | PodMonitor examples |

## Best Practices

1. **Use ServiceMonitors** when using Prometheus Operator
2. t labels
kubectl get svc -l app=my-app

# Check endpoints exist
kubectl get endpoints my-app
```

### Scrape Errors

```bash
# Check target status in Prometheus UI
# http://localhost:9090/targets

# Common errors:
# - "connection refused" - Pod not running or wrong port
# - "context deadline exceeded" - Timeout, increase scrape_timeout
# - "server returned HTTP status 404" - Wrong path
```

### RBAC Issues

```bash
# Test permissions
kubectl auth can-i list pods --as=system:serviceaccount:monitoring:prometheusoups: [""]
    resources:
      - configmaps
    verbs: ["get"]
  - apiGroups: ["networking.k8s.io"]
    resources:
      - ingresses
    verbs: ["get", "list", "watch"]
  - nonResourceURLs: ["/metrics"]
    verbs: ["get"]
```

## Troubleshooting

### Targets Not Discovered

```bash
# Check ServiceMonitor labels match Prometheus selector
kubectl get prometheus -n monitoring -o yaml | grep -A10 serviceMonitorSelector

# Check ServiceMonitor exists
kubectl get servicemonitors -n monitoring

# Check service has correcMonitor Namespace Selection

```yaml
spec:
  namespaceSelector:
    # Specific namespaces
    matchNames:
      - production

    # Or all namespaces
    # any: true
```

## RBAC Requirements

Prometheus needs permissions to discover resources:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources:
      - nodes
      - nodes/metrics
      - services
      - endpoints
      - pods
    verbs: ["get", "list", "watch"]
  - apiGr:
  - role: service
```

### Endpoints Role

Discovers service endpoints:

```yaml
kubernetes_sd_configs:
  - role: endpoints
```

### Node Role

Discovers cluster nodes:

```yaml
kubernetes_sd_configs:
  - role: node
```

## Namespace Filtering

### Specific Namespaces

```yaml
kubernetes_sd_configs:
  - role: pod
    namespaces:
      names:
        - production
        - staging
```

### All Namespaces

```yaml
kubernetes_sd_configs:
  - role: pod
    # No namespaces filter = all namespaces
```

### Serviceovers all pods:

```yaml
kubernetes_sd_configs:
  - role: pod
```

Available labels:
- `__meta_kubernetes_pod_name`
- `__meta_kubernetes_pod_ip`
- `__meta_kubernetes_pod_label_<labelname>`
- `__meta_kubernetes_pod_annotation_<annotationname>`
- `__meta_kubernetes_namespace`
- `__meta_kubernetes_pod_node_name`
- `__meta_kubernetes_pod_container_name`
- `__meta_kubernetes_pod_container_port_name`
- `__meta_kubernetes_pod_container_port_number`

### Service Role

Discovers services:

```yaml
kubernetes_sd_configsegex: 'go_.*'
          action: drop
```

## PodMonitor

PodMonitors scrape pods directly without requiring a service.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: my-app-pods
  namespace: monitoring
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: my-app

  namespaceSelector:
    matchNames:
      - default

  podMetricsEndpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

## Service Discovery Roles

### Pod Role

Discy: password
```

#### With TLS

```yaml
spec:
  endpoints:
    - port: metrics
      scheme: https
      tlsConfig:
        insecureSkipVerify: true
        # Or use CA
        # ca:
        #   secret:
        #     name: my-app-tls
        #     key: ca.crt
```

#### Relabeling

```yaml
spec:
  endpoints:
    - port: metrics
      relabelings:
        - sourceLabels: [__meta_kubernetes_pod_label_version]
          targetLabel: version
      metricRelabelings:
        - sourceLabels: [__name__]
          rnitoring svc/prometheus-operated 9090:9090
# Visit http://localhost:9090/targets
```

### Common ServiceMonitor Patterns

#### Multiple Endpoints

```yaml
spec:
  endpoints:
    - port: http-metrics
      interval: 15s
    - port: grpc-metrics
      interval: 30s
      path: /grpc/metrics
```

#### With Authentication

```yaml
spec:
  endpoints:
    - port: metrics
      basicAuth:
        username:
          name: my-app-auth
          key: username
        password:
          name: my-app-auth
          ke```

### Service Requirements

Your service must have a named port:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  labels:
    app: my-app  # Must match ServiceMonitor selector
spec:
  ports:
    - name: metrics  # Must match ServiceMonitor endpoint port
      port: 8080
      targetPort: 8080
  selector:
    app: my-app
```

### Verify ServiceMonitor

```bash
# Check ServiceMonitor exists
kubectl get servicemonitors -n monitoring

# Check Prometheus discovered it
kubectl port-forward -n mo```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: monitoring
  labels:
    release: prometheus  # Must match Prometheus selector
spec:
  # Select services to monitor
  selector:
    matchLabels:
      app: my-app

  # Namespaces to search
  namespaceSelector:
    matchNames:
      - default
      - production

  # Scrape configuration
  endpoints:
    - port: metrics        # Service port name
      interval: 30s
      path: /metrics
      scheme: http
(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

      # Add namespace label
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: namespace

      # Add pod name label
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: pod
```

## ServiceMonitor (Prometheus Operator)

ServiceMonitors provide declarative scrape configuration for Kubernetes services.

### Create ServiceMonitor

"true"
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

      # Use prometheus.io/path annotation
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)

      # Use prometheus.io/port annotation
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)Default | Description |
|------------|---------|-------------|
| `prometheus.io/scrape` | - | Set to "true" to enable scraping |
| `prometheus.io/port` | Container port | Port to scrape |
| `prometheus.io/path` | `/metrics` | Metrics endpoint path |
| `prometheus.io/scheme` | `http` | `http` or `https` |

### Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod

    relabel_configs:
      # Only scrape pods with prometheus.io/scrape: endpoints | `kubernetes_sd_config` |

## Pod Annotation-Based Discovery

### Enable Scraping

Add annotations to your pod/deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: my-app
          ports:
            - containerPort: 8080
```

### Supported Annotations

| Annotation |
