# Test Types

This document describes each test type available in the Prometheus Testing Framework.

## Overview

| Test Type | Purpose | Default Duration | Enabled by Default |
|-----------|---------|------------------|-------------------|
| Sanity | Quick validation | 60s | Yes |
| Integration | Component verification | 5min | Yes |
| Load | Performance under load | 30min | Yes |
| Stress | Breaking point discovery | 20min | Yes |
| Performance | Benchmark measurements | 10min | Yes |
| Scalability | Scaling behavior | 30min | Yes |
| Endurance | Long-running stability | 24h | No |
| Reliability | Failure handling | 15min | Yes |
| Chaos | Unexpected failures | 20min | No |
| Regression | Version comparison | 30min | No |
| Security | Security validation | 10min | Yes |

---

## Sanity Tests

Quick validation tests to verify Prometheus is functioning correctly after deployment.

### What It Tests

- HTTP API accessibility at `/api/v1/status/config`
- Health endpoint (`/-/healthy`) returns HTTP 200
- Readiness endpoint (`/-/ready`) returns HTTP 200
- Self-monitoring (`up{job="prometheus"} == 1`)
- Basic PromQL query execution
- Web UI accessibility at `/graph`

### When to Use

- After initial deployment
- After configuration changes
- As a smoke test in CI/CD pipelines
- Before running more intensive tests

### Running Sanity Tests

```bash
python3 -m tests.cli run --type sanity --platform docker
```


### Configuration

```yaml
sanity:
  enabled: true
  timeout: 60s
  healthcheck_endpoints:
    - "/-/healthy"
    - "/-/ready"
    - "/api/v1/status/runtimeinfo"
```

### Pass/Fail Criteria

| Metric | Threshold |
|--------|-----------|
| API Response Time | < 1000ms |
| All endpoints accessible | Required |

---

## Integration Tests

Verify Prometheus works correctly with other monitoring ecosystem components.

### What It Tests

- Node Exporter metrics scraping
- Custom application metrics via `/metrics` endpoint
- Alert delivery to Alertmanager
- Remote write to backend (Mimir/Thanos)
- Grafana data source connectivity
- ServiceMonitor discovery (Kubernetes)
- Federation endpoint (distributed mode)

### When to Use

- After deploying the full monitoring stack
- When adding new scrape targets
- When configuring remote write
- Before production deployment

### Running Integration Tests

```bash
python3 -m tests.cli run --type integration --platform minikube
```

### Configuration

```yaml
integration:
  enabled: true
  components:
    - node-exporter
    - alertmanager
    - grafana
  test_federation: true  # Only for distributed mode
```

---

## Load Tests

Simulate realistic production workloads to measure performance characteristics.

### What It Tests

- Query response times under load (p50, p90, p99)
- Scrape duration and success rate
- Memory and CPU utilization
- Throughput at various target counts (100, 1000, 10000)
- Active series handling (10K, 100K, 1M, 10M)

### When to Use

- Capacity planning
- Performance baseline establishment
- Before production deployment
- After infrastructure changes

### Running Load Tests

```bash
# Default configuration
python3 -m tests.cli run --type load --platform eks

# Custom k6 options
python3 -m tests.cli run --type load --k6-vus 100 --k6-duration 30m
```

### Configuration

```yaml
load:
  enabled: true
  duration: 30m
  k6:
    vus: 100
    scripts:
      - "k6/query-load.js"
      - "k6/query-range-load.js"
      - "k6/remote-write-load.js"
  targets:
    - 100
    - 1000
    - 10000
  series:
    - 10000
    - 100000
    - 1000000
```

### Pass/Fail Criteria

| Metric | Threshold |
|--------|-----------|
| Query Latency p99 | < 500ms |
| Scrape Success Rate | > 99% |
| CPU Utilization | < 80% |
| Memory Utilization | < 85% |

---

## Stress Tests

Push Prometheus beyond normal limits to find breaking points and understand failure modes.

### What It Tests

- High cardinality scenarios (millions of unique label combinations)
- High ingestion rate limits (samples per second)
- Concurrent query load
- Memory pressure scenarios (approaching OOM)
- Progressive load increase until failure

### When to Use

