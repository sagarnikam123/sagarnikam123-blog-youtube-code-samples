# Loki 3.5.x Development Minikube Microservices

> 🧪 **DEVELOPMENT & LEARNING ENVIRONMENT** - Educational project optimized for Minikube with hardcoded credentials for easy setup. Perfect for blog tutorials and YouTube demonstrations. See [SECURITY.md](SECURITY.md) and [PRODUCTION.md](PRODUCTION.md) for production hardening.

Quick-start Loki 3.5.x distributed microservices stack for development, testing, and learning on Minikube with automated deployment and comprehensive tooling.

## 📚 Related Content

- 📝 **Blog**: [https://sagarnikam123.github.io/](https://sagarnikam123.github.io/)
- 🎥 **YouTube**: [https://www.youtube.com/sagarnikam123](https://www.youtube.com/sagarnikam123)

## Prerequisites

- Minikube or Kubernetes cluster
- kubectl configured
- 6 CPUs, 12GB RAM recommended

## Directory Structure

```
loki-dev-minikube-microservices/
├── 📁 config/                 # Component configurations
│   ├── distributor.yaml      # Log ingestion & distribution
│   ├── ingester.yaml         # Storage with WAL & MinIO
│   ├── querier.yaml          # Query execution
│   ├── query-frontend.yaml   # Query optimization & caching
│   ├── query-scheduler.yaml  # Query scheduling (bypassed)
│   ├── compactor.yaml        # Log compaction & retention
│   ├── ruler.yaml            # Alerting rules
│   └── index-gateway.yaml    # TSDB index management
├── 📁 k8s/                    # Kubernetes manifests
│   ├── 📁 deployments/       # Component deployments & StatefulSets
│   ├── 📁 infrastructure/    # MinIO & secrets
│   ├── 📁 storage/           # Persistent volume claims
│   ├── 📁 fluent-bit/        # Log collection DaemonSet
│   └── services.yaml         # All service definitions
├── 📁 scripts/                # Essential automation scripts
│   ├── cleanup.sh            # Sequential resource cleanup
│   ├── cleanup-single-resource.sh # Individual cleanup commands
│   ├── validate-deployment.sh # Health validation
│   ├── validate-configs.sh   # Configuration validation
│   ├── check-all-logs.sh     # Component log analysis
│   └── test-api.sh           # API functionality testing
├── 📁 archive/                # Archive documentation
│   └── README.md             # Archive information
├── 📄 run-on-minikube.sh      # 🚀 Main deployment script
├── 📄 README.md               # Operations guide
└── 📄 CONFIGURATION.md        # Configuration reference
```

## Quick Start

```bash
# 🚀 Deploy everything
./run-on-minikube.sh

# ✅ Validate deployment
./scripts/validate-deployment.sh

# 🧪 Test API functionality
./scripts/test-api.sh

# 🔍 Check component logs
./scripts/check-all-logs.sh

# 🧹 Cleanup when done
./scripts/cleanup.sh
```

## Architecture

**9 Loki Components + MinIO + Fluent Bit:**
- Distributor, Ingester, Querier, Query-Frontend, Compactor, Ruler, Index-Gateway, Query-Scheduler
- MinIO for S3-compatible storage
- Fluent Bit for log collection

**Key Features:**
- Memberlist coordination with POD_IP
- Environment variable expansion
- Direct query-frontend to querier connection

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

### Common Issues

**1. Memberlist Connection Issues**
```bash
# Check memberlist logs
kubectl logs -n loki [pod-name] | grep memberlist

# Verify DNS resolution
kubectl run test-dns --image=busybox:1.35 --rm -it --restart=Never -n loki -- nslookup ingester.loki.svc.cluster.local
```

**2. MinIO Connection Issues**
```bash
# Test MinIO DNS
kubectl run test-dns --image=busybox:1.35 --rm -it --restart=Never -n loki -- nslookup minio.loki.svc.cluster.local

# Check MinIO service
kubectl get svc -n loki minio
```

**3. Ring Health Issues**
```bash
# Check ring status
kubectl logs -n loki [distributor-pod] | grep ring
kubectl logs -n loki [ingester-pod] | grep ring
```

**4. Configuration Issues**

See [CONFIGURATION.md](CONFIGURATION.md) for troubleshooting procedures.

### Health Checks
```bash
kubectl get pods -n loki                    # Pod status
kubectl get svc -n loki                     # Services
kubectl get pvc -n loki                     # Storage
kubectl logs -n loki loki-ingester-0 | grep flush  # Storage ops
```

## Monitoring

### Component Log Analysis

**Automated Log Checking:**
```bash
# Check all component logs at once
./scripts/check-all-logs.sh
```

**Manual Log Checking:**
```bash
kubectl logs -n loki -l app=loki-distributor --tail=10
kubectl logs -n loki loki-ingester-0 --tail=10
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

**Manual API Testing:**
```bash
# Port forward and test readiness
kubectl port-forward -n loki svc/query-frontend 3108:3100 &
curl -s "http://localhost:3108/ready"

# Test labels API
curl -s "http://localhost:3108/loki/api/v1/labels" | jq .

# Query logs
START_TIME=$(date -u -v-1H +%s)000000000
END_TIME=$(date -u +%s)000000000
curl -s "http://localhost:3108/loki/api/v1/query_range?query={job=\"fluentbit\"}&start=$START_TIME&end=$END_TIME&limit=5" | jq .
```


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

## Scripts

See **Quick Start** section above for all available scripts and usage.

## Cleanup

```bash
# Recommended: Sequential cleanup
./scripts/cleanup.sh

# Quick: Delete entire namespace
kubectl delete namespace loki

# Individual: View selective deletion commands
./scripts/cleanup-single-resource.sh
```



## Success Indicators

**Healthy Deployment:**
- All 12 pods running (3 Fluent Bit + 9 Loki components)
- Labels API returns JSON array: `curl localhost:3108/loki/api/v1/labels`
- Distributor: `memberlist cluster succeeded`
- Ingester: `checkpoint done`, `uploading tables`
- Fluent Bit: `flush chunk succeeded`

This provides a fully functional Loki 3.5.x distributed microservices stack with memberlist coordination and MinIO storage.