# Dashboard Variables Configuration for Monolithic Setup

## 🎯 Your Prometheus Configuration

Based on your Prometheus scrape config:
```yaml
job: "loki"
instance: "loki-monolithic"
```

## ⚙️ Required Variable Updates for Official Dashboards

### **1. Update Dashboard Variables**

When importing official dashboards, configure these variables:

```json
{
  "templating": {
    "list": [
      {
        "name": "datasource",
        "type": "datasource",
        "query": "prometheus",
        "current": {
          "value": "Prometheus",
          "text": "Prometheus"
        }
      },
      {
        "name": "cluster",
        "type": "constant",
        "current": {
          "value": "local",
          "text": "local"
        }
      },
      {
        "name": "namespace", 
        "type": "constant",
        "current": {
          "value": "default",
          "text": "default"
        }
      },
      {
        "name": "job",
        "type": "constant",
        "current": {
          "value": "loki",
          "text": "loki"
        }
      }
    ]
  }
}
```

### **2. Query Adaptations**

#### **Original Official Query**:
```promql
sum by (status) (
  rate(loki_request_duration_seconds_count{
    cluster=~"$cluster",
    job=~"($namespace)/query-frontend"
  }[5m])
)
```

#### **Your Monolithic Adaptation**:
```promql
sum by (status_code) (
  rate(loki_request_duration_seconds_count{
    job="loki"
  }[5m])
)
```

### **3. Common Query Patterns for Your Setup**

#### **Request Rate**:
```promql
# Total request rate
sum(rate(loki_request_duration_seconds_count{job="loki"}[5m]))

# By status code
sum by (status_code) (rate(loki_request_duration_seconds_count{job="loki"}[5m]))

# By route
sum by (route) (rate(loki_request_duration_seconds_count{job="loki"}[5m]))
```

#### **Latency Metrics**:
```promql
# P99 latency
histogram_quantile(0.99, sum(rate(loki_request_duration_seconds_bucket{job="loki"}[5m])) by (le))

# P95 latency  
histogram_quantile(0.95, sum(rate(loki_request_duration_seconds_bucket{job="loki"}[5m])) by (le))

# Average latency
sum(rate(loki_request_duration_seconds_sum{job="loki"}[5m])) / sum(rate(loki_request_duration_seconds_count{job="loki"}[5m]))
```

#### **Ingestion Metrics**:
```promql
# Lines received per second
rate(loki_distributor_lines_received_total{job="loki"}[5m])

# Bytes received per second
rate(loki_distributor_bytes_received_total{job="loki"}[5m])

# Ingestion failures
rate(loki_distributor_ingester_append_failures_total{job="loki"}[5m])
```

#### **Cache Performance**:
```promql
# Cache hit rate by cache name
(rate(loki_cache_hits{job="loki"}[5m]) / rate(loki_cache_fetched_keys{job="loki"}[5m])) * 100

# Cache requests per second
rate(loki_cache_fetched_keys{job="loki"}[5m])
```

#### **Service Health**:
```promql
# Service up/down
up{job="loki"}

# Compactor running
loki_boltdb_shipper_compactor_running{job="loki"}

# Time since last compaction (hours)
(time() - loki_boltdb_shipper_compact_tables_operation_last_successful_run_timestamp_seconds{job="loki"}) / 3600
```

---

## 🔧 Quick Dashboard Adaptation Script

### **Automated Query Replacement**:
```bash
#!/bin/bash
# adapt-queries.sh - Replace distributed queries with monolithic

DASHBOARD_FILE="$1"
OUTPUT_FILE="${DASHBOARD_FILE%.json}-monolithic.json"

# Replace distributed job selectors
sed 's/job=~"($namespace)\/[^"]*"/job="loki"/g' "$DASHBOARD_FILE" > "$OUTPUT_FILE"

# Remove cluster/namespace filters
sed -i 's/cluster=~"$cluster",//g' "$OUTPUT_FILE"
sed -i 's/,cluster=~"$cluster"//g' "$OUTPUT_FILE"
sed -i 's/namespace=~"$namespace",//g' "$OUTPUT_FILE"
sed -i 's/,namespace=~"$namespace"//g' "$OUTPUT_FILE"

# Simplify grouping
sed -i 's/by (cluster, namespace, job)/by (job)/g' "$OUTPUT_FILE"
sed -i 's/by (cluster, job)/by (job)/g' "$OUTPUT_FILE"

echo "Adapted: $OUTPUT_FILE"
```

### **Usage**:
```bash
# Adapt official dashboard
./adapt-queries.sh loki-operational.json

# Result: loki-operational-monolithic.json
```

---

## 📊 Ready-to-Use Dashboard

I've created `loki-monolithic-dashboard.json` specifically for your setup with:

✅ **Correct job selector**: `job="loki"`
✅ **Simplified queries**: No cluster/namespace complexity
✅ **Key metrics**: Request rate, latency, ingestion, cache hit rate
✅ **Service status**: Up/down monitoring
✅ **Proper variables**: Only datasource variable needed

### **Import Instructions**:
1. Open Grafana: http://localhost:3000
2. Go to Dashboards → Import
3. Upload `loki-monolithic-dashboard.json`
4. Set datasource to "Prometheus"
5. Save & view

---

## 🎯 Variable Configuration Summary

| Variable | Type | Value | Description |
|----------|------|-------|-------------|
| `datasource` | datasource | `Prometheus` | Your Prometheus datasource |
| `cluster` | constant | `local` | Fixed value for compatibility |
| `namespace` | constant | `default` | Fixed value for compatibility |
| `job` | constant | `loki` | Your actual Loki job name |

This configuration ensures all official dashboards work perfectly with your monolithic Loki setup! 🚀