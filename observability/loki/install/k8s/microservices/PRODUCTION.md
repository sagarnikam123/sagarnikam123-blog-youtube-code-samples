# Production Deployment Guide

> See README.md for current versions and deployment instructions

## Production Readiness Checklist

> Development deployment is functional. See README.md for setup details.

### ⚠️ Production Requirements (Missing)

#### Security
- [ ] Enable authentication (`auth_enabled: true`)
- [ ] Configure TLS encryption
- [ ] Secure MinIO credentials
- [ ] Network policies implemented
- [ ] RBAC hardening

#### Monitoring & Observability
- [x] Prometheus metrics collection
- [x] Grafana dashboards
- [ ] Alerting rules configured
- [x] Log aggregation for Loki itself (Fluent Bit)
- [x] Health check endpoints
- [x] Automated validation scripts
- [x] API functionality testing
- [x] Component log analysis tools

#### High Availability
- [ ] Multiple replicas for stateless components
- [ ] Pod disruption budgets
- [ ] Anti-affinity rules
- [ ] Multi-zone deployment
- [ ] Load balancing

#### Resource Management
- [ ] Resource limits and requests
- [ ] Horizontal Pod Autoscaling
- [ ] Persistent volume monitoring
- [ ] Storage capacity planning

#### Backup & Recovery
- [ ] MinIO backup strategy
- [ ] Configuration backup
- [ ] Disaster recovery procedures
- [ ] Data retention policies

## Scaling Guidelines

### When to Scale Components

**Scale Distributors when:**
- CPU usage > 80% consistently
- Ingestion rate > 10MB/s per distributor
- HTTP 5xx errors > 1% of requests
- Memory usage > 1GB per distributor
```bash
kubectl scale deployment loki-distributor --replicas=3 -n loki
```

**Scale Ingesters when:**
- Memory usage > 2GB per ingester
- WAL disk usage > 80%
- Chunk flush latency > 30s
- Ring unhealthy instances detected
```bash
kubectl scale statefulset loki-ingester --replicas=3 -n loki
```

**Scale Queriers when:**
- Query response time > 10s (p95)
- CPU usage > 70% consistently
- Query queue depth > 100
- Concurrent queries > 50 per querier
```bash
kubectl scale deployment loki-querier --replicas=3 -n loki
```

**Scale Query-Frontend when:**
- Query queue length > 200
- Frontend response time > 15s
- High number of query retries
```bash
kubectl scale deployment loki-query-frontend --replicas=2 -n loki
```

### Scaling Triggers & Metrics

**Monitor these key metrics:**
- `loki_distributor_ingester_append_failures_total` - Ingestion failures
- `loki_ingester_memory_chunks` - Memory usage per ingester
- `loki_request_duration_seconds` - Query latency
- `loki_ingester_wal_disk_full_failures_total` - WAL disk issues
- `prometheus_tsdb_head_series` - Series cardinality

**Automated scaling conditions:**
```yaml
# HPA example for distributors
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: loki-distributor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: loki-distributor
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Resource Sizing

**Small Environment (< 100GB/day):**
- Distributors: 2 replicas, 500m CPU, 1Gi RAM
- Ingesters: 3 replicas, 1 CPU, 2Gi RAM
- Queriers: 2 replicas, 1 CPU, 2Gi RAM

**Medium Environment (100GB-1TB/day):**
- Distributors: 3 replicas, 1 CPU, 2Gi RAM
- Ingesters: 6 replicas, 2 CPU, 4Gi RAM
- Queriers: 4 replicas, 2 CPU, 4Gi RAM

**Large Environment (> 1TB/day):**
- Distributors: 6 replicas, 2 CPU, 4Gi RAM
- Ingesters: 12 replicas, 4 CPU, 8Gi RAM
- Queriers: 8 replicas, 4 CPU, 8Gi RAM

> See CONFIGURATION.md for performance tuning parameters

## Monitoring Setup

### Essential Metrics to Monitor
- **Ingestion rate**: logs/second per distributor
- **Query latency**: p95, p99 response times
- **Storage usage**: MinIO bucket size growth
- **Error rates**: HTTP 4xx/5xx responses
- **Resource usage**: CPU, memory, disk per component

### Alerting Rules
```yaml
# High ingestion error rate
- alert: LokiHighIngestionErrorRate
  expr: rate(loki_distributor_ingester_append_failures_total[5m]) > 0.1

# Query latency high
- alert: LokiHighQueryLatency
  expr: histogram_quantile(0.99, rate(loki_request_duration_seconds_bucket[5m])) > 10
```

> See LABELS.md for labeling standards and operational commands

## Upgrade Procedures

### Rolling Update Strategy
1. Update configurations first
2. Upgrade stateless components (distributors, queriers)
3. Upgrade stateful components (ingesters) one by one
4. Verify functionality after each step

### Rollback Plan
1. Keep previous configuration versions
2. Test rollback procedures regularly
3. Monitor metrics during upgrades
4. Have emergency contact procedures

> See README.md for operational scripts and LABELS.md for label-based operations

## Production Troubleshooting

> See README.md for diagnostic tools and basic troubleshooting

### Production-Specific Issues
1. **High load**: Use scaling guidelines above
2. **Storage full**: Implement retention policies, monitor growth
3. **Security incidents**: Rotate credentials, review access logs
4. **Multi-zone failures**: Follow disaster recovery procedures
