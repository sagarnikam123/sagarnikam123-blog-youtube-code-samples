# Prometheus Installation using kube-prometheus-stack

Complete guide to install Prometheus on Kubernetes/EKS using the kube-prometheus-stack Helm chart.

## Overview

**kube-prometheus-stack** is the recommended way to deploy Prometheus on Kubernetes. It includes:

- ✅ Prometheus Operator (CRD-based configuration)
- ✅ Prometheus Server
- ✅ Alertmanager
- ✅ Grafana
- ✅ Node Exporter
- ✅ Kube-state-metrics
- ✅ Pre-configured dashboards and alerts

## Prerequisites

- Kubernetes cluster (1.19+) or AWS EKS
- kubectl configured
- Helm 3.x installed

```bash
# Verify prerequisites
kubectl version --client
helm version
```

## Check Versions Before Installing

```bash
# Add repo first
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# List available chart versions
helm search repo prometheus-community/kube-prometheus-stack --versions

# Check Prometheus version in a specific chart
# prometheus:v3.9.0 (Latest)
helm show values prometheus-community/kube-prometheus-stack --version 80.13.0 | grep -B2 -A2 "prometheus/prometheus"

# Check all default images that will be deployed
# prometheus:v3.5.0 (LTS)
helm template prometheus prometheus-community/kube-prometheus-stack --version 77.10.0 | grep "image:" | sort -u

# get default values
helm show values prometheus-community/kube-prometheus-stack > default-values.yaml
```

> **Note:** The `appVersion` in chart metadata is the Prometheus Operator version, not Prometheus itself.

