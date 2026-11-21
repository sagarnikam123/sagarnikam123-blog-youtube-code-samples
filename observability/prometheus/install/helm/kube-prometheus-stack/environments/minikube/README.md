# Minikube Installation Guide

Quick setup for kube-prometheus-stack on minikube with persistent storage.

## Prerequisites

```bash
# Start minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --disk-size=20g

# Verify storage provisioner is enabled
minikube addons list | grep storage
```

## Installation

### Option 1: Quick Install (Recommended)

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install with layered values (base + version + environment)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace prometheus \
  --create-namespace \
  -f ../../base/values.yaml \
  -f ../../versions/v3.5.0-lts/values.yaml \
  -f values.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n prometheus --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n prometheus --timeout=300s
```

### Option 2: Custom Installation

```bash
# Create custom values file
cat > my-values.yaml <<EOF
prometheus:
  prometheusSpec:
    retention: 7d
    resources:
      requests:
        memory: 1Gi
      limits:
        memory: 2Gi
EOF

# Install with custom overrides
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace prometheus \
  --create-namespace \
  -f ../../base/values.yaml \
  -f ../../versions/v3.5.0-lts/values.yaml \
  -f values.yaml \
  -f my-values.yaml
```

## Access Services

```bash
# Prometheus
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open: http://localhost:9090

# Grafana
kubectl port-forward -n prometheus svc/prometheus-grafana 3000:80
# Open: http://localhost:3000
# Username: admin
# Password: prom-operator (default)

# Alertmanager
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-alertmanager 9093:9093
# Open: http://localhost:9093
```

## Verify Installation

```bash
# Check all pods
kubectl get pods -n prometheus

# Check PVCs
kubectl get pvc -n prometheus

# Check Prometheus targets
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-prometheus 9090:9090 &
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
```

## Troubleshooting

### Grafana Init Container Failing

**Symptom**: `init-chown-data` container fails with exit code 1

**Solution**: Already fixed in `values.yaml` with `runAsUser: 0`

### Prometheus Storage Issues

**Symptom**: `CreateContainerConfigError` - storage directory doesn't exist

**Solution**: Minikube's storage provisioner auto-creates directories. If issues persist:

```bash
# Delete and recreate PVCs
kubectl delete pvc --all -n prometheus
helm uninstall prometheus -n prometheus
# Reinstall
```

### Check Logs

```bash
# Prometheus logs
kubectl logs -n prometheus prometheus-prometheus-kube-prometheus-prometheus-0 -c prometheus

# Grafana logs
kubectl logs -n prometheus deployment/prometheus-grafana -c grafana

# Operator logs
kubectl logs -n prometheus deployment/prometheus-kube-prometheus-operator
```

## Cleanup

```bash
# Uninstall release
helm uninstall prometheus -n prometheus

# Delete namespace (removes all resources including PVCs)
kubectl delete namespace prometheus
```

## Configuration Details

### Storage
- **Prometheus**: emptyDir (5Gi limit, 3 day retention) - no persistent storage
- **Grafana**: emptyDir (no persistence) - data lost on restart
- **Alertmanager**: emptyDir (default)

> **Note**: Minikube environment uses emptyDir to avoid hostpath provisioner permission issues. Data is not persisted across pod restarts.

### Resources
- **Prometheus**: 500m CPU / 512Mi memory (request), 1 CPU / 1Gi memory (limit)
- **Grafana**: 50m CPU / 64Mi memory (request), 200m CPU / 256Mi memory (limit)
- **Alertmanager**: 50m CPU / 64Mi memory (request), 100m CPU / 128Mi memory (limit)

### Security Context
- **runAsUser: 0** - Required for minikube hostpath provisioner
- **runAsNonRoot: false** - Allows root user
- **fsGroup: 0** - Root group for file permissions

### Disabled Components
- kubeEtcd (not accessible in minikube)
- kubeControllerManager (not accessible in minikube)
- kubeScheduler (not accessible in minikube)
- kubeProxy (not accessible in minikube)
- kubeApiServer (reduces noise for local dev)
- coreDns (reduces noise for local dev)
- kubelet (reduces noise for local dev)
- kube-state-metrics (reduces noise for local dev)
- prometheusOperator selfMonitor (reduces noise for local dev)

## Values Hierarchy

```
base/values.yaml                    # Common defaults
  ↓
versions/v3.5.0-lts/values.yaml    # Version-specific overrides
  ↓
environments/minikube/values.yaml   # Environment-specific overrides
  ↓
my-values.yaml (optional)           # Custom overrides
```

## Next Steps

- Configure remote write to Mimir: See `../../README.md`
- Add custom dashboards: See Grafana documentation
- Configure alerting: See Alertmanager documentation
- Scale for production: Use `environments/prod/values.yaml`

## Support

- **Issues**: Check troubleshooting section above
- **Documentation**: [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- **Prometheus**: [prometheus.io](https://prometheus.io/docs/)
