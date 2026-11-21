# Configuration Schema Reference

This document provides the complete YAML configuration schema for the Prometheus Testing Framework.

## Overview

Configuration files are written in YAML format and control all aspects of test execution. The framework supports:

- Test suite metadata and platform settings
- Prometheus instance configuration
- Test Runner Host configuration
- Remote cluster credentials
- Individual test type configurations

## File Location

Default configuration file: `tests/config/default.yaml`

Custom configurations can be specified via CLI:
```bash
python3 -m tests.cli run --config path/to/config.yaml
```

## Complete Schema

### Root Structure

```yaml
test:           # Test suite configuration
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

## test

Main test suite configuration section.

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

### test Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | string | No | `prometheus-test-suite` | Name of the test suite |
| `platform` | enum | No | `minikube` | Target platform |
| `deployment_mode` | enum | No | `monolithic` | Deployment mode |
| `prometheus` | object | No | See below | Prometheus instance config |
| `runner` | object | No | See below | Test Runner Host config |
| `credentials` | object | No | See below | Remote cluster credentials |

### test.platform Values

| Value | Description |
|-------|-------------|
| `minikube` | Local Kubernetes via Minikube |
| `eks` | Amazon Elastic Kubernetes Service |
| `gke` | Google Kubernetes Engine |
| `aks` | Azure Kubernetes Service |
| `docker` | Docker container (monolithic only) |
| `binary` | Binary installation (monolithic only) |

### test.deployment_mode Values

| Value | Description |
|-------|-------------|
| `monolithic` | Single Prometheus instance |
| `distributed` | Multi-replica with federation/Thanos/Mimir |

> **Note:** `docker` and `binary` platforms only support `monolithic` deployment mode.

### test.prometheus Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `version` | string | No | `v3.5.0` | Prometheus version (pattern: `v?X.Y.Z`) |
| `namespace` | string | No | `monitoring` | Kubernetes namespace |
| `url` | string | No | `http://localhost:9090` | Prometheus API URL |

### test.runner Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `python_version` | string | No | `3.10+` | Required Python version |
| `k6_path` | string | No | `/usr/local/bin/k6` | Path to k6 binary |
| `kubectl_path` | string | No | `/usr/local/bin/kubectl` | Path to kubectl binary |

### test.credentials Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `kubeconfig` | string | No | `${KUBECONFIG}` | Kubernetes config path |
| `aws_profile` | string | No | `${AWS_PROFILE}` | AWS profile name |
| `gcp_credentials` | string | No | `${GOOGLE_APPLICATION_CREDENTIALS}` | GCP credentials file |
| `azure_subscription` | string | No | `${AZURE_SUBSCRIPTION_ID}` | Azure subscription ID |

> **Note:** Environment variable syntax `${VAR_NAME}` is supported and will be expanded at runtime.

---

## sanity

Quick validation test configuration.

```yaml
sanity:
  enabled: true
  timeout: "60s"
  healthcheck_endpoints:
    - "/-/healthy"
    - "/-/ready"
    - "/api/v1/status/runtimeinfo"
```

### sanity Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable sanity tests |
| `timeout` | string | No | `60s` | Test timeout (pattern: `Ns`, `Nm`, `Nh`) |
| `healthcheck_endpoints` | array[string] | No | See above | Endpoints to check |

---

## integration

Component integration test configuration.

```yaml
integration:
  enabled: true
  components:
    - node-exporter
    - alertmanager
    - grafana
  test_federation: true
```

### integration Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable integration tests |
| `components` | array[string] | No | See above | Components to test |
| `test_federation` | boolean | No | `true` | Test federation (distributed only) |

---

## load

Load test configuration using k6.