Version mapping reference: [ArtifactHub](https://artifacthub.io/packages/helm/prometheus-community/kube-prometheus-stack)

## Override Component Versions

To install a specific Prometheus version (e.g., v3.5.0 LTS), override the image tag:

```yaml
# values.yaml
prometheus:
  prometheusSpec:
    image:
      registry: quay.io
      repository: prometheus/prometheus
      tag: v3.5.0
```

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f values.yaml
```

Or inline:
```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  --set prometheus.prometheusSpec.image.tag=v3.5.0
```

### Other Components

```yaml
# Override Grafana version
grafana:
  image:
    tag: 11.4.0

# Override Alertmanager version
alertmanager:
  alertmanagerSpec:
    image:
      tag: v0.28.0

# Override Node Exporter version
prometheus-node-exporter:
  image:
    tag: v1.9.0
```

Check available versions:
- [Prometheus releases](https://github.com/prometheus/prometheus/releases)
- [Grafana releases](https://github.com/grafana/grafana/releases)
- [Alertmanager releases](https://github.com/prometheus/alertmanager/releases)

## Verify Installed Versions

After installation, check what versions are running:

```bash
# Check Prometheus version
kubectl get prometheus -n prometheus -o jsonpath='{.items[*].spec.version}'

# Or from the running pod
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- prometheus --version

# Check Grafana version
kubectl exec -n prometheus deploy/prometheus-grafana -c grafana -- grafana-server -v

# Check Alertmanager version
kubectl exec -n prometheus alertmanager-prometheus-kube-prometheus-alertmanager-0 -c alertmanager -- alertmanager --version

# Check all pod images at once
kubectl get pods -n prometheus -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{range .spec.containers[*]}{.image}{'\n'}{end}{end}"
```

## Quick Start

### 1. Add Helm Repository

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

### 2. Install with Default Configuration

```bash
# Create namespace
kubectl create namespace prometheus

# Install
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus
```

### 3. Verify Installation

```bash
# Check pods
kubectl get pods -n prometheus

# Expected output:
# NAME                                                     READY   STATUS    RESTARTS   AGE
# alertmanager-prometheus-kube-prometheus-alertmanager-0   2/2     Running   0          2m
# prometheus-grafana-xxx                                   3/3     Running   0          2m
# prometheus-kube-prometheus-operator-xxx                  1/1     Running   0          2m
# prometheus-kube-state-metrics-xxx                        1/1     Running   0          2m
# prometheus-prometheus-kube-prometheus-prometheus-0       2/2     Running   0          2m
# prometheus-prometheus-node-exporter-xxx                  1/1     Running   0          2m
```

### 4. Access Prometheus UI

```bash
# Port-forward
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-prometheus 9090:9090

# Open browser
open http://localhost:9090
```

### 5. Access Grafana

```bash
# Port-forward
kubectl port-forward -n prometheus svc/prometheus-grafana 3000:80

# Get admin password
kubectl get secret -n prometheus prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
echo

# Open browser (username: admin)
open http://localhost:3000
```

## Folder Structure

This repository organizes Helm values for multi-version and multi-environment deployments:

```
kube-prometheus-stack/
├── README.md                           # This file
├── base/
│   └── values.yaml                     # Common settings (retention, resources, etc.)
├── versions/
│   ├── v3.5.0-lts/
│   │   ├── values.yaml                 # LTS version override
│   │   ├── default-values.yaml         # Chart defaults for reference
│   │   └── README.md                   # LTS release notes
│   └── v3.9.0-latest/
│       ├── values.yaml                 # Latest version override
│       ├── default-values.yaml         # Chart defaults for reference
│       └── README.md                   # Latest release notes
└── environments/
    ├── minikube/
    │   └── values.yaml                 # Minikube-specific (fixes PV permissions)
    ├── dev/
    │   └── values.yaml                 # Minimal resources
    ├── staging/
    │   └── values.yaml                 # Moderate resources
    └── prod/
        └── values.yaml                 # HA, production-grade resources
```

## Version-Specific Installation

### Install on Minikube

Minikube requires special `securityContext` settings to fix hostpath PV permission issues:

```bash
# v3.5.0 LTS on Minikube
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f versions/v3.5.0-lts/values.yaml \
  -f environments/minikube/values.yaml

# v3.9.0 Latest on Minikube
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f versions/v3.9.0-latest/values.yaml \
  -f environments/minikube/values.yaml
```

### Install v3.5.0 LTS (Recommended for Production)

```bash
# Development (non-minikube)
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f versions/v3.5.0-lts/values.yaml \
  -f environments/dev/values.yaml

# Production
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f versions/v3.5.0-lts/values.yaml \
  -f environments/prod/values.yaml
```

### Install v3.9.0 Latest

```bash
# Development (non-minikube)
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f versions/v3.9.0-latest/values.yaml \
  -f environments/dev/values.yaml

# Staging
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f versions/v3.9.0-latest/values.yaml \
  -f environments/staging/values.yaml
```

### Using Specific Chart Version

Alternatively, use the chart version directly (includes matching Prometheus version):

```bash
# v3.5.0 LTS (chart 77.10.0)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --version 77.10.0 \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f environments/dev/values.yaml

# v3.9.0 Latest (chart 80.13.0)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --version 80.13.0 \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f environments/dev/values.yaml
```

### Version Mapping (Prometheus 3.x)

| Chart Version | Prometheus Version | Type   |
|---------------|--------------------|--------|
| 80.13.0       | v3.9.0             | Latest |
| 77.10.0       | v3.5.0             | LTS    |

## Custom Installation

### Using Values File

Create `values.yaml`:

```yaml
# values.yaml
prometheus:
  prometheusSpec:
    retention: 15d
    resources:
      requests:
        cpu: 2
        memory: 4Gi
      limits:
        cpu: 4
        memory: 8Gi
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi

grafana:
  enabled: true
  adminPassword: "your-secure-password"

alertmanager:
  enabled: true
```

Install with custom values:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus \
  -f values.yaml
```

### AWS EKS Specific Configuration

For EKS with EBS storage:

```yaml
# eks-values.yaml
prometheus:
  prometheusSpec:
    retention: 15d
    resources:
      requests:
        cpu: 2
        memory: 4Gi
      limits:
        cpu: 4
        memory: 8Gi
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3  # EKS gp3 storage class
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi

# Enable service monitors for AWS services
serviceMonitor:
  enabled: true
```

Install:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus \
  -f eks-values.yaml
```

## Configuration Examples

### 1. Enable Remote Write to Mimir

Create `remote-write-values.yaml`:

```yaml
prometheus:
  prometheusSpec:
    remoteWrite:
      - url: http://mimir-nginx.mimir.svc.cluster.local/api/v1/push
        headers:
          X-Scope-OrgID: demo
        queueConfig:
          capacity: 100000
          maxShards: 200
```

Apply:

```bash
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus \
  -f remote-write-values.yaml
```

### 2. Stateless Forwarder Mode (Minimal Retention)

```yaml
prometheus:
  prometheusSpec:
    retention: 2h
    disableCompaction: true
    walCompression: true
    remoteWrite:
      - url: http://mimir-nginx.mimir.svc.cluster.local/api/v1/push
        headers:
          X-Scope-OrgID: demo
```

### 3. High Availability Setup

```yaml
prometheus:
  prometheusSpec:
    replicas: 2
    retention: 15d
    resources:
      requests:
        cpu: 4
        memory: 8Gi
      limits:
        cpu: 8
        memory: 16Gi

alertmanager:
  alertmanagerSpec:
    replicas: 3
```

## Upgrade

```bash
# Update repo
helm repo update

# Check available versions
helm search repo prometheus-community/kube-prometheus-stack --versions

# Upgrade
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus \
  -f values.yaml
```

## Uninstall

```bash
# Uninstall release
helm uninstall prometheus -n prometheus

# Delete CRDs (optional, removes all Prometheus resources)
kubectl delete crd alertmanagerconfigs.monitoring.coreos.com
kubectl delete crd alertmanagers.monitoring.coreos.com
kubectl delete crd podmonitors.monitoring.coreos.com
kubectl delete crd probes.monitoring.coreos.com
kubectl delete crd prometheuses.monitoring.coreos.com
kubectl delete crd prometheusrules.monitoring.coreos.com
kubectl delete crd servicemonitors.monitoring.coreos.com
kubectl delete crd thanosrulers.monitoring.coreos.com

# Delete namespace
kubectl delete namespace prometheus
```

## Troubleshooting

### Check Prometheus Status

```bash
# Check pods
kubectl get pods -n prometheus

# Check Prometheus CRD
kubectl get prometheus -n prometheus

# Check logs
kubectl logs -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus --tail=100
```

### Check Resource Usage

```bash
# CPU and Memory
kubectl top pod -n prometheus

# Storage
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  df -h /prometheus
```

### Check Targets

```bash
# Port-forward
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-prometheus 9090:9090

# Open targets page
open http://localhost:9090/targets
```

### Common Issues

**1. Pod stuck in Pending:**
```bash
# Check events
kubectl describe pod -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0

# Common causes:
# - Insufficient resources
# - PVC not bound
# - Node selector mismatch
```

**2. High memory usage:**
```bash
# Check active series
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_tsdb_head_series' 2>/dev/null

# Reduce retention or increase memory
```

**3. Remote write failing:**
```bash
# Check failed samples
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_failed_total' 2>/dev/null

# Check logs for errors
kubectl logs -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus | grep -i error
```

## Monitoring Prometheus

### Key Metrics

```bash
# Active series
prometheus_tsdb_head_series

# Scrape duration
prometheus_target_interval_length_seconds

# Remote write rate
rate(prometheus_remote_storage_samples_total[5m])

# Memory usage
process_resident_memory_bytes
```

### Alerts

Pre-configured alerts are available in Prometheus rules:

```bash
# List all rules
kubectl get prometheusrules -n prometheus

# View specific rule
kubectl get prometheusrules -n prometheus prometheus-kube-prometheus-prometheus-operator -o yaml
```

## Best Practices

### Resource Planning

| Active Series | CPU Request | Memory Request | Storage |
|---------------|-------------|----------------|---------|
| < 100K        | 1 core      | 2Gi            | 10Gi    |
| 100K - 500K   | 2 cores     | 4Gi            | 25Gi    |
| 500K - 1M     | 4 cores     | 8Gi            | 50Gi    |
| 1M - 5M       | 8 cores     | 16Gi           | 100Gi   |
| > 5M          | 16+ cores   | 32Gi+          | 200Gi+  |

### Retention Strategy

- **Development**: 7 days
- **Production**: 15-30 days
- **Long-term**: Use remote write to Mimir/Thanos

### High Cardinality

If you have high cardinality (millions of series):

1. Enable remote write to Mimir
2. Reduce local retention to 2h
3. Increase memory limits
4. Consider metric relabeling to drop unnecessary labels

## References

- [kube-prometheus-stack Chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/cost_optimization/cost_opt_observability/)

## Version Compatibility

| Chart Version | Prometheus Version | Kubernetes Version |
|---------------|--------------------|--------------------|
| 55.x          | 2.49.x             | 1.19+              |
| 54.x          | 2.48.x             | 1.19+              |
| 53.x          | 2.47.x             | 1.19+              |
| 52.x          | 2.46.x             | 1.19+              |
| 51.x          | 2.45.x             | 1.19+              |

Check current versions:
```bash
helm search repo prometheus-community/kube-prometheus-stack
```

## Support

- GitHub Issues: https://github.com/prometheus-community/helm-charts/issues
- Slack: #prometheus-operator on Kubernetes Slack
