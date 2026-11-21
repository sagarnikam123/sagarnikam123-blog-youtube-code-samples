# Grafana Alloy - Metrics Collection for Mimir

Uses [Grafana Alloy](https://grafana.com/docs/alloy/latest/) (successor to Grafana Agent) to collect and send metrics to Mimir.

## What is Grafana Alloy?

Grafana Alloy is an OpenTelemetry Collector distribution with native Prometheus support:
- **Replaces**: Grafana Agent (deprecated)
- **Configuration**: River language (declarative, component-based)
- **Features**: Prometheus scraping, remote write, service discovery, clustering

## Quick Start

### 1. Install via Helm

```bash
# Add Grafana Helm repo
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Alloy
helm install alloy grafana/alloy \
  -n mimir-test \
  -f configs/alloy-mimir.yaml
```

### 2. Install via Kubernetes Manifest

```bash
kubectl apply -f kubernetes/alloy-deployment.yaml -n mimir-test
```

### 3. Install via Docker

```bash
docker run -d --name alloy \
  -v $(pwd)/configs/config.alloy:/etc/alloy/config.alloy \
  -p 12345:12345 \
  grafana/alloy:latest \
  run --server.http.listen-addr=0.0.0.0:12345 /etc/alloy/config.alloy
```

## Configuration (River Language)

### Basic Prometheus Scrape + Remote Write

```river
// Scrape Prometheus metrics
prometheus.scrape "default" {
  targets = [
    {"__address__" = "localhost:9090"},
  ]
  forward_to = [prometheus.remote_write.mimir.receiver]
}

// Remote write to Mimir
prometheus.remote_write "mimir" {
  endpoint {
    url = "http://mimir-gateway.mimir-test.svc.cluster.local/api/v1/push"

    headers = {
      "X-Scope-OrgID" = "demo",
    }

    queue_config {
      capacity             = 10000
      max_shards           = 10
      min_shards           = 1
      max_samples_per_send = 2000
      batch_send_deadline  = "5s"
    }
  }
}
```

### Multi-Tenant Configuration

```river
// Tenant 1
prometheus.scrape "tenant1" {
  targets = [
    {"__address__" = "app1:8080"},
  ]
  forward_to = [prometheus.remote_write.tenant1.receiver]
}

prometheus.remote_write "tenant1" {
  endpoint {
    url = "http://mimir-gateway/api/v1/push"
    headers = {
      "X-Scope-OrgID" = "tenant-1",
    }
  }
}

// Tenant 2
prometheus.scrape "tenant2" {
  targets = [
    {"__address__" = "app2:8080"},
  ]
  forward_to = [prometheus.remote_write.tenant2.receiver]
}

prometheus.remote_write "tenant2" {
  endpoint {
    url = "http://mimir-gateway/api/v1/push"
    headers = {
      "X-Scope-OrgID" = "tenant-2",
    }
  }
}
```

### Kubernetes Service Discovery

```river
// Discover pods with prometheus.io/scrape annotation
discovery.kubernetes "pods" {
  role = "pod"
}

// Relabel discovered targets
discovery.relabel "kubernetes" {
  targets = discovery.kubernetes.pods.targets

  rule {
    source_labels = ["__meta_kubernetes_pod_annotation_prometheus_io_scrape"]
    action        = "keep"
    regex         = "true"
  }

  rule {
    source_labels = ["__meta_kubernetes_pod_annotation_prometheus_io_path"]
    target_label  = "__metrics_path__"
    regex         = "(.+)"
  }

  rule {
    source_labels = ["__address__", "__meta_kubernetes_pod_annotation_prometheus_io_port"]
    target_label  = "__address__"
    regex         = "([^:]+)(?::\\d+)?;(\\d+)"
    replacement   = "$1:$2"
  }
}

prometheus.scrape "kubernetes" {
  targets    = discovery.relabel.kubernetes.output
  forward_to = [prometheus.remote_write.mimir.receiver]
}

prometheus.remote_write "mimir" {
  endpoint {
    url = "http://mimir-gateway/api/v1/push"
    headers = {
      "X-Scope-OrgID" = "k8s-cluster",
    }
  }
}
```

### Load Testing Configuration

```river
// Scrape Avalanche metric generator
prometheus.scrape "avalanche" {
  targets = [
    {"__address__" = "avalanche:9001"},
  ]
  scrape_interval = "15s"
  forward_to      = [prometheus.remote_write.mimir.receiver]
}

// Scrape node-exporter
prometheus.scrape "node_exporter" {
  targets = [
    {"__address__" = "node-exporter-1:9100"},
    {"__address__" = "node-exporter-2:9100"},
    {"__address__" = "node-exporter-3:9100"},
  ]
  scrape_interval = "30s"
  forward_to      = [prometheus.remote_write.mimir.receiver]
}

// Remote write with high throughput settings
prometheus.remote_write "mimir" {
  endpoint {
    url = "http://mimir-gateway/api/v1/push"

    headers = {
      "X-Scope-OrgID" = "load-test",
    }

    queue_config {
      capacity             = 50000
      max_shards           = 50
      min_shards           = 5
      max_samples_per_send = 5000
      batch_send_deadline  = "3s"
    }
  }
}
```

## Key Components

| Component | Purpose |
|-----------|---------|
| `prometheus.scrape` | Scrape Prometheus metrics |
| `prometheus.remote_write` | Send metrics to remote endpoint |
| `discovery.kubernetes` | Kubernetes service discovery |
| `discovery.relabel` | Relabel discovered targets |
| `prometheus.relabel` | Relabel scraped metrics |

## Monitoring Alloy

```bash
# Alloy UI (metrics, config, targets)
kubectl port-forward -n mimir-test svc/alloy 12345:12345
# Open: http://localhost:12345

# Check targets
curl http://localhost:12345/api/v0/web/targets

# Check metrics
curl http://localhost:12345/metrics
```

## Migration from Grafana Agent

| Grafana Agent (YAML) | Grafana Alloy (River) |
|----------------------|------------------------|
| `prometheus_config` | `prometheus.scrape` |
| `remote_write` | `prometheus.remote_write` |
| `scrape_configs` | `prometheus.scrape` blocks |
| `relabel_configs` | `discovery.relabel` / `prometheus.relabel` |

## Useful Commands

```bash
# Validate config
alloy fmt config.alloy

# Run with config
alloy run config.alloy

# Check component health
curl http://localhost:12345/api/v0/web/components
```

## Resources

- [Alloy Documentation](https://grafana.com/docs/alloy/latest/)
- [River Language](https://grafana.com/docs/alloy/latest/reference/config-blocks/)
- [Migration Guide](https://grafana.com/docs/alloy/latest/set-up/migrate/from-agent/)
