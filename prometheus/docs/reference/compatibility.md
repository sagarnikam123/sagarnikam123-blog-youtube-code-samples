# Version Compatibility Matrix

This document provides compatibility information for the Prometheus Installation and Testing Framework.

## Prometheus Versions

### Supported Versions

| Version | Type | Status | End of Support |
|---------|------|--------|----------------|
| v3.5.0 | LTS | Supported | TBD |
| v3.4.x | Latest | Supported | v3.6.0 release |
| v3.3.x | Previous | Supported | v3.5.0 release |
| v3.2.x | Previous | Deprecated | v3.4.0 release |
| v2.x.x | Legacy | Not Supported | - |

### Version Features

| Feature | v3.3.x | v3.4.x | v3.5.0 LTS |
|---------|--------|--------|------------|
| Native Histograms | ✓ | ✓ | ✓ |
| UTF-8 Metric Names | ✓ | ✓ | ✓ |
| Remote Write 2.0 | ✓ | ✓ | ✓ |
| OTLP Ingestion | ✓ | ✓ | ✓ |
| Agent Mode | ✓ | ✓ | ✓ |

## Platform Compatibility

### Operating Systems (Binary Installation)

| OS | Architecture | Status | Notes |
|----|--------------|--------|-------|
| Linux | amd64 | ✓ Supported | Primary platform |
| Linux | arm64 | ✓ Supported | |
| Linux | armv7 | ✓ Supported | Raspberry Pi |
| macOS | amd64 | ✓ Supported | Intel Macs |
| macOS | arm64 | ✓ Supported | Apple Silicon |
| Windows | amd64 | ✓ Supported | |
| Windows | arm64 | ✗ Not Supported | |

### Kubernetes Platforms

| Platform | Version | Status | Deployment Modes |
|----------|---------|--------|------------------|
| Minikube | 1.28+ | ✓ Supported | Monolithic, Distributed |
| AWS EKS | 1.27+ | ✓ Supported | Monolithic, Distributed |
| Google GKE | 1.27+ | ✓ Supported | Monolithic, Distributed |
| Azure AKS | 1.27+ | ✓ Supported | Monolithic, Distributed |
| OpenShift | 4.12+ | ✓ Supported | Monolithic, Distributed |
| k3s | 1.27+ | ○ Experimental | Monolithic |
| kind | 0.20+ | ○ Experimental | Monolithic |

### Docker

| Docker Version | Status | Notes |
|----------------|--------|-------|
| 24.x | ✓ Supported | Recommended |
| 23.x | ✓ Supported | |
| 20.x | ○ Deprecated | Upgrade recommended |

### Docker Compose

| Version | Status | Notes |
|---------|--------|-------|
| v2.x | ✓ Supported | Recommended |
| v1.x | ✗ Not Supported | Use v2 |

## Helm Chart Compatibility

### kube-prometheus-stack

| Chart Version | Prometheus | Alertmanager | Grafana | Status |
|---------------|------------|--------------|---------|--------|
| 65.x | v3.5.0 | v0.27.x | 11.x | ✓ Current |
| 64.x | v3.4.x | v0.27.x | 11.x | ✓ Supported |
| 63.x | v3.3.x | v0.26.x | 10.x | ○ Deprecated |
| 62.x | v3.2.x | v0.26.x | 10.x | ✗ Not Supported |

### Prometheus Operator

| Operator Version | Prometheus | CRD Version | Status |
|------------------|------------|-------------|--------|
| v0.75.x | v3.5.0 | v1 | ✓ Current |
| v0.74.x | v3.4.x | v1 | ✓ Supported |
| v0.73.x | v3.3.x | v1 | ○ Deprecated |

## Test Framework Dependencies

### Python

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.12.x | ✓ Supported | Recommended |
| 3.11.x | ✓ Supported | |
| 3.10.x | ✓ Supported | Minimum required |
| 3.9.x | ✗ Not Supported | |

### Python Packages

| Package | Minimum Version | Recommended | Purpose |
|---------|-----------------|-------------|---------|
| pytest | 7.0.0 | 8.x | Test runner |
| hypothesis | 6.0.0 | 6.x | Property-based testing |
| httpx | 0.24.0 | 0.27.x | HTTP client |
| pyyaml | 6.0 | 6.x | YAML parsing |
| jsonschema | 4.0.0 | 4.x | Config validation |
| click | 8.0.0 | 8.x | CLI framework |
| rich | 13.0.0 | 13.x | Terminal output |
| kubernetes | 28.0.0 | 29.x | K8s client |

