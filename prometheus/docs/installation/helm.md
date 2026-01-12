# Helm Installation Guide

Deploy Prometheus on Kubernetes using the kube-prometheus-stack Helm chart.

## Overview

Helm installation is the recommended method for Kubernetes deployments. The kube-prometheus-stack chart provides:

- Prometheus Server
- Prometheus Operator
- Alertmanager
- Grafana
- Node Exporter
- Kube-state-metrics
- Pre-configured dashboards and alerts

## Prerequisites

- Kubernetes cluster 1.19+
- kubectl configured
- Helm 3.x installed
- Sufficient cluster resources

```bash
# Verify prerequisites
kubectl version --client
helm version
kubectl cluster-info
```

## Quick Start

### 1. Add Helm Repository

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

### 2. Install

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
```

### 3. Verify

```bash
kubectl get pods -n monitoring
```

### 4. Access Prometheus

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open http://localhost:9090
```

### 5. Access Grafana

```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Get admin password
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
echo

# Open http://localhost:3000 (username: admin)
```

## Values File Structure

This repository organizes Helm values for multi-version and multi-environment deployments:

```
install/helm/kube-prometheus-stack/
├── base/
│   └── values.yaml                 # Common settings
├── versions/
│   ├── v3.5.0-lts/
│   │   └── values.yaml             # LTS version
│   └── v3.9.0-latest/
│       └── values.yaml             # Latest version
└── environments/
    ├── minikube/
    │   └── values.yaml             # Minikube-specific
    ├── dev/
    │   └── values.yaml             # Development
    ├── staging/
    │   └── values.yaml             # Staging
    └── prod/
        └── values.yaml             # Production (HA)
```

## Environment-Specific Installation

### Minikube

Minikube requires special `securityContext` settings:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f install/helm/kube-prometheus-stack/base/values.yaml \
  -f install/helm/kube-prometheus-stack/versions/v3.5.0-lts/values.yaml \
  -f install/helm/kube-prometheus-stack/environments/minikube/values.yaml
```

### Development

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f install/helm/kube-prometheus-stack/base/values.yaml \
  -f install/helm/kube-prometheus-stack/versions/v3.5.0-lts/values.yaml \
  -f install/helm/kube-prometheus-stack/environments/dev/values.yaml
```

### Staging

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f install/helm/kube-prometheus-stack/base/values.yaml \
  -f install/helm/kube-prometheus-stack/versions/v3.9.0-latest/values.yaml \
  -f install/helm/kube-prometheus-stack/environments/staging/values.yaml
```

### Production

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f install/helm/kube-prometheus-stack/base/values.yaml \
  -f install/helm/kube-prometheus-stack/versions/v3.5.0-lts/values.yaml \
  -f install/helm/kube-prometheus-stack/environments/prod/values.yaml
```

## Version Selection

### Prometheus Versions

| Type | Version | Chart Version | Use Case |
|------|---------|---------------|----------|
| LTS | v3.5.0 | 77.10.0 | Production (stability) |
| Latest | v3.9.0 | 80.13.0 | Development (features) |

### Install Specific Chart Version

```bash
# LTS (v3.5.0)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --version 77.10.0 \
  -n monitoring --create-namespace

# Latest (v3.9.0)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --version 80.13.0 \
  -n monitoring --create-namespace
```

### Override Prometheus Version

```yaml
# values.yaml
prometheus:
  prometheusSpec:
    image:
      registry: quay.io
      repository: prometheus/prometheus
      tag: v3.5.0
```

## Configuration

### Basic Configuration

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

### AWS EKS Configuration

```yaml
# eks-values.yaml
prometheus:
  prometheusSpec:
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 100Gi
```

### High Availability

```yaml
# ha-values.yaml
prometheus:
  prometheusSpec:
    replicas: 2
    podAntiAffinity: hard

alertmanager:
  alertmanagerSpec:
    replicas: 3
```

### Remote Write to Mimir

