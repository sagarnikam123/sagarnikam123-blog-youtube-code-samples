# VictoriaLogs vs Grafana Loki — Detailed Comparison

---

## 1. Architecture

| Aspect | VictoriaLogs | Grafana Loki |
|--------|-------------|--------------|
| **Deployment model** | Single binary, zero external dependencies | Monolithic mode OR microservices (distributor, ingester, querier, compactor, index-gateway, ruler) |
| **Scaling** | Vertical on single-node; horizontal cluster mode available (linear scaling across nodes) | Horizontal via microservices mode; read/write path separation |
| **Storage backend** | Local disk (SSD/NVMe recommended); S3/object storage on roadmap | Local filesystem, AWS S3, GCS, Azure Blob, MinIO — mature object store support |
| **Indexing approach** | Full-text index + column-oriented storage; indexes all fields automatically | Label-based index only; full-text search on log content requires filtering after label match |
| **Schema** | Schemaless — ingests any JSON/structured log without predefined schema | Schema-less for log lines but labels need to be kept low-cardinality |

**Verdict:** VL is simpler to deploy and operate. Loki offers more flexibility for large distributed setups with object storage tiering.

---

## 2. Resource Usage & Performance

| Metric | VictoriaLogs | Grafana Loki |
|--------|-------------|--------------|
| **RAM usage** | Up to 30x less than Elasticsearch; significantly less than Loki for same workload | Higher memory pressure, especially with high-cardinality labels and large queries |
| **Disk usage** | Up to 15x less storage due to superior compression | Chunk-based storage with moderate compression; relies on object store for cost savings |
| **CPU** | Low CPU usage at ingest and query time | Higher CPU for compaction, query processing over large time ranges |
| **Query range** | Handles queries over hours/days/weeks efficiently | Struggles beyond 30–60 min ranges without recording rules, caching, or query-frontend sharding |
| **Ingest throughput** | Single node can handle TBs/day depending on hardware | Needs horizontal scaling (multiple ingesters) for TB/day workloads |

**Verdict:** VL wins on raw resource efficiency. Real-world reports confirm 3–10x less RAM and better query latency over large time ranges.

---

## 3. Query Language

| Feature | VictoriaLogs (LogsQL) | Grafana Loki (LogQL) |
|---------|----------------------|---------------------|
| **Full-text search** | Native, fast full-text search across all fields | Must filter by labels first, then `|=` or regex on content |
| **Aggregations** | Pipes-based: `| stats count() by (field)` | `count_over_time`, `rate`, `sum` — Prometheus-style |
| **Transformations** | Extract, rename, calculate at query time via pipes | Limited: `| json`, `| logfmt`, `| regexp` parsers |
| **SQL-like operations** | Joins, subqueries, sorting, post-filters via pipes | Not available |
| **Learning curve** | Intuitive for devs, pipes are similar to Unix shell | Steeper; combines label selectors with PromQL-like syntax |
| **Migration** | Official LogQL → LogsQL conversion guide available | N/A |

**Verdict:** LogsQL is more powerful and intuitive for ad-hoc log investigation. LogQL integrates better with Prometheus/PromQL if you're already in that ecosystem.

---

## 4. Data Ingestion & Collector Support

| Collector/Protocol | VictoriaLogs | Grafana Loki |
|-------------------|-------------|--------------|
| **Fluent Bit** | ✅ Native support (HTTP JSON output) | ✅ Loki output plugin |
| **Fluentd** | ✅ Supported | ✅ Supported |
| **Filebeat** | ✅ Elasticsearch Bulk API compatible | ❌ Not native (needs Logstash or custom) |
| **OpenTelemetry** | ✅ OTLP protocol | ✅ OTLP protocol |
| **Syslog (RFC3164/5424)** | ✅ Native TCP/UDP syslog listener | ❌ Needs Promtail/Alloy as intermediary |
| **Promtail** | ✅ Compatible (Loki push API supported) | ✅ Native agent |
| **Grafana Alloy** | ✅ Supported | ✅ Recommended agent |
| **Datadog API** | ✅ Compatible | ❌ Not supported |
| **Journald** | ✅ Native protocol support | ✅ Via Promtail |
| **Elasticsearch Bulk API** | ✅ Drop-in for ES migration | ❌ Not supported |

**Verdict:** VL supports more ingestion protocols natively. Since you use Fluent Bit, both work — VL just needs the HTTP output plugin pointed at `/insert/jsonline`.

---

## 5. Grafana Integration