- Determining system limits
- Understanding failure modes
- Capacity planning for peak loads
- Comparing monolithic vs distributed performance

### Running Stress Tests

```bash
python3 -m tests.cli run --type stress --platform eks
```


### Configuration

```yaml
stress:
  enabled: true
  k6:
    stages:
      - duration: "5m"
        target: 100
      - duration: "10m"
        target: 500
      - duration: "5m"
        target: 1000
  cardinality:
    max_labels: 1000000
  ingestion:
    max_samples_per_second: 1000000
  queries:
    concurrent: 100
```

### Pass/Fail Criteria

| Metric | Threshold |
|--------|-----------|
| Min Series Before Failure | > 1,000,000 |
| Min Ingestion Rate | > 100,000 samples/s |

---

## Performance Tests

Measure response times, throughput, and resource utilization for benchmarking.

### What It Tests

- Simple query latency (single metric lookup)
- Complex query latency (aggregations, rate, joins)
- Range query latency (1h, 6h, 24h, 7d ranges)
- Remote write throughput and latency
- TSDB compaction time and resource usage
- WAL replay time on restart
- API endpoint response times (`/api/v1/labels`, `/api/v1/series`)

### When to Use

- Establishing performance baselines
- Comparing versions or configurations
- Identifying performance regressions
- Optimizing query patterns

### Running Performance Tests

```bash
python3 -m tests.cli run --type performance --platform minikube
```

### Configuration

```yaml
performance:
  enabled: true
  iterations: 100
  k6:
    scripts:
      - "k6/benchmark.js"
  api_endpoints:
    - "/api/v1/query"
    - "/api/v1/query_range"
    - "/api/v1/labels"
    - "/api/v1/label/__name__/values"
    - "/api/v1/series"
```

### Pass/Fail Criteria

| Metric | Threshold |
|--------|-----------|
| Simple Query Latency | < 50ms |
| Complex Query Latency | < 500ms |
| Range Query (1h) | < 200ms |
| Range Query (24h) | < 1000ms |

---

## Scalability Tests

Measure how Prometheus scales with increasing workloads across multiple dimensions.

### What It Tests

- Performance as scrape targets increase (10 → 100 → 1000 → 10000)
- Performance as active series increase (10K → 100K → 1M → 10M)
- Performance as label cardinality increases
- Performance as retention period increases
- Performance as concurrent queries increase
- Horizontal scaling (distributed mode)

### When to Use

- Capacity planning
- Architecture decisions (monolithic vs distributed)
- Understanding scaling limits
- Predicting resource requirements

### Running Scalability Tests

```bash
python3 -m tests.cli run --type scalability --platform eks --deployment-mode distributed
```

### Configuration

```yaml
scalability:
  enabled: true
  k6:
    concurrent_users:
      - 10
      - 50
      - 100
      - 200
      - 500
  dimensions:
    - targets
    - series
    - cardinality
    - retention
    - queries
  test_horizontal_scaling: true  # Only for distributed mode
```

### Pass/Fail Criteria

| Metric | Threshold |
|--------|-----------|
| Degradation Threshold | < 20% at 2x load |

---

## Endurance Tests

Verify Prometheus remains stable over extended periods (soak tests).

### What It Tests

- Memory leak detection over time
- Disk space growth patterns
- TSDB compaction across multiple cycles
- Query performance stability
- Gradual performance degradation

### When to Use

- Pre-production validation
- Memory leak detection
- Long-term stability verification
- Resource planning

### Running Endurance Tests

```bash
# Note: This runs for 24 hours by default
python3 -m tests.cli run --type endurance --platform eks
```


### Configuration

```yaml
endurance:
  enabled: false  # Disabled by default due to duration
  duration: 24h
  k6:
    vus: 50
    scripts:
      - "k6/query-load.js"
  healthcheck_interval: 5m
```

### Pass/Fail Criteria

| Metric | Threshold |
|--------|-----------|
| Memory Growth | < 1% per hour |
| Query Latency Degradation | < 10% |

---

## Reliability Tests

Verify Prometheus behavior during failures and recoveries.

### What It Tests

