# Prometheus Testing Framework

A comprehensive testing framework for validating Prometheus deployments across multiple platforms and deployment modes.

## Overview

The Prometheus Testing Framework provides automated testing capabilities to validate Prometheus installations, measure performance, and ensure reliability. It supports testing both monolithic and distributed Prometheus deployments across local environments and cloud platforms.

## Key Features

- **Multi-Platform Support**: Test on Minikube, EKS, GKE, AKS, Docker, and bare-metal
- **Deployment Modes**: Validate both monolithic and distributed Prometheus configurations
- **Comprehensive Test Types**: Sanity, load, stress, performance, scalability, endurance, reliability, chaos, regression, and security tests
- **k6 Integration**: Load testing powered by Grafana k6
- **Flexible Configuration**: YAML-based configuration with environment variable support
- **Rich Reporting**: JSON, Markdown, HTML, and CSV report formats

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Test Runner Host (Local)                      │
├─────────────────────────────────────────────────────────────────┤
│  CLI Interface  │  Python3 Scripts  │  k6 Load Testing          │
└────────┬────────┴─────────┬─────────┴──────────┬────────────────┘
         │                  │                    │
         ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Test Framework Core                         │
├─────────────────────────────────────────────────────────────────┤
│  Config Loader  │  Test Runner  │  Prometheus API  │  Reporter  │
└────────┬────────┴───────────────┴─────────┬────────┴────────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Target Prometheus Deployment                  │
├─────────────────────────────────────────────────────────────────┤
│  Minikube  │  EKS  │  GKE  │  AKS  │  Docker  │  Binary         │
└─────────────────────────────────────────────────────────────────┘
```

## Test Types

| Test Type | Purpose | Duration |
|-----------|---------|----------|
| [Sanity](./test-types.md#sanity-tests) | Quick validation after deployment | ~60s |
| [Integration](./test-types.md#integration-tests) | Component integration verification | ~5min |
| [Load](./test-types.md#load-tests) | Performance under realistic workloads | ~30min |
| [Stress](./test-types.md#stress-tests) | Breaking point discovery | ~20min |
| [Performance](./test-types.md#performance-tests) | Benchmark measurements | ~10min |
| [Scalability](./test-types.md#scalability-tests) | Scaling behavior analysis | ~30min |
| [Endurance](./test-types.md#endurance-tests) | Long-running stability (soak) | 24h+ |
| [Reliability](./test-types.md#reliability-tests) | Failure and recovery handling | ~15min |
| [Chaos](./test-types.md#chaos-tests) | Unexpected failure scenarios | ~20min |
| [Regression](./test-types.md#regression-tests) | Version comparison | ~30min |
| [Security](./test-types.md#security-tests) | Security configuration validation | ~10min |

## Quick Start

**Working Directory**: All commands must be run from the repository root:
```bash
cd /Users/snikam/Documents/git/sagarnikam123-blog-youtube-code-samples/prometheus
```

**Install dependencies:**
```bash
pip install -r tests/requirements.txt
```

**Run tests:**
```bash
# Run sanity tests against local Minikube deployment
python3 -m tests.cli run --type sanity --platform minikube

# Run all tests on Minikube
python3 -m tests.cli run --platform minikube

# Run load tests with custom k6 options
python3 -m tests.cli run --type load --platform minikube --k6-vus 100 --k6-duration 30m

# Check Prometheus status
python3 -m tests.cli status --platform minikube

# View framework info
python3 -m tests.cli info
```

See [Getting Started](./getting-started.md) for detailed setup instructions.

## Prerequisites

- Python 3.10+
- kubectl (for Kubernetes platforms)
- k6 (for load testing)
- Access to target Prometheus deployment

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](./getting-started.md) | Installation and first test run |
| [Test Types](./test-types.md) | Detailed description of each test type |
| [Configuration](./configuration.md) | Test configuration reference |
| [CI/CD Integration](./ci-cd-integration.md) | Pipeline integration examples |
| [Interpreting Results](./interpreting-results.md) | How to read test reports |

## Supported Platforms

### Local Development
- **Docker**: Single-node Prometheus in containers
- **Binary**: Direct binary installation on host

### Kubernetes
- **Minikube**: Local Kubernetes cluster
- **EKS**: Amazon Elastic Kubernetes Service
- **GKE**: Google Kubernetes Engine
- **AKS**: Azure Kubernetes Service

## Deployment Modes

### Monolithic
Single Prometheus instance. Supported on all platforms.

### Distributed
Multi-replica Prometheus with federation or Thanos/Mimir integration. Supported on Kubernetes platforms only (Minikube, EKS, GKE, AKS).

## Technology Stack

- **Test Framework**: Python 3.10+ with pytest
- **Property Testing**: hypothesis
- **HTTP Client**: httpx
- **Load Testing**: k6 by Grafana Labs
- **Kubernetes Client**: kubernetes-client
- **CLI**: click with rich formatting

## Related Documentation

- [Installation Guide](../installation/README.md)
- [Configuration Guide](../configuration/README.md)
- [CLI Reference](../reference/cli-reference.md)
