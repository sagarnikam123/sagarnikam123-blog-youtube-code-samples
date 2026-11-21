#!/usr/bin/env bash
# Install Coroot on k3s using Helm (benchmark setup)
set -euo pipefail

echo "=== Installing Coroot on Kubernetes ==="

# Add Helm repo
helm repo add coroot https://coroot.github.io/helm-charts
helm repo update coroot

# Install operator
echo "Installing Coroot Operator..."
helm install -n coroot --create-namespace coroot-operator coroot/coroot-operator

# Install Coroot CE with benchmark values
echo "Installing Coroot Community Edition..."
helm install -n coroot coroot coroot/coroot-ce -f values.yaml

echo ""
echo "=== Installation initiated ==="
echo "Wait for pods to be ready:"
echo "  kubectl get pods -n coroot -w"
echo ""
echo "Access Coroot:"
echo "  kubectl port-forward -n coroot service/coroot-coroot 8080:8080"
echo "  Open http://localhost:8080"
