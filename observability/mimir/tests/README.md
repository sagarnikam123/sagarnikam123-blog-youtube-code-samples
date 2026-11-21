# Mimir Performance Testing

Comprehensive testing suite for Mimir - both **load testing** (expected capacity) and **stress testing** (breaking points).

## Structure

```
tests/
├── load-tests/          # Normal capacity validation
│   ├── prometheus-remote-write/
│   ├── grafana-alloy/
│   ├── avalanche/
│   ├── k6/
│   ├── promtool/
│   ├── mimirtool/
│   └── node-exporter/
│
└── stress-tests/        # Breaking point discovery
    ├── high-cardinality/
    ├── burst-traffic/
    ├── component-failure/
    ├── resource-exhaustion/
    └── chaos-mesh/
```

## Testing Types

### Load Tests (Expected Capacity)
**Goal**: Verify system handles normal and peak loads with acceptable performance.

**Scenarios**:
- Steady-state ingestion (1K-10K samples/sec)
- Multi-tenant workloads
- Query performance validation
- Mixed read/write operations

**Success Criteria**:
- ✅ Write latency < 1s (p99)
- ✅ Query latency < 5s (p99)
- ✅ Error rate < 0.1%
- ✅ No pod restarts

### Stress Tests (Breaking Points)
**Goal**: Find system limits, degradation patterns, and recovery behavior.

**Scenarios**:
- Cardinality explosion (10M+ series)
- Traffic bursts (10x-100x normal)
- Component failures (pod kills)
- Resource exhaustion (OOM, CPU)

**Failure Indicators**:
- ❌ Pod OOMKilled
- ❌ Metrics dropped
- ❌ Query timeouts
- ❌ Ring instability

## Testing Tools

| Tool | Load Testing | Stress Testing | Purpose |
|------|--------------|----------------|---------|
| **Prometheus Benchmark** | ✅ | ✅ | Remote write performance |
| **Grafana Alloy** | ✅ | ✅ | Multi-tenant ingestion |
| **Avalanche** | ✅ | ✅ | Metric generation |
| **k6** | ✅ | ✅ | API load/stress testing |
| **Promtool** | ✅ | ✅ | Query testing, rule validation |
| **Mimirtool** | ✅ | ✅ | Mimir-specific operations |
| **Node Exporter** | ✅ | ✅ | Realistic system metrics |
| **Chaos Mesh** | ❌ | ✅ | Kubernetes chaos engineering |

## Quick Start

### Load Testing

```bash
# Prometheus remote write benchmark
cd load-tests/prometheus-remote-write/prometheus-benchmark
helm install prom-bench vm/prometheus-benchmark -n mimir-test -f configs/mimir-basic.yaml

# Grafana Alloy metric collection
cd load-tests/grafana-alloy
helm install alloy grafana/alloy -n mimir-test -f helm/alloy-mimir.yaml

# Avalanche metric generator
cd load-tests/avalanche
kubectl apply -f kubernetes/avalanche-deployment.yaml -n mimir-test

# Node Exporter (realistic metrics)
cd load-tests/node-exporter
kubectl apply -f kubernetes/node-exporter-daemonset.yaml -n mimir-test

# Query testing with promtool
cd load-tests/promtool
./test-queries.sh

# Mimir operations with mimirtool
cd load-tests/mimirtool
mimirtool rules list --address=http://localhost:8080 --id=demo
```

### Stress Testing

```bash
# High cardinality test
cd stress-tests/high-cardinality
./cardinality-bomb.sh

# Burst traffic test
cd stress-tests/burst-traffic
./burst-test.sh

# Chaos engineering (pod failures)
cd stress-tests/chaos-mesh
kubectl apply -f experiments/kill-ingester.yaml

# Resource exhaustion
cd stress-tests/resource-exhaustion
./memory-stress.sh
```

## Monitoring During Tests

```bash
# Watch pod status
kubectl get pods -n mimir-test -w

# Monitor resource usage
kubectl top pods -n mimir-test
kubectl top nodes

# Check Mimir metrics
kubectl port-forward -n mimir-test svc/mimir-gateway 8080:80
curl http://localhost:8080/metrics

# Check ring status
kubectl exec -n mimir-test -l app.kubernetes.io/component=ingester -- \
  wget -q -O- http://localhost:8080/ingester/ring

# Query performance
promtool query instant http://localhost:8080 'up' \
  --header "X-Scope-OrgID: demo"
```

## Test Workflow

1. **Baseline**: Run load tests to establish normal performance
2. **Stress**: Gradually increase load to find breaking points
3. **Failure**: Test component failures and recovery
4. **Analysis**: Review metrics, logs, and resource usage
5. **Optimize**: Adjust configuration based on findings

## Tool Selection Guide

### For Write Path Testing
- **Prometheus Benchmark** - Standard remote write testing
- **Grafana Alloy** - Multi-tenant scenarios
- **Avalanche** - High-volume metric generation
- **Node Exporter** - Realistic system metrics

### For Read Path Testing
- **Promtool** - Query validation and performance
- **k6** - API load testing
- **Mimirtool** - Mimir-specific queries

### For Resilience Testing
- **Chaos Mesh** - Pod failures, network issues
- **Component Failure** - Manual failure injection
- **Resource Exhaustion** - OOM, CPU stress

### For Operations
- **Mimirtool** - Rules, alertmanager, ACL management
- **Promtool** - Rule validation, TSDB analysis
