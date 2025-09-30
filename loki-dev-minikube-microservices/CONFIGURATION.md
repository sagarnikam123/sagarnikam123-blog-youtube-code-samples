# Loki Configuration Guide

> ⚠️ **Development Configuration** - These configs use insecure settings for ease of setup. See [SECURITY.md](SECURITY.md) for production hardening.

## 🏷️ **Kubernetes Standard Labels**

**All components use consistent Kubernetes standard labels for operations and automation.**

See [LABELS.md](LABELS.md) for complete labeling standards, component mappings, and operational examples.

## 🔄 **Version Management**

**All component versions are centrally managed.** See [README.md](README.md) for version management details and procedures.

## Configuration Files Overview

All configuration files are located in the `k8s/loki/configs/` directory:

```
k8s/loki/configs/
├── distributor.yaml      # Log ingestion and distribution
├── ingester.yaml         # Log storage with WAL and MinIO
├── querier.yaml          # Query execution with direct frontend connection
├── query-frontend.yaml   # Query optimization and caching
├── query-scheduler.yaml  # Query scheduling (currently bypassed)
├── compactor.yaml        # Log compaction and retention
├── ruler.yaml            # Alerting rules evaluation
└── index-gateway.yaml    # TSDB index management
```

## Critical Configuration Patterns

### 1. Environment Variable Expansion

**All configurations support environment variable substitution:**
```yaml
common:
  instance_addr: "${POD_IP}"
  path_prefix: "/loki"
  storage:
    s3:
      access_key_id: "${MINIO_ACCESS_KEY}"
      secret_access_key: "${MINIO_SECRET_KEY}"
```

**Required deployment flag:**
```yaml
args:
- -config.expand-env=true
```

### 2. Memberlist Configuration

**Applied to ring-based services (distributor, ingester, querier):**
```yaml
memberlist:
  bind_addr: ["0.0.0.0"]
  bind_port: 7946
  advertise_addr: "${POD_IP}"
  advertise_port: 7946
  # join_members only needed for some components
  join_members:
    - "ingester.loki.svc.cluster.local:7946"
  abort_if_cluster_join_fails: false  # true for ingester
```

### 3. MinIO Storage Integration

**Applied to storage-accessing components (ingester, querier, query-frontend, compactor):**
```yaml
common:
  storage:
    s3:
      endpoint: "minio.loki.svc.cluster.local:9000"
      bucketnames: "loki-chunks"
      access_key_id: "${MINIO_ACCESS_KEY}"
      secret_access_key: "${MINIO_SECRET_KEY}"
      insecure: true
      s3forcepathstyle: true

storage_config:
  aws:
    endpoint: "minio.loki.svc.cluster.local:9000"
    bucketnames: "loki-chunks"
    access_key_id: "${MINIO_ACCESS_KEY}"
    secret_access_key: "${MINIO_SECRET_KEY}"
    s3forcepathstyle: true
    insecure: true
```

## Component-Specific Configurations

### Distributor (distributor.yaml)
- **Purpose**: Log ingestion and distribution to ingesters
- **Key Features**: Memberlist ring coordination, rate limiting
- **Ring**: Uses memberlist for ingester discovery
- **Storage**: No direct storage config (routes to ingesters)

### Ingester (ingester.yaml)
- **Purpose**: Log storage with Write-Ahead Log (WAL)
- **Key Features**: MinIO persistence, WAL checkpointing, TSDB indexing
- **Storage**: Persistent volumes for data and WAL

### Querier (querier.yaml)
- **Purpose**: Query execution against ingesters and storage
- **Key Features**: Direct frontend connection, compactor integration
- **Configuration**: `frontend_worker.frontend_address` for direct connection

### Query Frontend (query-frontend.yaml)
- **Purpose**: Query optimization, caching, and load balancing
- **Key Features**: Direct querier connection (bypassing scheduler)
- **Configuration**: Uses `${HOSTNAME}` instead of `${POD_IP}`, inmemory ring
- **Connection**: `frontend_worker.frontend_address` for self-connection

### Query Scheduler (query-scheduler.yaml)
- **Purpose**: Query scheduling and distribution (currently bypassed)
- **Status**: Deployed but not used in query path
- **Reason**: Ring coordination issues resolved by direct frontend-querier connection

