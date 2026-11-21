# Mimir Kubernetes Deployment

Distributed Mimir deployment with zone-aware replication, Kafka ingest, and MinIO storage.

## Quick Start

### Minikube
```bash
./deploy.sh minikube
```

### EKS
```bash
./deploy.sh eks
```

The script automatically configures storage class, creates namespace, and deploys all resources.

---

## Platform Configuration

| Platform | Storage Class | Prerequisites |
|----------|---------------|---------------|
| Minikube | `standard` | Minikube running |
| EKS | `gp2` | EKS cluster + EBS CSI driver + IAM permissions |
| EKS | `efs-sc` | EKS cluster + EFS CSI driver + EFS filesystem |
| EKS | `gp3` | EKS cluster + EBS CSI driver + IAM permissions |

### Storage Class Configuration

**Current Configuration**: All PVCs and Kafka volumeClaimTemplate use `storageClassName: efs-sc` (EFS storage).

**To switch storage class for different platforms:**

```bash
# For Minikube (uses standard StorageClass)
sed -i 's/storageClassName: efs-sc/storageClassName: standard/g' v3.0.x/pvcs/*.yaml
sed -i 's/storageClassName: efs-sc/storageClassName: standard/g' v3.0.x/statefulsets/mimir-kafka.yaml

# For EKS with EBS gp2 (requires IAM permissions - see AWS-PERMISSIONS-REQUIRED.md)
sed -i 's/storageClassName: efs-sc/storageClassName: gp2/g' v3.0.x/pvcs/*.yaml
sed -i 's/storageClassName: efs-sc/storageClassName: gp2/g' v3.0.x/statefulsets/mimir-kafka.yaml

# For EKS with EFS (current default)
# No changes needed - already configured for efs-sc
```

**Note**:
- EFS (`efs-sc`) requires `provisioningMode`, `fileSystemId`, and `directoryPerms` parameters in StorageClass
- EBS (`gp2`/`gp3`) requires IAM permissions for `ec2:CreateVolume` (see `AWS-PERMISSIONS-REQUIRED.md`)
- Minikube `standard` StorageClass works out of the box

### EKS Prerequisites

1. **Create EKS Cluster**
   ```bash
   eksctl create cluster --name mimir-dev --region us-east-1 --nodes 3 --node-type t3.medium
   ```

2. **Install EBS CSI Driver**
   ```bash
   eksctl create addon --name aws-ebs-csi-driver --cluster mimir-dev
   ```

3. **Configure kubectl**
   ```bash
   aws eks update-kubeconfig --name mimir-dev --region us-east-1
   ```

### Switch Platform
```bash
./switch-storage-class.sh minikube  # or eks, eks-gp3
```

---

## Manual Deployment

### Step-by-Step

```bash
# 1. Configure storage
./switch-storage-class.sh minikube  # or eks

# 2. Create namespace
kubectl create namespace mimir-test

# 3. Deploy CRDs (for rollout-operator)
kubectl apply -f v3.0.x/crds/

# 4. Deploy resources
kubectl apply -f serviceaccounts/ -n mimir-test
kubectl apply -f v3.0.x/roles/ -n mimir-test
kubectl apply -f v3.0.x/rolebindings/ -n mimir-test
kubectl apply -f v3.0.x/clusterroles/
kubectl apply -f v3.0.x/clusterrolebindings/
kubectl apply -f secrets/ -n mimir-test
kubectl apply -f configmaps/ -n mimir-test
kubectl apply -f pvcs/ -n mimir-test
kubectl apply -f services/ -n mimir-test

# 5. Deploy MinIO first (object storage dependency)
kubectl apply -f deployments/mimir-minio.yaml -n mimir-test
kubectl wait --for=condition=ready pod -l app=minio -n mimir-test --timeout=300s

# 6. Create MinIO buckets
kubectl apply -f jobs/all-jobs.yaml -n mimir-test
kubectl wait --for=condition=complete job/mimir-make-minio-buckets -n mimir-test --timeout=120s

# 7. Deploy Kafka (ingest dependency)
kubectl apply -f statefulsets/mimir-kafka.yaml -n mimir-test
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=kafka -n mimir-test --timeout=300s

# 8. Deploy remaining StatefulSets and Deployments
kubectl apply -f statefulsets/ -n mimir-test
kubectl apply -f deployments/ -n mimir-test

# 9. Wait for all pods ready
kubectl wait --for=condition=ready pod --all -n mimir-test --timeout=600s
```

