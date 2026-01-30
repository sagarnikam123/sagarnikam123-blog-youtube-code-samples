# Prometheus FAQ

Common questions and troubleshooting for Prometheus on Kubernetes.

## Table of Contents

1. [Getting Started](#getting-started)
   - [How to check Prometheus version?](#how-to-check-prometheus-version)
   - [How to get current Prometheus configuration?](#how-to-get-current-prometheus-configuration)
   - [How to check Prometheus logs?](#how-to-check-prometheus-logs)
   - [How to reload Prometheus configuration?](#how-to-reload-prometheus-configuration)

2. [Targets & Scraping](#targets--scraping)
   - [How to find the number of targets?](#how-to-find-the-number-of-targets-prometheus-is-scraping)
   - [How to check which targets are down?](#how-to-check-which-targets-are-down)
   - [How to check scrape duration?](#how-to-check-scrape-duration)
   - [How to list all ServiceMonitors?](#how-to-list-all-servicemonitors)
   - [How to enable ServiceMonitor for a namespace?](#how-to-enable-servicemonitor-for-a-namespace)
   - [How to enable PodMonitor for a namespace?](#how-to-enable-podmonitor-for-a-namespace)
   - [ServiceMonitor vs PodMonitor - When to use which?](#servicemonitor-vs-podmonitor---when-to-use-which)
   - [How to exclude namespaces/services from scraping?](#how-to-exclude-namespacesservices-from-scraping)

3. [Resources & Sizing](#resources--sizing)
   - [How to check Prometheus resource usage?](#how-to-check-prometheus-resource-usage)
   - [How to check and modify Prometheus resources?](#how-to-check-and-modify-prometheus-resources)
   - [Prometheus Sizing Guidelines](#resource-sizing-guidelines)
   - [Alertmanager Sizing Guidelines](#alertmanager-sizing-guidelines)
   - [Grafana Sizing Guidelines](#grafana-sizing-guidelines)
   - [Complete Stack Sizing Examples](#complete-stack-sizing-examples)

4. [Storage](#storage)
   - [How to check PVC status?](#how-to-check-pvc-status)
   - [How to setup EKS storage (gp3)?](#how-to-setup-eks-storage-gp3-storageclass)
   - [How to check Prometheus retention?](#how-to-check-prometheus-retention)

5. [Remote Write](#remote-write)
   - [How to check if remote_write is enabled?](#how-to-check-if-remote_write-is-enabled)
   - [How to verify remote_write is working?](#how-to-verify-remote_write-is-working)

6. [Cardinality & Performance](#cardinality--performance)
   - [How to analyze cardinality?](#how-to-analyze-cardinality-high-series-count)

7. [Advanced Features](#advanced-features)
   - [How to enable exemplars?](#how-to-enable-exemplars)

8. [Troubleshooting](#troubleshooting)
   - [How to troubleshoot external URL not accessible?](#how-to-troubleshoot-external-url-not-accessible)
   - [How to check why pods are not scheduling?](#how-to-check-why-pods-are-not-scheduling)
   - [How to access Grafana?](#how-to-access-grafana)

9. [Quick Reference](#quick-reference---common-commands)

---

## Getting Started

### How to check Prometheus version?

```bash
# Via Prometheus API
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/buildinfo' 2>/dev/null | jq -r '.data.version'

# Via container image
kubectl get pod prometheus-prometheus-kube-prometheus-prometheus-0 -n prometheus \
  -o jsonpath='{.spec.containers[?(@.name=="prometheus")].image}' | cut -d: -f2
```

### How to get current Prometheus configuration?

```bash
# Get full config as YAML
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/config' 2>/dev/null | jq -r '.data.yaml'

# Save config to file
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/config' 2>/dev/null | jq -r '.data.yaml' > prometheus-config.yaml

# Get remote write config
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/config' 2>/dev/null | jq -r '.data.yaml' | grep -A 30 "remote_write:"

# Get runtime flags
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/flags' 2>/dev/null | jq '.data'
```

### How to check Prometheus logs?

```bash
# Prometheus server logs
kubectl logs -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus --tail=100

# Config reloader logs
kubectl logs -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c config-reloader --tail=100

# Prometheus operator logs
kubectl logs -n prometheus -l app.kubernetes.io/name=prometheus-operator --tail=100
```

### How to reload Prometheus configuration?

```bash
# Trigger config reload via API
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget --post-data='' -qO- http://localhost:9090/-/reload

# Or kill the config-reloader sidecar (it will restart and reload)
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c config-reloader -- kill -HUP 1
```

---

## Targets & Scraping

### How to find the number of targets Prometheus is scraping?

#### Method 1: Using kubectl exec

```bash
# Get total count of active targets
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | jq '.data.activeTargets | length'

# Get targets grouped by job
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets | group_by(.labels.job) | .[] | "\(.[0].labels.job): \(length)"'
```

#### Method 2: Using port-forward

```bash
# Port-forward to Prometheus
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-prometheus 9090:9090 &

# Query targets API
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'

# Or open in browser
open http://localhost:9090/targets
```

#### Method 3: Using PromQL

```bash
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=count(up)' 2>/dev/null | jq '.data.result[0].value[1]'
```

Or run in Prometheus UI: `count(up)`

### How to check which targets are down?

```bash
# List unhealthy targets
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets[] | select(.health != "up") | "\(.labels.job) - \(.labels.instance): \(.health)"'
```

Or run in Prometheus UI: `up == 0`

### How to check scrape duration?

```bash
# Average scrape duration by job
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=scrape_duration_seconds' 2>/dev/null | \
  jq -r '.data.result[] | "\(.metric.job): \(.value[1])s"'
```

### How to list all ServiceMonitors?

```bash
# List all ServiceMonitors in the cluster
kubectl get servicemonitors -A

# List ServiceMonitors in prometheus namespace
kubectl get servicemonitors -n prometheus

# View details of a specific ServiceMonitor
kubectl get servicemonitor -n prometheus prometheus-kube-prometheus-prometheus -o yaml

# List all scrape jobs
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets | group_by(.scrapePool) | .[] | .[0].scrapePool' | sort

# Count targets per job
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets | group_by(.scrapePool) | .[] | "\(.[0].scrapePool): \(length)"'
```

### How to enable ServiceMonitor for a namespace?

This guide walks through enabling Prometheus to scrape metrics from a namespace using ServiceMonitor (e.g., `warpstream`).

Use ServiceMonitor when a Service exists that exposes the metrics port.

#### Step 1: Check if Already Being Scraped

```bash
# Check targets API
curl -s "https://<prometheus-url>/prometheus/api/v1/targets" | jq '.data.activeTargets[] | select(.labels.namespace == "warpstream")'

# Or in Grafana Explore
up{namespace="warpstream"}

# Or check Prometheus UI
# Navigate to: https://<prometheus-url>/prometheus/targets?search=warpstream
```

If empty, the namespace is not being scraped.

#### Step 2: Check Existing ServiceMonitor

```bash
# Check all ServiceMonitors across all namespaces
kubectl get servicemonitor -A

# Check specifically in warpstream namespace
kubectl get servicemonitor -n warpstream
```

If "No resources found", you need to create one.

#### Step 3: Check Services in the Namespace

```bash
kubectl get svc -n warpstream
```

Example output:

```
NAME                        TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE
warpstream-agent            ClusterIP      172.20.197.188   <none>        9092/TCP,8080/TCP   182d
warpstream-agent-headless   ClusterIP      None             <none>        9092/TCP,8080/TCP   182d
warpstream-agent-kafka      LoadBalancer   172.20.60.194    <elb-url>     9093:30867/TCP      182d
```

Get service labels:

```bash
kubectl get svc warpstream-agent -n warpstream --show-labels
```

Example output:

```
NAME               TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE    LABELS
warpstream-agent   ClusterIP   172.20.35.252   <none>        9092/TCP,8080/TCP   49d   app.kubernetes.io/instance=warpstream-agent,app.kubernetes.io/managed-by=Helm,app.kubernetes.io/name=warpstream-agent,app.kubernetes.io/version=v720,helm.sh/chart=warpstream-agent-0.15.78,prometheus=true
```

#### Step 4: Check Pods

```bash
kubectl get pods -n warpstream -o wide
```

Ensure pods are in `Running` state.

#### Step 5: Check Metrics Endpoint Accessibility

Test if the `/metrics` endpoint is exposed:

```bash
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -- curl -s http://warpstream-agent.warpstream.svc:8080/metrics | head -20
```

If you see Prometheus metrics output (lines starting with `# HELP`, `# TYPE`), the endpoint is working.

#### Step 6: Check Prometheus ServiceMonitor Selector

Find what label selector your Prometheus operator uses:

```bash
kubectl get prometheus -n prometheus -o jsonpath='{.items[0].spec.serviceMonitorSelector}' | jq
```

- If `{}` (empty), Prometheus picks up all ServiceMonitors.
- If specific labels are required, add them to your ServiceMonitor metadata.

Also check namespace selector:

```bash
kubectl get prometheus -n prometheus -o jsonpath='{.items[0].spec.serviceMonitorNamespaceSelector}' | jq
```

- If `{}` (empty), Prometheus watches all namespaces.

#### Step 7: Check Port Name

Get the port names for the service:

```bash
kubectl get svc warpstream-agent -n warpstream -o jsonpath='{.spec.ports}' | jq
```

Example output:

```json
[
  {"name": "kafka", "port": 9092, "protocol": "TCP", "targetPort": "kafka"},
  {"name": "http", "port": 8080, "protocol": "TCP", "targetPort": "http"}
]
```

The metrics port (8080) has name `http`.

#### Step 8: Create ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: warpstream-agent
  namespace: warpstream
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: warpstream-agent
  endpoints:
    - port: http
      interval: 30s
      path: /metrics
```

Apply it:

```bash
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: warpstream-agent
  namespace: warpstream
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: warpstream-agent
  endpoints:
    - port: http
      interval: 30s
      path: /metrics
EOF
```

#### Step 9: Verify ServiceMonitor

Check ServiceMonitor was created:

```bash
kubectl get servicemonitor -n warpstream
```

Wait ~30 seconds, then verify Prometheus is scraping:

```bash
curl -s "https://<prometheus-url>/prometheus/api/v1/targets" | jq '.data.activeTargets[] | select(.labels.namespace == "warpstream")'
```

Or in Grafana Explore:

```promql
up{namespace="warpstream"}
```

You should now see warpstream targets with value `1` (healthy).

#### Troubleshooting

If ServiceMonitor is created but targets don't appear:

```bash
# Check Prometheus operator logs
kubectl logs -n prometheus -l app.kubernetes.io/name=prometheus-operator --tail=100 | grep -i "warpstream\|error"

# Force Prometheus config reload
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- kill -HUP 1

# Check if service labels match ServiceMonitor selector
kubectl get svc -n warpstream -l app.kubernetes.io/name=warpstream-agent
```

### How to enable PodMonitor for a namespace?

Use PodMonitor when pods expose metrics directly without a Service exposing the metrics port.

Example: `spark-operator` exposes metrics on pod port 10254, but only has a webhook Service on port 443 (no metrics Service).

#### Step 1: Check Services (confirm no metrics Service)

```bash
kubectl get svc -n spark-operator
```

Example output:

```
NAME                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
spark-operator-webhook   ClusterIP   172.20.230.112   <none>        443/TCP   330d
```

Only webhook service exists — no metrics port exposed via Service.

#### Step 2: Check Pod Ports

```bash
kubectl get pod -n spark-operator -l app.kubernetes.io/name=spark-operator -o jsonpath='{.items[0].spec.containers[*].ports}' | jq
```

Example output:

```json
[
  {"containerPort": 10254, "name": "metrics", "protocol": "TCP"}
]
```

Metrics are exposed on pod port 10254 with name `metrics`.

#### Step 3: Check Pod Labels

```bash
kubectl get pod -n spark-operator -l app.kubernetes.io/name=spark-operator -o jsonpath='{.items[0].metadata.labels}' | jq
```

Example output:

```json
{
  "app.kubernetes.io/instance": "spark-operator",
  "app.kubernetes.io/name": "spark-operator",
  "pod-template-hash": "6b8c5ddd74"
}
```

#### Step 4: Verify Metrics Endpoint

```bash
kubectl exec -n spark-operator deploy/spark-operator -- curl -s http://localhost:10254/metrics | head -15
```

Example output:

```
# HELP go_gc_duration_seconds A summary of the pause duration of garbage collection cycles.
# TYPE go_gc_duration_seconds summary
go_gc_duration_seconds{quantile="0"} 0.000136673
...
```

#### Step 5: Check Prometheus PodMonitor Selector

```bash
kubectl get prometheus -n prometheus -o jsonpath='{.items[0].spec.podMonitorSelector}' | jq
kubectl get prometheus -n prometheus -o jsonpath='{.items[0].spec.podMonitorNamespaceSelector}' | jq
```

- If `{}` (empty), Prometheus picks up all PodMonitors from all namespaces.

#### Step 6: Create PodMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: spark-operator
  namespace: spark-operator
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: spark-operator
  podMetricsEndpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

Apply it:

```bash
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: spark-operator
  namespace: spark-operator
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: spark-operator
  podMetricsEndpoints:
    - port: metrics
      interval: 30s
      path: /metrics
EOF
```

#### Step 7: Verify PodMonitor

```bash
kubectl get podmonitor -n spark-operator
```

Wait ~30 seconds, then verify:

```bash
curl -s "https://<prometheus-url>/prometheus/api/v1/targets" | jq '.data.activeTargets[] | select(.labels.namespace == "spark-operator")'
```

Or in Grafana Explore:

```promql
up{namespace="spark-operator"}
```

#### Troubleshooting

If PodMonitor is created but targets don't appear:

```bash
# Check if podMonitorSelectorNilUsesHelmValues is false
kubectl get prometheus -n prometheus -o yaml | grep -i podmonitor

# Force Prometheus config reload
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- kill -HUP 1

# Check Prometheus operator logs
kubectl logs -n prometheus -l app.kubernetes.io/name=prometheus-operator --tail=100 | grep -i "podmonitor\|error"
```

### ServiceMonitor vs PodMonitor - When to use which?

| Criteria | ServiceMonitor | PodMonitor |
|----------|----------------|------------|
| Metrics exposed via Service | ✅ Use this | ❌ |
| Metrics exposed only on Pod (no Service) | ❌ | ✅ Use this |
| Service exists but metrics on different port | Create new Service or | ✅ Use this |
| Multiple pods behind a Service | ✅ Use this | Works but less efficient |
| Sidecar containers with metrics | ❌ | ✅ Use this |
| DaemonSets without Service | ❌ | ✅ Use this |

#### Examples

| Application | Has Metrics Service? | Recommendation |
|-------------|---------------------|----------------|
| warpstream-agent | Yes (port 8080 `http`) | ServiceMonitor |
| spark-operator | No (only webhook on 443, metrics on pod:10254) | PodMonitor |
| nginx-ingress | Yes (metrics port) | ServiceMonitor |
| node-exporter | Yes (DaemonSet with Service) | ServiceMonitor |
| Custom sidecar | No | PodMonitor |

#### Key Differences

```yaml
# ServiceMonitor - targets Service endpoints
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: warpstream-agent  # Matches Service labels
  endpoints:                                     # Note: "endpoints"
    - port: http

# PodMonitor - targets Pods directly
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: spark-operator    # Matches Pod labels
  podMetricsEndpoints:                          # Note: "podMetricsEndpoints"
    - port: metrics
```

#### Decision Flow

```
Does a Service exist that exposes the metrics port?
├── Yes → Use ServiceMonitor (e.g., warpstream-agent)
└── No
    ├── Can you create a metrics Service? → Create Service + ServiceMonitor
    └── No / Don't want to → Use PodMonitor (e.g., spark-operator)
```

### How to exclude namespaces/services from scraping?

When scraping all namespaces (`serviceMonitorSelectorNilUsesHelmValues: false`), you may want to exclude specific namespaces, services, or metrics. Here are 6 methods:

#### Method 1: Exclude by Namespace (Selector)

```yaml
prometheus:
  prometheusSpec:
    # Only scrape from namespaces with label "monitoring: enabled"
    serviceMonitorNamespaceSelector:
      matchLabels:
        monitoring: enabled

    # Or exclude specific namespaces using matchExpressions
    serviceMonitorNamespaceSelector:
      matchExpressions:
        - key: kubernetes.io/metadata.name
          operator: NotIn
          values:
            - kube-system
            - kube-public
            - castai-agent
```

#### Method 2: Exclude by ServiceMonitor Labels

```yaml
prometheus:
  prometheusSpec:
    # Only scrape ServiceMonitors with specific label
    serviceMonitorSelector:
      matchLabels:
        prometheus: main

    # Or exclude ServiceMonitors with certain labels
    serviceMonitorSelector:
      matchExpressions:
        - key: exclude-from-prometheus
          operator: DoesNotExist
```

#### Method 3: Exclude using relabelConfigs (Most Flexible)

```yaml
prometheus:
  prometheusSpec:
    additionalScrapeConfigs:
      - job_name: 'custom-job'
        relabel_configs:
          # Drop targets from specific namespaces
          - source_labels: [__meta_kubernetes_namespace]
            regex: 'kube-system|castai-agent|karpenter'
            action: drop
          # Drop targets with specific labels
          - source_labels: [__meta_kubernetes_pod_label_app]
            regex: 'some-app-to-exclude'
            action: drop
```

#### Method 4: Exclude Metrics (metric_relabel_configs)

Drop specific metrics after scraping:

```yaml
# In ServiceMonitor or additionalScrapeConfigs
metricRelabelings:
  # Drop high-cardinality metrics
  - sourceLabels: [__name__]
    regex: 'go_.*|process_.*'
    action: drop
  # Drop metrics with specific labels
  - sourceLabels: [pod]
    regex: '.*-canary-.*'
    action: drop
```

#### Method 5: Disable Specific Kubernetes Components

```yaml
kubeApiServer:
  enabled: false
kubeEtcd:
  enabled: false
kubeControllerManager:
  enabled: false
kubeScheduler:
  enabled: false
kubeProxy:
  enabled: false
coreDns:
  enabled: false
kubelet:
  enabled: false
```

#### Method 6: Delete/Label Specific ServiceMonitor

```bash
# Delete ServiceMonitor
kubectl delete servicemonitor -n analytics analytics-policy-management-service

# Or add label to exclude (if using selector)
kubectl label servicemonitor -n analytics analytics-policy-management-service exclude-from-prometheus=true
```

#### Quick Reference: What to Exclude

| What to Exclude | Method |
|-----------------|--------|
| Entire namespace | `serviceMonitorNamespaceSelector` |
| Specific ServiceMonitor | `serviceMonitorSelector` or delete it |
| Specific pods/targets | `relabel_configs` with `action: drop` |
| Specific metrics | `metric_relabel_configs` with `action: drop` |
| K8s components | Set `kubeApiServer.enabled: false`, etc. |
| By label | `matchExpressions` with `DoesNotExist` |

---

## Resources & Sizing

### How to check Prometheus resource usage?

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

### How to check and modify Prometheus resources?

#### Check Actual Resource Usage

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

#### Check Configured Limits

```bash
kubectl get pod prometheus-prometheus-kube-prometheus-prometheus-0 -n prometheus \
  -o jsonpath='{.spec.containers[?(@.name=="prometheus")].resources}' | jq .
```

#### Modify Resources

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

Memory is the most critical resource for Prometheus:

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

#### Monitoring Your Sizing

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

### Alertmanager Sizing Guidelines

| Alert Volume | Replicas | CPU Request | CPU Limit | Memory Request | Memory Limit |
|--------------|----------|-------------|-----------|----------------|--------------|
| < 100 alerts | 1 | 50m | 100m | 64Mi | 128Mi |
| 100 - 500 alerts | 2 | 100m | 200m | 128Mi | 256Mi |
| 500 - 1000 alerts | 3 | 100m | 200m | 256Mi | 512Mi |
| 1000+ alerts | 3 | 200m | 500m | 512Mi | 1Gi |

**Notes:**
- Use 3 replicas for HA in production
- Memory scales with alert history retention (default: 120h)
- CPU spikes during notification bursts

```yaml
alertmanager:
  alertmanagerSpec:
    replicas: 3
    retention: 120h
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        cpu: 200m
        memory: 512Mi
```

### Grafana Sizing Guidelines

| Users | Dashboards | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-------|------------|-------------|-----------|----------------|--------------|
| < 10 | Simple | 100m | 200m | 128Mi | 256Mi |
| 10 - 50 | Moderate | 200m | 500m | 256Mi | 512Mi |
| 50 - 100 | Complex | 500m | 1 | 512Mi | 1Gi |
| 100+ | Heavy | 1 | 2 | 1Gi | 2Gi |

**Notes:**
- Memory increases with concurrent dashboard renders
- CPU spikes during dashboard loads and query execution
- Enable persistence for dashboard/user data (10Gi typically sufficient)

```yaml
grafana:
  replicas: 1  # Use 2+ for HA with shared database
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
  persistence:
    enabled: true
    size: 10Gi
```

### Node Exporter & Kube-State-Metrics Sizing

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| Node Exporter | 50m | 100m | 32Mi | 64Mi |
| Kube-State-Metrics | 100m | 200m | 128Mi | 256Mi |

**Note:** Kube-State-Metrics memory scales with cluster size (pods, services, etc.)

### Complete Stack Sizing Examples

#### Small Environment (Dev/Test)
```yaml
# ~50K series, 50 targets, 10 users
prometheus:
  prometheusSpec:
    resources:
      requests: { cpu: 200m, memory: 512Mi }
      limits: { cpu: 500m, memory: 1Gi }
alertmanager:
  alertmanagerSpec:
    replicas: 1
    resources:
      requests: { cpu: 50m, memory: 64Mi }
      limits: { cpu: 100m, memory: 128Mi }
grafana:
  resources:
    requests: { cpu: 100m, memory: 128Mi }
    limits: { cpu: 200m, memory: 256Mi }
```

#### Medium Environment (Production)
```yaml
# ~500K series, 200 targets, 50 users
prometheus:
  prometheusSpec:
    resources:
      requests: { cpu: 1, memory: 4Gi }
      limits: { cpu: 2, memory: 8Gi }
alertmanager:
  alertmanagerSpec:
    replicas: 3
    resources:
      requests: { cpu: 100m, memory: 256Mi }
      limits: { cpu: 200m, memory: 512Mi }
grafana:
  resources:
    requests: { cpu: 200m, memory: 256Mi }
    limits: { cpu: 500m, memory: 512Mi }
```

#### Large Environment (Enterprise)
```yaml
# ~5M series, 1000 targets, 100+ users
prometheus:
  prometheusSpec:
    resources:
      requests: { cpu: 4, memory: 16Gi }
      limits: { cpu: 8, memory: 32Gi }
alertmanager:
  alertmanagerSpec:
    replicas: 3
    resources:
      requests: { cpu: 200m, memory: 512Mi }
      limits: { cpu: 500m, memory: 1Gi }
grafana:
  replicas: 2
  resources:
    requests: { cpu: 500m, memory: 512Mi }
    limits: { cpu: 1, memory: 1Gi }
```

---

## Storage

### How to check PVC status?

```bash
# List PVCs
kubectl get pvc -n prometheus

# Describe PVC for details
kubectl describe pvc prometheus-prometheus-kube-prometheus-prometheus-db-prometheus-prometheus-kube-prometheus-prometheus-0 -n prometheus
```

### How to setup EKS storage (gp3 StorageClass)?

EKS requires the EBS CSI driver and a StorageClass for dynamic volume provisioning.

#### Prerequisites: EBS CSI Driver

```bash
# Check if EBS CSI driver is installed
kubectl get pods -n kube-system | grep ebs-csi

# If not installed, enable the EKS addon
aws eks create-addon \
  --cluster-name <your-cluster-name> \
  --addon-name aws-ebs-csi-driver \
  --region <your-region>
```

#### Create gp3 StorageClass

```bash
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  fsType: ext4
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF
```

#### Common PVC Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `storageclass "gp3" not found` | StorageClass doesn't exist | Create gp3 StorageClass |
| `unbound immediate PersistentVolumeClaims` | PVC can't bind | Check StorageClass, EBS CSI driver |
| `waiting for first consumer` | Normal with `WaitForFirstConsumer` | Pod needs to be scheduled first |
| `volume node affinity conflict` | AZ mismatch | Use `WaitForFirstConsumer` binding mode |

#### gp2 vs gp3 Comparison

| Feature | gp2 | gp3 |
|---------|-----|-----|
| Baseline IOPS | 3 IOPS/GB (min 100) | 3000 IOPS (included) |
| Max IOPS | 16,000 | 16,000 |
| Throughput | 250 MB/s | 125-1000 MB/s |
| Cost | Higher for small volumes | 20% cheaper |

**Recommendation**: Use gp3 for all new deployments.

### How to check Prometheus retention?

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

#### Common Retention Values

| Use Case | Retention |
|----------|-----------|
| Stateless Forwarder | `2h` |
| Development | `3d` - `7d` |
| Default | `15d` |
| Production | `15d` - `30d` |

---

## Remote Write

### How to check if remote_write is enabled?

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

### How to verify remote_write is working?

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

#### Remote Write Health Reference

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Pending Samples | < 10,000 | 10K - 100K | > 100K |
| Failed Samples | 0 | < 100 | > 100 |
| Lag (seconds) | < 60 | 60 - 300 | > 300 |

---

## Cardinality & Performance

### How to analyze cardinality (high series count)?

#### Quick Summary

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

#### Common High-Cardinality Culprits

| Pattern | Issue | Solution |
|---------|-------|----------|
| `*_bucket` | Many histogram buckets | Use summaries or recording rules |
| `*_by_path` | Unique URL paths | Aggregate by pattern |
| `container_*` | Pod churn | Filter by namespace |
| `*_by_id` | Unique IDs | Use labeldrop |

---

## Advanced Features

### How to enable exemplars?

Exemplars link metrics to traces, enabling correlation between Prometheus metrics and distributed tracing systems (Jaeger, Tempo, etc.).

#### Enable via Helm values

```yaml
prometheus:
  prometheusSpec:
    enableFeatures:
      - exemplar-storage
    exemplars:
      maxSize: 100000
```

#### Enable via kubectl patch

```bash
kubectl patch prometheus prometheus-kube-prometheus-prometheus -n prometheus \
  --type=merge -p '{
    "spec": {
      "enableFeatures": ["exemplar-storage"],
      "exemplars": {"maxSize": 100000}
    }
  }'
```

#### Verify exemplars are enabled

```bash
# Check feature flags
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/status/flags' 2>/dev/null | jq '.data["enable-feature"]'
```

#### Memory considerations

| maxSize | Memory (~) | Use Case |
|---------|------------|----------|
| 10000 | ~1MB | Low traffic |
| 100000 | ~10MB | Default |
| 500000 | ~50MB | High traffic |
| 1000000 | ~100MB | Very high traffic |

---

## Troubleshooting

### How to troubleshoot external URL not accessible?

If Prometheus/Grafana ingress is created but the external URL is not accessible, follow these steps:

#### Step 1: Verify Ingress is Created

```bash
kubectl get ingress -n prometheus
kubectl describe ingress -n prometheus prometheus-kube-prometheus-prometheus
```

Check that ADDRESS is populated (should show Load Balancer hostname).

#### Step 2: Check DNS Resolution

```bash
# Check if DNS resolves
nslookup scnx-global-demo-use2-eks.securonix.net
dig scnx-global-demo-use2-eks.securonix.net

# If NXDOMAIN - DNS record doesn't exist
```

#### Step 3: Check External-DNS

```bash
# Check if external-dns pods are running
kubectl get pods -A | grep external-dns

# Check external-dns logs for your hostname
kubectl logs -n external-dns -l app.kubernetes.io/name=external-dns --tail=200 | grep -i "your-hostname"

# Check for errors
kubectl logs -n external-dns -l app.kubernetes.io/name=external-dns --tail=100 | grep -i "error\|fail"

# For internal ingress, check internal external-dns
kubectl logs -n external-dns external-dns-internal-xxx --tail=100 | grep -i "error\|fail"
```

#### Step 4: Verify Annotations

External-dns may filter by annotations. Check what filter is configured:

```bash
# Check external-dns configuration
kubectl get deployment -n external-dns external-dns-internal -o yaml | grep -A20 "args:"
```

If you see `--annotation-filter=kubernetes.io/ingress.class in (nginx-internal)`, your ingress needs this annotation:

```yaml
ingress:
  annotations:
    kubernetes.io/ingress.class: nginx-internal  # Required for external-dns
    external-dns.alpha.kubernetes.io/hostname: your-hostname.domain.com
```

#### Step 5: Check for TXT/CNAME Conflicts

External-dns creates TXT records for ownership tracking. Conflicts can block all updates:

```bash
# Check Route53 for conflicting records
aws route53 list-resource-record-sets --hosted-zone-id YOUR_ZONE_ID \
  --query "ResourceRecordSets[?contains(Name, 'conflicting-hostname')]"
```

Error example:
```
InvalidChangeBatch: RRSet of type TXT with DNS name xxx.domain.com is not permitted
because a conflicting RRSet of type CNAME with the same DNS name already exists
```

Fix: Delete the conflicting TXT or CNAME record in Route53.

#### Step 6: Create DNS Record Manually (Workaround)

If external-dns isn't working, create the record manually:

```bash
# Get the Load Balancer address from ingress
kubectl get ingress -n prometheus -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}'

# Create CNAME in Route53
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "your-hostname.domain.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "your-load-balancer.region.elb.amazonaws.com"}]
      }
    }]
  }'
```

#### Common Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| DNS not resolving | `NXDOMAIN` | Check external-dns or create record manually |
| Annotation filter | External-dns ignores ingress | Add `kubernetes.io/ingress.class` annotation |
| TXT/CNAME conflict | External-dns batch fails | Delete conflicting records in Route53 |
| Wrong external-dns | Using internal LB | Check `external-dns-internal` logs |
| Ingress no ADDRESS | Empty ADDRESS field | Check ingress controller is running |

---

### How to check why pods are not scheduling?

```bash
# Describe pod for events
kubectl describe pod -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 | grep -A20 Events

# Check node taints
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# Check pod tolerations
kubectl get pod -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -o jsonpath='{.spec.tolerations}' | jq
```

### How to access Grafana?

```bash
# Port-forward
kubectl port-forward -n prometheus svc/prometheus-grafana 3000:80

# Get credentials
echo "Username: admin"
echo "Password: $(kubectl get secret -n prometheus prometheus-grafana -o jsonpath='{.data.admin-password}' | base64 --decode)"

# Open browser
open http://localhost:3000
```

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
  wget -qO- 'http://localhost:9090/api/v1/query?query=sum(rate(prometheus_remote_storage_samples_total[15m]))' 2>/dev/null | \
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
kubectl get servicemonitors -A

# List scrape targets by job
kubectl exec -n prometheus $PROM_POD -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/targets' 2>/dev/null | \
  jq -r '.data.activeTargets | group_by(.scrapePool) | .[] | "\(.[0].scrapePool): \(length)"'
```