| Feature | VictoriaLogs | Grafana Loki |
|---------|-------------|--------------|
| **Data source plugin** | ✅ Official plugin (Apache-2.0) | ✅ Native, first-class support |
| **Explore mode** | ✅ Works | ✅ Full support with log context |
| **Live streaming** | ✅ Supported | ✅ Supported |
| **Dashboards** | ✅ Works, requires LogsQL | ✅ Mature, many community dashboards |
| **Alerting (Grafana Alerting)** | ✅ Supported via data source | ✅ Native integration |
| **Log-based alerting (Ruler)** | ⚠️ Via vmalert (external) | ✅ Built-in Loki Ruler for LogQL alerts |
| **Ad Hoc filters** | ✅ Supported | ✅ Supported |

**Verdict:** Loki has deeper Grafana integration out of the box. VL works well but the plugin is still maturing — fewer community dashboards and templates.

---

## 6. Multi-Tenancy

| Feature | VictoriaLogs | Grafana Loki |
|---------|-------------|--------------|
| **Tenant model** | AccountID + ProjectID (32-bit integers), default 0:0 | X-Scope-OrgID HTTP header |
| **Isolation** | Query and storage isolation per tenant | Full isolation per tenant |
| **Per-tenant limits** | Configurable | Extensive (ingestion rate, query limits, retention per tenant) |
| **Maturity** | Functional but less battle-tested | Production-proven in large multi-tenant SaaS |

**Verdict:** Loki's multi-tenancy is more mature and flexible. VL supports it but with simpler configuration.

---

## 7. High Availability & Clustering

| Feature | VictoriaLogs | Grafana Loki |
|---------|-------------|--------------|
| **Single-node HA** | Replication not built-in; use external (EBS snapshots, etc.) | Same — monolithic mode has no built-in replication |
| **Cluster mode** | Available — horizontal scaling across nodes with linear performance | Microservices mode with ring-based replication |
| **Replication factor** | Cluster mode handles this | Configurable (typically RF=3) |
| **Data durability** | Depends on underlying disk/storage | Object store provides durability by default |

**Verdict:** Loki in microservices mode is more mature for HA. VL cluster mode is newer but actively developed.

---

## 8. Operational Complexity

| Aspect | VictoriaLogs | Grafana Loki |
|--------|-------------|--------------|
| **Setup time** | Minutes — download binary, run | Moderate — config for ingester, compactor, storage backend |
| **Configuration** | Minimal flags needed, sensible defaults | YAML config can be complex (especially for distributed mode) |
| **Upgrades** | Single binary replacement | Rolling upgrades across microservices |
| **Compaction** | Automatic, internal | Requires compactor component |
| **Retention** | Simple flag: `-retentionPeriod=30d` | Per-tenant retention rules in config |
| **Monitoring the monitor** | Built-in metrics at `/metrics` | Built-in metrics; needs separate Prometheus to scrape |
| **Troubleshooting** | Single process, single log stream | Multiple components = multiple failure points |

**Verdict:** VL is dramatically simpler to operate. This matters for small SRE teams.

---

## 9. Retention Policies

| Feature | VictoriaLogs | Grafana Loki |
|---------|-------------|--------------|
| **Global retention** | ✅ `-retentionPeriod=30d` flag | ✅ `retention_period` in limits_config |
| **Per-tenant retention** | ❌ Not supported (same retention for all tenants) | ✅ Configurable per tenant in `overrides` |
| **Per-stream/label retention** | ❌ Not supported | ✅ `retention_stream` with label selectors (e.g., `{namespace="payments"}` → 30d) |
| **Per-namespace retention** | ❌ Not supported natively | ✅ Via stream-based retention selectors |
| **Per-service retention** | ❌ Not supported natively | ✅ Via stream-based retention selectors |
| **Roadmap** | Not listed on current roadmap | Already available |

### VictoriaLogs Retention — How It Works

```bash
# Single global value — applies to ALL logs in this instance
./victoria-logs-prod -retentionPeriod=30d
```

No per-label, per-stream, per-tenant, or per-namespace granularity. That's it.

### Grafana Loki Retention — How It Works

```yaml
# Loki config — granular retention
limits_config:
  retention_period: 7d            # Global default

overrides:
  tenant-compliance:
    retention_period: 90d          # Per-tenant override

  retention_stream:
    - selector: '{namespace="payments"}'
      period: 30d                  # Keep payments logs for 30 days
    - selector: '{service="audit-service"}'
      period: 90d                  # Keep audit logs for 90 days
    - selector: '{namespace="load-testing"}'
      period: 1d                   # Aggressively expire test logs
```

