# Prometheus Operator Local Simulation

Simulates the `prod-eks` cluster's Prometheus namespace on local minikube.

## Production Reference

| Component | Version |
|-----------|---------|
| Helm Chart | kube-prometheus-stack 77.10.0 |
| Prometheus | v3.5.0 |
| Alertmanager | v0.28.1 |
| kube-state-metrics | 2.17.0 |
| node-exporter | 1.9.1 |
| Grafana | 12.1.1 |

## Quick Start

```bash
# Start minikube (if not running)
minikube start --cpus=4 --memory=8192

# Run the setup script
./setup.sh
```

## What Gets Deployed

1. **Prometheus Operator** (via Helm) - manages CRDs
2. **Prometheus CR** - matching prod spec (scaled down for local)
3. **Alertmanager CR** - 1 replica (prod has 3)
4. **ServiceMonitors** - all 5 from prod (grafana, alertmanager, prometheus, kube-state-metrics, node-exporter)
5. **PrometheusRules** - general.rules + prometheus self-monitoring rules
6. **RBAC** - ServiceAccount, ClusterRole, ClusterRoleBinding

## Differences from Production

| Setting | Production | Local |
|---------|-----------|-------|
| Prometheus replicas | 1 | 1 |
| Alertmanager replicas | 3 | 1 |
| Storage | 20Gi gp3 EBS | 5Gi standard |
| CPU request | 1 | 500m |
| Memory request | 4Gi | 1Gi |
| CPU limit | 2 | 1 |
| Memory limit | 8Gi | 2Gi |
| Tolerations | app-support | removed |
| External URL | https://\<prod-url>/prometheus | http://localhost:9090 |
| Scrape interval | 5m | 30s (faster feedback locally) |

## Accessing Services

```bash
# Prometheus UI
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n prometheus

# Alertmanager UI
kubectl port-forward svc/prometheus-kube-prometheus-alertmanager 9093:9093 -n prometheus

# Grafana UI (admin/prom-operator)
kubectl port-forward svc/prometheus-grafana 3000:80 -n prometheus
```

## Chart Versions

| | Chart Version | App Version | Notes |
|--|---------------|-------------|-------|
| Production | 77.10.0 | - | Currently deployed |
| Latest | 88.5.4 | v0.93.1 | As of Aug 2026 |

To find the latest version:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm search repo prometheus-community/kube-prometheus-stack --versions | head -5
```

To use the latest instead of prod-matching version, update `CHART_VERSION` in `setup.sh`.

## Teardown

```bash
./teardown.sh
```
