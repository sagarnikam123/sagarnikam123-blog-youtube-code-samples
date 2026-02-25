# Prometheus Installation using kube-prometheus-stack

Complete guide to install Prometheus on Kubernetes/EKS using the kube-prometheus-stack Helm chart.

## Overview

**kube-prometheus-stack** is the recommended way to deploy Prometheus on Kubernetes. It includes:

- Prometheus Operator (CRD-based configuration)
- Prometheus Server
- Alertmanager
- Grafana
- Node Exporter
- Kube-state-metrics
- Pre-configured dashboards and alerts

## Prerequisites

- Kubernetes cluster (1.19+) or AWS EKS
- kubectl configured
- Helm 3.x installed

```bash
# Verify prerequisites
kubectl version --client
helm version

# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

## Folder Structure

This repository uses a layered values file approach for multi-version and multi-environment deployments:

```
kube-prometheus-stack/
├── README.md                           # This file
├── base/
│   └── values.yaml                     # Common settings (retention, resources, serviceMonitor)
├── versions/
│   ├── v3.5.0-lts/
│   │   ├── values.yaml                 # LTS version image tags
│   │   ├── default-values.yaml         # Chart defaults for reference
│   │   └── README.md                   # Release notes
│   └── v3.9.0-latest/
│       ├── values.yaml                 # Latest version image tags
│       ├── default-values.yaml         # Chart defaults for reference
│       └── README.md                   # Release notes
└── environments/
    ├── minikube/
    │   └── values.yaml                 # Minikube-specific (PV permissions, disabled alerts)
    ├── dev/
    │   └── values.yaml                 # Dev environment (tolerations, ingress, sub-path)
    ├── staging/
    │   └── values.yaml                 # Staging environment
    └── prod/
        └── values.yaml                 # Production (HA, resources)
```

**Values file precedence** (later files override earlier):
```
base/values.yaml → versions/<version>/values.yaml → environments/<env>/values.yaml
```

## Quick Start

### Default Installation (without custom values)

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace
```

### Verify Installation

```bash
# Check pods
kubectl get pods -n prometheus

# Access Prometheus UI
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-prometheus 9090:9090
open http://localhost:9090

# Access Grafana (username: admin)
kubectl port-forward -n prometheus svc/prometheus-grafana 3000:80
kubectl get secret -n prometheus prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
open http://localhost:3000
```

## Installation by Environment

### Minikube

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --version 77.10.0 \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f environments/minikube/values.yaml \
  --timeout 15m
```

### Development (EKS)

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --version 77.10.0 \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f environments/dev/scnx-global-dev-aps1-eks.yaml \
  --timeout 15m
```

### Production (EKS)

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --version 77.10.0 \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f environments/prod/scnx-dts01-eks.yaml \
  --timeout 15m
```

### Using Latest Version (v3.9.0)

Replace `--version 77.10.0` with `--version 80.13.0`:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --version 80.13.0 \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f environments/dev/values.yaml \
  --timeout 15m
```

> **Note:** The `versions/` folder contains `default-values.yaml` for reference only. Use `-f versions/<version>/values.yaml` only when you need to override the default Prometheus version bundled with the chart.

## Version Management

### Check Available Versions

```bash
# List chart versions
helm search repo prometheus-community/kube-prometheus-stack --versions

# Check Prometheus version in a specific chart
helm show values prometheus-community/kube-prometheus-stack --version 77.10.0 | grep -A2 "prometheus/prometheus"

# Get default values for reference
helm show values prometheus-community/kube-prometheus-stack --version 77.10.0 > default-values.yaml
```

### Version Mapping (Prometheus 3.x)

| Chart Version | Prometheus | Grafana | Alertmanager | Type   |
|---------------|------------|---------|--------------|--------|
| 80.13.0       | v3.9.0     | 12.3.1  | v0.28.0      | Latest |
| 77.10.0       | v3.5.0     | 11.4.0  | v0.28.0      | LTS    |

> **Note:** The chart's `appVersion` is the Prometheus Operator version, not Prometheus itself.

### Verify Installed Versions

```bash
# Prometheus
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 \
  -c prometheus -- prometheus --version

# Grafana
kubectl exec -n prometheus deploy/prometheus-grafana -c grafana -- grafana-server -v

# Alertmanager
kubectl exec -n prometheus alertmanager-prometheus-kube-prometheus-alertmanager-0 \
  -c alertmanager -- alertmanager --version

# All images
kubectl get pods -n prometheus -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{range .spec.containers[*]}{.image}{'\n'}{end}{end}"
```

