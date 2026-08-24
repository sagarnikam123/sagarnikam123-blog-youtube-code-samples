# SigNoz — Kubernetes with Kustomize

SigNoz supports Kubernetes deployment via Foundry's Kustomize casting. Foundry generates Kustomize manifests that you apply with `kubectl`.

## Install

```bash
# 1. Install Foundry CLI
curl -fsSL https://signoz.io/foundry.sh | bash

# 2. Create casting.yaml
cat <<'EOF' > casting.yaml
apiVersion: v1alpha1
kind: Installation
metadata:
  name: signoz
spec:
  deployment:
    flavor: kustomize
    mode: kubernetes
EOF

# 3. Generate manifests
foundryctl cast -f casting.yaml

# 4. Apply generated manifests
kubectl apply -k pours/deployment/
```

For Helm-based deployment, see [`helm/standalone/`](../../helm/standalone/) and [`helm/cluster/`](../../helm/cluster/).

Official guide: [SigNoz Kubernetes installation](https://signoz.io/docs/install/kubernetes/).