### Deployment Order (Dependencies)

1. **CRDs** → Custom Resource Definitions (ZoneAwarePodDisruptionBudget)
2. **ServiceAccounts** → RBAC identities
3. **Roles** → RBAC namespace permissions
4. **RoleBindings** → RBAC namespace bindings
5. **ClusterRoles** → RBAC cluster permissions (webhooks)
6. **ClusterRoleBindings** → RBAC cluster bindings
7. **Secrets** → MinIO credentials
8. **ConfigMaps** → Configuration
9. **PVCs** → Storage claims
10. **Services** → Networking
11. **MinIO Deployment** → Object storage (wait for ready)
12. **MinIO Buckets Job** → Create buckets (wait for complete)
13. **Kafka StatefulSet** → Ingest storage (wait for ready)
14. **Remaining StatefulSets** → Ingesters, Store-Gateways, Compactor, Alertmanager
15. **Remaining Deployments** → Distributor, Query-Scheduler, Querier, Query-Frontend, Ruler, Gateway, Rollout-Operator, Continuous-Test

---

## Access Mimir

### Check Mimir Version
```bash
# Via API (from inside cluster)
kubectl exec -n mimir-test deployment/mimir-gateway -- wget -qO- http://localhost:8080/api/v1/status/buildinfo

# Via port-forward
kubectl port-forward -n mimir-test svc/mimir-gateway 8080:80
curl http://localhost:8080/api/v1/status/buildinfo

# From container image
kubectl get pods -n mimir-test -o jsonpath='{.items[0].spec.containers[0].image}'
```

### Port Forward (Testing)
```bash
kubectl port-forward svc/mimir-gateway 8080:80 -n mimir-test
curl http://localhost:8080/ready
```

### LoadBalancer (EKS)
```bash
kubectl patch svc mimir-gateway -n mimir-test -p '{"spec":{"type":"LoadBalancer"}}'
kubectl get svc mimir-gateway -n mimir-test
```

### Test Write/Read
```bash
# Write
cat <<EOF | curl -X POST -H "Content-Type: application/json" -H "X-Scope-OrgID: demo" --data-binary @- http://localhost:8080/api/v1/push
{
  "series": [{
    "labels": [
      {"name": "__name__", "value": "test_metric"},
      {"name": "job", "value": "test"}
    ],
    "samples": [{"value": 42, "timestamp": $(date +%s)000}]
  }]
}
EOF

# Read
curl "http://localhost:8080/prometheus/api/v1/query?query=test_metric" -H "X-Scope-OrgID: demo"
```

---

## Customization

### Scale Components
```bash
kubectl scale deployment mimir-querier -n mimir-test --replicas=5
```

### Update Resources
Edit YAML files and apply:
```bash
kubectl apply -f deployments/mimir-querier.yaml -n mimir-test
```

### Change Service Type
```bash
# Edit services/mimir-gateway.yaml
spec:
  type: LoadBalancer
```

---

## Production Setup (EKS)

### Replace MinIO with S3

1. **Create S3 Buckets**
   ```bash
   aws s3 mb s3://mimir-tsdb-prod --region us-east-1
   aws s3 mb s3://mimir-ruler-prod --region us-east-1
   ```

2. **Create IAM Policy**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
       "Resource": [
         "arn:aws:s3:::mimir-tsdb-prod",
         "arn:aws:s3:::mimir-tsdb-prod/*",
         "arn:aws:s3:::mimir-ruler-prod",
         "arn:aws:s3:::mimir-ruler-prod/*"
       ]
     }]
   }
   ```

3. **Setup IRSA**
   ```bash
   eksctl create iamserviceaccount \
     --name mimir \
     --namespace mimir-test \
     --cluster your-eks-cluster \
     --attach-policy-arn arn:aws:iam::ACCOUNT:policy/MimirS3Policy \
     --approve
   ```

4. **Update ConfigMap**
   ```yaml
   blocks_storage:
     backend: s3
     s3:
       bucket_name: mimir-tsdb-prod
       region: us-east-1
   ```

5. **Remove MinIO**
   ```bash
   rm deployments/mimir-minio.yaml
   rm services/mimir-minio*.yaml
   rm pvcs/mimir-minio.yaml
   rm jobs/all-jobs.yaml
   ```

### Use AWS MSK (Managed Kafka)

```yaml
# Update configmaps/mimir-config.yaml
ingest_storage:
  kafka:
    address: b-1.your-msk-cluster.kafka.us-east-1.amazonaws.com:9092
    topic: mimir-ingest

