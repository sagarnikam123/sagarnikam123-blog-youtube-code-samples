# Prometheus FAQ

Common questions and troubleshooting for Prometheus on Kubernetes.

## How to find the number of targets Prometheus is scraping?

### Method 1: Using kubectl exec

```bash
# Get total count of active targets
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | jq '.data.activeTargets | length'

# Get targets grouped by job
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets | group_by(.labels.job) | .[] | "\(.[0].labels.job): \(length)"'
```

### Method 2: Using port-forward

```bash
# Port-forward to Prometheus
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-prometheus 9090:9090 &

# Query targets API
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'

# Or open in browser
open http://localhost:9090/targets
```

### Method 3: Using PromQL

```bash
# Query via API
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=count(up)' 2>/dev/null | jq '.data.result[0].value[1]'
```

Or run in Prometheus UI: `count(up)`

## How to check which targets are down?

```bash
# List unhealthy targets
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets[] | select(.health != "up") | "\(.labels.job) - \(.labels.instance): \(.health)"'
```

Or run in Prometheus UI: `up == 0`

## How to check Prometheus resource usage?

```bash
# CPU and Memory
kubectl top pod -n prometheus -l app.kubernetes.io/name=prometheus

# Storage usage
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  df -h /prometheus

# Active time series
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_tsdb_head_series' 2>/dev/null | \
  jq '.data.result[0].value[1]'
```

## How to check scrape duration?

```bash
# Average scrape duration by job
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=scrape_duration_seconds' 2>/dev/null | \
  jq -r '.data.result[] | "\(.metric.job): \(.value[1])s"'
```

## How to list all ServiceMonitors?

```bash
# List all ServiceMonitors in the cluster
kubectl get servicemonitors -A

# List ServiceMonitors in prometheus namespace
kubectl get servicemonitors -n prometheus

# View details of a specific ServiceMonitor
kubectl get servicemonitor -n prometheus prometheus-kube-prometheus-prometheus -o yaml
```

## How to reload Prometheus configuration?

```bash
# Trigger config reload via API
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget --post-data='' -qO- http://localhost:9090/-/reload

# Or kill the config-reloader sidecar (it will restart and reload)
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c config-reloader -- kill -HUP 1
```

## How to check Prometheus logs?

```bash
# Prometheus server logs
kubectl logs -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus --tail=100

# Config reloader logs
kubectl logs -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c config-reloader --tail=100

# Prometheus operator logs
kubectl logs -n prometheus -l app.kubernetes.io/name=prometheus-operator --tail=100
```

## How to access Grafana?

```bash
# Port-forward
kubectl port-forward -n prometheus svc/prometheus-grafana 3000:80

# Get credentials
echo "Username: admin"
echo "Password: $(kubectl get secret -n prometheus prometheus-grafana -o jsonpath='{.data.admin-password}' | base64 --decode)"

# Open browser
open http://localhost:3000
```

## How to check PVC status?

```bash
# List PVCs
kubectl get pvc -n prometheus

# Describe PVC for details
kubectl describe pvc prometheus-prometheus-kube-prometheus-prometheus-db-prometheus-prometheus-kube-prometheus-prometheus-0 -n prometheus
```

## How to check why pods are not scheduling?

```bash
# Describe pod for events
kubectl describe pod -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 | grep -A20 Events

# Check node taints
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# Check pod tolerations
kubectl get pod -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -o jsonpath='{.spec.tolerations}' | jq
```


## How to check Prometheus version?

```bash
# Via Prometheus API
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/buildinfo' 2>/dev/null | jq -r '.data.version'

# Via container image
kubectl get pod prometheus-prometheus-kube-prometheus-prometheus-0 -n prometheus \
  -o jsonpath='{.spec.containers[?(@.name=="prometheus")].image}' | cut -d: -f2
```

## How to check Prometheus retention?

```bash
# Check CRD
kubectl get prometheus prometheus-kube-prometheus-prometheus -n prometheus -o jsonpath='{.spec.retention}'

# Check from API
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/flags' 2>/dev/null | \
  jq -r '.data["storage.tsdb.retention.time"]'

# Change retention
kubectl patch prometheus prometheus-kube-prometheus-prometheus -n prometheus \
  --type=merge -p '{"spec":{"retention":"7d"}}'
```

### Common Retention Values

| Use Case | Retention |
|----------|-----------|
| Stateless Forwarder | `2h` |
| Development | `3d` - `7d` |
| Default | `15d` |
| Production | `15d` - `30d` |

## How to check and modify Prometheus resources?

