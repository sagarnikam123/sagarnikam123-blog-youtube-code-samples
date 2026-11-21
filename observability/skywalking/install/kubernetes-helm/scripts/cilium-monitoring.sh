#!/bin/bash
# =============================================================================
# Cilium Monitoring
# =============================================================================
# Monitors Cilium eBPF-based networking.
#
# Usage:
#   ./scripts/cilium-monitoring.sh [action] [namespace]
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
    log_header "Enabling Cilium Monitoring"
    echo ""

    log_info "Deploying OTel Collector for Cilium..."
    kubectl apply -f "${BASE_DIR}/base/cilium-monitoring/otel-collector-cilium.yaml" -n "${NAMESPACE}"

    log_success "Cilium monitoring enabled!"
    echo ""
    echo "View in UI: Cilium → Cilium Service"
    echo ""
    log_warn "Note: Requires Cilium CNI to be installed in the cluster."
}

do_disable() {
    log_info "Removing Cilium monitoring..."
    kubectl delete -f "${BASE_DIR}/base/cilium-monitoring/otel-collector-cilium.yaml" -n "${NAMESPACE}" --ignore-not-found
    log_success "Cilium monitoring removed!"
}

do_status() {
    echo ""
    log_header "Cilium Monitoring Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/name=otel-collector-cilium' 2>/dev/null || echo "No Cilium collector found"
    echo ""
    echo "Cilium status:"
    kubectl get pods -n kube-system -l 'k8s-app=cilium' 2>/dev/null | head -5 || echo "Cilium not installed"
    echo ""
}

do_info() {
    cat << 'EOF'

Cilium Monitoring
=================

Monitors Cilium eBPF-based networking.

Prerequisites:
  - Cilium CNI installed
  - Prometheus metrics enabled on Cilium

Cilium Ports:
  - Agent    : 9962
  - Operator : 9963
  - Hubble   : 9965

OAP Configuration:
  SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,cilium-service,..."

UI Location: Cilium → Cilium Service

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
