# Operator Installation Guide

Deploy Prometheus using the Prometheus Operator with Kubernetes Custom Resource Definitions (CRDs).

## Overview

The Prometheus Operator provides Kubernetes-native deployment and management of Prometheus and related monitoring components. It uses CRDs to define, configure, and manage Prometheus instances declaratively.

### When to Use Operator

| ✅ Good For | ❌ Not For |
|-------------|-----------|
| OpenShift environments | Quick local testing |
| GitOps workflows | Simple single-node setups |
| Multi-tenant clusters | Learning Prometheus basics |
| Automated lifecycle management | Minikube/Docker Desktop |
| Production with operator patterns | Teams new to Kubernetes |

## Prerequisites

- Kubernetes 1.21+ or OpenShift 4.10+
- kubectl configured
- Sufficient cluster resources
- Persistent storage (recommended)

```bash
# Verify prerequisites
kubectl version --client
kubectl cluster-info
```

## Installation Methods

### 1. OpenShift (OperatorHub)

The easiest method for OpenShift users:

```bash
# Apply subscription
kubectl apply -f install/operator/openshift/subscription.yaml
```

Or install via OpenShift Console:
1. Navigate to Operators → OperatorHub
2. Search for "Prometheus Operator"
3. Click Install
4. Select namespace and approval strategy

### 2. Kubernetes with OLM

Install Operator Lifecycle Manager first, then the Prometheus Operator:

```bash
# Install OLM (if not already installed)
curl -sL https://github.com/operator-framework/operator-lifecycle-manager/releases/download/v0.28.0/install.sh | bash -s v0.28.0

# Verify OLM
kubectl get pods -n olm

# Install Prometheus Operator
kubectl apply -f install/operator/olm/catalog-source.yaml
kubectl apply -f install/operator/olm/subscription.yaml
```

### 3. Direct Installation (Without OLM)

For clusters without OLM:

```bash
# Install CRDs and operator directly
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Verify
kubectl get pods -n default -l app.kubernetes.io/name=prometheus-operator
```

## Deploy Prometheus

### 1. Create Namespace and RBAC

```bash
# Create namespace
kubectl create namespace monitoring

# Apply RBAC resources
kubectl apply -f install/operator/prometheus/rbac.yaml
```

### 2. Choose Size and Deploy

Select a size based on your requirements:

| Size | Retention | Replicas | Storage | Memory | Use Case |
|------|-----------|----------|---------|--------|----------|
| Demo | 24h | 1 | 10Gi | 1Gi | Development/Testing |
| Small | 15d | 2 | 50Gi | 4Gi | Small production |
| Medium | 30d | 2 | 100Gi | 8Gi | Medium production |
| Large | 90d | 3 | 500Gi | 16Gi | Large production (HA) |

```bash
# Demo (development)
kubectl apply -f install/operator/prometheus/prometheus-demo.yaml

# Small production
kubectl apply -f install/operator/prometheus/prometheus-small.yaml

# Medium production
kubectl apply -f install/operator/prometheus/prometheus-medium.yaml

# Large production (HA)
kubectl apply -f install/operator/prometheus/prometheus-large.yaml
```

### 3. Verify Deployment

```bash
# Check Prometheus CR
kubectl get prometheus -n monitoring

# Check pods
kubectl get pods -n monitoring

# Check status
kubectl describe prometheus prometheus-sample -n monitoring
```

## Prometheus CR Examples

### Demo Configuration

```yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: prometheus-demo
  namespace: monitoring
spec:
  replicas: 1
  retention: 24h
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1
      memory: 2Gi
  storage:
    volumeClaimTemplate:
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
  serviceAccountName: prometheus
  serviceMonitorSelector: {}
  podMonitorSelector: {}
```

### Production Configuration (HA)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: prometheus-prod
  namespace: monitoring
spec:
  replicas: 3
  retention: 90d
  resources:
    requests:
      cpu: 4
      memory: 16Gi
    limits:
      cpu: 8
      memory: 32Gi
  storage:
    volumeClaimTemplate:
      spec:
        storageClassName: gp3
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 500Gi
  serviceAccountName: prometheus
  serviceMonitorSelector:
    matchLabels:
      release: prometheus
  podMonitorSelector:
    matchLabels:
      release: prometheus
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app.kubernetes.io/name: prometheus
          topologyKey: kubernetes.io/hostname
```

## ServiceMonitor Configuration

ServiceMonitors define how Prometheus discovers and scrapes targets:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: monitoring
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: my-app
  namespaceSelector:
    matchNames:
      - default
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

Apply and verify:

```bash
kubectl apply -f servicemonitor.yaml
kubectl get servicemonitors -n monitoring
```

## PodMonitor Configuration

For pods without services:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: my-pods
  namespace: monitoring
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: my-app
  namespaceSelector:
    matchNames:
      - default
  podMetricsEndpoints:
    - port: metrics
      interval: 30s
```

## Access Prometheus

### Port Forward

```bash
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Open http://localhost:9090
```

### Create Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prometheus
  namespace: monitoring
spec:
  rules:
    - host: prometheus.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: prometheus-operated
                port:
                  number: 9090
```

## RBAC Configuration

The RBAC manifest (`rbac.yaml`) creates:

```yaml
# ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring

