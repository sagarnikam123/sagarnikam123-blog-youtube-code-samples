# VictoriaLogs — Production Architecture

## Target State Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AWS Region: us-east-1                                    │
│                                                                                      │
│  ┌────────────────────────┐   ┌────────────────────────┐   ┌──────────────────────┐ │
│  │  EKS Cluster: app-prod │   │  EKS Cluster: data-prod│   │  EKS Cluster: infra  │ │
│  │                        │   │                        │   │                      │ │
│  │  ┌──────────────────┐  │   │  ┌──────────────────┐  │   │  ┌────────────────┐  │ │
│  │  │  Microservices   │  │   │  │  Microservices   │  │   │  │  Microservices │  │ │
│  │  │  (pods)          │  │   │  │  (pods)          │  │   │  │  (pods)        │  │ │
│  │  └────────┬─────────┘  │   │  └────────┬─────────┘  │   │  └───────┬────────┘  │ │
│  │           │ stdout      │   │           │ stdout      │   │          │ stdout    │ │
│  │  ┌────────▼─────────┐  │   │  ┌────────▼─────────┐  │   │  ┌───────▼────────┐  │ │
│  │  │  Fluent Bit /    │  │   │  │  Fluent Bit /    │  │   │  │  Fluent Bit /  │  │ │
│  │  │  Vector DaemonSet│  │   │  │  Vector DaemonSet│  │   │  │  Vector DS     │  │ │
│  │  │                  │  │   │  │                  │  │   │  │                │  │ │
│  │  │ Labels:          │  │   │  │ Labels:          │  │   │  │ Labels:        │  │ │
│  │  │  cluster=app-prod│  │   │  │  cluster=data-prod│  │   │  │  cluster=infra │  │ │
│  │  │  region=us-east-1│  │   │  │  region=us-east-1│  │   │  │  region=us-east│  │ │
│  │  │  env=production  │  │   │  │  env=production  │  │   │  │  env=production│  │ │
│  │  └────────┬─────────┘  │   │  └────────┬─────────┘  │   │  └───────┬────────┘  │ │
│  └───────────┼─────────────┘   └───────────┼─────────────┘   └─────────┼────────────┘ │
│              │                              │                            │              │
│              └──────────────────┬───────────┴────────────────────────────┘              │
│                                 │ HTTP push (jsonline)                                  │
│                                 ▼                                                       │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    EKS Cluster: observability-us-east-1                            │  │
│  │                                                                                   │  │
│  │  ┌─────────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐  │  │
│  │  │  VictoriaLogs   │   │   vmalert    │   │  AlertManager │   │   Grafana    │  │  │
│  │  │  (single/cluster)│   │              │   │               │   │              │  │  │
│  │  │  Port: 9428     │   │  Evaluates   │   │  Routes to:   │   │  Dashboards  │  │  │
│  │  │                 │◄──│  LogsQL rules│──►│  - Teams      │   │  + Explore   │  │  │
│  │  │  Storage:       │   │              │   │  - OpsGenie   │   │              │  │  │
│  │  │  EBS gp3 /      │   └──────┬───────┘   └───────────────┘   └──────────────┘  │  │
│  │  │  local NVMe     │          │ write                                             │  │
│  │  └─────────────────┘          ▼                                                   │  │
│  │                        ┌──────────────┐                                           │  │
│  │                        │VictoriaMetrics│                                           │  │
│  │                        │(alert state + │                                           │  │
│  │                        │ recording     │                                           │  │
│  │                        │ rules metrics)│                                           │  │
│  │                        └──────────────┘                                           │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AWS Region: eu-west-1                                    │
│                                                                                      │
│  ┌────────────────────────┐   ┌────────────────────────┐                            │
│  │  EKS Cluster: app-prod │   │  EKS Cluster: data-prod│                            │
│  │  Fluent Bit DaemonSet  │   │  Fluent Bit DaemonSet  │                            │
│  │  Labels:               │   │  Labels:               │                            │
│  │   cluster=app-prod-eu  │   │   cluster=data-prod-eu │                            │
│  │   region=eu-west-1     │   │   region=eu-west-1     │                            │
│  └───────────┬────────────┘   └───────────┬────────────┘                            │
│              │                             │                                         │
│              └──────────────┬──────────────┘                                         │
│                             ▼                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                    EKS Cluster: observability-eu-west-1                        │   │
│  │  VictoriaLogs + vmalert + AlertManager + Grafana (same pattern)               │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Design Decisions