### Workaround for VictoriaLogs Multi-Retention

Since VL doesn't support per-label retention, the only option is **multiple VL instances** with routing at the collector level:

```
Fluent Bit / Vector
  ├── service IN (payment, audit, compliance)  →  VL Instance A (-retentionPeriod=30d)
  └── everything else                          →  VL Instance B (-retentionPeriod=7d)
```

This adds operational complexity (two instances, two Grafana data sources, routing config).

**Verdict:** Loki wins clearly here. Per-stream retention is a significant operational advantage for orgs with compliance/audit requirements. VL requires multiple instances as a workaround.

---

## 10. Log Exclusion & Filtering

| Feature | VictoriaLogs | Grafana Loki |
|---------|-------------|--------------|
| **Server-side exclusion (drop at storage)** | ❌ No built-in drop/filter at ingest | ❌ No built-in drop/filter at ingest |
| **Collector-level exclusion** | ✅ Via Fluent Bit / Vector filters | ✅ Via Promtail / Alloy / Fluent Bit filters |
| **Exclude by namespace** | ✅ Fluent Bit `Exclude_Path` or `grep` filter | ✅ Promtail/Alloy pipeline stage `drop` |
| **Exclude by service/label** | ✅ Fluent Bit `grep` filter on any field | ✅ Promtail relabel_configs `action: drop` |
| **Exclude by pod annotation** | ✅ `fluentbit.io/exclude: "true"` | ✅ Promtail `__meta_kubernetes_pod_annotation_*` |
| **Exclude by log content** | ✅ Fluent Bit `grep` filter on message | ✅ Promtail pipeline `match` + `drop` |
| **Drop at ingest API** | ❌ VL accepts everything sent to it | ⚠️ Loki Distributor can enforce label rules but not content-based drops |

### How Exclusion Works (Both Systems)

Neither VL nor Loki has a "don't store logs matching label X" at the server side. Exclusion is always done at the **collector/shipper** before logs reach the backend.

#### Fluent Bit Exclusion Patterns (Works for Both VL and Loki)

```ini
# 1. Exclude entire namespaces (never reads the file — most efficient)
[INPUT]
    Name          tail
    Path          /var/log/containers/*.log
    Exclude_Path  /var/log/containers/*_kube-system_*,/var/log/containers/*_istio-system_*,/var/log/containers/*_monitoring_*

# 2. Exclude by pod annotation (fluentbit.io/exclude: "true")
[FILTER]
    Name             kubernetes
    Match            kube.*
    K8S-Logging.Exclude  On

# 3. Exclude specific service
[FILTER]
    Name    grep
    Match   *
    Exclude service debug-tool

# 4. Exclude sidecar containers
[FILTER]
    Name    grep
    Match   *
    Exclude container istio-proxy

# 5. Exclude healthcheck log lines
[FILTER]
    Name    grep
    Match   *
    Exclude log /health
```

#### Promtail/Alloy Exclusion (Loki ecosystem)

```yaml
# Promtail pipeline stages
pipeline_stages:
  - match:
      selector: '{namespace="kube-system"}'
      action: drop
  - match:
      selector: '{service="debug-tool"}'
      action: drop
  - match:
      selector: '{container="istio-proxy"}'
      action: drop
```

### Exclusion Methods Summary

| What to Exclude | Fluent Bit (VL + Loki) | Promtail/Alloy (Loki) | Vector (VL + Loki) |
|----------------|------------------------|------------------------|---------------------|
| Namespace | `Exclude_Path` in INPUT | `action: drop` by selector | `filter` transform condition |
| Specific pod | `fluentbit.io/exclude` annotation | `__meta_*` relabel drop | Pod label condition |
| Service/label | `grep` FILTER + `Exclude` | `action: drop` by label | `filter` condition |
| Container (sidecar) | `grep` on container name | `action: drop` by container | `filter` condition |
| Log content (healthcheck) | `grep` on `log` field | `match` + `drop` pipeline | `filter` on message field |
| Complex multi-condition | Lua script | Pipeline stages | VRL (Vector Remap Language) |

**Verdict:** Both VL and Loki are equal here — exclusion happens at the collector level, not at the storage level. The tooling (Fluent Bit, Vector, Promtail) is mature for both backends.

---

## 11. Alerting