### Override Component Versions

Add to your environment values file or use inline:

```yaml
prometheus:
  prometheusSpec:
    image:
      registry: quay.io
      repository: prometheus/prometheus
      tag: v3.5.0

grafana:
  image:
    tag: 11.4.0

alertmanager:
  alertmanagerSpec:
    image:
      tag: v0.28.0
```

Inline:
```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f base/values.yaml \
  -f environments/dev/values.yaml \
  --set prometheus.prometheusSpec.image.tag=v3.5.0
```

## Upgrade

```bash
helm repo update

helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --version 77.10.0 \
  -n prometheus \
  -f base/values.yaml \
  -f environments/dev/values.yaml \
  --timeout 15m
```

## AWS EKS Configuration

### Prerequisites: EBS CSI Driver

```bash
# Verify EBS CSI driver
kubectl get pods -n kube-system | grep ebs-csi

# If not installed
aws eks create-addon \
  --cluster-name <cluster-name> \
  --addon-name aws-ebs-csi-driver \
  --region <region>
```

### Create gp3 StorageClass

```bash
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  fsType: ext4
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF
```

## Configuration Examples

### Remote Write to Mimir

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

### Stateless Forwarder (Minimal Retention)

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

### High Availability

```yaml
prometheus:
  prometheusSpec:
    replicas: 2
    retention: 15d
    resources:
      requests:
        cpu: 4
        memory: 8Gi

alertmanager:
  alertmanagerSpec:
    replicas: 3
```

## Enable ServiceMonitor for Your Applications

ServiceMonitors tell Prometheus which services to scrape metrics from. Follow these steps to enable monitoring for your applications.

### Prerequisites

1. Your application must expose a metrics endpoint (e.g., `/actuator/prometheus` for Spring Boot, `/metrics` for most apps)
2. Prometheus must be configured to scrape from all namespaces (default in our setup):
   ```yaml
   prometheus:
     prometheusSpec:
       serviceMonitorNamespaceSelector: {}
       serviceMonitorSelector: {}
   ```

### Step 1: Verify Your App Exposes Metrics

Check if your application exposes metrics:

```bash
# For Spring Boot apps (Actuator)
kubectl exec -n <namespace> deploy/<deployment-name> -- \
  curl -s localhost:<port>/actuator/prometheus | head -10

# For generic apps
kubectl exec -n <namespace> deploy/<deployment-name> -- \
  curl -s localhost:<port>/metrics | head -10
```

Common metrics paths:
| Framework | Path | Default Port |
|-----------|------|--------------|
| Spring Boot Actuator | `/actuator/prometheus` | app port |
| Micrometer | `/actuator/prometheus` | app port |
| OpenTelemetry Collector | `/metrics` | 8888 |
| Node.js (prom-client) | `/metrics` | app port |
| Go (promhttp) | `/metrics` | app port |

### Step 2: Get Service Labels and Port Name

```bash
# Get service labels
kubectl get svc -n <namespace> <service-name> -o yaml | grep -A5 "labels:"

# Get port name
kubectl get svc -n <namespace> <service-name> -o yaml | grep -A3 "ports:"
```

### Step 3: Create ServiceMonitor

Create a ServiceMonitor in the same namespace as your service:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: <service-name>
  namespace: <namespace>
  labels:
    release: prometheus  # Required for Prometheus to discover
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: <service-name>  # Must match service labels
  endpoints:
    - port: http                              # Must match service port name
      path: /actuator/prometheus              # Metrics endpoint path
      interval: 30s                           # Scrape interval
```

Apply it:
```bash
kubectl apply -f servicemonitor.yaml
```

### Step 4: Verify ServiceMonitor is Working

```bash
# Check ServiceMonitor created
kubectl get servicemonitors -n <namespace>

# Check Prometheus targets (wait 1-2 minutes)
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open http://localhost:9090/targets and search for your service
```

### Examples

#### Spring Boot Application

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-spring-app
  namespace: my-namespace
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: my-spring-app
  endpoints:
    - port: http
      path: /actuator/prometheus
      interval: 30s
```

#### OpenTelemetry Collector

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: otel-collector
  namespace: observability
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: otel-collector-collector-monitoring
  endpoints:
    - port: monitoring
      path: /metrics
      interval: 30s
```

#### Multiple Endpoints (Different Ports)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: multi-port-app
  namespace: my-namespace
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: multi-port-app
  endpoints:
    - port: http
      path: /actuator/prometheus
      interval: 30s
    - port: grpc-metrics
      path: /metrics
      interval: 30s
```