### k6

| k6 Version | Status | Notes |
|------------|--------|-------|
| 0.50.x | ✓ Supported | Recommended |
| 0.49.x | ✓ Supported | |
| 0.48.x | ✓ Supported | |
| 0.47.x | ○ Deprecated | |

### kubectl

| kubectl Version | Status | Notes |
|-----------------|--------|-------|
| 1.30.x | ✓ Supported | |
| 1.29.x | ✓ Supported | Recommended |
| 1.28.x | ✓ Supported | |
| 1.27.x | ✓ Supported | Minimum |

## Exporter Compatibility

### Infrastructure Exporters

| Exporter | Version | Prometheus Compatibility |
|----------|---------|-------------------------|
| Node Exporter | 1.8.x | v3.x |
| kube-state-metrics | 2.12.x | v3.x |
| cAdvisor | 0.49.x | v3.x |
| Blackbox Exporter | 0.25.x | v3.x |

### Database Exporters

| Exporter | Version | Database Version |
|----------|---------|------------------|
| postgres_exporter | 0.15.x | PostgreSQL 12+ |
| mysqld_exporter | 0.15.x | MySQL 5.7+, 8.x |
| mongodb_exporter | 0.40.x | MongoDB 4.4+ |
| redis_exporter | 1.58.x | Redis 6.x, 7.x |

### Message Queue Exporters

| Exporter | Version | Queue Version |
|----------|---------|---------------|
| kafka_exporter | 1.7.x | Kafka 2.x, 3.x |
| rabbitmq_exporter | 1.0.x | RabbitMQ 3.x |

## Observability Stack Compatibility

| Component | Version | Prometheus Compatibility |
|-----------|---------|-------------------------|
| Grafana | 11.x | v3.x |
| Alertmanager | 0.27.x | v3.x |
| Mimir | 2.12.x | v3.x |
| Loki | 3.x | v3.x |
| Tempo | 2.x | v3.x |
| Thanos | 0.35.x | v3.x |

## Chaos Engineering Tools

| Tool | Version | Kubernetes Version |
|------|---------|-------------------|
| Chaos Mesh | 2.6.x | 1.26+ |
| Litmus | 3.x | 1.26+ |

## Browser Support (Web UI)

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 120+ | ✓ Supported |
| Firefox | 120+ | ✓ Supported |
| Safari | 17+ | ✓ Supported |
| Edge | 120+ | ✓ Supported |

## Deployment Mode Compatibility

### Platform vs Deployment Mode

| Platform | Monolithic | Distributed |
|----------|------------|-------------|
| Binary | ✓ | ✗ |
| Docker | ✓ | ✗ |
| Minikube | ✓ | ✓ |
| EKS | ✓ | ✓ |
| GKE | ✓ | ✓ |
| AKS | ✓ | ✓ |
| OpenShift | ✓ | ✓ |

### Test Type vs Deployment Mode

| Test Type | Monolithic | Distributed |
|-----------|------------|-------------|
| Sanity | ✓ | ✓ |
| Integration | ✓ | ✓ |
| Load | ✓ | ✓ |
| Stress | ✓ | ✓ |
| Performance | ✓ | ✓ |
| Scalability | ✓ | ✓ |
| Endurance | ✓ | ✓ |
| Reliability | ✓ | ✓ |
| Chaos | ✓ | ✓ |
| Regression | ✓ | ✓ |
| Security | ✓ | ✓ |

## Known Issues

### Prometheus v3.5.0

- None currently known

### Prometheus v3.4.x

- Remote write may experience delays under high cardinality (>10M series)

### Platform-Specific

| Platform | Issue | Workaround |
|----------|-------|------------|
| Minikube | Memory limits on M1 Macs | Increase VM memory to 8GB |
| EKS | IAM role propagation delay | Wait 60s after role creation |
| GKE | Autopilot resource limits | Use Standard mode for stress tests |

## Upgrade Paths

### Prometheus Upgrades

```
v3.3.x → v3.4.x → v3.5.0 (LTS)
```

### Helm Chart Upgrades

```
63.x → 64.x → 65.x
```

Always review release notes before upgrading.

## See Also

- [Installation Guide](../installation/README.md) - Installation documentation
- [Troubleshooting](../installation/troubleshooting.md) - Common issues and solutions
- [Architecture](architecture.md) - System architecture overview