### Compactor (compactor.yaml)
- **Purpose**: Log compaction, retention, and cleanup
- **Key Features**: MinIO integration, memberlist coordination
- **Ring**: Uses memberlist for coordination
- **Retention**: 7-day log retention policy

### Ruler (ruler.yaml)
- **Purpose**: Alerting rules evaluation
- **Key Features**: Memberlist coordination, rule evaluation
- **Ring**: Uses memberlist for coordination

### Index Gateway (index-gateway.yaml)
- **Purpose**: TSDB index management and caching
- **Key Features**: Index caching, query optimization
- **Ring**: Uses inmemory ring (no memberlist)

## Schema Configuration

**All components use consistent schema:**
```yaml
schema_config:
  configs:
    - from: 2024-04-01
      store: tsdb
      object_store: s3
      schema: v13
      index:
        prefix: index_
        period: 24h
```

## Environment Variables

**Required in all deployments:**
```yaml
env:
- name: POD_IP
  valueFrom:
    fieldRef:
      fieldPath: status.podIP
- name: HOSTNAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: MINIO_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: minio-creds
      key: accesskey
- name: MINIO_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: minio-creds
      key: secretkey
```

**Component Variations:**
- **Most components**: Use `${POD_IP}` for `instance_addr`
- **Query-frontend**: Uses `${HOSTNAME}` for `instance_addr`
- **Distributor**: No MinIO storage config (routes to ingesters)

## Configuration Validation

**Validate configurations before deployment:**

**Individual Component Validation:**
```bash
# Validate specific component (replace [component] and [target])
docker run --rm -v "$(pwd)/config:/config" grafana/loki:${LOKI_VERSION} \
  -config.file=/config/[component].yaml -verify-config -target=[component]

# Examples:
# distributor, ingester, querier, query-frontend,
# query-scheduler, compactor, ruler, index-gateway
```

**Automated Validation:**
```bash
# Use the validation script
./scripts/validate-loki-configs.sh
```

## 📊 **Cluster Sizing & Storage Optimization**

### **Development vs Production Sizing**

**Current Development Setup:**
- **Target**: < 1GB logs/day, 7-day retention
- **Ingesters**: 1 replica (development only)
- **Storage**: 10Gi total (78% reduction from production baseline)
- **Suitable for**: Testing, demos, learning

**Production Scaling Guidelines:**

| Log Volume/Day | Ingesters | Queriers | Distributors | Storage (Total) |
|----------------|-----------|----------|--------------|----------------|
| < 1GB | 1 | 1 | 1 | 10-20Gi |
| 1-10GB | 2-3 | 2 | 2 | 50-100Gi |
| 10-100GB | 3-5 | 3-5 | 2-3 | 500Gi-1Ti |
| > 100GB | 5+ | 5+ | 3+ | 1Ti+ |

**Key Scaling Factors:**
- **Ingester replicas**: Based on write throughput and availability needs
- **Querier replicas**: Based on query load and response time requirements
- **Storage per ingester**: ~10-50GB per 1GB/day log volume
- **Retention period**: Multiply storage by retention days

## 💻 **Development Storage Optimization**

**Optimized storage allocation for development:**
```yaml
# Total: 10Gi (78% reduction from original 45Gi)
PersistentVolumeClaims:
  ingester-data: 2Gi          # Reduced from 10Gi
  ingester-wal: 1Gi           # Reduced from 5Gi
  compactor-data: 2Gi         # Reduced from 10Gi
  querier-cache: 1Gi          # Reduced from 5Gi
  index-cache: 1Gi            # Reduced from 5Gi
  minio-pvc: 3Gi              # Reduced from 10Gi
```

**Benefits:**
- **MacBook friendly**: Reasonable for development environments
- **Faster deployment**: Less storage provisioning time
- **Cost-effective**: Reduced cloud storage costs
- **Still functional**: Adequate for testing and demos

### **Performance Considerations**

**Single Replica Limitations (Current Setup):**
- **No High Availability**: Single point of failure
- **Limited Throughput**: ~100MB/s ingestion rate (1 ingester)
- **Query Performance**: Single querier bottleneck (~1000 queries/min)
- **Memory Usage**: ~2-4GB per component
- **Suitable for**: Development, testing, demos only

**Production Throughput Guidelines:**
- **Ingester**: ~100MB/s per replica (sustained, from Grafana docs)
- **Distributor**: ~500MB/s per replica (burst)
- **Querier**: ~1000-5000 queries/min per replica
- **Storage**: 3:1 compression ratio typical

