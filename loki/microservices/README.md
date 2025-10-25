# Loki Microservices

> 🧪 **DEVELOPMENT & LEARNING ENVIRONMENT** - Educational project optimized for Minikube with hardcoded credentials for easy setup.
> Perfect for blog tutorials and YouTube demonstrations.
> See [SECURITY.md](SECURITY.md) and [PRODUCTION.md](PRODUCTION.md) for production hardening.

Quick-start Loki distributed microservices stack for development, testing, and learning on Minikube with automated deployment and comprehensive tooling.

## 📚 Related Content

- 📝 **Blog**: [https://sagarnikam123.github.io/](https://sagarnikam123.github.io/)
- 🎥 **YouTube**: [https://www.youtube.com/sagarnikam123](https://www.youtube.com/sagarnikam123)

## Prerequisites

- Minikube or Kubernetes cluster
- kubectl configured
- 6 CPUs, 12GB RAM recommended

## 💻 **Development Environment Requirements**

**Storage Requirements**: ~10Gi total (optimized for local development)
- Ingester: 3Gi (data + WAL)
- MinIO: 3Gi
- Compactor: 2Gi
- Caches: 2Gi total

**System Requirements:**
- **Memory**: 12GB recommended for Minikube
- **CPU**: 6 cores recommended
- **Disk**: 15Gi free space (10Gi + overhead)

### 📊 **Cluster Sizing Guidelines**

**Current Setup (Development):**
- **Log Volume**: ~1GB/day (suitable for testing/demos)
- **Retention**: 7 days
- **Ingesters**: 1 replica (single point of failure)
- **Queriers**: 1 replica (limited query performance)



**Sizing by Log Volume (Based on Grafana Documentation):**
- **< 1GB/day**: 1 ingester, 1 querier, 10-20Gi storage (current setup)
- **1-10GB/day**: 2-3 ingesters, 2 queriers, 50-100Gi storage
- **10-100GB/day**: 3-5 ingesters, 3-5 queriers, 500Gi-1Ti storage
- **100GB-1TB/day**: 5-10 ingesters, 5-10 queriers, 5-10Ti storage
- **> 1TB/day**: 10+ ingesters, dedicated storage clusters

**Key Scaling Factors:**
- **Ingestion Rate**: ~100MB/s per ingester (from Grafana docs)
- **Storage Ratio**: ~3:1 compression (1GB logs = ~333MB storage)
- **Retention Impact**: Multiply storage by retention days
- **Query Performance**: 1 querier per 1-2 ingesters recommended

## Directory Structure

```
microservices/
├── 📁 k8s/                    # Kubernetes manifests
│   ├── 📁 loki/              # Complete Loki stack
│   │   ├── 📁 configs/       # All Loki configurations
│   │   ├── 📁 deployments/   # All Loki deployments
│   │   ├── 📁 services/      # All Loki services
│   │   └── 📁 storage/       # All Loki PVCs
│   ├── 📁 fluent-bit/        # Complete Fluent Bit setup
│   │   ├── configmap.yaml     # Fluent Bit configuration
│   │   ├── daemonset.yaml     # Fluent Bit DaemonSet
│   │   ├── service.yaml       # Fluent Bit service
│   │   └── 📁 rbac/          # Fluent Bit RBAC
│   ├── 📁 grafana/           # Complete Grafana setup
│   │   ├── configmaps.yaml    # Grafana datasources & dashboards
│   │   ├── deployment.yaml    # Grafana deployment
│   │   └── service.yaml       # Grafana service
│   ├── 📁 prometheus/        # Complete Prometheus setup
│   │   ├── config.yaml        # Prometheus configuration
│   │   ├── deployment.yaml    # Prometheus deployment
│   │   └── service.yaml       # Prometheus service
│   └── 📁 minio/             # Complete MinIO setup
│       ├── deployment.yaml    # MinIO deployment
│       ├── service.yaml       # MinIO service
│       ├── secret.yaml        # MinIO credentials
│       └── storage.yaml       # MinIO PVC
├── 📁 scripts/                # Essential automation scripts
│   ├── validate-loki-configs.sh # Loki configuration validation
│   ├── check-deployment-health.sh # Deployment health validation
│   ├── check-all-logs.sh     # Component log analysis
│   ├── test-api.sh           # API functionality testing
│   ├── check-versions.sh     # Version check & drift detection
│   ├── cleanup.sh            # Sequential resource cleanup
│   └── show-cleanup-commands.sh # Individual cleanup commands
├── 📁 archive/                # Archive documentation
│   └── README.md             # Archive information
├── 📄 run-on-minikube.sh      # 🚀 Main deployment script
├── 📄 README.md               # Operations guide
├── 📄 CONFIGURATION.md        # Configuration reference
├── 📄 SECURITY.md             # Security hardening guide
├── 📄 PRODUCTION.md           # Production deployment guide
└── 📄 LABELS.md               # Kubernetes labeling standards
```

## Quick Start

```bash
# 🚀 Deploy everything
./run-on-minikube.sh

# ✅ Check deployment health
./scripts/check-deployment-health.sh

# 🔍 Check component logs
./scripts/check-all-logs.sh

# 🧪 Test API functionality
./scripts/test-api.sh

# 🔄 Check current versions
./scripts/check-versions.sh

# 🧹 Cleanup when done
./scripts/cleanup.sh
```

## Architecture

**5 Service Stack:**
- **Loki**: 8 microservices (Distributor, Ingester, Querier, Query-Frontend, Compactor, Ruler, Index-Gateway, Query-Scheduler)
- **MinIO**: S3-compatible object storage
- **Fluent Bit**: Log collection agent
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards

**Key Features:**
- Memberlist coordination with POD_IP
- Environment variable expansion
- Direct query-frontend to querier connection
- **Kubernetes standard labels** for all components
- **Component-based architecture** with consistent labeling

## 🔄 **Dynamic Version Management**

**All component versions are centrally managed in `run-on-minikube.sh`:**


| Component | Current Version | GitHub Releases | Docker Hub |
| --------- | -------------- | -------------- | ---------- |
| **Loki** | 3.5.5 | [grafana/loki](https://github.com/grafana/loki/releases) | [grafana/loki](https://hub.docker.com/r/grafana/loki/tags) |
| **Grafana** | 12.1.0 | [grafana/grafana](https://github.com/grafana/grafana/releases) | [grafana/grafana](https://hub.docker.com/r/grafana/grafana/tags) |
| **Prometheus** | v3.5.0 | [prometheus/prometheus](https://github.com/prometheus/prometheus/releases) | [prom/prometheus](https://hub.docker.com/r/prom/prometheus/tags) |
| **MinIO** | RELEASE.2025-09-07T16-13-09Z | [minio/minio](https://github.com/minio/minio/releases) | [minio/minio](https://hub.docker.com/r/minio/minio/tags) |
| **Fluent Bit** | 4.1.0 | [fluent/fluent-bit](https://github.com/fluent/fluent-bit/releases) | [fluent/fluent-bit](https://hub.docker.com/r/fluent/fluent-bit/tags) |

**Update any version:**
```bash
# Check latest versions from GitHub releases or Docker Hub tags
./scripts/check-versions.sh --update

# Edit version in run-on-minikube.sh
export LOKI_VERSION="3.6.0"  # Change to desired version

# Redeploy with new version
./run-on-minikube.sh

# Verify current versions
./scripts/check-versions.sh
```

> 💡 **Tip**: Docker Hub often has the latest container images before GitHub releases. Check both sources for the most current versions.

## 🏷️ **Kubernetes Standard Labels**

**All components use consistent Kubernetes standard labels for operations and automation.**

See [LABELS.md](LABELS.md) and [CONFIGURATION.md](CONFIGURATION.md) for complete labeling standards and examples.

## Configuration

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration patterns, component-specific settings, and validation procedures.

## Deployment

**Automated Deployment (Recommended):**
```bash
./run-on-minikube.sh
```

**Manual Deployment Steps:**
1. Infrastructure: MinIO and namespace
2. Storage: Persistent volume claims
3. Services: All component services
4. Components: Deployments and StatefulSets
5. Configuration: ConfigMaps for all components

See [CONFIGURATION.md](CONFIGURATION.md) for detailed deployment steps.

## Troubleshooting

**Quick Health Checks:**
```bash
kubectl get pods -n loki                    # Pod status
kubectl get svc -n loki                     # Services
kubectl get pvc -n loki                     # Storage
```

**Automated Validation:**
```bash
./scripts/check-deployment-health.sh      # Check deployment health
./scripts/check-all-logs.sh                # Component log analysis
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed troubleshooting procedures and common issues.

## Monitoring

### Component Log Analysis

**Automated Log Checking:**
```bash
# Check all component logs at once
./scripts/check-all-logs.sh
```

**Manual Log Checking (with standard labels):**
```bash
# Check specific Loki components
kubectl logs -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=distributor --tail=10
kubectl logs -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=ingester --tail=10

# Check all logging stack components
kubectl logs -n loki -l app.kubernetes.io/part-of=logging-stack --tail=5

# Check by component type
kubectl logs -n loki -l app.kubernetes.io/component=storage --tail=10  # MinIO
kubectl logs -n loki -l app.kubernetes.io/component=log-collector --tail=10  # Fluent Bit0  # Fluent Bit
```

### Performance Metrics
```bash
# Check resource usage
kubectl top pods -n loki

# Check storage usage
kubectl exec -n loki loki-ingester-0 -- df -h /loki

# Check MinIO usage
kubectl port-forward -n loki svc/minio 9000:9000
# Access http://localhost:9000 (minioadmin/minioadmin)
```

## API Testing

**Automated API Testing (Recommended):**
```bash
# Comprehensive API test suite
./scripts/test-api.sh
```

See [CONFIGURATION.md](CONFIGURATION.md) for manual API testing procedures and examples.

## Loki Web UI Access

**Loki Web UI is available via Query Frontend for log exploration and querying:**

```bash
# Access Loki Web UI via Query Frontend
kubectl port-forward -n loki svc/query-frontend 3100:3100
# Open: http://localhost:3100

# Alternative: Direct API access
kubectl port-forward -n loki svc/query-frontend 3100:3100
# API: http://localhost:3100/loki/api/v1/
```

**UI Features:**
- **Log Explorer**: Query and filter logs with LogQL
- **Label Browser**: Explore available labels and values
- **Query Builder**: Visual query construction
- **Live Tail**: Real-time log streaming
- **Query History**: Previous queries and results

**Access Methods:**
- **NodePort**: Direct access via Minikube IP:30100
- **Port Forward**: Local access via localhost:3100
- **Service**: Minikube service command for automatic browser opening


## Production Considerations

> ⚠️ **Security Warning**: This deployment uses development settings. Review [SECURITY.md](SECURITY.md) and [PRODUCTION.md](PRODUCTION.md) before production use.

### Scaling
```bash
# Scale distributors
kubectl scale deployment loki-distributor --replicas=3 -n loki

# Scale queriers
kubectl scale deployment loki-querier --replicas=3 -n loki

# Scale ingesters (StatefulSet)
kubectl scale statefulset loki-ingester --replicas=3 -n loki
```

**Production Scaling Recommendations:**
```bash
# Scale for higher availability
kubectl scale deployment loki-distributor --replicas=2 -n loki
kubectl scale deployment loki-querier --replicas=2 -n loki
kubectl scale statefulset loki-ingester --replicas=3 -n loki

# Increase storage for production workloads
# ingester-data: 50Gi+ (based on log volume)
# minio-pvc: 100Gi+ (for chunk storage)
```

See [PRODUCTION.md](PRODUCTION.md) for detailed scaling guidelines and resource sizing recommendations.

### Resource Optimization
- **CPU**: Adjust based on log volume
- **Memory**: Scale with retention period
- **Storage**: Monitor WAL and chunk usage
- **Network**: Ensure sufficient bandwidth for memberlist

### Security
- Enable authentication (`auth_enabled: true`)
- Configure TLS for inter-service communication
- Use proper RBAC for Kubernetes access
- Secure MinIO with proper credentials

See [SECURITY.md](SECURITY.md) for complete security hardening checklist and procedures.

## Scripts

See **Quick Start** section above for all available scripts and usage.

## Cleanup

```bash
# Recommended: Sequential cleanup
./scripts/cleanup.sh

# Quick: Delete entire namespace
kubectl delete namespace loki

# Individual: View selective deletion commands
./scripts/show-cleanup-commands.sh
```



## Success Indicators

**Healthy Deployment:**
- **All pods running** (Fluent Bit: 1 per node + 8 Loki components + MinIO + Prometheus + Grafana = 11+ pods total)
- **Standard labels applied**: `kubectl get pods -l app.kubernetes.io/part-of=logging-stack`
- **Loki Web UI accessible**: Query Frontend at http://localhost:3100
- **Labels API working**: `curl localhost:3100/loki/api/v1/labels`
- **Distributor**: `memberlist cluster succeeded`
- **Ingester**: `checkpoint done`, `uploading tables`, `flushing stream`
- **Fluent Bit**: `flush chunk succeeded`
- **Storage optimized**: 10Gi total (78% reduction from original)

**Component Health Check:**
```bash
# Check all components with standard labels
kubectl get all -n loki -l app.kubernetes.io/part-of=logging-stack

# Verify label consistency
kubectl get deployments -n loki -o custom-columns="NAME:.metadata.name,LABELS:.metadata.labels"
```

This provides a fully functional Loki distributed microservices stack with memberlist coordination and MinIO storage.