# Remove Kafka StatefulSet
rm statefulsets/mimir-kafka.yaml
rm services/mimir-kafka*.yaml
rm pvcs/kafka-data-*.yaml
```

### Security Context (Non-root)

```yaml
# Update statefulsets/*.yaml
securityContext:
  fsGroup: 10001
  runAsGroup: 10001
  runAsNonRoot: true
  runAsUser: 10001
  seccompProfile:
    type: RuntimeDefault
```

### ALB Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mimir-ingress
  namespace: mimir-test
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - host: mimir.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mimir-gateway
            port:
              number: 80
```

---

## Troubleshooting

### Pods Pending
```bash
kubectl get pvc -n mimir-test
kubectl describe pod <pod-name> -n mimir-test
kubectl get events -n mimir-test --sort-by='.lastTimestamp'
```

### EBS CSI Issues
```bash
kubectl get pods -n kube-system | grep ebs-csi
eksctl create addon --name aws-ebs-csi-driver --cluster mimir-dev
```

### Storage Class Not Found
```bash
kubectl get storageclass
```

### Pods Restarting
```bash
kubectl logs -n mimir-test <pod-name> --previous
kubectl top pods -n mimir-test
```

---

## Cleanup

### Delete All Resources
```bash
kubectl delete namespace mimir-test
```

### Delete Components Individually

```bash
# 1. Delete Deployments
kubectl delete deployment --all -n mimir-test
# Or specific:
kubectl delete -f deployments/ -n mimir-test

# 2. Delete StatefulSets
kubectl delete statefulset --all -n mimir-test
# Or specific:
kubectl delete -f statefulsets/ -n mimir-test

# 3. Delete Jobs
kubectl delete job --all -n mimir-test
# Or specific:
kubectl delete -f jobs/ -n mimir-test

# 4. Delete Services
kubectl delete service --all -n mimir-test
# Or specific:
kubectl delete -f services/ -n mimir-test

# 5. Delete PVCs (data will be retained with efs-sc-prom)
kubectl delete pvc --all -n mimir-test
# Or specific:
kubectl delete -f pvcs/ -n mimir-test

# 6. Delete ConfigMaps
kubectl delete configmap --all -n mimir-test
# Or specific:
kubectl delete -f configmaps/ -n mimir-test

# 7. Delete RBAC
kubectl delete -f clusterrolebindings/
kubectl delete -f clusterroles/
kubectl delete -f rolebindings/ -n mimir-test
kubectl delete -f roles/ -n mimir-test

# 8. Delete ServiceAccounts
kubectl delete serviceaccount --all -n mimir-test
# Or specific:
kubectl delete -f serviceaccounts/ -n mimir-test

# 9. Delete CRDs
kubectl delete -f crds/

# 10. Manually delete PVs (if using Retain policy)
kubectl get pv | grep mimir-test | awk '{print $1}' | xargs kubectl delete pv

# 11. Delete namespace
kubectl delete namespace mimir-test
```

### Delete EKS Cluster
```bash
eksctl delete cluster --name mimir-dev --region us-east-1
```

---

## Cost Estimates (Monthly)

### Dev Setup
- 3x t3.medium nodes: ~$75
- EBS volumes (17GB): ~$2
- LoadBalancer: ~$20
- **Total: ~$97/month**

### Production Setup
- 6x t3.xlarge nodes: ~$900
- EBS volumes (500GB gp3): ~$40
- ALB: ~$25
- S3 storage (1TB): ~$23
- **Total: ~$988/month**

---

## Resources

**Components:**
- 11 Deployments
- 10 StatefulSets
- 28 Services
- 7 ConfigMaps
- 11 PVCs
- 1 Job
- 1 ServiceAccount
- 1 Role
- 1 RoleBinding
- 1 ClusterRole
- 1 ClusterRoleBinding
- 1 CRD

**Storage:**
- Ingesters (3 zones): 3x 2GB
- Store-Gateways (3 zones): 3x 2GB
- Compactor: 2GB
- Alertmanager: 1GB
- MinIO: 5GB
- Kafka: 1GB

---

## Notes

- Helm metadata included in exported files
- Secrets not exported (security)
- Remove `.metadata.managedFields` and `.status` for clean manifests
- Use `./clean-helm-metadata.sh` to remove Helm annotations