| Feature | VictoriaLogs | Grafana Loki |
|---------|-------------|--------------|
| **Log-based alerting** | Via vmalert with AlertManager | Built-in Ruler component evaluates LogQL rules |
| **Integration with AlertManager** | ✅ | ✅ |
| **Recording rules** | Supported via vmalert | Built-in |
| **Complexity** | Separate vmalert process needed | All-in-one with Loki |

**Verdict:** Loki's built-in ruler is simpler if you're already using Loki. VL needs an external vmalert setup but it's lightweight.

---

## 12. Ecosystem & Community

| Aspect | VictoriaLogs | Grafana Loki |
|--------|-------------|--------------|
| **License** | Open source (Apache-2.0 community; enterprise available) | AGPLv3 (Loki), Apache-2.0 (some components) |
| **Maturity** | GA since 2024; cluster mode released mid-2025 | GA since 2019; very mature |
| **Community size** | Growing; VictoriaMetrics ecosystem | Very large; Grafana Labs backing |
| **Commercial support** | VictoriaMetrics enterprise plans | Grafana Cloud, Grafana Enterprise Logs |
| **Documentation** | Good, improving | Excellent, comprehensive |
| **Third-party integrations** | Growing | Extensive |

**Verdict:** Loki has a larger community and more integrations. VL is catching up quickly and the VictoriaMetrics ecosystem is well-regarded.

---

## 13. Migration Path (Loki → VictoriaLogs)

| Step | Effort |
|------|--------|
| Fluent Bit config change (add HTTP output to VL) | Low — add a second `[OUTPUT]` block |
| Run dual-write (both Loki and VL receive same logs) | Low — no application changes |
| Learn LogsQL (official LogQL → LogsQL migration guide) | Medium — syntax is different but simpler |
| Move Grafana dashboards to VL data source | Medium — rewrite queries in LogsQL |
| Migrate log-based alerts | Medium — set up vmalert + AlertManager |
| Decommission Loki | Low — once confidence is established |

---

## 14. Cost Comparison (Estimated for EC2)

| Factor | VictoriaLogs | Grafana Loki |
|--------|-------------|--------------|
| **Compute (EC2)** | Smaller instance needed (less RAM/CPU) | Larger instance or multiple components |
| **Storage (EBS/S3)** | Less disk due to better compression | More disk locally; cheaper on S3 long-term |
| **Operational cost** | Less toil, fewer components to manage | More operational overhead |
| **License cost** | Free (community) or enterprise pricing | Free (community) or Grafana Enterprise Logs |

---

## 15. Recommendation for Our Setup

| Scenario | Recommendation |
|----------|---------------|
| **PoC / Evaluation** | Run VL on same EC2, dual-write from Fluent Bit |
| **Small-medium workload (< 100 GB/day)** | VL single-node — simpler, cheaper, faster |
| **Large workload requiring object storage** | Loki with S3 backend — more mature for this pattern |
| **Need log-based alerting today** | Keep Loki for ruler; evaluate vmalert in parallel |
| **Want simplest possible operations** | VictoriaLogs wins clearly |

---

## 16. VictoriaLogs Alerting — Deep Dive

### How Alerts Work in VictoriaLogs

VictoriaLogs does NOT have a built-in alerting ruler. Instead, it uses **vmalert** — a separate lightweight process that evaluates rules against VictoriaLogs and forwards firing alerts to AlertManager.

**Architecture:**

```
┌──────────────┐         ┌──────────────┐         ┌────────────────┐
│ VictoriaLogs │◄────────│   vmalert    │────────►│  AlertManager  │
│  (datasource)│  query  │ (rule eval)  │  notify │                │
└──────────────┘         └──────┬───────┘         └───────┬────────┘
                                │                         │
                                │ write state             │ route
                                ▼                         ▼
                        ┌──────────────┐         ┌────────────────┐
                        │VictoriaMetrics│         │ Slack/PD/Email │
                        │(remote write)│         │  (receivers)   │
                        └──────────────┘         └────────────────┘
```

### Quick Start Command

```bash
./vmalert \
  -rule=/etc/vmalert/rules/*.yaml \
  -datasource.url=http://victorialogs:9428 \
  -notifier.url=http://alertmanager:9093 \
  -remoteWrite.url=http://victoriametrics:8428 \
  -remoteRead.url=http://victoriametrics:8428 \
  -rule.defaultRuleType=vlogs
```

### What Can You Alert On?

Alerts are **NOT limited to keyword "error"**. You can alert on anything queryable in LogsQL:

