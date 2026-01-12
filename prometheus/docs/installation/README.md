# Prometheus Installation Documentation

This guide covers all supported methods for installing Prometheus, from local development to production Kubernetes deployments.

## Quick Start

| Method | Best For | Time | Guide |
|--------|----------|------|-------|
| [Docker](#docker-installation) | Local dev, testing | 1 min | [→ Docker Guide](./docker.md) |
| [Binary](#binary-installation) | Bare-metal, VMs | 5 min | [→ Binary Guide](./binary.md) |
| [Helm](#helm-installation) | Kubernetes (recommended) | 5 min | [→ Helm Guide](./helm.md) |
| [Operator](#operator-installation) | OpenShift, GitOps | 15 min | [→ Operator Guide](./operator.md) |

## Installation Methods Overview

### Docker Installation

Best for local development and testing. Single command to get started:

```bash
docker run -d -p 9090:9090 prom/prometheus
```

For a full monitoring stack with Grafana and Alertmanager:

```bash
cd install/docker
docker-compose -f docker-compose.full.yml up -d
```

**Pros:**
- Fastest setup
- No system modifications
- Easy cleanup

**Cons:**
- Not suitable for production
- Limited persistence options

[→ Full Docker Guide](./docker.md)

### Binary Installation

Best for bare-metal servers and VMs where you need direct control.

```bash
# Linux
sudo ./install/binary/install-linux.sh --version 2.54.1

# macOS
./install/binary/install-macos.sh --version 2.54.1

# Windows (PowerShell as Administrator)
.\install\binary\install-windows.ps1 -Version 2.54.1
```

**Pros:**
- Full control over configuration
- Native performance
- Works without containers

**Cons:**
- Manual updates
- OS-specific setup

[→ Full Binary Guide](./binary.md)

### Helm Installation (Recommended for Kubernetes)

Best for Kubernetes deployments. Includes Prometheus, Grafana, Alertmanager, and exporters.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
```

**Pros:**
- Complete monitoring stack
- Production-ready defaults
- Easy upgrades

**Cons:**
- Requires Kubernetes
- More complex configuration

[→ Full Helm Guide](./helm.md)

### Operator Installation

Best for OpenShift, GitOps workflows, and automated lifecycle management.

```bash
# OpenShift
oc apply -f install/operator/openshift/subscription.yaml

# Kubernetes with OLM
kubectl apply -f install/operator/olm/catalog-source.yaml
kubectl apply -f install/operator/olm/subscription.yaml
```

**Pros:**
- CRD-based configuration
- Automated lifecycle management
- GitOps friendly

**Cons:**
- Steeper learning curve
- More complex setup

[→ Full Operator Guide](./operator.md)

## Choosing the Right Method

```
┌─────────────────────────────────────────────────────────────┐
│                    Which method to use?                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Local development/testing?                                  │
│  └─→ Docker                                                  │
│                                                              │
│  Bare-metal or VM?                                           │
│  └─→ Binary                                                  │
│                                                              │
│  Kubernetes?                                                 │
│  ├─→ Standard K8s cluster → Helm                            │
│  └─→ OpenShift or GitOps → Operator                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### All Methods
- Network access to download Prometheus binaries
- Port 9090 available (or configurable)

### Docker
- Docker Engine 20.10+
- Docker Compose v2+ (for full stack)

### Binary
- Linux: systemd, curl/wget
- macOS: launchd (built-in)
- Windows: PowerShell 5.1+, Administrator access

### Kubernetes (Helm/Operator)
- Kubernetes 1.19+
- kubectl configured
- Helm 3.x (for Helm installation)
- Sufficient cluster resources

## Post-Installation

After installation, verify Prometheus is running:

```bash
# Check API
curl http://localhost:9090/api/v1/status/config

# Check self-monitoring
curl 'http://localhost:9090/api/v1/query?query=up{job="prometheus"}'
```

Access the web UI at http://localhost:9090

## Next Steps

1. [Configure scrape targets](../configuration/README.md)
2. [Set up alerting rules](../configuration/alerting.md)
3. [Run validation tests](../testing/README.md)

## Troubleshooting

See [Troubleshooting Guide](./troubleshooting.md) for common issues and solutions.

## Documentation Index

| Document | Description |
|----------|-------------|
| [Binary Installation](./binary.md) | Install from pre-compiled binaries on Linux, macOS, Windows |
| [Docker Installation](./docker.md) | Run Prometheus in Docker containers |
| [Helm Installation](./helm.md) | Deploy on Kubernetes using kube-prometheus-stack |
| [Operator Installation](./operator.md) | Deploy using Prometheus Operator CRDs |
| [Troubleshooting](./troubleshooting.md) | Common issues and solutions |