### Check Actual Resource Usage
```bash
# Memory and CPU from kubectl top
kubectl top pod prometheus-prometheus-kube-prometheus-prometheus-0 -n prometheus --containers

# Memory RSS from metrics
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=process_resident_memory_bytes' 2>/dev/null | \
  jq -r '.data.result[0].value[1] | tonumber / 1024 / 1024 / 1024 | "Memory RSS: \(.) GB"'

# TSDB storage on disk
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_tsdb_storage_blocks_bytes' 2>/dev/null | \
  jq -r '.data.result[0].value[1] | tonumber / 1024 / 1024 / 1024 | "TSDB Storage: \(.) GB"'
```

### Check Configured Limits
```bash
kubectl get pod prometheus-prometheus-kube-prometheus-prometheus-0 -n prometheus \
  -o jsonpath='{.spec.containers[?(@.name=="prometheus")].resources}' | jq .
```

### Modify Resources
```bash
# Update limits only
kubectl patch prometheus prometheus-kube-prometheus-prometheus -n prometheus \
  --type=merge -p '{"spec":{"resources":{"limits":{"cpu":"4","memory":"8Gi"}}}}'

# Update both requests and limits
kubectl patch prometheus prometheus-kube-prometheus-prometheus -n prometheus \
  --type=merge -p '{
    "spec": {
      "resources": {
        "requests": {"cpu": "1", "memory": "2Gi"},
        "limits": {"cpu": "2", "memory": "4Gi"}
      }
    }
  }'
```

### Resource Sizing Guidelines

#### Memory Sizing (Primary Factor)

Memory is the most critical resource for Prometheus. The rule of thumb:

| Active Series | Memory Request | Memory Limit | Notes |
|---------------|----------------|--------------|-------|
| < 100K | 512Mi | 1Gi | Small dev/test |
| 100K - 500K | 1Gi | 2Gi | Small production |
| 500K - 1M | 2Gi | 4Gi | Medium production |
| 1M - 3M | 4Gi | 8Gi | Large production |
| 3M - 5M | 8Gi | 16Gi | Very large |
| 5M - 10M | 16Gi | 32Gi | Enterprise |
| 10M+ | 32Gi+ | 64Gi+ | Consider sharding |

**Formula**: `Memory ≈ Active Series × 2-4 KB` (varies by label cardinality)

#### CPU Sizing

CPU scales with scrape targets and query load:

| Scrape Targets | Scrape Interval | CPU Request | CPU Limit |
|----------------|-----------------|-------------|-----------|
| < 100 | 30s | 100m | 500m |
| 100 - 500 | 30s | 250m | 1 |
| 500 - 1000 | 30s | 500m | 2 |
| 1000 - 2000 | 30s | 1 | 4 |
| 2000+ | 30s | 2+ | 4+ |

**Note**: Heavy query workloads (dashboards, alerts) may require 2-3x more CPU.

#### Storage Sizing

Storage depends on retention, series count, and sample rate:

| Active Series | Retention | Estimated Storage |
|---------------|-----------|-------------------|
| 100K | 15d | 5-10 GB |
| 500K | 15d | 25-50 GB |
| 1M | 15d | 50-100 GB |
| 1M | 30d | 100-200 GB |
| 5M | 15d | 250-500 GB |
| 5M | 30d | 500GB - 1TB |

**Formula**: `Storage ≈ Active Series × Retention Days × 1-2 bytes/sample × samples/day`

#### Remote Write Overhead

When using remote_write to Mimir/Cortex/Thanos:

| Factor | Additional Resources |
|--------|---------------------|
| Memory | +10-20% for WAL and queue |
| CPU | +10-30% for encoding/sending |
| Network | ~1-2 KB/sample (compressed) |

#### Quick Sizing Examples

| Environment | Series | Targets | Retention | CPU | Memory | Storage |
|-------------|--------|---------|-----------|-----|--------|---------|
| Dev/Test | 50K | 50 | 3d | 200m/500m | 512Mi/1Gi | 10Gi |
| Small Prod | 200K | 100 | 15d | 500m/1 | 2Gi/4Gi | 50Gi |
| Medium Prod | 1M | 500 | 15d | 1/2 | 4Gi/8Gi | 100Gi |
| Large Prod | 5M | 1000 | 30d | 2/4 | 16Gi/32Gi | 500Gi |
| Enterprise | 10M+ | 2000+ | 30d | 4/8 | 32Gi/64Gi | 1Ti+ |

#### Monitoring Your Sizing

Use these metrics to validate sizing:

```bash
# Check if memory is sufficient
prometheus_tsdb_head_series  # Should be stable, not growing unbounded
process_resident_memory_bytes / container_spec_memory_limit_bytes  # Should be < 80%

# Check if CPU is sufficient
rate(process_cpu_seconds_total[5m])  # Compare to limits
prometheus_engine_query_duration_seconds  # Query latency

# Check storage
prometheus_tsdb_storage_blocks_bytes  # Current disk usage
predict_linear(prometheus_tsdb_storage_blocks_bytes[7d], 30*24*3600)  # 30-day projection
```

