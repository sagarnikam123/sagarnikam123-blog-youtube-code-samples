# Official Loki Recording Rules Analysis

## 📋 Overview

Downloaded from: https://raw.githubusercontent.com/grafana/loki/refs/heads/main/production/loki-mixin-compiled/rules.yaml

**Rule Type**: Recording Rules (not alerting rules)
**Purpose**: Pre-compute expensive queries for faster dashboard performance

---

## 🔍 Rule Categories

### **1. Cluster + Job Level Aggregation**
```yaml
cluster_job:loki_request_duration_seconds:99quantile
cluster_job:loki_request_duration_seconds:50quantile
cluster_job:loki_request_duration_seconds:avg
```

**Purpose**: High-level performance metrics aggregated by cluster and job
**Use Case**: Overview dashboards, SLA monitoring

### **2. Cluster + Job + Route Level**
```yaml
cluster_job_route:loki_request_duration_seconds:99quantile
cluster_job_route:loki_request_duration_seconds:50quantile
cluster_job_route:loki_request_duration_seconds:avg
```

**Purpose**: API endpoint-specific performance metrics
**Use Case**: API performance analysis, route-specific SLAs

### **3. Cluster + Namespace + Job + Route Level**
```yaml
cluster_namespace_job_route:loki_request_duration_seconds:99quantile
cluster_namespace_job_route:loki_request_duration_seconds:50quantile
cluster_namespace_job_route:loki_request_duration_seconds:avg
```

**Purpose**: Most granular performance metrics for multi-tenant environments
**Use Case**: Namespace isolation, tenant-specific monitoring

---

## 📊 Metrics Computed

### **Latency Percentiles**
- **P99**: `histogram_quantile(0.99, ...)` - Tail latency (worst 1%)
- **P50**: `histogram_quantile(0.50, ...)` - Median latency

### **Average Latency**
- **Formula**: `sum(duration_sum) / sum(duration_count)`
- **Benefit**: Simple average calculation

### **Rate Aggregations**
- **Bucket rates**: Pre-computed histogram bucket rates
- **Sum rates**: Pre-computed duration sum rates
- **Count rates**: Pre-computed request count rates

---

## 🎯 Benefits for Monolithic Setup

### **✅ Performance Optimization**
```prometheus
# Instead of expensive real-time calculation:
histogram_quantile(0.99, sum(rate(loki_request_duration_seconds_bucket[1m])) by (le, cluster, job))

# Use pre-computed recording rule:
cluster_job:loki_request_duration_seconds:99quantile
```

### **✅ Dashboard Speed**
- Faster Grafana dashboard loading
- Reduced Prometheus query load
- Consistent aggregation across panels

### **✅ Alerting Efficiency**
- Use recording rules in alert expressions
- Faster alert evaluation
- Lower resource consumption

---

## 🔧 Adaptation for Monolithic

### **Simplified Labels for Single Instance**

**Original (Multi-cluster)**:
```yaml
expr: histogram_quantile(0.99, sum(rate(loki_request_duration_seconds_bucket[1m])) by (le, cluster, job))
record: cluster_job:loki_request_duration_seconds:99quantile
```

**Adapted (Monolithic)**:
```yaml
expr: histogram_quantile(0.99, sum(rate(loki_request_duration_seconds_bucket[1m])) by (le, job))
record: job:loki_request_duration_seconds:99quantile
```

### **Route-Specific Rules**
```yaml
expr: histogram_quantile(0.99, sum(rate(loki_request_duration_seconds_bucket[1m])) by (le, job, route))
record: job_route:loki_request_duration_seconds:99quantile
```

---

## 🚨 Missing Alert Rules

**Note**: This file contains only **recording rules**, not **alerting rules**.

### **Recommended Alert Rules to Add**

```yaml
groups:
  - name: loki_alerts
    rules:
      # High latency alert using recording rule
      - alert: LokiHighLatency
        expr: job:loki_request_duration_seconds:99quantile > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Loki high latency detected"
          description: "Loki P99 latency is {{ $value }}s"

      # Request rate alert
      - alert: LokiHighRequestRate
        expr: sum(rate(loki_request_duration_seconds_count[5m])) > 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Loki high request rate"
          description: "Loki receiving {{ $value }} requests/sec"
```

---

## 💡 Implementation Recommendations

### **1. Use in Prometheus Config**
```yaml
# prometheus.yml
rule_files:
  - "alert-rules/loki-official-rules.yaml"
  - "alert-rules/loki-alerts.yaml"  # Custom alerts
```

### **2. Dashboard Queries**
```prometheus
# Use recording rules in Grafana:
job:loki_request_duration_seconds:99quantile
job:loki_request_duration_seconds:avg
job_route:loki_request_duration_seconds:99quantile{route="loki_api_v1_push"}
```

### **3. Alerting Queries**
```prometheus
# Efficient alerts using recording rules:
job:loki_request_duration_seconds:99quantile > 5
rate(job:loki_request_duration_seconds_count:sum_rate[5m]) > 50
```

---

## 🔄 Next Steps

1. **Adapt Rules**: Modify for single-instance monolithic setup
2. **Add Alerts**: Create alerting rules using these recording rules
3. **Update Dashboards**: Use recording rules for faster performance
4. **Test Performance**: Compare dashboard speed before/after

---

## 📈 Expected Benefits

- **50-80% faster** dashboard loading
- **Reduced Prometheus load** during peak query times
- **Consistent metrics** across all dashboards
- **Efficient alerting** with pre-computed values

This analysis shows these are production-grade recording rules optimized for performance! 🚀
