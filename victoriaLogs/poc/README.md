# VictoriaLogs PoC — Deployment Options

Three deployment approaches for different stages of evaluation:

```
poc/
├── binary/     ← Simplest. Run binaries directly on Mac. Best for quick testing.
├── docker/     ← Docker Compose. Full stack in one command. Best for team demos.
└── helm/       ← Helm charts for EKS. Production-ready templates.
```

## Which One to Start With?

| Stage | Use | Why |
|-------|-----|-----|
| **Day 1 — Quick test** | `binary/` | Fastest startup, no Docker needed, easy to debug |
| **Day 2 — Full flow** | `docker/` | One `docker-compose up`, everything connected |
| **Day 3+ — EKS deploy** | `helm/` | Production-grade, per-region, per-cluster |

## What Each Setup Includes

| Component | binary/ | docker/ | helm/ |
|-----------|---------|---------|-------|
| VictoriaLogs | ✅ | ✅ | ✅ |
| VictoriaMetrics | ✅ | ✅ | ✅ |
| vmalert (alerting) | ✅ | ✅ | ✅ |
| AlertManager | ✅ | ✅ | ✅ |
| Grafana | ❌ (use VMUI) | ✅ | ✅ |
| Fluent Bit | ✅ | ✅ | ✅ (DaemonSet) |
| Fake log generator | ✅ (flog) | ✅ (flog) | N/A (real pods) |
| Webhook receiver | ✅ | ✅ | N/A (real Teams/OpsGenie) |
| Teams integration | Simulated | Simulated | prometheus-msteams |
| OpsGenie integration | Simulated | Simulated | Native AlertManager config |

## Multi-Cluster Log Separation

All three setups use the same strategy for distinguishing logs from different EKS clusters:

**Stream fields** injected by Fluent Bit/Vector at the collector level:

```
cluster   = eks-cluster-name    (e.g., app-prod, data-prod)
region    = aws-region           (e.g., us-east-1, eu-west-1)
namespace = k8s-namespace        (e.g., payments, auth)
service   = app-name             (e.g., api-gateway, order-service)
```

Query examples:
```logsql
# All logs from one cluster
{cluster="app-prod"}

# Errors across all clusters in a region
{region="us-east-1"} error

# Specific service, any cluster
{service="payment-service"} "timeout"
```

## Related Docs

- [VictoriaLogs vs Loki Comparison](../docs/VictoriaLogs_vs_Loki_Comparison.md)
- [Production Architecture](../docs/production-architecture.md)
