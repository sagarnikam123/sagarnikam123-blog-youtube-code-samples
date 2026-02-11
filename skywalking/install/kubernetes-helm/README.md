# Apache SkyWalking Kubernetes Deployment

Production-grade Apache SkyWalking deployment using Helm charts with BanyanDB storage.

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Upgrade](#upgrade)
- [Uninstall](#uninstall)
- [Kubernetes Monitoring](#kubernetes-monitoring)
- [Gateway Monitoring](#gateway-monitoring)
- [Database Monitoring](#database-monitoring)
- [Message Queue Monitoring](#message-queue-monitoring)
- [Flink Monitoring](#flink-monitoring)
- [Service Mesh Monitoring](#service-mesh-monitoring)
- [Cilium Monitoring](#cilium-monitoring)
- [AWS Monitoring (EKS Only)](#aws-monitoring-eks-only)
- [Testing Services (Minikube)](#testing-services-minikube)
- [Agent Configuration](#agent-configuration)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### Overall Architecture

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                              Kubernetes Cluster                                   │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│                            DATA COLLECTION LAYER                                  │
│  ┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐ │
│  │        Application Agents           │  │     Infrastructure Monitoring       │ │
│  │   (Java, Python, Go, Node.js...)    │  │                                     │ │
│  └─────────────────┬───────────────────┘  │  ┌─────────────┐ ┌─────────────┐    │ │
│                    │                      │  │kube-state-  │ │node-exporter│    │ │
│                    ▼                      │  │metrics      │ │             │    │ │
│  ┌─────────────────────────────────────┐  │  └──────┬──────┘ └──────┬──────┘    │ │
│  │   SkyWalking Satellite (Optional)   │  │         └───────┬───────┘           │ │
│  │  Load balancing, buffering, proxy   │  │                 ▼                   │ │
│  └─────────────────┬───────────────────┘  │  ┌─────────────────────────────┐    │ │
│                    │                      │  │      OTel Collector         │    │ │
│                    │                      │  │   (Prometheus → OTLP)       │    │ │
│                    │                      │  └──────────────┬──────────────┘    │ │
│                    │                      └─────────────────┼───────────────────┘ │
│                    │                                        │                     │
│                    │  Traces, Logs, Agent Metrics           │  Infra Metrics      │
│                    │  (gRPC)                                │  (OTLP)             │
│                    └────────────────────┬───────────────────┘                     │
│                                         ▼                                         │
│                         PROCESSING & STORAGE LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                        SkyWalking OAP Server                                │  │
│  │        ┌─────────┐        ┌─────────┐        ┌─────────┐                    │  │
│  │        │  OAP-1  │        │  OAP-2  │        │  OAP-3  │   (Cluster mode)   │  │
│  │        └─────────┘        └─────────┘        └─────────┘                    │  │
│  └────────────────────────────────┬────────────────────────────────────────────┘  │
│                                   │                                               │
│                                   ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                           BanyanDB Storage                                  │  │
│  │                                                                             │  │
│  │    ┌─────────────────┐       ┌────────────────────────────────────────┐     │  │
│  │    │ Liaison (Query) │       │          Data Nodes (Storage)          │     │  │
│  │    │   (x2, HA)      │       │    ┌────────┐ ┌────────┐ ┌────────┐    │     │  │
│  │    └────────┬────────┘       │    │ Data-1 │ │ Data-2 │ │ Data-3 │    │     │  │
│  │             │                │    └────────┘ └────────┘ └────────┘    │     │  │
│  │             ▼                └────────────────────────────────────────┘     │  │
│  │    ┌─────────────────┐                        ▲                             │  │
│  │    │  etcd (x3)      │────────────────────────┘                             │  │
│  │    │ (coordination)  │  cluster metadata, shard mapping                     │  │
│  │    └─────────────────┘                                                      │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
│                              VISUALIZATION LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                            SkyWalking UI                                    │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Auto-Injection Architecture (SWCK Operator)

The SkyWalking Cloud on Kubernetes (SWCK) operator provides automatic Java agent injection.
Just label a namespace and all Java pods get instrumented automatically.

```text
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         Application Namespaces                                       │
│  (hunt, shared, response, analytics, etc.)                                           │
│                                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                       │
│  │   Java App      │  │   Java App      │  │   Java App      │                       │
│  │   + Agent       │  │   + Agent       │  │   + Agent       │  ← Auto-injected      │
│  │   (auto)        │  │   (auto)        │  │   (auto)        │    by SWCK            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                       │
│           │                    │                    │                                │
└───────────┼────────────────────┼────────────────────┼────────────────────────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │ gRPC (11800)
                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────-─┐
│                              skywalking namespace                                    │
│                              (Deployed via Helm)                                     │
│                                                                                      │
│  ┌──────────────┐       ┌──────────────┐       ┌────────────────────────────────┐    │
│  │   Satellite  │──────▶│     OAP      │──────▶│       BanyanDB Cluster         │    │
│  │     (x2)     │       │    (x3)      │       │                                │    │
│  └──────────────┘       └──────────────┘       │   ┌────────┐    ┌────────┐     │    │
│                                                │   │Liaison │    │Liaison │     │    │
│  ┌──────────────┐                              │   │  (1)   │    │  (2)   │     │    │
│  │      UI      │                              │   └───┬────┘    └───┬────┘     │    │
│  │     (x2)     │                              │       │             │          │    │
│  └──────────────┘                              │       ▼             ▼          │    │
│                                                │   ┌────────┐    ┌────────┐     │    │
│                                                │   │  Data  │    │  Data  │     │    │
│                                                │   │  (1)   │    │  (2)   │     │    │
│                                                │   └───┬────┘    └───┬────┘     │    │
│                                                │       │             │          │    │
│                                                │       ▼             ▼          │    │
│                                                │   ┌────────────────────────┐   │    │
│                                                │   │      etcd (x3)         │   │    │
│                                                │   │    (coordination)      │   │    │
│                                                │   └────────────────────────┘   │    │
│                                                └────────────────────────────────┘    │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         skywalking-swck-system namespace                             │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────-─┐  │
│  │  SWCK Operator                                                                 │  │
│  │  - Watches pod creation in labeled namespaces                                  │  │
│  │  - Injects init container + env vars + volumes                                 │  │
│  │  - Points agents to: skywalking-satellite.skywalking.svc:11800                 │  │
│  └──────────────────────────────────────────────────────────────────────────-─────┘  │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**Deployment Summary:**

| Component | Deployment Method | Purpose |
|-----------|------------------|---------|
| OAP + UI + BanyanDB + Satellite | Helm (`values.yaml`) | Backend infrastructure |
| SWCK Operator | `kubectl apply` (one-time) | Auto-inject agents |
| Java Agents | Auto-injected by SWCK | Send traces to Satellite |

**Enable auto-injection:**

```bash
# 1. Deploy SWCK operator (one-time)
./agents/java/swck-operator/deploy.sh install

# 2. Label namespace for injection (note: uses 'swck-injection' label)
kubectl label namespace hunt swck-injection=enabled

# 3. Restart pods to trigger injection
kubectl rollout restart deployment -n hunt
```

---

## Prerequisites

| Requirement | Minikube | Production (EKS) |
|-------------|----------|------------------|
| Kubernetes | 1.24+ | 1.27+ |
| Helm | 3.x | 3.x |
| kubectl | Configured | Configured |
| CPU | 4 cores | 3+ nodes (m5.xlarge) |
| Memory | 8 GB | 16 GB per node |
| Storage | - | EBS CSI Driver |
| **Expected Load** | | |
| Services | 1-10 | 50-500+ |
| Requests/day | ~10K | ~10M+ |
| Traces/day | ~100K spans | ~100M+ spans |
| Data Retention | 2 days | 7-30 days |
| Storage (approx) | ~5 GB | ~500 GB+ |

### SkyWalking Helm Chart

This deployment uses the official [Apache SkyWalking Helm Chart](https://github.com/apache/skywalking-helm).

#### Required Values

When deploying SkyWalking, these values must be set:

| Name | Description | Example |
|------|-------------|---------|
| `oap.image.tag` | OAP docker image tag | `10.3.0` |
| `oap.storageType` | Storage backend type | `banyandb`, `elasticsearch`, `postgresql` |
| `ui.image.tag` | UI docker image tag | `10.3.0` |

#### Check Available Helm Chart Versions

The SkyWalking Helm chart is distributed via OCI registry (Docker Hub).

```bash
# List all available chart versions from OCI registry
# Option 1: Using crane (recommended)
crane ls registry-1.docker.io/apache/skywalking-helm

# Option 2: Using skopeo
skopeo list-tags docker://registry-1.docker.io/apache/skywalking-helm

# Option 3: Using Docker Hub API
curl -s "https://hub.docker.com/v2/repositories/apache/skywalking-helm/tags?page_size=20" | \
  jq -r '.results[].name'

# Option 4: Visit Docker Hub directly
# https://hub.docker.com/r/apache/skywalking-helm/tags
```

```bash
# Check currently installed version
helm list -n skywalking

# View release history (shows all installed/upgraded versions)
helm history skywalking -n skywalking

# Show values used in current release
helm get values skywalking -n skywalking
```

#### Version Compatibility Matrix

| Helm Chart | OAP Server | BanyanDB | Satellite | UI |
|------------|------------|----------|-----------|-----|
| 4.8.0 | 10.3.0 | 0.9.0 | v1.2.0+ | 10.3.0 |
| 4.7.0 | 10.2.0 | 0.8.0 | v1.2.0 | 10.2.0 |
| 4.6.0 | 10.1.0 | 0.7.0 | v1.1.0 | 10.1.0 |

> **⚠️ BanyanDB 0.9.0 Bug Warning**: BanyanDB 0.9.0 has a critical bug in **cluster mode** that causes Data nodes to crash with `panic: not enough parts to merge`. This is fixed in the main branch ([PR #967](https://github.com/apache/skywalking-banyandb/pull/967)) but not yet released. **Workarounds**: Use standalone mode, or downgrade to 0.8.0. See [environment README](environments/scnx-global-dev-aps1-eks/README.md#banyandb-090-cluster-mode-bug-critical) for details.

> **Note**: `helm search repo` doesn't work for OCI registries. Use the methods above to check available versions.
>
> **Tip**: Always check the [SkyWalking Helm Chart releases](https://github.com/apache/skywalking-helm/releases) for the latest version and changelog before upgrading.

---

## Quick Start

### Minikube (Local Development)

```bash
# 1. Start Minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --nodes=3

# 2. Install SkyWalking
helm install skywalking oci://registry-1.docker.io/apache/skywalking-helm \
  --version 4.8.0 \
  -n skywalking --create-namespace \
  -f environments/minikube/values.yaml

# Note: You may see warnings about duplicate env vars (SATELLITE_GRPC_CLIENT_FINDER, SW_CLUSTER).
# These are harmless - the Helm chart templates have hardcoded defaults that merge with custom values.
# The last definition wins, so your custom values take effect.

# 3. Wait for pods to be ready
kubectl wait --for=condition=Ready pods --all -n skywalking --timeout=10m

# 4. Access UI
kubectl port-forward svc/skywalking-ui 8080:80 -n skywalking
# Open: http://localhost:8080
```

### Production (AWS EKS)

```bash
# 1. Apply base resources
kubectl apply -f base/storage-class.yaml
kubectl apply -f base/namespace.yaml

# 2. Install SkyWalking
./scripts/install.sh production --wait

# 3. Access UI via Ingress or port-forward
kubectl port-forward svc/skywalking-ui 8080:80 -n skywalking
```

---

## Installation

### Directory Structure

```
kubernetes-helm/
├── README.md                           # This file
├── environments/
│   ├── minikube/values.yaml           # Local development
│   ├── dev/values.yaml                # Development cluster
│   ├── staging/values.yaml            # Staging environment
│   └── production/values.yaml         # Production (HA)
├── base/
│   ├── namespace.yaml                 # Namespace + quotas
│   ├── storage-class.yaml             # EBS GP3 storage
│   ├── network-policy.yaml            # Network security
│   ├── service-account.yaml           # RBAC
│   ├── k8s-monitoring/                # Infrastructure monitoring
│   │   ├── kube-state-metrics.yaml
│   │   ├── node-exporter.yaml
│   │   └── otel-collector.yaml
│   ├── gateway-monitoring/            # API Gateway monitoring
│   │   ├── nginx-exporter.yaml
│   │   ├── apisix-config.yaml
│   │   └── kong-prometheus.yaml
│   ├── database-monitoring/           # Database monitoring
│   │   ├── mysql-exporter.yaml
│   │   ├── postgresql-exporter.yaml
│   │   ├── redis-exporter.yaml
│   │   └── otel-collector-database.yaml
│   ├── mq-monitoring/                 # Message queue monitoring
│   │   ├── kafka-exporter.yaml
│   │   ├── rabbitmq-config.yaml
│   │   ├── pulsar-config.yaml
│   │   ├── activemq-exporter.yaml
│   │   └── rocketmq-exporter.yaml
│   ├── flink-monitoring/              # Flink monitoring
│   │   ├── flink-config.yaml
│   │   └── otel-collector-flink.yaml
│   ├── service-mesh-monitoring/       # Istio/Envoy monitoring
│   │   ├── istio-als-config.yaml
│   │   ├── oap-mesh-config.yaml
│   │   └── otel-collector-mesh.yaml
│   ├── cilium-monitoring/             # Cilium monitoring
│   │   ├── cilium-config.yaml
│   │   └── otel-collector-cilium.yaml
│   └── aws-monitoring/                # AWS services (EKS only)
│       ├── yace-exporter.yaml
│       ├── iam-policy.json
│       └── otel-collector-aws.yaml
├── scripts/
│   ├── install.sh                     # Installation script
│   ├── upgrade.sh                     # Upgrade/rollback
│   ├── backup.sh                      # BanyanDB backup
│   ├── minikube-setup.sh              # Minikube helper
│   ├── monitoring.sh                  # Unified monitoring manager
│   ├── lib/common.sh                  # Shared functions
│   ├── general-service-monitoring.sh  # Demo apps
│   ├── kubernetes-monitoring.sh       # K8s monitoring
│   ├── service-mesh-monitoring.sh     # Istio/Envoy
│   ├── cilium-monitoring.sh           # Cilium eBPF
│   ├── infrastructure-monitoring.sh   # Linux hosts
│   ├── aws-cloud-monitoring.sh        # AWS CloudWatch
│   ├── browser-monitoring.sh          # Browser/RUM
│   ├── gateway-monitoring.sh          # API Gateways
│   ├── database-monitoring.sh         # Databases
│   ├── message-queue-monitoring.sh    # Message queues
│   ├── flink-monitoring.sh            # Apache Flink
│   └── self-observability-monitoring.sh # SkyWalking self
├── demos/                  # Test services for verification
│   ├── demo-mysql.yaml                # MySQL + exporter
│   ├── demo-postgresql.yaml           # PostgreSQL + exporter
│   ├── demo-redis.yaml                # Redis + exporter
│   ├── demo-nginx.yaml                # Nginx + exporter
│   ├── demo-kafka.yaml                # Kafka + exporter
│   └── otel-collector-demo.yaml       # Collector for test scraping
└── docs/
    ├── eks-setup.md                   # EKS setup guide
    └── satellite-usage.md             # Satellite configuration
```

### Environment Comparison

| Feature | Minikube | Dev | Staging | Production |
|---------|----------|-----|---------|------------|
| OAP Replicas | 1 | 1 | 2 | 3 |
| UI Replicas | 1 | 1 | 1 | 2 |
| Satellite | 1 | - | - | 2 |
| BanyanDB Mode | Standalone | Standalone | Standalone | Cluster (3 data) |
| Data Retention | 2 days | 1 day | 3 days | 7 days |
| Storage Size | - | 10 GB | 50 GB | 100 GB |
| Network Policies | No | No | No | Yes |
| PDB | No | No | Yes | Yes |

### Installation Methods

#### Method 1: Using Scripts (Recommended)

```bash
# Minikube
./scripts/minikube-setup.sh start

# Development
./scripts/install.sh dev

# Staging
./scripts/install.sh staging --wait

# Production
./scripts/install.sh production --wait

# Dry run (preview changes)
./scripts/install.sh production --dry-run
```

#### Method 2: Direct Helm Commands

```bash
# Set variables
export NAMESPACE=skywalking
export RELEASE_NAME=skywalking
export HELM_VERSION=4.8.0
export ENV=minikube  # or dev, staging, production

# Install (--create-namespace creates the namespace if it doesn't exist)
helm install ${RELEASE_NAME} oci://registry-1.docker.io/apache/skywalking-helm \
  --version ${HELM_VERSION} \
  -n ${NAMESPACE} --create-namespace \
  -f environments/${ENV}/values.yaml \
  --wait --timeout=10m
```

### Verify Installation

```bash
# Check pods
kubectl get pods -n skywalking

# Expected output (minikube):
# NAME                                    READY   STATUS
# skywalking-banyandb-0                   1/1     Running
# skywalking-oap-xxx                      1/1     Running
# skywalking-satellite-xxx                1/1     Running
# skywalking-ui-xxx                       1/1     Running

# Check services
kubectl get svc -n skywalking

# Check Helm release
helm list -n skywalking
```

---

## Upgrade

### Upgrade to New Version

```bash
# Using script
./scripts/upgrade.sh production --wait

# Or direct Helm command
helm upgrade skywalking oci://registry-1.docker.io/apache/skywalking-helm \
  --version 4.8.0 \
  -n skywalking \
  -f environments/production/values.yaml \
  --wait
```

### Upgrade with New Values

```bash
# Edit values file first
vim environments/minikube/values.yaml

# Then upgrade
helm upgrade skywalking oci://registry-1.docker.io/apache/skywalking-helm \
  --version 4.8.0 \
  -n skywalking \
  -f environments/minikube/values.yaml
```

### Rollback

```bash
# Using script
./scripts/upgrade.sh production --rollback

# Or direct Helm command
# List history
helm history skywalking -n skywalking

# Rollback to previous
helm rollback skywalking -n skywalking

# Rollback to specific revision
helm rollback skywalking 2 -n skywalking
```

### Check Upgrade Status

```bash
# View release history
helm history skywalking -n skywalking

# Check current values
helm get values skywalking -n skywalking
```

---

## Uninstall

### Uninstall SkyWalking

```bash
# Uninstall Helm release
helm uninstall skywalking -n skywalking

# Delete PVCs (WARNING: Data will be lost!)
kubectl delete pvc --all -n skywalking

# Delete namespace (optional)
kubectl delete namespace skywalking
```

### Forceful Uninstall

Use these methods when normal uninstall fails or resources are stuck.

#### Force Delete Helm Release

```bash
# If helm uninstall hangs or fails
helm uninstall skywalking -n skywalking --no-hooks --timeout 60s

# If release is stuck, delete secret directly
kubectl delete secret -n skywalking -l owner=helm,name=skywalking
```

#### Force Delete Stuck Pods

```bash
# Delete pods with grace period 0
kubectl delete pods --all -n skywalking --grace-period=0 --force

# Delete specific stuck pod
kubectl delete pod <pod-name> -n skywalking --grace-period=0 --force
```

#### Force Delete Stuck PVCs

```bash
# Remove finalizers from PVCs
kubectl patch pvc <pvc-name> -n skywalking -p '{"metadata":{"finalizers":null}}'

# Or remove finalizers from all PVCs
kubectl get pvc -n skywalking -o name | xargs -I {} kubectl patch {} -n skywalking -p '{"metadata":{"finalizers":null}}'

# Then delete
kubectl delete pvc --all -n skywalking --force --grace-period=0
```

#### Force Delete Stuck Namespace

```bash
# If namespace is stuck in Terminating state
# 1. Get namespace JSON
kubectl get namespace skywalking -o json > ns.json

# 2. Remove finalizers (edit ns.json, set "finalizers": [])
# Or use jq:
kubectl get namespace skywalking -o json | jq '.spec.finalizers = []' > ns.json

# 3. Replace via API
kubectl replace --raw "/api/v1/namespaces/skywalking/finalize" -f ns.json
```

#### Nuclear Option - Delete Everything

```bash
# Delete all resources in namespace
kubectl delete all --all -n skywalking --force --grace-period=0

# Delete all PVCs
kubectl delete pvc --all -n skywalking --force --grace-period=0

# Delete all secrets and configmaps
kubectl delete secrets,configmaps --all -n skywalking

# Delete namespace
kubectl delete namespace skywalking --force --grace-period=0

# If namespace still stuck, use finalize API
kubectl get namespace skywalking -o json | jq '.spec.finalizers = []' | \
  kubectl replace --raw "/api/v1/namespaces/skywalking/finalize" -f -
```

#### Clean Up CRDs (if any)

```bash
# List SkyWalking related CRDs
kubectl get crd | grep skywalking

# Delete CRDs (if using SWCK)
kubectl delete crd oapservers.operator.skywalking.apache.org
kubectl delete crd uis.operator.skywalking.apache.org
kubectl delete crd storages.operator.skywalking.apache.org
```

### Uninstall Infrastructure Monitoring

```bash
# Remove K8s monitoring components
kubectl delete -f base/k8s-monitoring/otel-collector.yaml -n skywalking
kubectl delete -f base/k8s-monitoring/node-exporter.yaml -n skywalking
kubectl delete -f base/k8s-monitoring/kube-state-metrics.yaml -n skywalking
```

### Uninstall Test Deployments

```bash
# Remove all test deployments
kubectl delete -f demos/ -n skywalking
```

### Clean Minikube

```bash
# Using script
./scripts/minikube-setup.sh clean

# Or manually
minikube delete
```

---

## Kubernetes Monitoring

Enable infrastructure monitoring to see Kubernetes metrics in SkyWalking UI.

### Enable K8s Monitoring

```bash
# Using unified script
./scripts/monitoring.sh kubernetes enable

# Or using individual script
./scripts/kubernetes-monitoring.sh enable

# Or manually
kubectl apply -f base/k8s-monitoring/kube-state-metrics.yaml -n skywalking
kubectl apply -f base/k8s-monitoring/node-exporter.yaml -n skywalking
kubectl apply -f base/k8s-monitoring/otel-collector.yaml -n skywalking
```

### Verify Monitoring

```bash
# Check monitoring pods
kubectl get pods -n skywalking -l app.kubernetes.io/component=monitoring

# Check OTel Collector logs
kubectl logs deployment/otel-collector -n skywalking
```

### View in UI

After enabling, metrics appear in SkyWalking UI under:
- **Kubernetes → Cluster** - Cluster state, pod counts
- **Kubernetes → Service** - Service-level metrics
- **Infrastructure → Linux** - Node-exporter host metrics

### Expected Behavior (Infrastructure-Only Monitoring)

When using only infrastructure monitoring (kube-state-metrics, node-exporter) without instrumented applications, the following panels will show "No Data":

| Panel | Reason | Solution |
|-------|--------|----------|
| Service HTTP Apdex | Requires application traces | Deploy instrumented app |
| HTTP Success Rate | Requires application traces | Deploy instrumented app |
| Service Avg HTTP Response Time | Requires application traces | Deploy instrumented app |
| Service HTTP Load | Requires application traces | Deploy instrumented app |

These HTTP metrics require one of:
1. **SkyWalking Agent** - Instrument apps with Java/Python/Go/Node.js agents
2. **Service Mesh** - Enable Istio/Envoy ALS for traffic metrics
3. **eBPF** - Use SkyWalking Rover for kernel-level observability

To test with instrumented applications, see [Sample Instrumented Apps](#sample-instrumented-apps).

---

## Gateway Monitoring

Monitor API Gateways (Nginx, APISIX, Kong) in SkyWalking.

### Supported Gateways

| Gateway | Exporter | SkyWalking Menu |
|---------|----------|-----------------|
| Nginx | nginx-prometheus-exporter | Gateway → NGINX |
| APISIX | Built-in Prometheus | Gateway → APISIX |
| Kong | Built-in Prometheus | Gateway → Kong |

### Enable Gateway Monitoring

```bash
# Show all gateway configurations
./scripts/enable-gateway-monitoring.sh all

# Deploy Nginx exporter
./scripts/enable-gateway-monitoring.sh nginx --nginx-uri http://my-nginx:80/nginx_status

# Show APISIX/Kong configuration
./scripts/enable-gateway-monitoring.sh apisix
./scripts/enable-gateway-monitoring.sh kong
```

### Update OAP Rules

Add gateway rules to your values.yaml:

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,nginx,apisix,kong,k8s-cluster,..."
```

### Configuration Files

| File | Description |
|------|-------------|
| `base/gateway-monitoring/nginx-exporter.yaml` | Nginx Prometheus Exporter |
| `base/gateway-monitoring/apisix-config.yaml` | APISIX Prometheus configuration |
| `base/gateway-monitoring/kong-prometheus.yaml` | Kong Prometheus configuration |
| `base/gateway-monitoring/otel-collector-gateway.yaml` | OTel Collector scrape configs |

---

## Database Monitoring

Monitor databases (MySQL, PostgreSQL, Redis, Elasticsearch, MongoDB, etc.) in SkyWalking.

### Supported Databases

| Database | Exporter | Port | SkyWalking Menu |
|----------|----------|------|-----------------|
| MySQL/MariaDB | mysqld_exporter | 9104 | Database → MySQL/MariaDB |
| PostgreSQL | postgres_exporter | 9187 | Database → PostgreSQL |
| Redis | redis_exporter | 9121 | Database → Redis |
| Elasticsearch | elasticsearch_exporter | 9114 | Database → Elasticsearch |
| MongoDB | mongodb_exporter | 9216 | Database → MongoDB |
| BookKeeper | Built-in Prometheus | 8000 | Database → BookKeeper |
| ClickHouse | clickhouse_exporter | 9363 | Database → ClickHouse |

### Enable Database Monitoring

```bash
# Show all database configurations
./scripts/enable-database-monitoring.sh all

# Show specific database setup
./scripts/enable-database-monitoring.sh mysql
./scripts/enable-database-monitoring.sh postgresql
./scripts/enable-database-monitoring.sh redis
```

### Deploy Database Exporters

```bash
# MySQL/MariaDB (update secret with your credentials first)
kubectl apply -f base/database-monitoring/mysql-exporter.yaml -n <db-namespace>

# PostgreSQL
kubectl apply -f base/database-monitoring/postgresql-exporter.yaml -n <db-namespace>

# Redis
kubectl apply -f base/database-monitoring/redis-exporter.yaml -n <db-namespace>

# Elasticsearch
kubectl apply -f base/database-monitoring/elasticsearch-exporter.yaml -n <db-namespace>

# MongoDB
kubectl apply -f base/database-monitoring/mongodb-exporter.yaml -n <db-namespace>
```

### Update OAP Rules

Add database rules to your values.yaml:

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,mysql,postgresql,redis,elasticsearch,mongodb,bookkeeper,clickhouse,..."
```

### Configuration Files

| File | Description |
|------|-------------|
| `base/database-monitoring/mysql-exporter.yaml` | MySQL/MariaDB Prometheus Exporter |
| `base/database-monitoring/postgresql-exporter.yaml` | PostgreSQL Prometheus Exporter |
| `base/database-monitoring/redis-exporter.yaml` | Redis Prometheus Exporter |
| `base/database-monitoring/elasticsearch-exporter.yaml` | Elasticsearch Prometheus Exporter |
| `base/database-monitoring/mongodb-exporter.yaml` | MongoDB Prometheus Exporter |
| `base/database-monitoring/bookkeeper-config.yaml` | BookKeeper Prometheus configuration |
| `base/database-monitoring/clickhouse-exporter.yaml` | ClickHouse Prometheus Exporter |
| `base/database-monitoring/otel-collector-database.yaml` | OTel Collector scrape configs |

---

## Message Queue Monitoring

Monitor message queues (Kafka, RabbitMQ, Pulsar, ActiveMQ, RocketMQ) in SkyWalking.

### Supported Message Queues

| Message Queue | Exporter | Port | SkyWalking Menu |
|---------------|----------|------|-----------------|
| Kafka | kafka_exporter | 9308 | MQ → Kafka |
| RabbitMQ | Built-in Prometheus | 15692 | MQ → RabbitMQ |
| Pulsar | Built-in Prometheus | 8080 | MQ → Pulsar |
| ActiveMQ | JMX Exporter | 8161 | MQ → ActiveMQ |
| RocketMQ | rocketmq_exporter | 5557 | MQ → RocketMQ |

### Deploy MQ Exporters

```bash
# Kafka
kubectl apply -f base/mq-monitoring/kafka-exporter.yaml -n <mq-namespace>

# RabbitMQ (enable prometheus plugin)
kubectl apply -f base/mq-monitoring/rabbitmq-config.yaml -n <mq-namespace>

# RocketMQ
kubectl apply -f base/mq-monitoring/rocketmq-exporter.yaml -n <mq-namespace>
```

### Update OAP Rules

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,kafka,rabbitmq,pulsar,activemq,rocketmq,..."
```

---

## Flink Monitoring

Monitor Apache Flink data processing engine in SkyWalking.

### Enable Flink Prometheus Metrics

Add to `flink-conf.yaml`:

```yaml
metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporterFactory
metrics.reporter.prom.port: 9249
```

### Update OAP Rules

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,flink,..."
```

### Configuration Files

| File | Description |
|------|-------------|
| `base/flink-monitoring/flink-config.yaml` | Flink Prometheus configuration |
| `base/flink-monitoring/otel-collector-flink.yaml` | OTel Collector scrape configs |

---

## Service Mesh Monitoring

Monitor Istio/Envoy service mesh in SkyWalking using Envoy ALS (Access Log Service).

### Supported Components

| Component | Method | SkyWalking Menu |
|-----------|--------|-----------------|
| Istio Control Plane | Prometheus | Service Mesh → Control Plane |
| Istio Data Plane | Envoy ALS | Service Mesh → Data Plane |
| Services | Envoy ALS | Service Mesh → Services |

### Enable Envoy ALS

Add to your OAP values:

```yaml
oap:
  env:
    SW_ENVOY_METRIC_ALS_HTTP_ANALYSIS: "k8s-mesh"
    SW_ENVOY_METRIC_ALS_TCP_ANALYSIS: "k8s-mesh"
```

### Configure Istio

```bash
# Apply EnvoyFilter for ALS
kubectl apply -f base/service-mesh-monitoring/istio-als-config.yaml
```

### Configuration Files

| File | Description |
|------|-------------|
| `base/service-mesh-monitoring/istio-als-config.yaml` | Istio EnvoyFilter for ALS |
| `base/service-mesh-monitoring/oap-mesh-config.yaml` | OAP mesh configuration |
| `base/service-mesh-monitoring/otel-collector-mesh.yaml` | OTel Collector scrape configs |

---

## Cilium Monitoring

Monitor Cilium eBPF-based networking in SkyWalking.

### Supported Components

| Component | Port | SkyWalking Menu |
|-----------|------|-----------------|
| Cilium Agent | 9962 | Cilium → Cilium Service |
| Cilium Operator | 9963 | Cilium → Cilium Service |
| Hubble | 9965 | Cilium → Cilium Service |

### Enable OAP Rule

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,cilium-service,..."
```

### Verify Cilium Metrics

```bash
# Check Cilium agent metrics
kubectl exec -n kube-system ds/cilium -- cilium metrics list
```

### Configuration Files

| File | Description |
|------|-------------|
| `base/cilium-monitoring/cilium-config.yaml` | Cilium Prometheus configuration |
| `base/cilium-monitoring/otel-collector-cilium.yaml` | OTel Collector scrape configs |

---

## AWS Monitoring (EKS Only)

Monitor AWS managed services (API Gateway, DynamoDB) in SkyWalking using YACE (Yet Another CloudWatch Exporter).

> **Note**: This requires EKS with IRSA (IAM Roles for Service Accounts) enabled.

### Supported AWS Services

| Service | Method | SkyWalking Menu |
|---------|--------|-----------------|
| API Gateway | CloudWatch via YACE | Gateway → AWS API Gateway |
| DynamoDB | CloudWatch via YACE | Database → DynamoDB |

### Prerequisites

1. EKS cluster with IRSA enabled
2. IAM role with CloudWatch read permissions

### Setup IAM Role

```bash
# Create IAM policy from provided file
aws iam create-policy \
  --policy-name YACECloudWatchPolicy \
  --policy-document file://base/aws-monitoring/iam-policy.json

# Create service account with IRSA
eksctl create iamserviceaccount \
  --name yace-cloudwatch-exporter \
  --namespace skywalking \
  --cluster <your-cluster> \
  --attach-policy-arn arn:aws:iam::<account-id>:policy/YACECloudWatchPolicy \
  --approve
```

### Deploy YACE

```bash
# Update region in yace-exporter.yaml first
kubectl apply -f base/aws-monitoring/yace-exporter.yaml -n skywalking
```

### Configuration Files

| File | Description |
|------|-------------|
| `base/aws-monitoring/yace-exporter.yaml` | YACE deployment + config |
| `base/aws-monitoring/iam-policy.json` | IAM policy for CloudWatch access |
| `base/aws-monitoring/otel-collector-aws.yaml` | OTel Collector scrape configs |

---

## Agent Configuration

### Connect via Satellite (Recommended for Production)

Satellite provides load balancing and buffering between agents and OAP.

```
Agent → Satellite → OAP
```

| Language | Configuration |
|----------|---------------|
| Java | `collector.backend_service=skywalking-satellite.skywalking:11800` |
| Python | `agent_collector_backend_services='skywalking-satellite.skywalking:11800'` |
| Go | `reporter.NewGRPCReporter("skywalking-satellite.skywalking:11800")` |
| Node.js | `collectorAddress: 'skywalking-satellite.skywalking:11800'` |

### Connect Directly to OAP (Dev/Testing)

```
Agent → OAP
```

| Language | Configuration |
|----------|---------------|
| Java | `collector.backend_service=skywalking-oap.skywalking:11800` |
| Python | `agent_collector_backend_services='skywalking-oap.skywalking:11800'` |

### Java Agent Example

```bash
java -javaagent:/path/to/skywalking-agent.jar \
  -Dskywalking.agent.service_name=my-service \
  -Dskywalking.collector.backend_service=skywalking-satellite.skywalking:11800 \
  -jar my-app.jar
```

### Kubernetes Deployment Example

```yaml
env:
  - name: SW_AGENT_NAME
    value: "my-service"
  - name: SW_AGENT_COLLECTOR_BACKEND_SERVICES
    value: "skywalking-satellite.skywalking:11800"
```

### OpenTelemetry Collector

```yaml
exporters:
  otlp:
    endpoint: skywalking-oap.skywalking:11800
    tls:
      insecure: true
```

---

## Service Endpoints

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Satellite | `skywalking-satellite.skywalking:11800` | Agent connection (via proxy) |
| OAP gRPC | `skywalking-oap.skywalking:11800` | Direct agent connection |
| OAP REST | `skywalking-oap.skywalking:12800` | GraphQL API |
| UI | `skywalking-ui.skywalking:80` | Web interface |
| BanyanDB | `skywalking-banyandb-grpc.skywalking:17912` | Storage (internal) |

---

## Testing Services (Minikube)

Step-by-step guide to deploy and test each monitoring feature one by one.

### Prerequisites

```bash
# Verify minikube is running
minikube status

# Check available resources
kubectl top nodes

# Deploy SkyWalking first (required for all tests)
helm install skywalking oci://registry-1.docker.io/apache/skywalking-helm \
  --version 4.8.0 -n skywalking --create-namespace -f environments/minikube/values.yaml

# Wait for SkyWalking to be ready
kubectl wait --for=condition=Ready pods --all -n skywalking --timeout=10m

# Deploy OTel Collector for test scraping
kubectl apply -f demos/otel-collector-demo.yaml -n skywalking

# Access UI
kubectl port-forward svc/skywalking-ui 8080:80 -n skywalking
```

### Test Services Overview

| Service | Memory | Deploy Time | SkyWalking Menu |
|---------|--------|-------------|-----------------|
| Nginx | ~100 MB | ~30s | Gateway → NGINX |
| MySQL | ~300 MB | ~60s | Database → MySQL |
| PostgreSQL | ~300 MB | ~60s | Database → PostgreSQL |
| Redis | ~100 MB | ~30s | Database → Redis |
| MongoDB | ~300 MB | ~60s | Database → MongoDB |
| Elasticsearch | ~600 MB | ~120s | Database → Elasticsearch |
| Kafka | ~600 MB | ~90s | MQ → Kafka |
| RabbitMQ | ~300 MB | ~60s | MQ → RabbitMQ |
| Pulsar | ~600 MB | ~120s | MQ → Pulsar |
| ActiveMQ | ~300 MB | ~60s | MQ → ActiveMQ |
| RocketMQ | ~600 MB | ~90s | MQ → RocketMQ |
| Flink | ~1 GB | ~120s | Flink |

---

### 1. Test Nginx (Gateway)

```bash
# Deploy
kubectl apply -f demos/demo-nginx.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-nginx -n skywalking --timeout=120s

# Verify metrics
kubectl exec -it deploy/demo-nginx -c nginx-exporter -n skywalking -- wget -qO- http://localhost:9113/metrics | head

# Check in UI: Gateway → NGINX

# Remove
kubectl delete -f demos/demo-nginx.yaml -n skywalking
```

---

### 2. Test MySQL (Database)

```bash
# Deploy
kubectl apply -f demos/demo-mysql.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-mysql -n skywalking --timeout=180s

# Connect to MySQL
kubectl exec -it deploy/demo-mysql -c mysql -n skywalking -- mysql -uroot -ptest123 -e "SHOW DATABASES;"

# Verify metrics
kubectl exec -it deploy/demo-mysql -c mysql-exporter -n skywalking -- wget -qO- http://localhost:9104/metrics | head

# Check in UI: Database → MySQL

# Remove
kubectl delete -f demos/demo-mysql.yaml -n skywalking
```

---

### 3. Test PostgreSQL (Database)

```bash
# Deploy
kubectl apply -f demos/demo-postgresql.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-postgresql -n skywalking --timeout=180s

# Connect to PostgreSQL
kubectl exec -it deploy/demo-postgresql -c postgres -n skywalking -- psql -U postgres -c "\l"

# Verify metrics
kubectl exec -it deploy/demo-postgresql -c postgres-exporter -n skywalking -- wget -qO- http://localhost:9187/metrics | head

# Check in UI: Database → PostgreSQL

# Remove
kubectl delete -f demos/demo-postgresql.yaml -n skywalking
```

---

### 4. Test Redis (Database)

```bash
# Deploy
kubectl apply -f demos/demo-redis.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-redis -n skywalking --timeout=120s

# Connect to Redis
kubectl exec -it deploy/demo-redis -c redis -n skywalking -- redis-cli PING

# Verify metrics
kubectl exec -it deploy/demo-redis -c redis-exporter -n skywalking -- wget -qO- http://localhost:9121/metrics | head

# Check in UI: Database → Redis

# Remove
kubectl delete -f demos/demo-redis.yaml -n skywalking
```

---

### 5. Test MongoDB (Database)

```bash
# Deploy
kubectl apply -f demos/demo-mongodb.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-mongodb -n skywalking --timeout=180s

# Connect to MongoDB
kubectl exec -it deploy/demo-mongodb -c mongodb -n skywalking -- mongosh --eval "db.adminCommand('ping')"

# Verify metrics
kubectl exec -it deploy/demo-mongodb -c mongodb-exporter -n skywalking -- wget -qO- http://localhost:9216/metrics | head

# Check in UI: Database → MongoDB

# Remove
kubectl delete -f demos/demo-mongodb.yaml -n skywalking
```

---

### 6. Test Elasticsearch (Database)

```bash
# Deploy
kubectl apply -f demos/demo-elasticsearch.yaml -n skywalking

# Wait for ready (takes longer)
kubectl wait --for=condition=Ready pod -l app=demo-elasticsearch -n skywalking --timeout=300s

# Check Elasticsearch health
kubectl exec -it deploy/demo-elasticsearch -c elasticsearch -n skywalking -- curl -s localhost:9200/_cluster/health | head

# Verify metrics
kubectl exec -it deploy/demo-elasticsearch -c es-exporter -n skywalking -- wget -qO- http://localhost:9114/metrics | head

# Check in UI: Database → Elasticsearch

# Remove
kubectl delete -f demos/demo-elasticsearch.yaml -n skywalking
```

---

### 7. Test Kafka (Message Queue)

```bash
# Deploy
kubectl apply -f demos/demo-kafka.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-kafka -n skywalking --timeout=180s

# Create test topic
kubectl exec -it deploy/demo-kafka -c kafka -n skywalking -- \
  /opt/kafka/bin/kafka-topics.sh --create --topic test --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1 2>/dev/null || true

# List topics
kubectl exec -it deploy/demo-kafka -c kafka -n skywalking -- \
  /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Verify metrics
kubectl exec -it deploy/demo-kafka -c kafka-exporter -n skywalking -- wget -qO- http://localhost:9308/metrics | head

# Check in UI: MQ → Kafka

# Remove
kubectl delete -f demos/demo-kafka.yaml -n skywalking
```

---

### 8. Test RabbitMQ (Message Queue)

```bash
# Deploy
kubectl apply -f demos/demo-rabbitmq.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-rabbitmq -n skywalking --timeout=180s

# Check RabbitMQ status
kubectl exec -it deploy/demo-rabbitmq -n skywalking -- rabbitmqctl status | head -20

# Access management UI (optional)
kubectl port-forward svc/demo-rabbitmq 15672:15672 -n skywalking
# Open http://localhost:15672 (guest/guest)

# Verify metrics
kubectl exec -it deploy/demo-rabbitmq -n skywalking -- wget -qO- http://localhost:15692/metrics | head

# Check in UI: MQ → RabbitMQ

# Remove
kubectl delete -f demos/demo-rabbitmq.yaml -n skywalking
```

---

### 9. Test Pulsar (Message Queue)

```bash
# Deploy
kubectl apply -f demos/demo-pulsar.yaml -n skywalking

# Wait for ready (takes longer)
kubectl wait --for=condition=Ready pod -l app=demo-pulsar -n skywalking --timeout=300s

# Check Pulsar health
kubectl exec -it deploy/demo-pulsar -n skywalking -- bin/pulsar-admin brokers healthcheck

# Verify metrics
kubectl exec -it deploy/demo-pulsar -n skywalking -- curl -s localhost:8080/metrics | head

# Check in UI: MQ → Pulsar

# Remove
kubectl delete -f demos/demo-pulsar.yaml -n skywalking
```

---

### 10. Test ActiveMQ (Message Queue)

```bash
# Deploy
kubectl apply -f demos/demo-activemq.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-activemq -n skywalking --timeout=180s

# Access web console (optional)
kubectl port-forward svc/demo-activemq 8161:8161 -n skywalking
# Open http://localhost:8161/admin (admin/admin)

# Verify metrics
kubectl exec -it deploy/demo-activemq -c jmx-exporter -n skywalking -- wget -qO- http://localhost:9404/metrics | head

# Check in UI: MQ → ActiveMQ

# Remove
kubectl delete -f demos/demo-activemq.yaml -n skywalking
```

---

### 11. Test RocketMQ (Message Queue)

```bash
# Deploy
kubectl apply -f demos/demo-rocketmq.yaml -n skywalking

# Wait for ready (multiple deployments)
kubectl wait --for=condition=Ready pod -l app=demo-rocketmq,component=nameserver -n skywalking --timeout=180s
kubectl wait --for=condition=Ready pod -l app=demo-rocketmq,component=broker -n skywalking --timeout=180s
kubectl wait --for=condition=Ready pod -l app=demo-rocketmq,component=exporter -n skywalking --timeout=180s

# Verify metrics
kubectl exec -it deploy/demo-rocketmq-exporter -n skywalking -- wget -qO- http://localhost:5557/metrics | head

# Check in UI: MQ → RocketMQ

# Remove
kubectl delete -f demos/demo-rocketmq.yaml -n skywalking
```

---

### 12. Test Flink (Data Processing)

```bash
# Deploy
kubectl apply -f demos/demo-flink.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-flink -n skywalking --timeout=180s

# Access Flink Dashboard (optional)
kubectl port-forward svc/demo-flink-jobmanager 8081:8081 -n skywalking
# Open http://localhost:8081

# Verify JobManager metrics
kubectl exec -it deploy/demo-flink-jobmanager -n skywalking -- wget -qO- http://localhost:9249/metrics | head

# Check in UI: Flink

# Remove
kubectl delete -f demos/demo-flink.yaml -n skywalking
```

---

### Deploy All Test Services

```bash
# Deploy all at once
kubectl apply -f demos/ -n skywalking

# Wait for all to be ready
kubectl wait --for=condition=Ready pods -l app -n skywalking --timeout=600s

# Check all pods
kubectl get pods -n skywalking | grep demo-
```

### Remove All Test Services

```bash
# Remove all test deployments
kubectl delete -f demos/ -n skywalking

# Verify removal
kubectl get pods -n skywalking | grep demo-
```

---

### Quick Reference: Verify Metrics Flow

```bash
# Check OTel Collector is scraping
kubectl logs deploy/otel-collector-demo -n skywalking | tail -20

# Check OAP is receiving metrics
kubectl logs deploy/skywalking-oap -n skywalking | grep -i "metrics\|received" | tail -10

# Restart OTel Collector if needed
kubectl rollout restart deploy/otel-collector-demo -n skywalking
```

---

## Sample Instrumented Apps

Deploy sample applications instrumented with SkyWalking agents to generate traces, metrics, and logs.

### Quick Start (Using Script)

```bash
# Using unified script
./scripts/monitoring.sh general-service enable

# Or using individual script
./scripts/general-service-monitoring.sh enable

# Check status
./scripts/monitoring.sh general-service status

# Remove demo apps
./scripts/monitoring.sh general-service disable
```

### Overview

| App | Language | Agent | Features |
|-----|----------|-------|----------|
| demo-app-java | Java | SkyWalking Java Agent 9.3.0 | Traces, Metrics, Logs |
| demo-app-python | Python | SkyWalking Python Agent 1.1.0 | Traces, Metrics, Logs, Cross-service calls |

### Deploy Java Sample App (Manual)

```bash
# Deploy (uses Spring Petclinic with SkyWalking Java Agent)
kubectl apply -f demos/demo-app-java.yaml -n skywalking

# Wait for ready (takes ~2 min for Spring Boot startup)
kubectl wait --for=condition=Ready pod -l app=demo-app-java -n skywalking --timeout=180s

# Test endpoints
kubectl port-forward svc/demo-app-java 8081:8080 -n skywalking &
curl http://localhost:8081/
curl http://localhost:8081/owners/find
curl http://localhost:8081/vets.html
curl http://localhost:8081/oups  # Triggers error

# View in UI: General Service → demo-app-java

# Remove
kubectl delete -f demos/demo-app-java.yaml -n skywalking
```

### Deploy Python Sample App (Manual)

```bash
# Deploy
kubectl apply -f demos/demo-app-python.yaml -n skywalking

# Wait for ready (takes longer due to pip install)
kubectl wait --for=condition=Ready pod -l app=demo-app-python -n skywalking --timeout=300s

# Test endpoints
kubectl port-forward svc/demo-app-python 8082:8080 -n skywalking &
curl http://localhost:8082/hello?name=Test
curl http://localhost:8082/slow
curl http://localhost:8082/chain  # Calls Java app (distributed trace)

# View in UI: General Service → demo-app-python

# Remove
kubectl delete -f demos/demo-app-python.yaml -n skywalking
```

### Deploy Both Apps (Distributed Tracing Demo)

```bash
# Deploy both apps
kubectl apply -f demos/demo-app-java.yaml -n skywalking
kubectl apply -f demos/demo-app-python.yaml -n skywalking

# Wait for ready
kubectl wait --for=condition=Ready pod -l app=demo-app-java -n skywalking --timeout=180s
kubectl wait --for=condition=Ready pod -l app=demo-app-python -n skywalking --timeout=300s

# Generate cross-service traffic
kubectl port-forward svc/demo-app-python 8082:8080 -n skywalking &
for i in $(seq 1 10); do curl -s http://localhost:8082/chain; sleep 1; done

# View distributed traces in UI:
#   Trace → Search → demo-app-python
#   Click on a trace to see the call chain: Python → Java
```

### Traffic Generation

Both apps include CronJobs that generate traffic every minute automatically. To generate manual traffic:

```bash
# Generate traffic to Java app
kubectl run traffic-java --rm -it --restart=Never --image=curlimages/curl -n skywalking -- \
  sh -c 'for i in $(seq 1 20); do curl -s http://demo-app-java:8080/hello; curl -s http://demo-app-java:8080/slow; sleep 1; done'

# Generate traffic to Python app
kubectl run traffic-python --rm -it --restart=Never --image=curlimages/curl -n skywalking -- \
  sh -c 'for i in $(seq 1 20); do curl -s http://demo-app-python:8080/hello; curl -s http://demo-app-python:8080/chain; sleep 1; done'
```

### What to Expect in UI

After deploying instrumented apps, you'll see:

| UI Section | Data |
|------------|------|
| General Service | demo-app-java, demo-app-python |
| Topology | Service dependency graph |
| Trace | Individual request traces |
| Service → Endpoint | /hello, /slow, /error, /chain |
| Service → Instance | Pod-level metrics |
| Kubernetes → Service | HTTP Apdex, Success Rate, Response Time, Load |

### Remove Sample Apps

```bash
kubectl delete -f demos/demo-app-java.yaml -n skywalking
kubectl delete -f demos/demo-app-python.yaml -n skywalking
```

---

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n skywalking
kubectl describe pod <pod-name> -n skywalking
kubectl logs <pod-name> -n skywalking
```

### Common Issues

#### Pods Stuck in Pending

```bash
# Check events
kubectl get events -n skywalking --sort-by='.lastTimestamp'

# Check node resources
kubectl describe nodes | grep -A 5 "Allocated resources"
```

#### OAP Not Starting

```bash
# Check OAP logs
kubectl logs deployment/skywalking-oap -n skywalking

# Check BanyanDB connectivity
kubectl exec -it deployment/skywalking-oap -n skywalking -- \
  nc -zv skywalking-banyandb-grpc 17912
```

#### OAP Stuck in "no-init" Mode (BanyanDB Fresh Deploy)

On fresh deployments with BanyanDB, OAP pods may be stuck in `0/1 Running` state with logs showing:
```
OAP is running in 'no-init' mode, waiting create or update... retry 3s later.
```

**Cause:** The Helm chart's init Job has hardcoded BanyanDB service names (`banyandb-grpc`) that don't match actual services (`skywalking-banyandb-grpc`) when using `fullnameOverride`.

**Fix:** Remove `-Dmode=no-init` to allow OAP pods to initialize schemas:

```bash
# Check if OAP pods are stuck
kubectl get pods -n skywalking -l component=oap
kubectl logs -n skywalking -l component=oap --tail=5

# Apply fix - remove no-init mode
kubectl set env deployment/skywalking-oap -n skywalking \
  JAVA_OPTS="-Xms2g -Xmx2g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+ParallelRefProcEnabled -XX:+DisableExplicitGC"

# Wait for pods to restart and become ready (2-3 minutes)
kubectl get pods -n skywalking -l component=oap -w
```

> **Note:** This is a one-time fix per fresh deployment. Once schemas are created, subsequent pod restarts work normally.

#### Satellite Connection Issues

```bash
# Check Satellite logs
kubectl logs deployment/skywalking-satellite -n skywalking

# Verify OAP is reachable from Satellite
kubectl exec -it deployment/skywalking-satellite -n skywalking -- \
  nc -zv skywalking-oap 11800
```

##### Satellite DeadlineExceeded Errors

If you see `DeadlineExceeded desc = context deadline exceeded` errors in Satellite logs, this indicates timeout issues when forwarding data to OAP. This can happen due to:

1. **OAP under heavy load** - BanyanDB writes taking too long
2. **Network latency** - Slow connection between Satellite and OAP
3. **Default timeout too short** - Satellite's default gRPC timeout may be insufficient

**Solutions:**

1. **Increase Satellite timeout** (in values.yaml):
   ```yaml
   satellite:
     env:
       SATELLITE_GRPC_CLIENT_TIMEOUT: "30s"  # Default is 10s
   ```

2. **Send directly to OAP** (recommended for single-OAP deployments):
   ```yaml
   # In your application deployment
   env:
     - name: SW_AGENT_COLLECTOR_BACKEND_SERVICES
       value: "skywalking-oap:11800"  # Instead of skywalking-satellite:11800
   ```

3. **Scale OAP** - Add more OAP replicas to handle load

**When to use Satellite vs Direct OAP:**

| Scenario | Recommendation |
|----------|----------------|
| Single OAP, low traffic | Direct to OAP |
| Multiple OAP replicas | Satellite (load balancing) |
| OAP restarts frequently | Satellite (buffering) |
| High agent count | Satellite (connection pooling) |

#### No Metrics in UI

```bash
# Check OTel Collector logs
kubectl logs deployment/otel-collector -n skywalking

# Verify kube-state-metrics is running
kubectl get pods -n skywalking -l app.kubernetes.io/name=kube-state-metrics
```

### Health Check Script

A comprehensive health check script is available to verify all SkyWalking components:

```bash
# Run health check (default namespace: skywalking)
./scripts/health-check.sh

# Run health check for custom namespace
./scripts/health-check.sh my-namespace
```

**Checks performed:**
- Pod status (etcd, BanyanDB Liaison/Data, OAP, Satellite, UI)
- Service endpoints availability
- OAP health endpoint (`/healthcheck`)
- OAP GraphQL API (version query)
- UI accessibility (HTTP 200)

**Sample output:**
```
╔═══════════════════════════════════════════════════════════════╗
║     SkyWalking Health Check - Namespace: skywalking
╚═══════════════════════════════════════════════════════════════╝

▶ POD STATUS
  ✓ etcd: 3/3 ready
  ✓ BanyanDB Liaison: 2/2 ready
  ✓ BanyanDB Data: 2/2 ready
  ✓ OAP Server: 3/3 ready
  ✓ Satellite: 2/2 ready
  ✓ UI: 2/2 ready

▶ SERVICES
  ✓ skywalking-oap: 3 endpoints
  ✓ skywalking-satellite: 2 endpoints
  ✓ skywalking-ui: 2 endpoints
  ✓ skywalking-banyandb-grpc: 2 endpoints

▶ OAP HEALTH (via kubectl exec)
  ✓ Health endpoint: OK
  ✓ GraphQL API: v10.3.0

▶ UI HEALTH
  ✓ UI accessible: HTTP 200

▶ SUMMARY
  Passed: 13
  Failed: 0

✓ All health checks passed!
```

### Useful Commands

```bash
# Watch pods
kubectl get pods -n skywalking -w

# Get all resources
kubectl get all -n skywalking

# Check PVCs
kubectl get pvc -n skywalking

# Port-forward UI
kubectl port-forward svc/skywalking-ui 8080:80 -n skywalking

# Port-forward OAP (for debugging)
kubectl port-forward svc/skywalking-oap 12800:12800 -n skywalking
```

---

## References

- [SkyWalking Documentation](https://skywalking.apache.org/docs/)
- [SkyWalking Helm Chart](https://github.com/apache/skywalking-helm)
- [BanyanDB Documentation](https://skywalking.apache.org/docs/skywalking-banyandb/latest/readme/)
- [SkyWalking Satellite](https://skywalking.apache.org/docs/skywalking-satellite/next/readme/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
