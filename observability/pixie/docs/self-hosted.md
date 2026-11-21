# Self-Hosted Pixie

Source: https://docs.px.dev/installing-pixie/install-guides/self-hosted-pixie/

Content rephrased for compliance with licensing restrictions.

## Overview

Pixie is a hybrid system with two components:
- **Pixie Cloud** — control plane (can be self-hosted or use a hosted offering)
- **Vizier** — in-cluster data collection and query execution

Self-hosting deploys both components on your own infrastructure.

## Prerequisites

- Kubernetes cluster meeting [requirements](requirements.md)
- OLM (Operator Lifecycle Manager) — check if already deployed in `olm` namespace
- PersistentVolume support
- Privileged pod access for BPF programs
- `mkcert` for local TLS certificates
- `kustomize` for manifest generation

## Step 1: Deploy Pixie Cloud

```bash
# Clone and checkout latest cloud release
git clone https://github.com/pixie-io/pixie.git
cd pixie
export LATEST=$(git tag -l "release/cloud/*" | sort -V | tail -1)
git checkout "$LATEST"

# Create namespace (must be 'plc')
kubectl create namespace plc

# Generate TLS certs
mkcert -install
./scripts/create_cloud_secrets.sh

# Deploy dependencies
kustomize build k8s/cloud_deps/base/elastic/operator | kubectl apply -f -
# Wait for all pods in plc to be ready

# Deploy Pixie Cloud
kustomize build k8s/cloud/base | kubectl apply -f -
# Wait for all pods in plc to be ready
```

## Step 2: DNS Setup

Ensure `cloud-proxy-service` and `vzconn-service` LoadBalancers have external IPs:

```bash
kubectl -n plc get svc cloud-proxy-service vzconn-service
```

Default domain: `dev.withpixie.dev` (customizable by replacing occurrences in config files).

For minikube, run `minikube tunnel` to assign external IPs.

## Step 3: Install CLI

```bash
# Set cloud address (use custom domain if configured)
export PL_CLOUD_ADDR=dev.withpixie.dev

# Install CLI
bash -c "$(curl -fsSL https://withpixie.ai/install.sh)"
```

## Step 4: Deploy Vizier

```bash
px deploy
```

Deploys to namespaces: `pl`, `plc`, `px-operator`, `olm`

## Step 5: Login

Default credentials:
- Email: `admin@default.com`
- Password: `admin`

Navigate to your configured domain in browser.

## Multi-cluster deployment

Two options:
1. **Separate Pixie Cloud per cluster** — repeat all steps
2. **Shared Pixie Cloud** — configure custom domain, DNS, and TLS, then deploy Vizier to each cluster pointing at the shared Cloud

## Hosted alternatives

If self-hosting is not needed:
- [Cosmic Cloud](https://docs.px.dev/installing-pixie/install-guides/hosted-pixie/)
- [New Relic Cloud](https://docs.px.dev/installing-pixie/install-guides/hosted-pixie/)

Telemetry data stays on-cluster even with hosted backends.
