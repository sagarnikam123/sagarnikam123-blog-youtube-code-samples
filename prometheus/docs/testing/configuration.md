# Test Configuration Reference

This document provides a complete reference for configuring the Prometheus Testing Framework.

## Configuration Files

Configuration is loaded from YAML files. The framework looks for configuration in:

1. `tests/config/default.yaml` - Default configuration
2. Custom path via `--config` CLI option
3. Environment-specific files in `tests/config/environments/`

## Configuration Structure

```yaml
test:           # Test suite metadata and target configuration
sanity:         # Sanity test configuration
integration:    # Integration test configuration
load:           # Load test configuration
stress:         # Stress test configuration
performance:    # Performance test configuration
scalability:    # Scalability test configuration
endurance:      # Endurance test configuration
reliability:    # Reliability test configuration
chaos:          # Chaos test configuration
regression:     # Regression test configuration
security:       # Security test configuration
```

---

## Test Section

Core test suite configuration.

```yaml
test:
  name: "prometheus-test-suite"
  platform: "minikube"
  deployment_mode: "monolithic"
  prometheus:
    version: "v3.5.0"
    namespace: "monitoring"
    url: "http://localhost:9090"
  runner:
    python_version: "3.10+"
    k6_path: "/usr/local/bin/k6"
    kubectl_path: "/usr/local/bin/kubectl"
  credentials:
    kubeconfig: "${KUBECONFIG}"
    aws_profile: "${AWS_PROFILE}"
    gcp_credentials: "${GOOGLE_APPLICATION_CREDENTIALS}"
    azure_subscription: "${AZURE_SUBSCRIPTION_ID}"
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | `prometheus-test-suite` | Test suite name |
| `platform` | string | `minikube` | Target platform |
| `deployment_mode` | string | `monolithic` | Deployment mode |


### Platform Values

| Value | Description |
|-------|-------------|
| `minikube` | Local Kubernetes via Minikube |
| `eks` | Amazon Elastic Kubernetes Service |
| `gke` | Google Kubernetes Engine |
| `aks` | Azure Kubernetes Service |
| `docker` | Docker containers (monolithic only) |
| `binary` | Direct binary installation (monolithic only) |

### Deployment Mode Values

| Value | Description | Supported Platforms |
|-------|-------------|---------------------|
| `monolithic` | Single Prometheus instance | All |
| `distributed` | Multi-replica with federation | minikube, eks, gke, aks |

### Prometheus Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `version` | string | `v3.5.0` | Prometheus version |
| `namespace` | string | `monitoring` | Kubernetes namespace |
| `url` | string | `http://localhost:9090` | Prometheus API URL |

### Runner Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `python_version` | string | `3.10+` | Required Python version |
| `k6_path` | string | `/usr/local/bin/k6` | Path to k6 binary |
| `kubectl_path` | string | `/usr/local/bin/kubectl` | Path to kubectl binary |

### Credentials Configuration

Environment variables are expanded using `${VAR_NAME}` syntax.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `kubeconfig` | string | `${KUBECONFIG}` | Kubernetes config path |
| `aws_profile` | string | `${AWS_PROFILE}` | AWS profile name |
| `gcp_credentials` | string | `${GOOGLE_APPLICATION_CREDENTIALS}` | GCP credentials path |
| `azure_subscription` | string | `${AZURE_SUBSCRIPTION_ID}` | Azure subscription ID |

---

## Sanity Tests

```yaml
sanity:
  enabled: true
  timeout: 60s
  healthcheck_endpoints:
    - "/-/healthy"
    - "/-/ready"
    - "/api/v1/status/runtimeinfo"
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable sanity tests |
| `timeout` | string | `60s` | Test timeout |
| `healthcheck_endpoints` | list | See above | Endpoints to check |

---

## Integration Tests

```yaml
integration:
  enabled: true
  components:
    - node-exporter
    - alertmanager
    - grafana
  test_federation: true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable integration tests |
| `components` | list | See above | Components to test |
| `test_federation` | boolean | `true` | Test federation (distributed only) |

---

## Load Tests

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

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable load tests |
| `duration` | string | `30m` | Test duration |
| `k6.vus` | integer | `100` | Virtual users |
| `k6.scripts` | list | See above | k6 scripts to run |
| `targets` | list | `[100, 1000, 10000]` | Target counts to test |
| `series` | list | `[10000, 100000, 1000000]` | Series counts to test |

---

## Stress Tests

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

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable stress tests |
| `k6.stages` | list | See above | k6 ramping stages |
| `cardinality.max_labels` | integer | `1000000` | Max label combinations |
| `ingestion.max_samples_per_second` | integer | `1000000` | Max ingestion rate |
| `queries.concurrent` | integer | `100` | Concurrent queries |


---

## Performance Tests

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

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable performance tests |
| `iterations` | integer | `100` | Benchmark iterations |
| `k6.scripts` | list | See above | k6 benchmark scripts |
| `api_endpoints` | list | See above | API endpoints to benchmark |

---