- Recovery after pod/container restart
- WAL replay completion after crash
- Data integrity after unclean shutdown
- Network partition handling
- Scrape target re-discovery after restart
- Alerting rule continuity after restart
- Replica failure handling (distributed mode)

### When to Use

- Disaster recovery planning
- High availability validation
- Before production deployment
- After infrastructure changes

### Running Reliability Tests

```bash
python3 -m tests.cli run --type reliability --platform minikube
```

### Configuration

```yaml
reliability:
  enabled: true
  healthcheck_endpoints:
    - "/-/healthy"
    - "/-/ready"
  test_replica_failure: true  # Only for distributed mode
```

### Pass/Fail Criteria

| Metric | Threshold |
|--------|-----------|
| Recovery Time | < 60s |
| Data Loss Tolerance | 0% |

---

## Chaos Tests

Verify Prometheus handles unexpected failures gracefully.

### What It Tests

- Random pod kills and recovery
- CPU throttling impact
- Memory pressure and OOM handling
- Disk I/O latency impact
- Network latency to scrape targets
- Scrape target failures (partial and complete)

### Prerequisites

- Chaos Mesh or Litmus installed on Kubernetes cluster

### When to Use

- Resilience validation
- Failure mode discovery
- High availability testing
- Production readiness assessment

### Running Chaos Tests

```bash
python3 -m tests.cli run --type chaos --platform eks
```

### Configuration

```yaml
chaos:
  enabled: false  # Requires chaos tools
  tool: "chaos-mesh"  # chaos-mesh, litmus
  scenarios:
    monolithic:
      - container_kill
      - process_kill
    distributed:
      - pod_kill
      - replica_failure
```

---

## Regression Tests

Verify upgrades don't break existing functionality.

### What It Tests

- Query result comparison between versions
- Alerting rule consistency after upgrade
- Recording rule consistency after upgrade
- Scrape configuration compatibility
- Remote write continuity
- Performance comparison between versions

### When to Use

- Before upgrading Prometheus
- After configuration changes
- Validating new releases
- Comparing configurations

### Running Regression Tests

```bash
python3 -m tests.cli run --type regression --platform minikube
```

### Configuration

```yaml
regression:
  enabled: false
  baseline_version: "v3.4.0"
```

---

## Security Tests

Verify Prometheus security configuration.

### What It Tests

- TLS configuration for scrape targets
- Authentication enforcement
- RBAC permissions (Kubernetes)
- Sensitive data exposure in metrics
- API endpoint protection
- Known vulnerability scanning

### When to Use

- Security audits
- Compliance validation
- Before production deployment
- After security configuration changes

### Running Security Tests

```bash
python3 -m tests.cli run --type security --platform eks
```

### Configuration

```yaml
security:
  enabled: true
  scan_vulnerabilities: true
  test_api_auth: true
```

---

## Running Multiple Test Types

You can run multiple test types in a single command:

```bash
# Run sanity and integration tests
python3 -m tests.cli run --type sanity --type integration --platform docker

# Run all enabled tests
python3 -m tests.cli run --platform minikube
```

## Test Type Selection Guide

```
┌─────────────────────────────────────────────────────────────┐
│                 Which tests should I run?                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Quick validation after deployment?                          │
│  └─→ Sanity tests                                           │
│                                                              │
│  Verify monitoring stack integration?                        │
│  └─→ Integration tests                                       │
│                                                              │
│  Measure performance under load?                             │
│  └─→ Load tests                                              │
│                                                              │
│  Find breaking points?                                       │
│  └─→ Stress tests                                            │
│                                                              │
│  Establish performance baselines?                            │
│  └─→ Performance tests                                       │
│                                                              │
│  Understand scaling behavior?                                │
│  └─→ Scalability tests                                       │
│                                                              │
│  Verify long-term stability?                                 │
│  └─→ Endurance tests                                         │
│                                                              │
│  Test failure recovery?                                      │
│  └─→ Reliability tests                                       │
│                                                              │
│  Test unexpected failures?                                   │
│  └─→ Chaos tests                                             │
│                                                              │
│  Validate upgrades?                                          │
│  └─→ Regression tests                                        │
│                                                              │
│  Security audit?                                             │
│  └─→ Security tests                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```
