# Mimir Scripts

Post-deployment scripts for testing, monitoring, and validating Mimir.

## 📋 Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `test-mimir-endpoints.sh` | Test all HTTP endpoints | `bash test-mimir-endpoints.sh` |
| `check-memberlist-status.sh` | Check memberlist cluster status | `bash check-memberlist-status.sh` |
| `resource-usage.sh` | Monitor CPU, memory, storage | `bash resource-usage.sh` |
| `analyze-pod-errors.sh` | Find errors/warnings in logs | `bash analyze-pod-errors.sh` |
| `check-pod-logs.sh` | View raw pod logs | `bash check-pod-logs.sh` |

## 🚀 Quick Start

After deploying Mimir:

```bash
cd scripts

# 1. Test all endpoints
bash test-mimir-endpoints.sh

# 2. Check memberlist health
bash check-memberlist-status.sh

# 3. Monitor resource usage
bash resource-usage.sh

# 4. Analyze for errors
bash analyze-pod-errors.sh
```

## 📖 Scripts

### 1. test-mimir-endpoints.sh
**Purpose:** Automated testing of all Mimir HTTP endpoints

**Features:**
- Tests 50+ endpoints across all components
- Uses kubectl proxy (works on minikube & remote EKS)
- Color-coded pass/fail results

**Usage:**
```bash
# Basic
bash test-mimir-endpoints.sh

# Custom namespace
NAMESPACE=production bash test-mimir-endpoints.sh

# Custom tenant
TENANT_ID=team-a bash test-mimir-endpoints.sh
```

### 2. check-memberlist-status.sh
**Purpose:** Check memberlist gossip cluster health

**Features:**
- Shows total members and alive count per pod
- Uses kubectl proxy (works on minikube & remote EKS)
- Detects suspect/dead/left members

**Usage:**
```bash
# Basic
bash check-memberlist-status.sh

# Custom namespace
NAMESPACE=production bash check-memberlist-status.sh
```

### 3. resource-usage.sh
**Purpose:** Monitor CPU, memory, and storage usage

**Features:**
- Cluster-level node resources
- Namespace-level allocation & utilization
- Pod-level breakdown by component
- Storage (PVC) summary

**Usage:**
```bash
# Basic
bash resource-usage.sh

# Custom namespace
NAMESPACE=production bash resource-usage.sh
```

### 4. analyze-pod-errors.sh
**Purpose:** Find errors and warnings in pod logs

**Features:**
- Filters logs for errors/warnings only
- Shows top 10 errors, top 5 warnings per pod
- Quick health check

**Usage:**
```bash
# Basic (last 50 lines)
bash analyze-pod-errors.sh

# More lines
LINES=100 bash analyze-pod-errors.sh

# Custom namespace
NAMESPACE=production bash analyze-pod-errors.sh
```

### 5. check-pod-logs.sh
**Purpose:** View raw pod logs for detailed inspection

**Features:**
- Shows unfiltered logs from all pods
- Useful for debugging specific issues

**Usage:**
```bash
# Basic (last 50 lines)
bash check-pod-logs.sh

# More lines
LINES=200 bash check-pod-logs.sh
```

## 🔄 Typical Workflow

```bash
# 1. Deploy Mimir
cd ../install/helm/distributed/v2.17.x/small
helm install mimir grafana/mimir-distributed -f small-dev-minio-half.yaml -n mimir-test --create-namespace --timeout=10m

# 2. Wait for pods
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=mimir -n mimir-test --timeout=300s

# 3. Run health checks
cd ../../../../scripts
bash test-mimir-endpoints.sh
bash check-memberlist-status.sh
bash resource-usage.sh
bash analyze-pod-errors.sh
```

## 🛠️ Environment Variables

### test-mimir-endpoints.sh
- `NAMESPACE` (default: `mimir-test`)
- `GATEWAY_SVC` (default: `mimir-nginx`)
- `TENANT_ID` (default: `anonymous`)

### check-memberlist-status.sh
- `NAMESPACE` (default: `mimir-test`)

### resource-usage.sh
- `NAMESPACE` (default: `mimir-test`)

### analyze-pod-errors.sh
- `NAMESPACE` (default: `mimir-test`)
- `LINES` (default: `50`)

### check-pod-logs.sh
- `NAMESPACE` (default: `mimir-test`)
- `LINES` (default: `50`)

## 🔧 Technical Notes

- **kubectl proxy**: Scripts use `kubectl proxy` instead of port-forward for better compatibility with remote EKS clusters
- **Distroless images**: Mimir uses distroless containers, so scripts access endpoints via Kubernetes API proxy
- **Works everywhere**: All scripts work on both local minikube and remote EKS/AKS/GKE clusters
