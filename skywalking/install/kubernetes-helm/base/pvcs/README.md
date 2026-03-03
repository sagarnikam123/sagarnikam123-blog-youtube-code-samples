# Persistent Volume Claims (PVCs) for SkyWalking Cluster

This directory contains PVC templates for SkyWalking full cluster mode deployment with BanyanDB storage and etcd coordination.

## Overview

The SkyWalking cluster requires persistent storage for:
1. **BanyanDB Stream Data**: Traces and logs (time-series data)
2. **BanyanDB Measure Data**: Metrics (aggregated data)
3. **etcd Data**: Cluster metadata and coordination state

Each component uses separate PVCs to optimize I/O patterns, enable independent scaling, and support different retention policies.

## PVC Templates

### 1. BanyanDB Stream Data PVC
**File**: `banyandb-stream-pvc-template.yaml`

Stores trace and log data for BanyanDB data nodes.

**Configuration**:
- **Access Mode**: ReadWriteOnce
- **Volume Mode**: Filesystem
- **Storage Class**: `standard` (Minikube) or `gp3` (EKS)
- **Size**: 10Gi (Minikube) or 50Gi (EKS)
- **Mount Path**: `/data/stream`
- **Retention**: 2-3 days (Minikube), 7 days (EKS)

**Naming Pattern**: `stream-data-banyandb-data-{replica-index}`
- Example: `stream-data-banyandb-data-0`, `stream-data-banyandb-data-1`

### 2. BanyanDB Measure Data PVC
**File**: `banyandb-measure-pvc-template.yaml`

Stores metrics data for BanyanDB data nodes.

**Configuration**:
- **Access Mode**: ReadWriteOnce
- **Volume Mode**: Filesystem
- **Storage Class**: `standard` (Minikube) or `gp3` (EKS)
- **Size**: 10Gi (Minikube) or 50Gi (EKS)
- **Mount Path**: `/data/measure`
- **Retention**: 3 days (Minikube), 30 days (EKS)

**Naming Pattern**: `measure-data-banyandb-data-{replica-index}`
- Example: `measure-data-banyandb-data-0`, `measure-data-banyandb-data-1`

### 3. etcd Data PVC
**File**: `etcd-pvc-template.yaml`

Stores etcd cluster data for BanyanDB coordination.

**Configuration**:
- **Access Mode**: ReadWriteOnce
- **Volume Mode**: Filesystem
- **Storage Class**: `standard` (Minikube) or `gp3` (EKS)
- **Size**: 10Gi (both environments)
- **Mount Path**: `/var/lib/etcd`

**Naming Pattern**: `data-etcd-{replica-index}`
- Example: `data-etcd-0`, `data-etcd-1`, `data-etcd-2`

## Usage

### StatefulSet Integration (Recommended)

PVC templates are typically defined in StatefulSet `volumeClaimTemplates` section. Kubernetes automatically creates PVCs for each replica.

**Example StatefulSet Configuration**:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: banyandb-data
spec:
  replicas: 2
  volumeClaimTemplates:
  - metadata:
      name: stream-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "standard"
      resources:
        requests:
          storage: 10Gi
  - metadata:
      name: measure-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "standard"
      resources:
        requests:
          storage: 10Gi
```

### Manual PVC Creation

For pre-provisioning PVCs or testing, apply templates manually:

```bash
# Create BanyanDB stream data PVC
kubectl apply -f banyandb-stream-pvc-template.yaml

# Create BanyanDB measure data PVC
kubectl apply -f banyandb-measure-pvc-template.yaml

