#!/bin/bash
# =============================================================================
# Infrastructure Monitoring (Linux)
# =============================================================================
# Monitors Linux host metrics using node-exporter.
#
# Usage:
#   ./scripts/infrastructure-monitoring.sh [action] [namespace]
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
    log_header "Enabling Infrastructure Monitoring"
    echo ""

    log_info "Deploying node-exporter..."
    kubectl apply -f "${BASE_DIR}/base/k8s-monitoring/node-exporter.yaml"

    log_info "Deploying OTel Collector..."
    kubectl apply -f "${BASE_DIR}/base/k8s-monitoring/otel-collector.yaml"

    log_info "Waiting for deployments..."
    kubectl rollout status daemonset/node-exporter -n "${NAMESPACE}" --timeout=120s
    kubectl rollout status deployment/otel-collector -n "${NAMESPACE}" --timeout=120s

    log_success "Infrastructure monitoring enabled!"
    echo ""
    echo "View in UI: Infrastructure → Linux"
}

do_disable() {
    log_info "Removing infrastructure monitoring..."
    kubectl delete -f "${BASE_DIR}/base/k8s-monitoring/node-exporter.yaml" --ignore-not-found
    log_success "Infrastructure monitoring removed!"
    log_warn "Note: OTel Collector kept as it may be used by other services."
}

do_status() {
    echo ""
    log_header "Infrastructure Monitoring Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/name=node-exporter' 2>/dev/null || echo "No node-exporter found"
    echo ""
}

do_info() {
    cat << 'EOF'

Infrastructure Monitoring (Linux)
=================================

Monitors Linux host metrics using node-exporter.

Components:
  - node-exporter  : Host-level metrics (CPU, memory, disk, network)
  - otel-collector : Scrapes and forwards to OAP

Metrics:
  - CPU usage, load average
  - Memory usage
  - Disk I/O, space
  - Network traffic

UI Location: Infrastructure → Linux

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
