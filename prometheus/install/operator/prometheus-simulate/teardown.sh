#!/bin/bash
set -euo pipefail

NAMESPACE="prometheus"
RELEASE_NAME="prometheus"

echo "=== Tearing down Prometheus simulation ==="

kubectl config use-context minikube

# Uninstall Helm release
helm uninstall "${RELEASE_NAME}" --namespace "${NAMESPACE}" 2>/dev/null || true

# Delete namespace
kubectl delete namespace "${NAMESPACE}" --ignore-not-found

# Optional: remove CRDs (Helm doesn't delete these by design)
echo ""
read -p "Remove monitoring.coreos.com CRDs? (y/N): " REMOVE_CRDS
if [[ "${REMOVE_CRDS}" =~ ^[Yy]$ ]]; then
  kubectl delete crd \
    alertmanagerconfigs.monitoring.coreos.com \
    alertmanagers.monitoring.coreos.com \
    podmonitors.monitoring.coreos.com \
    probes.monitoring.coreos.com \
    prometheusagents.monitoring.coreos.com \
    prometheuses.monitoring.coreos.com \
    prometheusrules.monitoring.coreos.com \
    scrapeconfigs.monitoring.coreos.com \
    servicemonitors.monitoring.coreos.com \
    thanosrulers.monitoring.coreos.com \
    --ignore-not-found
  echo "CRDs removed."
fi

echo "=== Teardown complete ==="