```yaml
# remote-write-values.yaml
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

## Resource Planning

| Active Series | CPU Request | Memory Request | Storage |
|---------------|-------------|----------------|---------|
| < 100K | 1 core | 2Gi | 10Gi |
| 100K - 500K | 2 cores | 4Gi | 25Gi |
| 500K - 1M | 4 cores | 8Gi | 50Gi |
| 1M - 5M | 8 cores | 16Gi | 100Gi |
| > 5M | 16+ cores | 32Gi+ | 200Gi+ |

## Common Operations

### Check Installation

```bash
# Pods
kubectl get pods -n monitoring

# Prometheus CRD
kubectl get prometheus -n monitoring

# ServiceMonitors
kubectl get servicemonitors -n monitoring
```

### View Logs

```bash
kubectl logs -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -f
```

### Check Targets

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open http://localhost:9090/targets
```

### Reload Configuration

```bash
# Prometheus reloads automatically when ConfigMaps change
# Or force reload:
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  kill -HUP 1
```

## Upgrade

```bash
# Update repo
helm repo update

# Check available versions
helm search repo prometheus-community/kube-prometheus-stack --versions

# Upgrade
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f values.yaml
```

## Uninstall

```bash
# Uninstall release
helm uninstall prometheus -n monitoring

# Delete CRDs (optional)
kubectl delete crd alertmanagerconfigs.monitoring.coreos.com
kubectl delete crd alertmanagers.monitoring.coreos.com
kubectl delete crd podmonitors.monitoring.coreos.com
kubectl delete crd probes.monitoring.coreos.com
kubectl delete crd prometheuses.monitoring.coreos.com
kubectl delete crd prometheusrules.monitoring.coreos.com
kubectl delete crd servicemonitors.monitoring.coreos.com
kubectl delete crd thanosrulers.monitoring.coreos.com

# Delete namespace
kubectl delete namespace monitoring
```

## Troubleshooting

### Pod Stuck in Pending

```bash
kubectl describe pod -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0

# Common causes:
# - Insufficient resources
# - PVC not bound (check StorageClass)
# - Node selector mismatch
```

### PVC Not Bound

```bash
kubectl get pvc -n monitoring
kubectl describe pvc -n monitoring prometheus-prometheus-kube-prometheus-prometheus-db-prometheus-prometheus-kube-prometheus-prometheus-0

# Check StorageClass
kubectl get storageclass
```

### High Memory Usage

```bash
# Check active series
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_tsdb_head_series'

# Reduce retention or increase memory
```

### ServiceMonitor Not Working

```bash
# Check ServiceMonitor
kubectl get servicemonitors -n monitoring
kubectl describe servicemonitor <name> -n monitoring

# Verify labels match
kubectl get prometheus -n monitoring -o yaml | grep -A10 serviceMonitorSelector
```

### Remote Write Failing

```bash
# Check failed samples
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_failed_total'

# Check logs
kubectl logs -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus | grep -i error
```

## Verify Installed Versions

```bash
# Prometheus version
kubectl exec -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus -- \
  prometheus --version

# Grafana version
kubectl exec -n monitoring deploy/prometheus-grafana -c grafana -- grafana-server -v

# All pod images
kubectl get pods -n monitoring -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{range .spec.containers[*]}{.image}{'\n'}{end}{end}"
```

## Best Practices

1. **Use LTS for production** - More stable, longer support
2. **Set resource limits** - Prevent resource exhaustion
3. **Enable persistent storage** - Survive pod restarts
4. **Configure retention** - Balance storage vs history needs
5. **Use remote write** - For long-term storage (Mimir/Thanos)
6. **Monitor Prometheus** - Meta-monitoring is essential
7. **Regular backups** - Especially for Alertmanager state

## Next Steps

1. [Configure scrape targets](../configuration/kubernetes-discovery.md)
2. [Set up ServiceMonitors](../configuration/servicemonitors.md)
3. [Configure alerting](../configuration/alerting.md)
4. [Run validation tests](../testing/README.md)
