# Prometheus Scripts

Post-deployment scripts for monitoring, testing, and validating Prometheus (kube-prometheus-stack).

## 📋 Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `check-prometheus-health.sh` | **Comprehensive health check** | `bash check-prometheus-health.sh` |
| `check-targets.sh` | Scrape targets status | `bash check-targets.sh` |
| `check-alerts.sh` | Alert rules & firing alerts | `bash check-alerts.sh` |
| `check-remote-write.sh` | Remote write health | `bash check-remote-write.sh` |
| `resource-usage.sh` | CPU, memory, storage usage | `bash resource-usage.sh` |
| `quick-report.sh` | Generate markdown report | `bash quick-report.sh` |
| `backup-grafana-dashboards.sh` | Export/import Grafana dashboards | `bash backup-grafana-dashboards.sh export <URL> <API_KEY>` |
| `backup-grafana-alerting.sh` | Export/import Grafana alerting config | `bash backup-grafana-alerting.sh export <URL> <API_KEY>` |
| `backup-prometheus-rules.sh` | Export/import PrometheusRule CRDs | `bash backup-prometheus-rules.sh export` |

## 🚀 Quick Start

```bash
cd scripts

# 1. Comprehensive health check (recommended first)
bash check-prometheus-health.sh

# 2. Check scrape targets
bash check-targets.sh

# 3. Check alerts
bash check-alerts.sh

# 4. Check remote write (if configured)
bash check-remote-write.sh

# 5. Resource usage
bash resource-usage.sh

# 6. Generate report
bash quick-report.sh
```

## 📖 Scripts

### 1. check-prometheus-health.sh ⭐

**Purpose:** Comprehensive health check via Prometheus API

**Features:**
- Build info & version
- Runtime status (retention, goroutines)
- TSDB status (active series, chunks)
- Scrape targets summary
- Alert rules summary
- Firing alerts
- Remote write status
- Pod health
- Overall health score (0-100%)

**Usage:**
```bash
# Default (prometheus namespace)
bash check-prometheus-health.sh

# Custom namespace
bash check-prometheus-health.sh -n monitoring

# Custom service name
bash check-prometheus-health.sh -s prometheus-server
```

**Exit Codes:**
- `0` - Healthy (≥80% score)
- `1` - Degraded or Unhealthy

---

### 2. check-targets.sh

**Purpose:** Detailed scrape target analysis

**Features:**
- Target summary (up/down/unknown)
- Targets grouped by job
- Down targets with error details
- Scrape duration analysis (slowest targets)

**Usage:**
```bash
# All targets
bash check-targets.sh

# Filter by job
bash check-targets.sh -j kubelet

# Show only down targets
bash check-targets.sh --down-only
```

---

### 3. check-alerts.sh

**Purpose:** Alert rules and firing alerts analysis

**Features:**
- Firing alerts with details
- Pending alerts
- Rule groups summary
- Rules by severity
- Unhealthy rules detection

**Usage:**
```bash
# Full analysis
bash check-alerts.sh

# Show only firing alerts
bash check-alerts.sh --firing-only

# Filter by group
bash check-alerts.sh -g kubernetes
```

---

### 4. check-remote-write.sh

**Purpose:** Monitor remote_write health and performance

**Features:**
- Configuration check
- Samples sent/pending/failed/dropped
- Shard status
- Write lag
- Throughput metrics
- Health summary

**Usage:**
```bash
bash check-remote-write.sh
```

**Key Metrics Monitored:**
| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `prometheus_remote_storage_samples_pending` | Queue backlog | > 100,000 |
| `prometheus_remote_storage_samples_failed_total` | Failed samples | > 0 |
| `prometheus_remote_storage_samples_dropped_total` | Dropped samples | > 0 |
| `prometheus_remote_storage_shards` | Current shards | Near max |

---

### 5. resource-usage.sh

**Purpose:** Resource usage analysis

**Features:**
- Pod status overview
- Resource allocation (requests/limits)
- Actual usage (if metrics-server available)
- Resource efficiency indicators
- PVC storage summary
- Pod-level breakdown

**Usage:**
```bash
bash resource-usage.sh

# Custom namespace
bash resource-usage.sh -n monitoring
```

---

### 6. quick-report.sh

**Purpose:** Generate markdown status report

**Features:**
- Cluster information
- Prometheus version & status
- Scrape targets summary
- Firing alerts
- Pod status
- Overall health assessment

**Output:** `../results/prometheus_report_<cluster>_<timestamp>.md`

**Usage:**
```bash
bash quick-report.sh

# Custom output directory
REPORT_DIR=/tmp bash quick-report.sh
```

---

## 🔧 Environment Variables

All scripts support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NAMESPACE` | `prometheus` | Kubernetes namespace |
| `PROM_SVC` | `prometheus-kube-prometheus-prometheus` | Prometheus service name |
| `LOCAL_PORT` | `9090` | Local port for port-forward |

**Examples:**
```bash
# Different namespace
NAMESPACE=monitoring bash check-prometheus-health.sh

# Different service name
PROM_SVC=prometheus-server bash check-targets.sh

