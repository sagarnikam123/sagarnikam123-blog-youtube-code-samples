#!/bin/bash
# =============================================================================
# Self Observability Monitoring
# =============================================================================
# Monitors SkyWalking's own components (OAP, Satellite, BanyanDB).
#
# Usage:
#   ./scripts/self-observability-monitoring.sh [action] [namespace]
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
    log_header "Enabling Self Observability"
    echo ""

    log_info "Deploying self-observability services..."
    kubectl apply -f "${BASE_DIR}/base/k8s-monitoring/self-observability-services.yaml" -n "${NAMESPACE}" 2>/dev/null || true

    log_success "Self observability enabled!"
    echo ""
    echo "View in UI: SkyWalking → OAP Server, Satellite"
    echo ""
    log_info "Note: OAP must have SW_TELEMETRY=prometheus enabled (default in our values)."
}

do_disable() {
    log_info "Removing self-observability services..."
    kubectl delete -f "${BASE_DIR}/base/k8s-monitoring/self-observability-services.yaml" -n "${NAMESPACE}" --ignore-not-found 2>/dev/null || true
    log_success "Self observability services removed!"
}

do_status() {
    echo ""
    log_header "Self Observability Status"
    echo "OAP metrics service:"
    kubectl get svc -n "${NAMESPACE}" skywalking-oap-metrics 2>/dev/null || echo "  Not found"
    echo ""
    echo "Satellite metrics service:"
    kubectl get svc -n "${NAMESPACE}" skywalking-satellite-metrics 2>/dev/null || echo "  Not found"
    echo ""
}

do_info() {
    cat << 'EOF'

Self Observability
==================

Monitors SkyWalking's own components (OAP, Satellite, BanyanDB).

Components Monitored:
  - OAP Server : JVM metrics, query performance, storage latency
  - Satellite  : Throughput, buffer usage, forwarding latency
  - BanyanDB   : Storage metrics, query performance

OAP Configuration (already enabled by default):
  oap:
    env:
      SW_TELEMETRY: "prometheus"
      SW_TELEMETRY_PROMETHEUS_HOST: "0.0.0.0"
      SW_TELEMETRY_PROMETHEUS_PORT: "1234"
      SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,..."

Services:
  - skywalking-oap-metrics       : Exposes OAP metrics on port 1234
  - skywalking-satellite-metrics : Exposes Satellite metrics on port 1234

UI Location: SkyWalking → OAP Server, Satellite

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