---
# ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources:
      - nodes
      - nodes/metrics
      - services
      - endpoints
      - pods
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources:
      - configmaps
    verbs: ["get"]
  - apiGroups: ["networking.k8s.io"]
    resources:
      - ingresses
    verbs: ["get", "list", "watch"]
  - nonResourceURLs: ["/metrics"]
    verbs: ["get"]

---
# ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
  - kind: ServiceAccount
    name: prometheus
    namespace: monitoring
```

## Common Operations

### Check Status

```bash
# Operator status
kubectl get pods -n operators

# Prometheus status
kubectl get prometheus -n monitoring
kubectl describe prometheus prometheus-sample -n monitoring

# ServiceMonitors
kubectl get servicemonitors -n monitoring
```

### View Logs

```bash
# Operator logs
kubectl logs -n operators -l app.kubernetes.io/name=prometheus-operator

# Prometheus logs
kubectl logs -n monitoring prometheus-prometheus-sample-0 -c prometheus
```

### Scale Replicas

```bash
kubectl patch prometheus prometheus-sample -n monitoring \
  --type merge -p '{"spec":{"replicas":3}}'
```

### Update Configuration

Edit the Prometheus CR:

```bash
kubectl edit prometheus prometheus-sample -n monitoring
```

Or apply updated manifest:

```bash
kubectl apply -f prometheus-updated.yaml
```

## Upgrade

### Upgrade Operator

```bash
# OLM manages upgrades automatically based on approval strategy
# Check current version
kubectl get csv -n operators

# For manual approval, approve pending InstallPlan
kubectl get installplan -n operators
kubectl patch installplan <name> -n operators --type merge -p '{"spec":{"approved":true}}'
```

### Upgrade Prometheus Version

```bash
kubectl patch prometheus prometheus-sample -n monitoring \
  --type merge -p '{"spec":{"version":"v2.55.0"}}'
```

## Uninstall

### Remove Prometheus Instance

```bash
kubectl delete prometheus prometheus-sample -n monitoring
kubectl delete -f install/operator/prometheus/rbac.yaml
```

### Remove Operator (OLM)

```bash
kubectl delete subscription prometheus-operator -n operators
kubectl delete csv -n operators -l operators.coreos.com/prometheus.operators
```

### Remove CRDs

```bash
kubectl delete crd prometheuses.monitoring.coreos.com
kubectl delete crd servicemonitors.monitoring.coreos.com
kubectl delete crd podmonitors.monitoring.coreos.com
kubectl delete crd alertmanagers.monitoring.coreos.com
kubectl delete crd prometheusrules.monitoring.coreos.com
kubectl delete crd alertmanagerconfigs.monitoring.coreos.com
kubectl delete crd probes.monitoring.coreos.com
kubectl delete crd thanosrulers.monitoring.coreos.com
```

### Remove Namespace

```bash
kubectl delete namespace monitoring
```

## Troubleshooting

### Operator Not Starting

```bash
# Check operator pods
kubectl get pods -n operators
kubectl describe pod -n operators <operator-pod>
kubectl logs -n operators <operator-pod>
```

### Prometheus Not Creating Pods

```bash
# Check Prometheus CR status
kubectl describe prometheus prometheus-sample -n monitoring

# Common issues:
# - Missing RBAC permissions
# - Invalid ServiceMonitor selector
# - Insufficient resources
```

### ServiceMonitor Not Discovered

```bash
# Check selector labels match
kubectl get prometheus -n monitoring -o yaml | grep -A5 serviceMonitorSelector

# Verify ServiceMonitor labels
kubectl get servicemonitor <name> -n monitoring -o yaml | grep -A5 labels

# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Open http://localhost:9090/targets
```

### PVC Not Bound

```bash
kubectl get pvc -n monitoring
kubectl describe pvc -n monitoring <pvc-name>

# Check StorageClass
kubectl get storageclass
```

## Helm vs Operator Comparison

| Aspect | Helm | Operator |
|--------|------|----------|
| Complexity | Lower | Higher |
| Automation | Manual upgrades | Automated lifecycle |
| Best for | Most K8s clusters | OpenShift, GitOps |
| Learning curve | Easier | Steeper |
| Flexibility | High | Opinionated |
| Multi-tenancy | Manual | Built-in support |
| GitOps | Requires ArgoCD/Flux | Native CRD support |

## Files Reference

| File | Description |
|------|-------------|
| `prometheus/rbac.yaml` | ServiceAccount and RBAC |
| `prometheus/prometheus-demo.yaml` | Demo size (development) |
| `prometheus/prometheus-small.yaml` | Small production |
| `prometheus/prometheus-medium.yaml` | Medium production |
| `prometheus/prometheus-large.yaml` | Large production (HA) |
| `openshift/subscription.yaml` | OpenShift OperatorHub |
| `olm/catalog-source.yaml` | OLM catalog source |
| `olm/subscription.yaml` | OLM subscription |

## Resources

- [Prometheus Operator Documentation](https://prometheus-operator.dev/)
- [Prometheus CRD Reference](https://prometheus-operator.dev/docs/api-reference/api/)
- [GitHub Repository](https://github.com/prometheus-operator/prometheus-operator)
- [OperatorHub](https://operatorhub.io/operator/prometheus)

## Next Steps

1. [Configure ServiceMonitors](../configuration/servicemonitors.md)
2. [Set up alerting with PrometheusRules](../configuration/alerting.md)
3. [Run validation tests](../testing/README.md)
