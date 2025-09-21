# Loki 3.5.x Configuration Guide

> ⚠️ **Development Configuration** - These configs use insecure settings for ease of setup. See [SECURITY.md](SECURITY.md) for production hardening.

## Configuration Files Overview

All configuration files are located in the `config/` directory:

```
config/
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
docker run --rm -v "$(pwd)/config:/config" grafana/loki:3.5.5 \
  -config.file=/config/[component].yaml -verify-config -target=[component]

# Examples:
# distributor, ingester, querier, query-frontend, 
# query-scheduler, compactor, ruler, index-gateway
```

**Automated Validation:**
```bash
# Use the validation script
./scripts/validate-configs.sh
```

## Configuration Management

**Update Component Configuration:**
```bash
# Update ConfigMap and restart component
kubectl create configmap [component]-config --from-file=config/[component].yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl delete pod -n loki -l app=loki-[component]
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
# Validate config expansion
kubectl logs -n loki [pod-name] | grep "POD_IP\|HOSTNAME"

# Check environment variables
kubectl exec -n loki [pod-name] -- env | grep -E "POD_IP|HOSTNAME"
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

1. **POD_IP Usage**: Critical for memberlist in Kubernetes
2. **Config Expansion**: Required for environment variable substitution (`-config.expand-env=true`)
3. **Service DNS**: Proper naming for service discovery
4. **Ring Coordination**: Memberlist configuration across all components
5. **Storage Integration**: MinIO DNS resolution and connectivity
6. **Direct Query Path**: Frontend-Querier connection bypassing scheduler
7. **Health Monitoring**: Regular checks for ring and storage health
8. **Log Collection**: Fluent Bit DaemonSet for comprehensive log gathering