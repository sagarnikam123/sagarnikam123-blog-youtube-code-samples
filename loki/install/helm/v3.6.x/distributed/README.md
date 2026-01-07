# Loki Distributed (Microservices) Mode - v3.6.x

## Overview

Loki is deployed as individual microservices. The most complicated but most capable, useful for large installs, typically over 1TB/day.

Each component runs as a separate deployment for maximum scalability and control.

## Prerequisites

- Kubernetes cluster (or Minikube for local testing)
- Helm 3.x installed
- kubectl configured

## Base Directory

All commands assume you're running from:
```
loki/install/helm/v3.6.x/
```

## Minikube Cluster Setup (Local Testing)

For local development and testing on Minikube:

### Recommended Configuration

```bash
# Balanced setup for MacBook Pro (16GB RAM, 6 cores)
minikube start --nodes 3 --cpus 4 --memory 8192 --disk-size 30g --driver=docker
```

**Resource Allocation:**
- 3 nodes for distributed testing
- 4 CPU cores (leaves 2 for host OS)
- 8 GB memory (leaves 8 GB for host OS)
- 30 GB disk per node (90 GB total)

### Alternative Configurations

```bash
# Minimum testing (resource-constrained environments)
minikube start --nodes 3 --cpus 2 --memory 6144 --disk-size 30g --driver=docker

# High-performance local dev (if you have 32GB+ RAM)
minikube start --nodes 3 --cpus 4 --memory 10240 --disk-size 40g --driver=docker
```

### Loki Configuration for Minikube

For Minikube deployments, reduce replicas in your `distributed/values.yaml`:

```yaml
ingester:
  replicas: 1
distributor:
  replicas: 1
querier:
  replicas: 1
```

This ensures components fit within Minikube's resource constraints while maintaining full functionality.

## Chart Information

### List Available Versions

```bash
# Search for Loki chart versions (shows both chart and app versions)
helm search repo grafana/loki --versions
```

**Note**: Chart version and app version are different:
- **Chart version**: Helm chart packaging version (specified with `--version`)
- **App version**: Loki application version (defined in chart, can be overridden via image tags)

### View Default Values

```bash
# Show default values for latest version
helm show values grafana/loki

# Show default values for specific version
helm show values grafana/loki --version 6.49.0

# Save default values to file (already saved as default-values.yaml in parent directory)
helm show values grafana/loki > ../default-values.yaml
```

## Installation

### 1. Add Grafana Helm Repository

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### 2. Install Loki (Distributed Mode)

```bash
# From base directory: loki/install/helm/v3.6.x/

# Install with latest chart version
helm install loki grafana/loki \
  -f distributed/values.yaml \
  -n loki --create-namespace

# Install specific chart version
helm install loki grafana/loki \
  -f distributed/values.yaml \
  --version 6.49.0 \
  -n loki --create-namespace
```

**Override App Version**: To use a specific Loki application version, set image tags in `distributed/values.yaml`:

```yaml
loki:
  image:
    tag: "3.6.3"  # Specific Loki version
```

### 3. Verify Deployment

```bash
# Check Helm release status
helm status loki -n loki

# List Helm releases
helm list -n loki

# Check pod status
kubectl get pods -n loki

# Watch deployment progress
kubectl get pods -w -n loki
```

**Note**: If pods are slow to schedule, verify pod affinity can be fulfilled in your cluster.

## Upgrade

```bash
# From base directory: loki/install/helm/v3.6.x/
helm upgrade loki grafana/loki \
  -f distributed/values.yaml \
  -n loki
```

## Uninstallation

### Standard Uninstall

```bash
# Uninstall Loki release
helm uninstall loki -n loki

# Delete namespace (optional)
kubectl delete namespace loki
```

### Forceful Uninstall

If standard uninstall hangs or fails:

```bash
# 1. Force uninstall Helm release
helm uninstall loki -n loki --no-hooks

# 2. Delete all resources
kubectl delete all,svc,cm,secret,pvc,sa --all -n loki --grace-period=0 --force

# 3. Delete namespace
kubectl delete namespace loki --grace-period=0 --force
```

**If namespace stuck**, remove finalizers:

```bash
kubectl get namespace loki -o json | jq '.spec.finalizers = []' | kubectl replace --raw "/api/v1/namespaces/loki/finalize" -f -
```

### Cleanup Verification

```bash
kubectl get all -n loki
kubectl get pvc -n loki
kubectl get namespace loki
```

## Installed Components

The distributed deployment includes:

| Component | Purpose |
|-----------|---------|
| **gateway** | NGINX reverse proxy |
| **minio** | Object storage backend |
| **distributor** | Log ingestion |
| **ingester** | Log writing to storage |
| **querier** | Log query execution |
| **query-frontend** | Query optimization |
| **query-scheduler** | Query coordination |
| **index-gateway** | Index queries |
| **compactor** | Log compaction |
| **ruler** | Alerting rules (optional) |

## Usage

### Sending Logs to Loki

#### From Inside Cluster

```
http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push
```

#### From Outside Cluster

1. **Port-forward the gateway**:

```bash
kubectl port-forward -n loki svc/loki-gateway 3100:80 &
```

2. **Send test logs**:

```bash
curl -H "Content-Type: application/json" -XPOST -s "http://127.0.0.1:3100/loki/api/v1/push" \
  --data-raw '{"streams": [{"stream": {"job": "test"}, "values": [["'$(date +%s)'000000000", "fizzbuzz"]]}]}'
```

3. **Query logs**:

```bash
curl "http://127.0.0.1:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="test"}' | jq .data.result
```

### Connecting Grafana

Add Loki as a datasource in Grafana:

```
http://loki-gateway.loki.svc.cluster.local/
```

## File Structure

```
v3.6.x/                          # Base directory
├── default-values.yaml          # Full upstream chart defaults (reference)
├── distributed/
│   ├── values.yaml              # Distributed mode overrides
│   └── README.md                # This file
├── simple-scalable/
│   └── values.yaml
└── single-binary/
    └── values.yaml
```
