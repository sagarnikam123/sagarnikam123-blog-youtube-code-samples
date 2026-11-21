# SkyWalking Cloud on Kubernetes (SWCK)

Kubernetes-native deployment using the [SkyWalking Operator (SWCK)](https://github.com/apache/skywalking-swck) with BanyanDB storage.

## What is SWCK?

SWCK (SkyWalking Cloud on Kubernetes) is a bridge project between Apache SkyWalking and Kubernetes. It provisions, upgrades, and maintains SkyWalking components natively on Kubernetes.

### Key Features

| Feature | Description |
|---------|-------------|
| **Operator** | Manages SkyWalking components via CRDs (OAPServer, UI, BanyanDB, Satellite) |
| **Java Agent Injector** | Automatic agent injection for Java applications via admission webhook |
| **Custom Metrics Adapter** | Exposes SkyWalking metrics to Kubernetes HPA for autoscaling |

### SWCK vs Helm Chart

| Aspect | SWCK (Operator) | Helm Chart |
|--------|-----------------|------------|
| **Approach** | Kubernetes-native CRDs | Helm templates |
| **Agent Injection** | Automatic (SwAgent CR) | Manual configuration |
| **GitOps** | Native CRD support | Requires Helm plugin |
| **Custom Metrics** | Built-in adapter for HPA | External setup needed |
| **Learning Curve** | Higher (CRDs, Operator) | Lower (familiar Helm) |
| **Best For** | Platform teams, GitOps | Quick deployments |

## Versions

| Component | Version |
|-----------|---------|
| SkyWalking OAP | 10.3.0 |
| SkyWalking UI | 10.3.0 |
| BanyanDB | 0.9.0 |
| SWCK Operator | 0.9.0 |

## Prerequisites

- Kubernetes cluster (1.19+) - Minikube works great
- kubectl configured
- cert-manager (auto-installed by operator script)

## Namespaces

| Namespace | Components |
|-----------|------------|
| `cert-manager` | cert-manager (webhook certificates) |
| `skywalking-swck-system` | SWCK Operator |
| `skywalking` | BanyanDB, OAP Server, UI |

## Quick Start

```bash
# 1. Start Minikube (if not running)
minikube start --memory=4096 --cpus=2

# 2. Install SWCK Operator (installs cert-manager + operator)
./install-operator.sh

# 3. Deploy SkyWalking stack with BanyanDB
./deploy-all.sh
```

## Access UI

```bash
# Port forward
kubectl port-forward svc/skywalking-ui-ui 8080:80 -n skywalking

# Open browser
open http://localhost:8080

# Or use Minikube service
minikube service skywalking-ui-ui -n skywalking
```

## Available CRDs

| CRD | Description |
|-----|-------------|
| `banyandbs` | BanyanDB storage backend |
| `oapservers` | SkyWalking OAP backend server |
| `uis` | SkyWalking web interface |
| `swagents` | Java agent auto-injection |
| `satellites` | Edge data collector |
| `fetchers` | Metrics fetcher |
| `storages` | Storage (Elasticsearch only) |
| `oapserverconfigs` | OAP static configuration |
| `oapserverdynamicconfigs` | OAP dynamic configuration |
| `javaagents` | Java agent status |

## Files

| File | Description |
|------|-------------|
| `install-operator.sh` | Install cert-manager + SWCK operator |
| `deploy-all.sh` | Deploy BanyanDB + OAP + UI |
| `oap-server.yaml` | OAPServer CR examples |
| `ui.yaml` | UI CR examples |
| `banyandb.yaml` | BanyanDB CR example |
| `swagent.yaml` | Java agent injection CR |

## Manual Deployment

```bash
# Create namespace
kubectl create namespace skywalking

# Deploy BanyanDB first
kubectl apply -f banyandb.yaml -n skywalking

# Wait for BanyanDB to be ready
kubectl wait --for=condition=Available deployment/banyandb -n skywalking --timeout=120s

# Deploy OAP Server (configured for BanyanDB)
kubectl apply -f oap-server.yaml -n skywalking

# Deploy UI
kubectl apply -f ui.yaml -n skywalking
```

## Check Status

```bash
# Check operator
kubectl get pods -n skywalking-swck-system

# Check SkyWalking components
kubectl get pods -n skywalking

# Check CRDs
kubectl get crd | grep skywalking

# Check custom resources
kubectl get oapserver,ui,banyandb -n skywalking
```

## Java Agent Auto-Injection

Enable automatic agent injection for your Java applications:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      labels:
        # Enable injection
        swck-java-agent-injected: "true"
```

First deploy the SwAgent CR:
```bash
kubectl apply -f swagent.yaml -n skywalking
```

## Troubleshooting

```bash
# Check operator logs
kubectl logs -n skywalking-swck-system -l control-plane=controller-manager

# Check OAP logs
kubectl logs -n skywalking -l app=skywalking,component=oap

# Check BanyanDB logs
kubectl logs -n skywalking -l app=banyandb

# Describe resources
kubectl describe oapserver skywalking -n skywalking
kubectl describe ui skywalking -n skywalking
```

## Uninstall

```bash
# Delete SkyWalking components
kubectl delete namespace skywalking

# Delete SWCK operator
kubectl delete -f downloads/config/operator-bundle.yaml

# (Optional) Delete cert-manager
kubectl delete -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml
```

## References

- [SkyWalking GitHub](https://github.com/apache/skywalking)
- [BanyanDB GitHub](https://github.com/apache/skywalking-banyandb)
- [SWCK GitHub](https://github.com/apache/skywalking-swck)
- [SWCK Documentation](https://skywalking.apache.org/docs/skywalking-swck/latest/)
- [Operator Guide](https://skywalking.apache.org/docs/skywalking-swck/next/operator)
- [SkyWalking Helm](https://github.com/apache/skywalking-helm)