```yaml
load:
  enabled: true
  duration: "30m"
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

### load Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable load tests |
| `duration` | string | No | `30m` | Test duration |
| `k6` | object | No | See below | k6 configuration |
| `targets` | array[integer] | No | `[100, 1000, 10000]` | Target counts to test |
| `series` | array[integer] | No | `[10000, 100000, 1000000]` | Series counts to test |

### load.k6 Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `vus` | integer | No | `100` | Virtual users (min: 1) |
| `scripts` | array[string] | No | See above | k6 script paths |

---

## stress

Stress test configuration for breaking point discovery.

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

### stress Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable stress tests |
| `k6` | object | No | See below | k6 configuration |
| `cardinality` | object | No | See below | Cardinality limits |
| `ingestion` | object | No | See below | Ingestion limits |
| `queries` | object | No | See below | Query limits |

### stress.k6.stages Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `duration` | string | Yes | Stage duration |
| `target` | integer | Yes | Target VUs for stage |

### stress.cardinality Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `max_labels` | integer | No | `1000000` | Maximum label combinations |

### stress.ingestion Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `max_samples_per_second` | integer | No | `1000000` | Maximum samples/second |

### stress.queries Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `concurrent` | integer | No | `100` | Concurrent query count |

---

## performance

Performance benchmark configuration.

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

### performance Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable performance tests |
| `iterations` | integer | No | `100` | Benchmark iterations |
| `k6` | object | No | See below | k6 configuration |
| `api_endpoints` | array[string] | No | See above | Endpoints to benchmark |

---

## scalability

Scalability test configuration.

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

### scalability Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable scalability tests |
| `k6` | object | No | See below | k6 configuration |
| `dimensions` | array[string] | No | See above | Scaling dimensions |
| `test_horizontal_scaling` | boolean | No | `true` | Test horizontal scaling (distributed only) |

### scalability.k6 Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `concurrent_users` | array[integer] | No | `[10, 50, 100, 200, 500]` | User counts to test |

---

## endurance

Endurance (soak) test configuration.

```yaml
endurance:
  enabled: false
  duration: "24h"
  k6:
    vus: 50
    scripts:
      - "k6/query-load.js"
  healthcheck_interval: "5m"
```

### endurance Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `false` | Enable endurance tests |
| `duration` | string | No | `24h` | Test duration (pattern: `Ns`, `Nm`, `Nh`, `Nd`) |
| `k6` | object | No | See below | k6 configuration |
| `healthcheck_interval` | string | No | `5m` | Health check interval |

---

## reliability

Reliability test configuration.

```yaml
reliability:
  enabled: true
  healthcheck_endpoints:
    - "/-/healthy"
    - "/-/ready"
  test_replica_failure: true
```

### reliability Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable reliability tests |
| `healthcheck_endpoints` | array[string] | No | See above | Endpoints to monitor |
| `test_replica_failure` | boolean | No | `true` | Test replica failures (distributed only) |

---

## chaos

Chaos engineering test configuration.

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

### chaos Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `false` | Enable chaos tests |
| `tool` | enum | No | `chaos-mesh` | Chaos tool (`chaos-mesh`, `litmus`) |
| `scenarios` | object | No | See below | Chaos scenarios |

### chaos.scenarios Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `monolithic` | array[string] | No | See above | Monolithic scenarios |
| `distributed` | array[string] | No | See above | Distributed scenarios |

---

## regression

Regression test configuration.

```yaml
regression:
  enabled: false
  baseline_version: "v3.4.0"
```

### regression Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `false` | Enable regression tests |
| `baseline_version` | string | No | `v3.4.0` | Baseline version for comparison |

---

## security

Security test configuration.

```yaml
security:
  enabled: true
  scan_vulnerabilities: true
  test_api_auth: true
```

### security Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable security tests |
| `scan_vulnerabilities` | boolean | No | `true` | Scan for CVEs |
| `test_api_auth` | boolean | No | `true` | Test API authentication |

---

## Validation

Configuration files are validated against a JSON Schema. Validation errors include:

- Invalid property types
- Missing required properties
- Invalid enum values
- Pattern mismatches (e.g., version format)

Example validation error:
```
test.platform: 'invalid' is not one of ['minikube', 'eks', 'gke', 'aks', 'docker', 'binary']
```

## See Also

- [CLI Reference](cli-reference.md) - Command-line interface reference
- [Getting Started](../testing/getting-started.md) - Quick start guide
- [Test Configuration](../testing/configuration.md) - Configuration guide
