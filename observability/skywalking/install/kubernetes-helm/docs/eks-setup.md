# AWS EKS Setup Guide for SkyWalking

## Prerequisites

### 1. EKS Cluster Requirements

| Component | Minimum (Dev) | Recommended (Production) |
|-----------|---------------|--------------------------|
| Kubernetes Version | 1.27+ | 1.29+ |
| Node Instance Type | t3.medium | m5.xlarge or larger |
| Node Count | 2 | 6+ (across 3 AZs) |
| Node Groups | 1 | 2 (system + workload) |

### 2. Required Add-ons

```bash
# Check installed add-ons
aws eks describe-addon-versions --kubernetes-version 1.29 --query 'addons[].addonName'

# Required add-ons:
# - vpc-cni
# - coredns
# - kube-proxy
# - aws-ebs-csi-driver (CRITICAL for BanyanDB storage)
```

## Step-by-Step Setup

### Step 1: Create EKS Cluster (if not exists)

```bash
# Using eksctl (recommended)
eksctl create cluster \
  --name skywalking-cluster \
  --version 1.29 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 6 \
  --managed \
  --asg-access \
  --with-oidc
```

### Step 2: Install EBS CSI Driver

```bash
# Create IAM role for EBS CSI driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster skywalking-cluster \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --role-only \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve

# Install EBS CSI driver add-on
aws eks create-addon \
  --cluster-name skywalking-cluster \
  --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonEKS_EBS_CSI_DriverRole

# Verify installation
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
```

### Step 3: Install AWS Load Balancer Controller (for Ingress)

```bash
# Create IAM policy
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json

# Create service account
eksctl create iamserviceaccount \
  --cluster=skywalking-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install using Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=skywalking-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### Step 4: Configure kubectl

```bash
# Update kubeconfig
aws eks update-kubeconfig --name skywalking-cluster --region us-west-2

# Verify connection
kubectl get nodes
```

### Step 5: Apply Storage Classes

```bash
# Navigate to helm directory
cd skywalking/install/kubernetes-helm

# Apply storage classes
kubectl apply -f base/storage-class.yaml

# Verify
kubectl get storageclass
```

### Step 6: Install SkyWalking

```bash
# Development
./scripts/install.sh dev

# Staging
./scripts/install.sh staging --wait

# Production
./scripts/install.sh production --wait
```

## Production Checklist

### Security

- [ ] Enable encryption at rest for EBS volumes (configured in storage class)
- [ ] Configure network policies
- [ ] Set up IRSA for service accounts
- [ ] Enable audit logging on EKS cluster
- [ ] Configure security groups for node communication

### High Availability

- [ ] Deploy across 3 Availability Zones
- [ ] Configure Pod Disruption Budgets
- [ ] Set up pod anti-affinity rules
- [ ] Enable cluster autoscaler

### Monitoring

- [ ] Install Prometheus for metrics collection
- [ ] Configure CloudWatch Container Insights
- [ ] Set up alerting for critical metrics
- [ ] Enable SkyWalking self-observability

### Backup & Recovery

- [ ] Configure VolumeSnapshot class
- [ ] Set up automated backup schedule
- [ ] Test restore procedure
- [ ] Document RTO/RPO requirements

## Resource Sizing Guide

### OAP Server

| Traces/Day | Replicas | CPU (per pod) | Memory (per pod) |
|------------|----------|---------------|------------------|
| < 1M | 2 | 1 core | 2 GB |
| 1-10M | 3 | 2 cores | 4 GB |
| 10-50M | 5 | 4 cores | 8 GB |
| > 50M | 7+ | 8 cores | 16 GB |

### BanyanDB

| Data Retention | Data Nodes | CPU (per node) | Memory (per node) | Storage |
|----------------|------------|----------------|-------------------|---------|
| 3 days | 3 | 2 cores | 4 GB | 100 GB |
| 7 days | 3 | 4 cores | 8 GB | 250 GB |
| 14 days | 5 | 4 cores | 8 GB | 500 GB |
| 30 days | 7 | 8 cores | 16 GB | 1 TB |

## Troubleshooting

### Common Issues

1. **PVC stuck in Pending**
   ```bash
   kubectl describe pvc <pvc-name> -n skywalking
   # Check if EBS CSI driver is running
   kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
   ```

2. **OAP pods not starting**
   ```bash
   kubectl logs -f deployment/skywalking-oap -n skywalking
   # Check BanyanDB connectivity
   kubectl exec -it skywalking-oap-xxx -n skywalking -- nc -zv skywalking-banyandb 17912
   ```

3. **ALB not created**
   ```bash
   kubectl logs -n kube-system deployment/aws-load-balancer-controller
   # Check ingress status
   kubectl describe ingress skywalking-ui -n skywalking
   ```

## Cost Optimization

1. **Use Spot Instances** for non-critical workloads (dev/staging)
2. **Right-size** based on actual usage metrics
3. **Configure data retention** appropriately
4. **Use GP3** storage (better price-performance than GP2)
5. **Enable cluster autoscaler** for dynamic scaling