# Combined
NAMESPACE=monitoring PROM_SVC=prometheus bash check-alerts.sh
```

---

## 🔄 API Path Auto-Detection

Scripts automatically detect the correct API path:
- `/prometheus/api/v1/*` - kube-prometheus-stack with external URL prefix
- `/api/v1/*` - Standard Prometheus

No manual configuration needed.

---

## 📊 Prometheus API Endpoints Used

| Endpoint | Purpose | Script |
|----------|---------|--------|
| `/api/v1/status/buildinfo` | Version info | health, report |
| `/api/v1/status/runtimeinfo` | Runtime config | health |
| `/api/v1/status/tsdb` | TSDB stats | health, report |
| `/api/v1/status/config` | Configuration | remote-write |
| `/api/v1/targets` | Scrape targets | health, targets, report |
| `/api/v1/rules` | Alert/recording rules | alerts, report |
| `/api/v1/alerts` | Active alerts | health, alerts, report |
| `/api/v1/query` | PromQL queries | health, remote-write |

---

## 🛠️ Prerequisites

- `kubectl` - Kubernetes CLI
- `jq` - JSON processor
- `curl` - HTTP client
- Access to Kubernetes cluster with Prometheus

---

## 💡 Tips

### Check specific job targets
```bash
bash check-targets.sh -j node-exporter
```

### Monitor remote write continuously
```bash
watch -n 5 'bash check-remote-write.sh 2>/dev/null | tail -20'
```

### Quick health check in CI/CD
```bash
if bash check-prometheus-health.sh; then
    echo "Prometheus healthy"
else
    echo "Prometheus unhealthy"
    exit 1
fi
```

### Generate daily reports
```bash
# Add to crontab
0 9 * * * cd /path/to/scripts && bash quick-report.sh
```

---

## 📦 Backup & Restore Scripts

### 7. backup-grafana-dashboards.sh

**Purpose:** Export/import Grafana dashboards

**Features:**
- Export all dashboards organized by folder
- Import dashboards to another Grafana instance
- Filter by folder (include/exclude)
- Preserves folder structure

**Usage:**
```bash
# Export all dashboards
bash backup-grafana-dashboards.sh export https://grafana.example.com <API_KEY>

# Export to specific directory
bash backup-grafana-dashboards.sh export https://grafana.example.com <API_KEY> ./backup

# Export excluding specific folders
bash backup-grafana-dashboards.sh export https://grafana.example.com <API_KEY> ./backup \
  --exclude-folders "General,Test"

# Export only specific folders
bash backup-grafana-dashboards.sh export https://grafana.example.com <API_KEY> ./backup \
  --include-folders "Production,Alerts"

# Import dashboards
bash backup-grafana-dashboards.sh import https://target-grafana.com <API_KEY> ./backup

# Import excluding specific folders
bash backup-grafana-dashboards.sh import https://target-grafana.com <API_KEY> ./backup \
  --exclude-folders "General"
```

**API Key:** Create at Grafana > Administration > Service accounts > Add with Admin role > Generate token

---

### 8. backup-grafana-alerting.sh

**Purpose:** Export/import Grafana native alerting configuration

**Features:**
- Alert rules (by folder)
- Contact points
- Notification policies
- Mute timings
- Notification templates

**Usage:**
```bash
# Export all alerting config
bash backup-grafana-alerting.sh export https://grafana.example.com <API_KEY>

# Export to specific directory
bash backup-grafana-alerting.sh export https://grafana.example.com <API_KEY> ./backup-alerts

# Import alerting config
bash backup-grafana-alerting.sh import https://target-grafana.com <API_KEY> ./backup-alerts
```

> **Note:** This is for Grafana's native alerting. For Prometheus alerting rules (PrometheusRule CRDs), use `backup-prometheus-rules.sh`.

---

### 9. backup-prometheus-rules.sh

**Purpose:** Export/import PrometheusRule CRDs (Kubernetes)

**Features:**
- Export PrometheusRules from all namespaces
- Filter by namespace (include/exclude)
- Import to same or different cluster
- Override target namespace on import

**Usage:**
```bash
# Export all PrometheusRules
bash backup-prometheus-rules.sh export

# Export to specific file
bash backup-prometheus-rules.sh export ./prometheus-rules.yaml

# Export excluding namespaces (e.g., skip helm-managed rules)
bash backup-prometheus-rules.sh export --exclude-namespaces "prometheus,kube-system"

# Export with file and exclusions
bash backup-prometheus-rules.sh export ./rules.yaml --exclude-namespaces "prometheus"

# Export only specific namespaces
bash backup-prometheus-rules.sh export --include-namespaces "hunt,response,datascience"

# Import to original namespaces
bash backup-prometheus-rules.sh import ./prometheus-rules.yaml

# Import excluding certain namespaces
bash backup-prometheus-rules.sh import ./prometheus-rules.yaml --exclude-namespaces "prometheus"

# Import all rules to a specific namespace
bash backup-prometheus-rules.sh import ./prometheus-rules.yaml --target-namespace "monitoring"
```

> **Note:** The `prometheus` namespace typically contains rules installed by kube-prometheus-stack Helm chart. These are managed by Helm and should not be imported manually to avoid conflicts.