## Scalability Tests

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
  test_horizontal_scaling: true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable scalability tests |
| `k6.concurrent_users` | list | See above | User counts to test |
| `dimensions` | list | See above | Scaling dimensions |
| `test_horizontal_scaling` | boolean | `true` | Test horizontal scaling (distributed only) |

---

## Endurance Tests

```yaml
endurance:
  enabled: false
  duration: 24h
  k6:
    vus: 50
    scripts:
      - "k6/query-load.js"
  healthcheck_interval: 5m
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable endurance tests |
| `duration` | string | `24h` | Test duration |
| `k6.vus` | integer | `50` | Virtual users |
| `k6.scripts` | list | See above | k6 scripts to run |
| `healthcheck_interval` | string | `5m` | Health check frequency |

---

## Reliability Tests

```yaml
reliability:
  enabled: true
  healthcheck_endpoints:
    - "/-/healthy"
    - "/-/ready"
  test_replica_failure: true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable reliability tests |
| `healthcheck_endpoints` | list | See above | Endpoints to monitor |
| `test_replica_failure` | boolean | `true` | Test replica failures (distributed only) |

---

## Chaos Tests

```yaml
chaos:
  enabled: false
  tool: "chaos-mesh"
  scenarios:
    monolithic:
      - container_kill
      - process_kill
    distributed:
      - pod_kill
      - replica_failure
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable chaos tests |
| `tool` | string | `chaos-mesh` | Chaos tool (`chaos-mesh`, `litmus`) |
| `scenarios.monolithic` | list | See above | Monolithic scenarios |
| `scenarios.distributed` | list | See above | Distributed scenarios |

---

## Regression Tests

```yaml
regression:
  enabled: false
  baseline_version: "v3.4.0"
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable regression tests |
| `baseline_version` | string | `v3.4.0` | Version to compare against |

---

## Security Tests

```yaml
security:
  enabled: true
  scan_vulnerabilities: true
  test_api_auth: true
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable security tests |
| `scan_vulnerabilities` | boolean | `true` | Scan for CVEs |
| `test_api_auth` | boolean | `true` | Test API authentication |

---

## Thresholds Configuration

Pass/fail thresholds are configured in `tests/config/thresholds.yaml`:

```yaml
sanity:
  api_response_time_ms: 1000

load:
  query_latency_p99_ms: 500
  scrape_success_rate_percent: 99.0
  cpu_utilization_percent: 80
  memory_utilization_percent: 85

stress:
  min_series_before_failure: 1000000
  min_ingestion_rate: 100000

performance:
  simple_query_latency_ms: 50
  complex_query_latency_ms: 500
  range_query_1h_latency_ms: 200
  range_query_24h_latency_ms: 1000

endurance:
  memory_growth_percent_per_hour: 1
  query_latency_degradation_percent: 10

reliability:
  recovery_time_seconds: 60
  data_loss_tolerance_percent: 0

scalability:
  degradation_threshold_percent: 20
```

---

## Environment Variables

The following environment variables are used:

| Variable | Description |
|----------|-------------|
| `KUBECONFIG` | Kubernetes configuration file path |
| `AWS_PROFILE` | AWS credentials profile |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP service account key path |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |

---

## CLI Overrides

Many configuration options can be overridden via CLI:

```bash
# Override platform
python3 -m tests.cli run --platform eks

# Override deployment mode
python3 -m tests.cli run --deployment-mode distributed

# Override Prometheus URL
python3 -m tests.cli run --prometheus-url http://prometheus:9090

# Override k6 options
python3 -m tests.cli run --k6-vus 200 --k6-duration 1h

# Override timeout
python3 -m tests.cli run --timeout 600

# Use custom thresholds
python3 -m tests.cli run --thresholds tests/config/custom-thresholds.yaml
```

---

## Example Configurations

### Local Docker Testing

```yaml
test:
  name: "local-docker-tests"
  platform: "docker"
  deployment_mode: "monolithic"
  prometheus:
    url: "http://localhost:9090"

sanity:
  enabled: true
  timeout: 30s

load:
  enabled: true
  duration: 5m
  k6:
    vus: 10
```

### Production EKS Testing

```yaml
test:
  name: "production-eks-tests"
  platform: "eks"
  deployment_mode: "distributed"
  prometheus:
    namespace: "monitoring"
    url: "http://prometheus.monitoring.svc:9090"
  credentials:
    kubeconfig: "${KUBECONFIG}"
    aws_profile: "production"

sanity:
  enabled: true

load:
  enabled: true
  duration: 30m
  k6:
    vus: 100

stress:
  enabled: true

reliability:
  enabled: true
  test_replica_failure: true
```

### CI/CD Pipeline Testing

```yaml
test:
  name: "ci-cd-validation"
  platform: "minikube"
  deployment_mode: "monolithic"

sanity:
  enabled: true
  timeout: 60s

integration:
  enabled: true

load:
  enabled: false  # Skip for faster CI

security:
  enabled: true
  scan_vulnerabilities: true
```