**Resource Requirements per Component:**

| Component | CPU (cores) | Memory (GB) | Storage | Replicas |
|-----------|-------------|-------------|---------|----------|
| **Distributor** | 0.5-2 | 1-4 | - | 2-3 |
| **Ingester** | 1-4 | 4-16 | 50-500Gi | 3-10 |
| **Querier** | 1-2 | 2-8 | 10-50Gi | 2-5 |
| **Query-Frontend** | 0.5-1 | 1-2 | - | 2 |
| **Compactor** | 1-2 | 2-8 | 20-100Gi | 1 |

**Scaling Triggers:**
- **Ingestion lag**: Scale distributors and ingesters
- **Query timeouts**: Scale queriers and query-frontends
- **Storage pressure**: Increase PVC sizes or add retention policies
- **Memory pressure**: Increase resource limits or scale horizontally
- **CPU throttling**: Increase CPU limits or add replicas

**Storage Monitoring:**
```bash
# Check storage usage
kubectl get pvc -n loki -o custom-columns="NAME:.metadata.name,SIZE:.spec.resources.requests.storage,STATUS:.status.phase"

# Monitor actual usage
kubectl exec -n loki loki-ingester-0 -- df -h /loki
```

## Configuration Management

**Update Component Configuration:**
```bash
# Update ConfigMap and restart component (using standard labels)
kubectl create configmap [component]-config --from-file=k8s/loki/configs/[component].yaml -n loki --dry-run=client -o yaml | kubectl apply -f -

# Restart using standard labels
kubectl delete pod -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=[component]

# Examples:
kubectl delete pod -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=distributor
kubectl delete pod -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=ingester
```

**Bulk Configuration Updates:**
```bash
# Update all configurations at once
./run-on-minikube.sh  # Idempotent - safe to re-run
```
## Query Pipeline Architecture

**Current Setup:**
- **Active**: Query-Frontend ↔ Querier (Direct Connection)
- **Bypassed**: Query-Scheduler (due to ring coordination issues)
- **Configuration**: `frontend_worker.frontend_address` in querier config

## Configuration Troubleshooting

**Environment Variable Issues:**
```bash
# Validate config expansion (using standard labels)
kubectl logs -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=distributor | grep "POD_IP\|HOSTNAME"

# Check environment variables for specific components
kubectl exec -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=ingester -- env | grep -E "POD_IP|HOSTNAME"

# Check all logging stack components
kubectl get pods -n loki -l app.kubernetes.io/part-of=logging-stack -o wide
```

**Label-Based Troubleshooting:**
```bash
# Check component health by labels
kubectl describe pods -n loki -l app.kubernetes.io/component=storage  # MinIO
kubectl describe pods -n loki -l app.kubernetes.io/component=log-collector  # Fluent Bit

# Check logs by component type
kubectl logs -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=querier --tail=20
kubectl logs -n loki -l app.kubernetes.io/component=monitoring --tail=20  # Prometheus

# Scale components using labels
kubectl scale deployment -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=distributor --replicas=2
```

**Common Problems:**
1. **Environment Variable Expansion Not Working**
   - Ensure `-config.expand-env=true` flag is set
   - Check environment variables are properly defined

2. **MinIO Connection Issues**
   - Verify service name: `minio.loki.svc.cluster.local`
   - Check credentials in secret

3. **Memberlist Coordination Problems**
   - Ensure POD_IP is correctly set
   - Verify service ports include 7946

4. **Query Pipeline Issues**
   - Check frontend_worker configuration
   - Verify direct frontend-querier connection

## Key Success Factors

1. **Kubernetes Standard Labels**: Consistent labeling across all components for operations
2. **POD_IP Usage**: Critical for memberlist in Kubernetes
3. **Config Expansion**: Required for environment variable substitution (`-config.expand-env=true`)
4. **Service DNS**: Proper naming for service discovery
5. **Ring Coordination**: Memberlist configuration across all components
6. **Storage Integration**: MinIO DNS resolution and connectivity
7. **Storage Optimization**: MacBook Pro friendly 10Gi total allocation
8. **Direct Query Path**: Frontend-Querier connection bypassing scheduler
9. **Health Monitoring**: Regular checks for ring and storage health
10. **Log Collection**: Fluent Bit DaemonSet for comprehensive log gathering
11. **Label-Based Operations**: Use standard labels for troubleshooting and scaling
