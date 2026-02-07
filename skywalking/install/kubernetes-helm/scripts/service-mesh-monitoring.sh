#!/bin/bash
# =============================================================================
# Service Mesh Monitoring (Istio/Envoy)
# =============================================================================
# Monitors Istio service mesh using Envoy ALS.
#
# Usage:
#   ./scripts/service-mesh-monitoring.sh [action] [namespace]
#
# Actions: enable, disable, status, info
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

ACTION="${1:-enable}"
NAMESPACE="${2:-skywalking}"
BASE_DIR="$(get_base_dir)"

do_enable() {
    check_namespace "${NAMESPACE}"
    log_header "Enabling Service Mesh Monitoring"
    echo ""

    log_info "Deploying Istio ALS configuration..."
    kubectl apply -f "${BASE_DIR}/base/service-mesh-monitoring/istio-als-config.yaml" --ignore-not-found 2>/dev/null || true

    log_info "Deploying OTel Collector for mesh..."
    kubectl apply -f "${BASE_DIR}/base/service-mesh-monitoring/otel-collector-mesh.yaml" -n "${NAMESPACE}"

    log_success "Service mesh monitoring enabled!"
    echo ""
    echo "View in UI: Service Mesh → Control Plane, Data Plane, Services"
    echo ""
    log_warn "Note: Requires Istio to be installed in the cluster."
}

do_disable() {
    log_info "Removing service mesh monitoring..."
    kubectl delete -f "${BASE_DIR}/base/service-mesh-monitoring/otel-collector-mesh.yaml" -n "${NAMESPACE}" --ignore-not-found
    kubectl delete -f "${BASE_DIR}/base/service-mesh-monitoring/istio-als-config.yaml" --ignore-not-found 2>/dev/null || true
    log_success "Service mesh monitoring removed!"
}

do_status() {
    echo ""
    log_header "Service Mesh Monitoring Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/name=otel-collector-mesh' 2>/dev/null || echo "No mesh collector found"
    echo ""
    echo "Istio status:"
    kubectl get pods -n istio-system 2>/dev/null | head -5 || echo "Istio not installed"
    echo ""
}

do_info() {
    cat << 'EOF'

Service Mesh Monitoring (Istio/Envoy)
=====================================

Monitors Istio service mesh using Envoy ALS (Access Log Service).

Prerequisites:
  - Istio installed in the cluster
  - Envoy ALS enabled

OAP Configuration (add to values.yaml):
  oap:
    env:
      SW_ENVOY_METRIC_ALS_HTTP_ANALYSIS: "k8s-mesh"
      SW_ENVOY_METRIC_ALS_TCP_ANALYSIS: "k8s-mesh"

UI Location: Service Mesh → Control Plane, Data Plane, Services

EOF
}

case "${ACTION}" in
    enable)  do_enable ;;
    disable) do_disable ;;
    status)  do_status ;;
    info)    do_info ;;
    -h|--help|help) do_info ;;
    *) log_error "Unknown action: ${ACTION}. Use: enable, disable, status, info"; exit 1 ;;
esac