| Alert Type | Example LogsQL Expression |
|-----------|--------------------------|
| **Keyword-based** (error/warn) | `'{env=prod} error OR warn \| stats count() as errors \| filter errors:>10'` |
| **Status code patterns** | `'* \| extract "status_code=<code>" \| stats count() if (code:~"5.*") as server_errors \| filter server_errors:>5'` |
| **Rate of specific messages** | `'{service=payment} "timeout" \| stats count() as timeouts \| filter timeouts:>3'` |
| **Percentage thresholds** | `'* \| stats count() if (error) as errors, count() as total \| math (errors/total)*100 as error_pct \| filter error_pct:>15'` |
| **By pod/service/host** | `'{env=prod} status:in(error,warn) \| stats by (k8s.pod.name) count() as error_logs \| filter error_logs:>10'` |
| **Latency from logs** | `'* \| stats quantile(0.99, duration_ms) as p99 \| filter p99:>5000'` |
| **Absence of logs** (dead service) | `'{service=api-gateway} \| stats count() as logs \| filter logs:<1'` |
| **Failed request ratio by IP** | `'* \| extract "ip=<ip>" \| stats by (ip) count() if (code:~"4.*") as failed, count() as total \| math (failed/total)*100 as pct \| filter pct:>10'` |

### Example Alert Rule File (`alert.rules.yaml`)

```yaml
groups:
  - name: ProductionErrors
    type: vlogs
    interval: 5m
    rules:
      # Alert: Too many errors on a single pod
      - alert: PodErrorSpike
        expr: '{env=prod} status:in(error,warn) | stats by (k8s.pod.name) count() as error_logs | filter error_logs:>10'
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High error count on pod {{ $labels.k8s_pod_name }}"
          description: "Pod {{ $labels.k8s_pod_name }} has {{ $value }} error/warn logs in the last 5 minutes"

      # Alert: Service error rate > 15%
      - alert: HighErrorRate
        expr: '{env=prod} | stats by (service) count() if (error) as errors, count() as total | math (errors/total)*100 as error_pct | filter error_pct:>15'
        for: 10m
        labels:
          severity: critical
          team: sre
        annotations:
          summary: "Service {{ $labels.service }} error rate is {{ $value }}%"

      # Alert: Payment service timeouts
      - alert: PaymentTimeouts
        expr: '{service=payment} "connection timeout" OR "request timeout" | stats count() as timeouts | filter timeouts:>3'
        for: 5m
        labels:
          severity: critical
          team: payments
        annotations:
          summary: "Payment service has {{ $value }} timeouts in the last 5 minutes"
```

### Recording Rules (Pre-compute Metrics from Logs)

```yaml
groups:
  - name: LogMetrics
    type: vlogs
    interval: 5m
    rules:
      - record: service_request_count_5m
        expr: '{env=prod} | stats by (service) count() as requests'

      - record: service_error_rate_5m
        expr: '{env=prod} | stats by (service) count() if (error) as errors, count() as total | math (errors/total)*100 as error_pct | fields service, error_pct'
```

These recording rules generate time-series metrics that get written to VictoriaMetrics and can be used in Grafana dashboards or further Prometheus-style alerts.

### AlertManager Routing

AlertManager routing works **exactly the same** as with any other Prometheus-compatible source. vmalert sends alerts in standard Prometheus alert format:

```yaml
# alertmanager.yml
route:
  receiver: default
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: pagerduty-sre
    - match:
        team: payments
      receiver: slack-payments
    - match:
        severity: warning
      receiver: slack-platform

receivers:
  - name: default
    slack_configs:
      - channel: '#alerts-general'
        send_resolved: true

  - name: pagerduty-sre
    pagerduty_configs:
      - service_key: '<PD_SERVICE_KEY>'

  - name: slack-payments
    slack_configs:
      - channel: '#alerts-payments'
        send_resolved: true

  - name: slack-platform
    slack_configs:
      - channel: '#alerts-platform'
        send_resolved: true
```

### Key Points on Alerting

- **Labels** added in alert rules (team, severity, etc.) are used for AlertManager routing — same pattern as Prometheus alerts
- **`for` duration** — alert must be continuously firing for this period before it triggers (avoids flapping)
- **Time filter** — vmalert auto-appends `_time:<interval>` to queries, so a rule with `interval: 5m` checks the last 5 minutes of logs
- **Multi-tenancy** — use `headers: ["AccountID: X"]` in the rule group to target a specific VL tenant
- **Backfilling** — vmalert supports replaying rules against historical logs

---

## 17. Developer Log Access — UI Options

### Option 1: Built-in VMUI (Zero Setup)