#### When to Scale

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| OOMKilled | Memory too low | Increase memory limit |
| High query latency | CPU or memory | Increase both |
| WAL corruption | Disk too slow | Use faster storage (SSD) |
| Scrape timeouts | CPU or network | Increase CPU, check network |
| Remote write lag | CPU or shards | Increase CPU, adjust shards |

## How to check scrape targets and jobs?

```bash
# List all scrape jobs
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets | group_by(.scrapePool) | .[] | .[0].scrapePool' | sort

# Count targets per job
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets | group_by(.scrapePool) | .[] | "\(.[0].scrapePool): \(length)"'

# View full scrape config
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/config' 2>/dev/null | jq -r '.data.yaml' | head -100
```

## How to check if remote_write is enabled?

```bash
# Check the Prometheus config directly
kubectl exec -it prometheus-prometheus-kube-prometheus-prometheus-0 -n prometheus -c prometheus -- \
  cat /etc/prometheus/config_out/prometheus.env.yaml | grep -A 20 "remote_write"

# Via Prometheus API
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/config' 2>/dev/null | jq '.data.yaml' | grep -A 10 "remote_write"

# Check the Prometheus CR
kubectl get prometheus prometheus-kube-prometheus-prometheus -n prometheus -o yaml | grep -A 30 "remoteWrite"
```

## How to verify remote_write is working?

```bash
# Total samples sent
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_total' 2>/dev/null | \
  jq -r '.data.result[] | "\(.metric.remote_name // "default"): \(.value[1]) samples"'

# Failed samples (should be 0)
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_failed_total' 2>/dev/null | \
  jq -r '.data.result[] | "Failed: \(.value[1])"'

# Pending samples (queue backlog)
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_pending' 2>/dev/null | \
  jq -r '.data.result[] | "Pending: \(.value[1])"'

# Current shards
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_shards' 2>/dev/null | \
  jq -r '.data.result[] | "Shards: \(.value[1])"'

# Calculate remote write lag
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=time()-prometheus_remote_storage_queue_highest_sent_timestamp_seconds' 2>/dev/null | \
  jq -r '.data.result[] | "Lag: \(.value[1]) seconds"'
```

## How to analyze cardinality (high series count)?

### Quick Summary
```bash
PROM_POD="prometheus-prometheus-kube-prometheus-prometheus-0"

# Total active series
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=sum(prometheus_tsdb_head_series)' 2>/dev/null | \
  jq -r '"Total Active Series: \(.data.result[0].value[1])"'

# Top 20 metrics by series count
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=topk(20,count%20by%20(__name__)(%7B__name__%21%3D%22%22%7D))' 2>/dev/null | \
  jq -r '.data.result[] | "\(.metric.__name__): \(.value[1])"'

# Series by namespace (top 10)
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=count%20by%20(namespace)({namespace=~".%2B"})' 2>/dev/null | \
  jq -r '.data.result | sort_by(.value[1] | tonumber) | reverse | .[:10][] | "\(.metric.namespace): \(.value[1])"'

# Series by job (top 10)
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=count%20by%20(job)({job=~".%2B"})' 2>/dev/null | \
  jq -r '.data.result | sort_by(.value[1] | tonumber) | reverse | .[:10][] | "\(.metric.job): \(.value[1])"'

# Histogram bucket count (often high cardinality)
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=count({__name__=~".*_bucket"})' 2>/dev/null | \
  jq -r '"Histogram buckets: \(.data.result[0].value[1])"'
```

### Common High-Cardinality Culprits

| Pattern | Issue | Solution |
|---------|-------|----------|
| `*_bucket` | Many histogram buckets | Use summaries or recording rules |
| `*_by_path` | Unique URL paths | Aggregate by pattern |
| `container_*` | Pod churn | Filter by namespace |
| `*_by_id` | Unique IDs | Use labeldrop |

## How to exclude services from scraping?

### Method 1: Delete ServiceMonitor (quick, temporary)

```bash
# List ServiceMonitors
kubectl get servicemonitors -n prometheus

# Delete specific one
kubectl delete servicemonitor <name> -n prometheus
```

**Note:** Recreated on next `helm upgrade`

### Method 2: Disable via Helm values (permanent)