### Enable Metrics in Spring Boot

If your Spring Boot app doesn't expose metrics, add these dependencies:

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

```yaml
# application.yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
  endpoint:
    prometheus:
      enabled: true
```

### Troubleshooting ServiceMonitors

| Issue | Cause | Solution |
|-------|-------|----------|
| Target not appearing | Label mismatch | Verify `selector.matchLabels` matches service labels |
| Target down | Wrong port/path | Check port name and metrics path |
| No data | Metrics not exposed | Verify app exposes `/actuator/prometheus` or `/metrics` |
| 401/403 errors | Auth required | Add `basicAuth` or `bearerTokenSecret` to endpoint |

```bash
# Debug: Check if Prometheus can reach the target
kubectl exec -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -- \
  wget -qO- http://<service>.<namespace>.svc.cluster.local:<port>/actuator/prometheus | head -5
```

---

## Disable ServiceMonitors

See [FAQ.md - How to exclude services from scraping](../../docs/FAQ.md#how-to-exclude-services-from-scraping) for all 5 methods.

### Disable Kubernetes Components

```yaml
kubeApiServer:
  enabled: false
coreDns:
  enabled: false
kubelet:
  enabled: false
kubeEtcd:
  enabled: false
kubeControllerManager:
  enabled: false
kubeScheduler:
  enabled: false
kubeProxy:
  enabled: false
```

### Disable Stack Components

```yaml
kube-state-metrics:
  enabled: false

prometheus-node-exporter:
  enabled: false

prometheusOperator:
  serviceMonitor:
    selfMonitor: false

grafana:
  serviceMonitor:
    enabled: false
```

### ServiceMonitor Selectors

```yaml
prometheus:
  prometheusSpec:
    serviceMonitorSelector:
      matchLabels:
        prometheus: main
    serviceMonitorNamespaceSelector: {}
```

## Multiple Instances

To run multiple Prometheus instances, use unique names:

```bash
helm install prometheus-dev prometheus-community/kube-prometheus-stack \
  -n prometheus-dev --create-namespace \
  -f base/values.yaml \
  -f environments/dev/values.yaml \
  --set fullnameOverride=prometheus-dev \
  --set grafana.fullnameOverride=grafana-dev \
  --set prometheusOperator.fullnameOverride=prometheus-operator-dev
```

## Uninstall

```bash
helm uninstall prometheus -n prometheus

# Delete CRDs (optional - only if you want to completely remove Prometheus Operator)
kubectl delete crd alertmanagerconfigs.monitoring.coreos.com
kubectl delete crd alertmanagers.monitoring.coreos.com
kubectl delete crd podmonitors.monitoring.coreos.com
kubectl delete crd probes.monitoring.coreos.com
kubectl delete crd prometheusagents.monitoring.coreos.com
kubectl delete crd prometheuses.monitoring.coreos.com
kubectl delete crd prometheusrules.monitoring.coreos.com
kubectl delete crd scrapeconfigs.monitoring.coreos.com
kubectl delete crd servicemonitors.monitoring.coreos.com
kubectl delete crd thanosrulers.monitoring.coreos.com

kubectl delete namespace prometheus
```

## Troubleshooting

See [FAQ.md](../../docs/FAQ.md) for detailed troubleshooting commands and operational guides.

### Quick Checks

```bash
kubectl get pods -n prometheus
kubectl get prometheus -n prometheus
kubectl logs -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus --tail=100
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Pod Pending | PVC not bound | Check StorageClass, EBS CSI driver |
| OOMKilled | Memory too low | Increase memory limits |
| Scrape timeout | Target slow/unreachable | Check target health, network |
| Remote write lag | Queue backing up | Increase shards, check Mimir |

## Resource Sizing

See [FAQ.md - Resource Sizing Guidelines](../../docs/FAQ.md#resource-sizing-guidelines) for detailed sizing with formulas.

| Active Series | CPU | Memory | Storage |
|---------------|-----|--------|---------|
| < 100K | 1 | 2Gi | 10Gi |
| 100K - 500K | 2 | 4Gi | 25Gi |
| 500K - 1M | 4 | 8Gi | 50Gi |
| 1M - 5M | 8 | 16Gi | 100Gi |
| > 5M | 16+ | 32Gi+ | 200Gi+ |

## References

- [kube-prometheus-stack Chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [ArtifactHub - Version Mapping](https://artifacthub.io/packages/helm/prometheus-community/kube-prometheus-stack)
