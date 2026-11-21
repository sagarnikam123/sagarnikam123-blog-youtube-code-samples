#!/bin/bash
# =============================================================================
# Flink Monitoring
# =============================================================================
# Monitors Apache Flink data processing engine.
#
# Usage:
#   ./scripts/flink-monitoring.sh [action] [namespace]
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
    log_header "Enabling Flink Monitoring"
    echo ""

    log_info "Deploying OTel Collector for Flink..."
    kubectl apply -f "${BASE_DIR}/base/flink-monitoring/otel-collector-flink.yaml" -n "${NAMESPACE}"

    log_success "Flink collector deployed!"
    echo ""
    echo "Next: Enable Prometheus metrics in your Flink cluster."
    echo "View in UI: Flink"
}

do_disable() {
    log_info "Removing Flink monitoring..."
    kubectl delete -f "${BASE_DIR}/base/flink-monitoring/otel-collector-flink.yaml" -n "${NAMESPACE}" --ignore-not-found
    log_success "Flink monitoring removed!"
}

do_status() {
    echo ""
    log_header "Flink Monitoring Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/name=otel-collector-flink' 2>/dev/null || echo "No Flink collector found"
    echo ""
}

do_info() {
    cat << 'EOF'

Flink Monitoring
================

Monitors Apache Flink data processing engine.

Prerequisites:
  - Flink cluster with Prometheus metrics enabled

Flink Configuration (flink-conf.yaml):
  metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporterFactory
  metrics.reporter.prom.port: 9249

OAP Configuration:
  SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,flink,..."

UI Location: Flink

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