# Create etcd data PVC
kubectl apply -f etcd-pvc-template.yaml
```

### Environment-Specific Configuration

**Minikube**:
```bash
# Use standard storage class and 10Gi size
sed -i 's/storageClass: .*/storageClass: standard/' *.yaml
sed -i 's/storage: .*/storage: 10Gi/' banyandb-*-pvc-template.yaml
kubectl apply -f .
```

**AWS EKS**:
```bash
# Use gp3 storage class and 50Gi size for BanyanDB
sed -i 's/storageClass: .*/storageClass: gp3/' *.yaml
sed -i 's/storage: 10Gi/storage: 50Gi/' banyandb-*-pvc-template.yaml
kubectl apply -f .
```

## Storage Requirements

### Minikube Environment
| Component | PVCs per Replica | Size per PVC | Replicas | Total Storage |
|-----------|------------------|--------------|----------|---------------|
| BanyanDB Data (Stream) | 1 | 10Gi | 2 | 20Gi |
| BanyanDB Data (Measure) | 1 | 10Gi | 2 | 20Gi |
| etcd | 1 | 10Gi | 1 | 10Gi |
| **TOTAL** | | | | **50Gi** |

### AWS EKS Environment
| Component | PVCs per Replica | Size per PVC | Replicas | Total Storage |
|-----------|------------------|--------------|----------|---------------|
| BanyanDB Data (Stream) | 1 | 50Gi | 3 | 150Gi |
| BanyanDB Data (Measure) | 1 | 50Gi | 3 | 150Gi |
| etcd | 1 | 10Gi | 3 | 30Gi |
| **TOTAL** | | | | **330Gi** |

## Storage Classes

### Minikube
**Storage Class**: `standard`
- **Provisioner**: `k8s.io/minikube-hostpath`
- **Type**: Local hostpath
- **Performance**: Limited by host disk
- **Availability**: Single node

**Verify**:
```bash
kubectl get storageclass standard
```

### AWS EKS
**Storage Class**: `gp3`
- **Provisioner**: `ebs.csi.aws.com`
- **Type**: AWS EBS GP3 volumes
- **Performance**: 3000 IOPS, 125 MB/s baseline
- **Availability**: Single AZ per volume

**Create Storage Class**:
```bash
kubectl apply -f ../storage-class.yaml
```

**Verify**:
```bash
kubectl get storageclass gp3
```

## Access Modes

All PVCs use **ReadWriteOnce** access mode:
- Volume can be mounted as read-write by a single node
- Required for StatefulSet with pod anti-affinity
- Each pod gets its own dedicated PVC
- Prevents data corruption from concurrent writes

## Volume Modes

All PVCs use **Filesystem** volume mode:
- Volume is formatted with a filesystem (ext4, xfs)
- Mounted into pods as a directory
- Suitable for BanyanDB and etcd data storage

## Data Retention

Retention is managed by BanyanDB configuration, not at PVC level:

**Minikube**:
- Stream data (traces/logs): 2 days
- Measure data (metrics): 3 days

**EKS**:
- Stream data (traces/logs): 7 days
- Measure data (metrics): 30 days

**Configuration**:
```yaml
banyandb:
  data:
    retention:
      streamTTL: "7d"
      measureTTL: "30d"
```

## Backup and Recovery

### BanyanDB Data Backup

**Volume Snapshots** (Recommended):
```bash
# Create VolumeSnapshot for stream data
kubectl create -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: banyandb-stream-snapshot
  namespace: skywalking
spec:
  volumeSnapshotClassName: csi-aws-vsc
  source:
    persistentVolumeClaimName: stream-data-banyandb-data-0
EOF
```

**Restore from Snapshot**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: stream-data-banyandb-data-0-restored
spec:
  dataSource:
    name: banyandb-stream-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

### etcd Data Backup

**etcd Snapshot** (Critical):
```bash
# Create etcd snapshot
kubectl exec etcd-0 -n skywalking -- etcdctl snapshot save /tmp/snapshot.db

# Copy snapshot to local
kubectl cp skywalking/etcd-0:/tmp/snapshot.db ./etcd-snapshot.db

# Upload to S3 for safekeeping
aws s3 cp etcd-snapshot.db s3://my-backup-bucket/skywalking/etcd/
```

**Restore from Snapshot**:
```bash
# Restore etcd from snapshot
kubectl exec etcd-0 -n skywalking -- etcdctl snapshot restore /tmp/snapshot.db \
  --data-dir=/var/lib/etcd-restore
```

## Monitoring

### Storage Usage

**Check PVC Status**:
```bash
# List all PVCs
kubectl get pvc -n skywalking

# Detailed PVC information
kubectl describe pvc <pvc-name> -n skywalking

# Check storage usage in pods
kubectl exec <pod-name> -n skywalking -- df -h
```

**Prometheus Metrics**:
```promql
# PVC usage percentage
kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 100

# Available space
kubelet_volume_stats_available_bytes
```

### Alerts

**Recommended Alerts**:
```yaml
- alert: PVCStorageAlmostFull
  expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.8
  annotations:
    summary: "PVC {{ $labels.persistentvolumeclaim }} is 80% full"

- alert: PVCStorageCritical
  expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.9
  annotations:
    summary: "PVC {{ $labels.persistentvolumeclaim }} is 90% full"
```

## Scaling Storage

### Expand PVC Size

**Prerequisites**:
- Storage class must support volume expansion (`allowVolumeExpansion: true`)
- PVC must be bound to a PV

**Expand PVC**:
```bash
# Edit PVC and increase storage size
kubectl edit pvc stream-data-banyandb-data-0 -n skywalking

# Change spec.resources.requests.storage to new size
# Example: 50Gi -> 100Gi
```

**Verify Expansion**:
```bash
# Check PVC size
kubectl get pvc stream-data-banyandb-data-0 -n skywalking

# Check filesystem size in pod
kubectl exec banyandb-data-0 -n skywalking -- df -h /data/stream
```

### Add More Data Nodes

**Scale StatefulSet**:
```bash
# Increase BanyanDB data node replicas
kubectl scale statefulset banyandb-data -n skywalking --replicas=5

