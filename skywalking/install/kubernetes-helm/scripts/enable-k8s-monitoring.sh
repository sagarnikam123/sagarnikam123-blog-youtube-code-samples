#!/bin/bash
# =============================================================================
# Enable Kubernetes Infrastructure Monitoring for SkyWalking
# =============================================================================
# Deploys:
#   - kube-state-metrics (cluster state)
#   - node-exporter (host metrics)
#   - OpenTelemetry Collector (scrapes and forwards to OAP)
#
# Usage:
#   ./scripts/enable-k8s-monitoring.sh [namespace]
# =============================================================================

set -euo pipefail

NAMESPACE="${1:-skywalking}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

echo ""
echo "=============================================="
echo "Enabling Kubernetes Infrastructure Monitoring"
echo "=============================================="
echo ""

# Check if namespace exists
if ! kubectl get namespace "${NAMESPACE}" &> /dev/null; then
    log_info "Creating namespace: ${NAMESPACE}"
    kubectl create namespace "${NAMESPACE}"
fi

# Deploy kube-state-metrics
log_info "Deploying kube-state-metrics..."
kubectl apply -f "${BASE_DIR}/base/k8s-monitoring/kube-state-metrics.yaml"

# Deploy node-exporter
log_info "Deploying node-exporter..."
kubectl apply -f "${BASE_DIR}/base/k8s-monitoring/node-exporter.yaml"

# Deploy OpenTelemetry Collector
log_info "Deploying OpenTelemetry Collector..."
kubectl apply -f "${BASE_DIR}/base/k8s-monitoring/otel-collector.yaml"

# Wait for deployments
log_info "Waiting for deployments to be ready..."
kubectl rollout status deployment/kube-state-metrics -n "${NAMESPACE}" --timeout=120s
kubectl rollout status deployment/otel-collector -n "${NAMESPACE}" --timeout=120s
kubectl rollout status daemonset/node-exporter -n "${NAMESPACE}" --timeout=120s

echo ""
log_success "Kubernetes monitoring enabled!"
echo ""
echo "Components deployed:"
kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/component=monitoring'
echo ""
echo "Metrics will appear in SkyWalking UI under:"
echo "  - Kubernetes > Cluster (cluster state, CPU/memory usage)"
echo "  - Kubernetes > Service (service-level metrics)"
echo "  - Infrastructure > Linux (node-exporter host metrics)"
echo ""
echo "Note: It may take 1-2 minutes for metrics to appear."
echo ""
echo "Access UI: kubectl port-forward svc/skywalking-ui 8088:80 -n ${NAMESPACE}"
echo "Then open: http://localhost:8088"