### 1. One VL Instance Per Region (No Cross-Region Traffic)

- Each AWS region has its own VictoriaLogs instance in a dedicated observability EKS cluster
- All EKS clusters within the same region push logs to their region's VL
- **Zero cross-region data transfer costs**
- If you need a global view, use Grafana with multiple VL data sources (one per region)

### 2. Log Separation Strategy — Stream Fields + Labels

VictoriaLogs uses **stream fields** to uniquely identify log streams. We use these fields to separate logs from different EKS clusters:

| Stream Field | Purpose | Example Values |
|-------------|---------|----------------|
| `cluster` | Identifies the source EKS cluster | `app-prod`, `data-prod`, `infra-prod` |
| `region` | AWS region | `us-east-1`, `eu-west-1` |
| `namespace` | K8s namespace | `default`, `payments`, `auth` |
| `service` | Service/deployment name | `api-gateway`, `order-service` |

**Additional non-stream fields** (stored but not used as stream identifiers):

| Field | Purpose | Example Values |
|-------|---------|----------------|
| `environment` | Environment type | `production`, `staging` |
| `pod` | Pod name (high cardinality → NOT a stream field) | `api-gateway-7d8f9-xyz` |
| `container` | Container name | `main`, `sidecar` |
| `node` | EC2 node name | `ip-10-0-1-42` |

### 3. Why Stream Fields and NOT Multi-Tenancy for Cluster Separation

Two options exist:

| Approach | Pros | Cons |
|----------|------|------|
| **Stream fields** (recommended) | Single query across all clusters; simple config; one VL endpoint | Slightly more fields indexed |
| **Multi-tenancy (AccountID)** | Hard isolation; per-tenant rate limits | Can't query across clusters easily; complex routing |

**We chose stream fields** because:
- Developers want to search across clusters (`{region="us-east-1"} error` — finds errors in ALL clusters in the region)
- Single Grafana data source per region (no per-tenant data source setup)
- AlertManager rules can span clusters
- Simpler Fluent Bit config (just add record fields, no header routing)