# New PVCs are automatically created for new replicas
kubectl get pvc -n skywalking
```

## Troubleshooting

### PVC Stuck in Pending

**Symptoms**: PVC remains in Pending state

**Causes**:
1. Storage class doesn't exist
2. No available PVs (static provisioning)
3. Dynamic provisioner not running
4. Insufficient storage quota

**Resolution**:
```bash
# Check storage class exists
kubectl get storageclass

# Check PVC events
kubectl describe pvc <pvc-name> -n skywalking

# Check provisioner logs (EKS)
kubectl logs -n kube-system -l app=ebs-csi-controller

# Verify storage quota
kubectl describe resourcequota -n skywalking
```

### PVC Binding Failed

**Symptoms**: PVC fails to bind to PV

**Causes**:
1. PV selector mismatch
2. Access mode incompatibility
3. Storage size mismatch
4. PV already bound to another PVC

**Resolution**:
```bash
# Check PV availability
kubectl get pv

# Check PVC selector and requirements
kubectl get pvc <pvc-name> -n skywalking -o yaml

# Remove selector if using dynamic provisioning
kubectl edit pvc <pvc-name> -n skywalking
```

### Pod Fails to Mount PVC

**Symptoms**: Pod stuck in ContainerCreating, mount errors

**Causes**:
1. PVC not bound
2. Node doesn't have access to PV
3. Volume already mounted on different node
4. Filesystem corruption

**Resolution**:
```bash
# Check pod events
kubectl describe pod <pod-name> -n skywalking

# Check PVC status
kubectl get pvc -n skywalking

# Check node events
kubectl describe node <node-name>

# For EKS, check EBS volume attachment
aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/created-for/pvc/name,Values=<pvc-name>"
```

### Out of Storage Space

**Symptoms**: BanyanDB or etcd fails, "no space left on device" errors

**Causes**:
1. PVC size too small
2. Data retention not configured
3. Unexpected data growth

**Resolution**:
```bash
# Check storage usage
kubectl exec <pod-name> -n skywalking -- df -h

# Expand PVC (if supported)
kubectl edit pvc <pvc-name> -n skywalking

# Adjust retention policies
kubectl edit configmap skywalking-config -n skywalking

# Clean up old data (BanyanDB)
kubectl exec banyandb-data-0 -n skywalking -- bydbctl data cleanup --before 7d
```

## Performance Optimization

### I/O Performance

**Monitor I/O Metrics**:
```bash
# Check I/O stats in pod
kubectl exec <pod-name> -n skywalking -- iostat -x 1

# Prometheus metrics
rate(container_fs_reads_bytes_total[5m])
rate(container_fs_writes_bytes_total[5m])
```

**Optimize GP3 Volumes** (EKS):
```yaml
# Increase IOPS and throughput in storage class
parameters:
  type: gp3
  iops: "5000"      # Up to 16,000 IOPS
  throughput: "250"  # Up to 1,000 MB/s
```

### Separate Storage for Stream and Measure

**Benefits**:
- Optimized I/O patterns (sequential vs. random)
- Independent scaling
- Different retention policies
- Easier troubleshooting

**Implementation**: Already configured in templates (separate PVCs)

## Cost Optimization

### Right-Size Storage

**Monitor Usage**:
```bash
# Check actual usage vs. allocated
kubectl exec <pod-name> -n skywalking -- df -h
```

**Recommendations**:
- Start with recommended sizes
- Monitor usage for 1-2 weeks
- Adjust based on actual usage patterns
- Consider data retention policies

### Use GP3 Instead of GP2 (EKS)

**Cost Savings**: ~20% cheaper than GP2 for same performance

**Performance**: Better baseline (3000 IOPS vs. 100-16000 IOPS for GP2)

### Implement Data Retention

**Configure Retention**:
```yaml
banyandb:
  data:
    retention:
      streamTTL: "7d"   # Adjust based on requirements
      measureTTL: "30d"
```

## Security

### Encryption at Rest

**EKS**:
```yaml
# Enable encryption in storage class
parameters:
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:region:account:key/key-id"
```

**Minikube**: Not applicable (local storage)

### Access Control

**RBAC**:
```yaml
# Limit PVC access to specific service accounts
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pvc-manager
rules:
- apiGroups: [""]
  resources: ["persistentvolumeclaims"]
  verbs: ["get", "list", "watch"]
```

## References

- [Kubernetes Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [StatefulSet Basics](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)
- [AWS EBS CSI Driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)
- [Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)
- [BanyanDB Documentation](https://skywalking.apache.org/docs/skywalking-banyandb/latest/readme/)
- [etcd Backup and Restore](https://etcd.io/docs/latest/op-guide/recovery/)
