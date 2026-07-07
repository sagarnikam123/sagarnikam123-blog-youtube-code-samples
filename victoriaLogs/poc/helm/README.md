# VictoriaLogs — Helm Chart Deployment on EKS

Production-grade deployment using official VictoriaMetrics Helm charts on EKS.

## Prerequisites

- EKS cluster with `kubectl` access
- Helm 3 installed
- `aws-ebs-csi-driver` installed (for PersistentVolumes)
- Namespace: `observability`

## Architecture

```
EKS Cluster: observability-<region>
├── VictoriaLogs (StatefulSet, 1 replica for single / 3+ for cluster)
├── vmalert (Deployment)
├── AlertManager (Deployment)
├── VictoriaMetrics (StatefulSet, for recording rules)
├── Grafana (Deployment)
├── prometheus-msteams (Deployment, Teams webhook adapter)
└── Internal NLB (Service type: LoadBalancer, internal)
```

## Step 1: Add Helm Repos

```bash
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

## Step 2: Create Namespace

```bash
kubectl create namespace observability
```

## Step 3: Deploy VictoriaLogs (Single Node)

```bash
helm install victorialogs vm/victoria-logs-single \
  -n observability \
  -f values/victorialogs-single.yaml
```

For cluster mode:
```bash
helm install victorialogs vm/victoria-logs-cluster \
  -n observability \
  -f values/victorialogs-cluster.yaml
```

## Step 4: Deploy VictoriaMetrics (for recording rule metrics)

```bash
helm install victoriametrics vm/victoria-metrics-single \
  -n observability \
  -f values/victoriametrics.yaml
```

## Step 5: Deploy AlertManager

```bash
helm install alertmanager prometheus-community/alertmanager \
  -n observability \
  -f values/alertmanager.yaml
```

## Step 6: Deploy vmalert

```bash
helm install vmalert vm/victoria-metrics-alert \
  -n observability \
  -f values/vmalert.yaml
```

## Step 7: Deploy Grafana

```bash
helm install grafana grafana/grafana \
  -n observability \
  -f values/grafana.yaml
```

## Step 8: Deploy Fluent Bit DaemonSet (on EACH app EKS cluster)

```bash
# Run this on each app EKS cluster that needs to push logs
helm install fluent-bit fluent/fluent-bit \
  -n logging --create-namespace \
  -f values/fluentbit-daemonset.yaml \
  --set env[0].name=CLUSTER_NAME,env[0].value=app-prod \
  --set env[1].name=AWS_REGION,env[1].value=us-east-1
```

## Step 9: Expose VictoriaLogs via Internal NLB

The `victorialogs-single.yaml` values file configures a Service of type `LoadBalancer` with AWS internal NLB annotations. Other EKS clusters in the same VPC/region can push to this NLB endpoint.

## Verification

```bash
# Check all pods are running
kubectl get pods -n observability

# Port-forward VMUI for testing
kubectl port-forward svc/victorialogs -n observability 9428:9428

# Open http://localhost:9428/select/vmui/
```

## Updating Alert Rules

Alert rules are stored in a ConfigMap. To update:

```bash
# Edit the configmap
kubectl edit configmap vmalert-rules -n observability

# Or apply from file
kubectl create configmap vmalert-rules \
  --from-file=alert-rules.yaml=./rules/alert-rules.yaml \
  -n observability --dry-run=client -o yaml | kubectl apply -f -

# vmalert picks up changes automatically (watches configmap)
```