Use multi-tenancy only if you need hard isolation (e.g., different teams that must NOT see each other's logs).

### 4. Querying Logs by Cluster in VMUI / Grafana

```logsql
# All logs from a specific cluster
{cluster="app-prod", region="us-east-1"}

# Errors from all clusters in us-east-1
{region="us-east-1"} error

# Specific service across all clusters
{service="payment-service"} "timeout"

# Combine cluster + namespace + service
{cluster="data-prod", namespace="kafka", service="consumer"} "lag"
```

---

## Component Specifications

### VictoriaLogs (per region)

| Setting | Value | Notes |
|---------|-------|-------|
| **Mode** | Single-node (start here) or Cluster | Switch to cluster if >500GB/day |
| **Storage** | EBS gp3, 1TB+ | Size based on retention × daily ingest × compression ratio |
| **Retention** | 30 days | `-retentionPeriod=30d` |
| **Instance type** | r6i.xlarge (4 vCPU, 32GB RAM) | Adjust based on PoC results |
| **Replicas** | 1 (single) or 3+ (cluster) | |
| **Port** | 9428 | Expose via internal NLB or K8s Service |

### Fluent Bit / Vector DaemonSet (per EKS cluster)

```yaml
# Fluent Bit ConfigMap (production)
[SERVICE]
    Flush         5
    Log_Level     warn
    Daemon        off

[INPUT]
    Name              tail
    Path              /var/log/containers/*.log
    Parser            docker
    Tag               kube.*
    Refresh_Interval  10
    Mem_Buf_Limit     50MB
    Skip_Long_Lines   On

[FILTER]
    Name             kubernetes
    Match            kube.*
    Kube_URL         https://kubernetes.default.svc:443
    Kube_Tag_Prefix  kube.var.log.containers.
    Merge_Log        On
    Keep_Log         Off

[FILTER]
    Name             record_modifier
    Match            *
    Record           cluster ${CLUSTER_NAME}
    Record           region ${AWS_REGION}
    Record           environment production

[OUTPUT]
    Name             http
    Match            *
    Host             victorialogs.observability.svc.cluster.local
    Port             9428
    URI              /insert/jsonline?_stream_fields=cluster,region,namespace,service&_msg_field=log&_time_field=date
    Format           json_lines
    Json_date_format iso8601
    compress         gzip
    Retry_Limit      5
    net.keepalive    on
```

**Environment variables** set via DaemonSet env:
- `CLUSTER_NAME` — from ConfigMap or Helm values (e.g., `app-prod`)
- `AWS_REGION` — from instance metadata or Helm values

### Vector Alternative

```toml
# vector.toml (production)
[sources.kubernetes_logs]
type = "kubernetes_logs"

[transforms.add_metadata]
type = "remap"
inputs = ["kubernetes_logs"]
source = '''
.cluster = get_env_var!("CLUSTER_NAME")
.region = get_env_var!("AWS_REGION")
.environment = "production"
.service = .kubernetes.pod_labels."app.kubernetes.io/name" ?? .kubernetes.container_name
.namespace = .kubernetes.pod_namespace
'''

[sinks.victorialogs]
type = "http"
inputs = ["add_metadata"]
uri = "http://victorialogs.observability.svc.cluster.local:9428/insert/jsonline?_stream_fields=cluster,region,namespace,service&_msg_field=message&_time_field=timestamp"
encoding.codec = "json"
compression = "gzip"
```

### vmalert

| Setting | Value |
|---------|-------|
| **Evaluation interval** | 1m (default) |
| **Rules location** | ConfigMap mounted at `/etc/vmalert/` |
| **Datasource** | `http://victorialogs:9428` |
| **Notifier** | `http://alertmanager:9093` |
| **Remote write** | `http://victoriametrics:8428` |

### AlertManager Routing to Teams + OpsGenie

```yaml
# Production alertmanager.yaml
global:
  resolve_timeout: 5m
  opsgenie_api_key: '<OPSGENIE_GLOBAL_API_KEY>'

route:
  receiver: default
  group_by: ['alertname', 'service', 'cluster', 'region']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: critical-opsgenie-and-teams
      continue: false
    - match:
        severity: warning
      receiver: warning-teams-only

receivers:
  - name: default
    webhook_configs:
      - url: 'http://prometheus-msteams:2000/default'

  - name: critical-opsgenie-and-teams
    opsgenie_configs:
      - api_key: '<OPSGENIE_API_KEY>'
        message: '{{ .GroupLabels.alertname }} | {{ .GroupLabels.service }} | {{ .GroupLabels.cluster }}'
        description: '{{ .CommonAnnotations.description }}'
        priority: 'P1'
        tags: '{{ .GroupLabels.cluster }},{{ .GroupLabels.region }},victorialogs'
        responders:
          - type: team
            name: 'SRE'
    webhook_configs:
      # prometheus-msteams adapter for Teams
      - url: 'http://prometheus-msteams:2000/critical-channel'
        send_resolved: true

  - name: warning-teams-only
    webhook_configs:
      - url: 'http://prometheus-msteams:2000/warning-channel'
        send_resolved: true
```

**Teams Integration:** Use [prometheus-msteams](https://github.com/prometheus-msteams/prometheus-msteams) as a sidecar or separate deployment. It translates Prometheus alert format to Teams webhook card format.

---

## Network Architecture (Per Region)

```
┌─────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16                                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  EKS: app-prod (10.0.0.0/19)                   │    │
│  │  Fluent Bit → push to VL internal NLB           │    │
│  └───────────────────────┬─────────────────────────┘    │
│                          │                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  EKS: data-prod (10.0.32.0/19)                 │    │
│  │  Fluent Bit → push to VL internal NLB           │    │
│  └───────────────────────┬─────────────────────────┘    │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Internal NLB: victorialogs.internal.company.com │    │
│  │  Port 9428 (ingest) + Port 9428 (query)          │    │
│  └───────────────────────┬─────────────────────────┘    │
│                          │                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  EKS: observability (10.0.64.0/19)              │    │
│  │  - VictoriaLogs (NodePort/ClusterIP)             │    │
│  │  - vmalert                                       │    │
│  │  - AlertManager                                  │    │
│  │  - Grafana (ALB ingress for devs)                │    │
│  │  - VictoriaMetrics                               │    │
│  │  - prometheus-msteams                            │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**Key networking points:**
- Fluent Bit pushes to VL via **internal NLB** (no internet, no cross-region)
- Grafana exposed via **ALB + Ingress** with SSO/auth for developer access
- VMUI can be exposed alongside Grafana for power users
- All traffic stays within VPC peering or same VPC

---

## Developer Access

| Access Method | URL Pattern | Auth |
|--------------|-------------|------|
| **Grafana Explore** | `https://grafana.internal.company.com/explore` | SSO (SAML/OIDC) |
| **Grafana Dashboards** | `https://grafana.internal.company.com/d/...` | SSO |
| **VMUI (direct)** | `https://logs.internal.company.com/select/vmui/` | Basic auth or SSO proxy |
| **API (programmatic)** | `https://logs.internal.company.com/select/logsql/query` | API key or mTLS |

---

## Capacity Planning

| Metric | Formula | Example (100GB/day raw) |
|--------|---------|------------------------|
| **Disk needed** | daily_ingest × compression_ratio × retention_days | 100GB × 0.07 × 30 = ~210 GB |
| **RAM** | ~1GB per 10TB stored (VL is very efficient) | 210GB stored → <1GB RAM for data |
| **CPU** | 2-4 cores for <100GB/day single-node | 4 vCPU sufficient |
| **Network** | daily_ingest / 86400 × compression | ~80 Mbps sustained (compressed) |

VL compression ratio is typically 5-15x on structured logs. Budget for 7x as a conservative estimate.

---

## Migration Phases

| Phase | Scope | Duration |
|-------|-------|----------|
| **Phase 0: PoC** (current) | Local Mac, fake logs, validate alerting flow | 1-2 weeks |
| **Phase 1: Shadow** | Deploy VL in one region, dual-write from one EKS cluster | 2-3 weeks |
| **Phase 2: Expand** | All EKS clusters in one region push to VL; devs start using | 2-4 weeks |
| **Phase 3: Multi-region** | Deploy VL in all regions; same pattern | 2-3 weeks |
| **Phase 4: Cutover** | Deprecate Loki; VL becomes primary | 1-2 weeks |

---

## References

- [VictoriaLogs Data Ingestion: Fluent Bit](https://docs.victoriametrics.com/victorialogs/data-ingestion/fluentbit/)
- [VictoriaLogs Key Concepts (Stream Fields)](https://docs.victoriametrics.com/victorialogs/keyconcepts/)
- [VictoriaLogs Multi-tenancy](https://docs.victoriametrics.com/victorialogs/#multitenancy)
- [VictoriaLogs Alerting with vmalert](https://docs.victoriametrics.com/victorialogs/vmalert/)
- [prometheus-msteams (Teams adapter)](https://github.com/prometheus-msteams/prometheus-msteams)
- [VictoriaLogs Helm Chart](https://docs.victoriametrics.com/helm/victorialogs-single/)