See [README.md - Disable ServiceMonitors](../install/helm/kube-prometheus-stack/README.md#disable-servicemonitors) for Helm configuration.

### Method 3: Use relabelings to drop targets

Drop specific services or namespaces using relabel configs:

```yaml
prometheus:
  prometheusSpec:
    additionalScrapeConfigs:
      - job_name: 'my-job'
        relabel_configs:
          # Drop specific service by name
          - source_labels: [__meta_kubernetes_service_name]
            regex: 'my-service-to-exclude'
            action: drop
          # Drop by namespace
          - source_labels: [__meta_kubernetes_namespace]
            regex: 'kube-system|logging|monitoring'
            action: drop
```

### Method 4: Use ServiceMonitor selectors (recommended for multi-team)

```yaml
prometheus:
  prometheusSpec:
    serviceMonitorSelector:
      matchLabels:
        prometheus: main
    serviceMonitorNamespaceSelector: {}
```

Then label ServiceMonitors you want scraped:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  labels:
    prometheus: main  # Will be scraped
```

### Method 5: Use annotation on Service

```yaml
# Service with skip annotation
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    prometheus.io/scrape: "false"
```

### Quick Reference: What to use when

| Scenario | Method |
|----------|--------|
| Disable built-in K8s components | Helm values |
| Disable stack components | Helm values |
| Exclude specific namespace | Relabel config |
| Multi-team setup | ServiceMonitor selectors |
| App-level control | Service annotation |
| Quick testing | Delete ServiceMonitor |

## How to enable exemplars?

Exemplars link metrics to traces, enabling correlation between Prometheus metrics and distributed tracing systems (Jaeger, Tempo, etc.).

### Enable via Helm values

```yaml
# values.yaml
prometheus:
  prometheusSpec:
    enableFeatures:
      - exemplar-storage        # Store exemplars in TSDB
    exemplars:
      maxSize: 100000           # Max exemplars to store (default: 100000)
```

### Enable via kubectl patch

```bash
kubectl patch prometheus prometheus-kube-prometheus-prometheus -n prometheus \
  --type=merge -p '{
    "spec": {
      "enableFeatures": ["exemplar-storage"],
      "exemplars": {"maxSize": 100000}
    }
  }'
```

### Verify exemplars are enabled

```bash
# Check feature flags
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/flags' 2>/dev/null | jq '.data["enable-feature"]'

# Query exemplars API
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query_exemplars?query=http_request_duration_seconds_bucket&start=2024-01-01T00:00:00Z&end=2024-12-31T23:59:59Z' 2>/dev/null | jq .
```

### Requirements for exemplars to work

1. **Application must expose exemplars** - Use OpenTelemetry SDK or Prometheus client libraries that support exemplars
2. **Metrics must be histograms or counters** - Exemplars attach to these metric types
3. **Include trace_id label** - Exemplars typically contain `trace_id` for linking to traces

### Example: Go application with exemplars

```go
import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var httpDuration = promauto.NewHistogramVec(
    prometheus.HistogramOpts{
        Name: "http_request_duration_seconds",
        Help: "HTTP request duration with exemplars",
    },
    []string{"method", "path"},
)

// Record with exemplar
httpDuration.WithLabelValues("GET", "/api").
    (prometheus.ExemplarObserver).ObserveWithExemplar(
        duration.Seconds(),
        prometheus.Labels{"trace_id": traceID},
    )
```

### Query exemplars in Grafana

1. Add Prometheus datasource with exemplars enabled
2. In Explore, toggle "Exemplars" button
3. Click on exemplar dots to jump to trace

### Memory considerations

| maxSize | Memory (~) | Use Case |
|---------|------------|----------|
| 10000 | ~1MB | Low traffic |
| 100000 | ~10MB | Default |
| 500000 | ~50MB | High traffic |
| 1000000 | ~100MB | Very high traffic |

---

## Quick Reference - Common Commands

```bash
PROM_POD="prometheus-prometheus-kube-prometheus-prometheus-0"

# Active series
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=sum(prometheus_tsdb_head_series)' 2>/dev/null | \
  jq -r '.data.result[0].value[1]'

# Target count
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=count(up)' 2>/dev/null | \
  jq -r '.data.result[0].value[1]'

# Remote write rate (samples/sec)
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=sum(rate(prometheus_remote_storage_samples_total[30m]))' 2>/dev/null | \
  jq -r '.data.result[0].value[1]'

# Pending samples
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_pending' 2>/dev/null | \
  jq -r '.data.result[0].value[1]'

# Failed samples
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_failed_total' 2>/dev/null | \
  jq -r '.data.result[0].value[1]'

# List ServiceMonitors
kubectl get servicemonitors -n prometheus

# List scrape targets by job
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets | group_by(.scrapePool) | .[] | "\(.[0].scrapePool): \(length)"'
```


## How to get current Prometheus configuration?

```bash
# Get full config as YAML
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/config' 2>/dev/null | jq -r '.data.yaml'

# Save config to file
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/config' 2>/dev/null | jq -r '.data.yaml' > prometheus-config.yaml

# Get specific sections
# Remote write config
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/config' 2>/dev/null | jq -r '.data.yaml' | grep -A 30 "remote_write:"

# Scrape configs
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/config' 2>/dev/null | jq -r '.data.yaml' | grep -A 10 "scrape_configs:"

# Get runtime flags
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/flags' 2>/dev/null | jq '.data'
```