VictoriaLogs ships with a built-in web UI at:

```
http://<victorialogs-host>:9428/select/vmui/
```

**Features:**
- Full LogsQL query editor with autocomplete
- Time range selection
- Log distribution histogram over time
- Stream grouping (group logs by fields)
- Live streaming / tail mode
- JSON, table, and grouped view formats
- Query history and saved favorites
- No extra setup needed — just expose port 9428

**Best for:** Quick access, SREs, developers who want to search logs without Grafana.

### Option 2: Grafana with VictoriaLogs Data Source

Install the official [victorialogs-datasource](https://github.com/VictoriaMetrics/victorialogs-datasource) plugin:

```bash
grafana-cli plugins install victoriametrics-logs-datasource
```

**Features:**
- Explore mode with LogsQL
- Live streaming
- Build dashboards mixing logs + metrics
- Ad Hoc filters for quick field-based filtering
- Alerting via Grafana Alerting (unified)

**Best for:** Teams already using Grafana who want logs alongside metrics/traces.

### Option 3: Command-Line Tool

VictoriaLogs provides an interactive CLI for terminal-based log querying:

```bash
# Query logs from the last hour
curl -s "http://victorialogs:9428/select/logsql/query" -d 'query={service=api} error' -d 'limit=100'
```

**Best for:** CI/CD pipelines, scripts, developers who prefer terminal.

### Access Control for Developers

| Approach | How |
|----------|-----|
| **Direct VMUI access** | Expose VL port via internal LB or VPN; developers hit `http://victorialogs:9428/select/vmui/` |
| **Grafana RBAC** | Use Grafana orgs/teams to control who can query which data sources |
| **Multi-tenancy** | Separate tenants per team (AccountID); developers only see their team's logs |
| **vmauth proxy** | Put vmauth in front of VL to enforce auth and per-user query limits |

### Comparison: Developer Experience

| Aspect | VictoriaLogs VMUI | Grafana + VL Plugin | Loki + Grafana |
|--------|-------------------|--------------------:|----------------|
| **Setup effort** | Zero (built-in) | Install plugin + configure datasource | Native |
| **Query speed** | Fast (direct) | Fast | Slower on large ranges |
| **Learning curve** | LogsQL (intuitive) | LogsQL in Grafana | LogQL (steeper) |
| **Full-text search** | Native, instant | Native via plugin | Limited |
| **Live tail** | ✅ | ✅ | ✅ |
| **Standalone access** | ✅ No Grafana needed | ❌ Needs Grafana | ❌ Needs Grafana |
| **Mobile friendly** | Basic web UI | Grafana responsive | Grafana responsive |

### Recommended Setup for Your PoC

```
Developers  ──►  VMUI (http://victorialogs:9428/select/vmui/)   ← for quick searches
    │
    └──────────►  Grafana (VL datasource in Explore)             ← for dashboards + correlation with metrics
```

Both can run simultaneously. VMUI gives zero-friction access without any Grafana dependency.

---

## 18. References

- [VictoriaLogs Documentation](https://docs.victoriametrics.com/victorialogs)
- [VictoriaLogs Alerting with vmalert](https://docs.victoriametrics.com/victorialogs/vmalert/)
- [vmalert Full Docs](https://docs.victoriametrics.com/victoriametrics/vmalert/)
- [VictoriaLogs Cluster Mode](https://docs.victoriametrics.com/victorialogs/cluster/)
- [VictoriaLogs Architecture Basics](https://victoriametrics.com/blog/victorialogs-architecture-basics)
- [LogsQL Reference](https://docs.victoriametrics.com/victorialogs/logsql/)
- [LogQL to LogsQL Migration](https://docs.victoriametrics.com/victorialogs/logql-to-logsql/)
- [Fluent Bit → VictoriaLogs Setup](https://docs.victoriametrics.com/victorialogs/data-ingestion/fluentbit/)
- [Grafana Loki Architecture](https://grafana.com/docs/loki/latest/get-started/overview/)
- [VictoriaLogs Grafana Plugin](https://github.com/VictoriaMetrics/victorialogs-datasource)
- [VL vs Loki Benchmarks — TrueFoundry](https://www.truefoundry.com/blog/victorialogs-vs-loki)
- [Real-world dual-write experience](https://rtfm.co.ua/en/victorialogs-an-overview-run-in-kubernetes-logsql-and-grafana/)
- [VictoriaLogs Recording Rules with vmalert](https://itnext.io/victorialogs-creating-recording-rules-with-vmalert-f606c2b94c5e)
