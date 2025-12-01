# Grafana Dashboard Import Guide

## 🚀 Quick Import Methods

### **Method 1: Manual Import (Recommended for Testing)**

1. **Access Grafana**:
   ```bash
   # Start Grafana
   ./scripts/stack/start-grafana.sh
   
   # Open browser
   open http://localhost:3000
   # Login: admin/admin
   ```

2. **Import Dashboard**:
   - Go to **Dashboards** → **Import**
   - Click **Upload JSON file**
   - Select dashboard from `observability/grafana/dashboards/official/`
   - Configure variables (see below)
   - Click **Import**

### **Method 2: Grafana Provisioning (Automated)**

1. **Create Provisioning Config**:
   ```yaml
   # observability/grafana/configs/provisioning/dashboards/dashboards.yml
   apiVersion: 1
   providers:
     - name: 'loki-official'
       type: file
       disableDeletion: false
       updateIntervalSeconds: 10
       options:
         path: /var/lib/grafana/dashboards/official
   ```

2. **Copy Dashboards**:
   ```bash
   # Copy to Grafana dashboards directory
   cp observability/grafana/dashboards/official/*.json /path/to/grafana/dashboards/
   ```

---

## ⚙️ Variable Configuration

### **Required Variables for Monolithic Setup**

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
        "type": "query",
        "query": "label_values(up{job=~\"loki.*\"}, job)",
        "current": {
          "value": "loki",
          "text": "loki"
        }
      }
    ]
  }
}
```

### **Variable Values for Monolithic**
- **datasource**: `Prometheus` (your Prometheus datasource name)
- **cluster**: `local` (constant value)
- **namespace**: `default` (constant value)  
- **job**: `loki` (or your Loki job name)

---

## 🔧 Dashboard Adaptations

### **Common Query Modifications**

#### **Original Distributed Query**:
```promql
sum(rate(loki_request_duration_seconds_count{cluster=~"$cluster",job=~"($namespace)/query-frontend"}[5m])) by (job)
```

#### **Monolithic Adaptation**:
```promql
sum(rate(loki_request_duration_seconds_count{job=~"loki.*"}[5m])) by (job)
```

### **Label Simplifications**
```promql
# Remove cluster/namespace grouping
by (cluster, namespace, job) → by (job)

# Simplify job selectors  
{job=~"($namespace)/query-frontend"} → {job=~"loki.*"}
{job=~"($namespace)/distributor"} → {job=~"loki.*"}
{job=~"($namespace)/ingester"} → {job=~"loki.*"}
```

---

## 📊 Dashboard Priority Import Order

### **Phase 1: Core Monitoring (Day 1)**
```bash
# Import these first for basic monitoring
1. loki-operational.json     # Overall health
2. loki-reads.json          # Query performance  
3. loki-writes.json         # Ingestion performance
```

### **Phase 2: Storage & Efficiency (Week 1)**
```bash
4. loki-chunks.json         # Storage efficiency
5. loki-retention.json      # Data lifecycle
6. loki-mixin-recording-rules.json  # Recording rules health
```

### **Phase 3: Advanced Monitoring (Month 1)**
```bash
7. loki-reads-resources.json    # Resource monitoring
8. loki-writes-resources.json   # Capacity planning
9. loki-logs.json              # Internal troubleshooting
```

### **Phase 4: Specialized Features (As Needed)**
```bash
10. loki-bloom-build.json       # Bloom filters (Loki 3.0+)
11. loki-bloom-gateway.json     # Bloom gateway (Loki 3.0+)
12. loki-deletion.json          # Data compliance
13. loki-thanos-object-storage.json  # Thanos integration
```

---

## 🛠️ Troubleshooting Import Issues

### **Common Issues & Solutions**

#### **1. "No data" in panels**
```bash
# Check Prometheus is scraping Loki
curl http://localhost:9090/api/v1/targets

# Verify Loki metrics endpoint
curl http://localhost:3100/metrics

# Check Prometheus query
curl "http://localhost:9090/api/v1/query?query=up{job=~\"loki.*\"}"
```

#### **2. Variable errors**
- Set `cluster` and `namespace` as **constant** variables
- Use `loki` or `loki.*` for job variable
- Ensure datasource variable points to correct Prometheus

#### **3. Panel query errors**
```promql
# Replace distributed selectors:
{cluster=~"$cluster",job=~"($namespace)/component"} 
# With monolithic selectors:
{job=~"loki.*"}
```

#### **4. Missing metrics**
- Some panels expect specific Loki components (distributor, ingester, etc.)
- In monolithic mode, all components run in single process
- Metrics may have different labels or be missing entirely

---

## 📝 Dashboard Customization Script

### **Automated Adaptation Script**
```bash
#!/bin/bash
# adapt-dashboard.sh - Adapt official dashboards for monolithic

DASHBOARD_FILE="$1"
OUTPUT_FILE="${DASHBOARD_FILE%.json}-monolithic.json"

# Replace distributed job selectors with monolithic
sed 's/job=~"($namespace)\/[^"]*"/job=~"loki.*"/g' "$DASHBOARD_FILE" > "$OUTPUT_FILE"

# Simplify grouping clauses
sed -i 's/by (cluster, namespace, job)/by (job)/g' "$OUTPUT_FILE"
sed -i 's/by (cluster, job)/by (job)/g' "$OUTPUT_FILE"

echo "Adapted dashboard saved as: $OUTPUT_FILE"
```

### **Usage**:
```bash
# Adapt a dashboard for monolithic use
./adapt-dashboard.sh loki-operational.json

# Import the adapted version
# loki-operational-monolithic.json
```

---

## 🎯 Validation Checklist

### **After Import**:
- [ ] All panels load without errors
- [ ] Variables are properly configured
- [ ] Metrics are showing data
- [ ] Time ranges are appropriate
- [ ] Refresh intervals work correctly

### **Panel Validation**:
- [ ] QPS panels show request rates
- [ ] Latency panels show response times  
- [ ] Error rate panels show failure rates
- [ ] Resource panels show CPU/memory (if node_exporter available)

### **Functionality Test**:
- [ ] Generate some logs: `./scripts/logs/generate-logs.sh`
- [ ] Run some queries in Grafana Explore
- [ ] Verify dashboards update with new data
- [ ] Test alert annotations (if alerts configured)

---

## 💡 Pro Tips

### **Dashboard Organization**
- Create folders: "Loki Core", "Loki Advanced", "Loki Resources"
- Tag dashboards: "loki", "monitoring", "production"
- Set appropriate refresh intervals (10s for operational, 1m for resources)

### **Performance Optimization**
- Use recording rules for expensive queries
- Set reasonable time ranges (last 1h for operational dashboards)
- Enable query caching in Grafana

### **Alerting Integration**
- Add alert annotations to panels
- Link to runbooks and troubleshooting guides
- Configure notification channels

This guide ensures smooth integration of official Loki dashboards into your monolithic setup! 🚀