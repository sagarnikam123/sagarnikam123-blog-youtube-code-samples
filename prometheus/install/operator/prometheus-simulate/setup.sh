#!/bin/bash
set -euo pipefail

# Simulate prod Prometheus namespace on minikube
# Uses kube-prometheus-stack Helm chart (same as prod: v77.10.0)

NAMESPACE="prometheus"
RELEASE_NAME="prometheus"
CHART_VERSION="77.10.0"

echo "=== Prometheus Operator Local Simulation ==="
echo "Replicating prod prometheus namespace"
echo ""

# Check minikube is running
if ! minikube status &>/dev/null; then
  echo "ERROR: minikube is not running. Start it with: minikube start --cpus=4 --memory=8192"
  exit 1
fi

# Switch to minikube context
kubectl config use-context minikube

# Add helm repo
echo ">>> Adding prometheus-community Helm repo..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update

# Create namespace
echo ">>> Creating namespace: ${NAMESPACE}"
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Install kube-prometheus-stack with values matching prod
echo ">>> Installing kube-prometheus-stack ${CHART_VERSION}..."
helm upgrade --install "${RELEASE_NAME}" prometheus-community/kube-prometheus-stack \
  --namespace "${NAMESPACE}" \
  --version "${CHART_VERSION}" \
  --values values-local.yaml \
  --wait --timeout 10m

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Access Prometheus:    kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n ${NAMESPACE}"
echo "Access Alertmanager:  kubectl port-forward svc/prometheus-kube-prometheus-alertmanager 9093:9093 -n ${NAMESPACE}"
echo "Access Grafana:       kubectl port-forward svc/prometheus-grafana 3000:80 -n ${NAMESPACE}"
echo "  Grafana creds:      admin / prom-operator"
