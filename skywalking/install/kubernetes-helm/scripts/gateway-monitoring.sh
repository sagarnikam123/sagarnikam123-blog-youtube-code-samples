#!/bin/bash
# =============================================================================
# Gateway Monitoring (Nginx, APISIX, Kong)
# =============================================================================
# Monitors API Gateways.
#
# Usage:
#   ./scripts/gateway-monitoring.sh [action] [namespace]
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
    log_header "Enabling Gateway Monitoring"
    echo ""

    log_info "Deploying OTel Collector for gateways..."
    kubectl apply -f "${BASE_DIR}/base/gateway-monitoring/otel-collector-gateway.yaml" -n "${NAMESPACE}"

    log_success "Gateway collector deployed!"
    echo ""
    echo "Next steps:"
    echo "  - Nginx:  Deploy nginx-exporter sidecar"
    echo "  - APISIX: Enable Prometheus plugin"
    echo "  - Kong:   Enable Prometheus plugin"
    echo ""
    echo "View in UI: Gateway → NGINX, APISIX, Kong"
}

do_disable() {
    log_info "Removing gateway monitoring..."
    kubectl delete -f "${BASE_DIR}/base/gateway-monitoring/otel-collector-gateway.yaml" -n "${NAMESPACE}" --ignore-not-found
    log_success "Gateway monitoring removed!"
}

do_status() {
    echo ""
    log_header "Gateway Monitoring Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/name=otel-collector-gateway' 2>/dev/null || echo "No gateway collector found"
    echo ""
}

do_info() {
    cat << 'EOF'

Gateway Monitoring
==================

Monitors API Gateways (Nginx, APISIX, Kong).

Supported Gateways:
  - Nginx  : nginx-prometheus-exporter (port 9113)
  - APISIX : Built-in Prometheus (port 9091)
  - Kong   : Built-in Prometheus (port 8001)

Setup:
  1. Deploy OTel Collector for gateways
  2. Configure your gateway to expose Prometheus metrics
  3. Add gateway rules to OAP:
     SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,nginx,apisix,kong,..."

Configuration files:
  - base/gateway-monitoring/nginx-exporter.yaml
  - base/gateway-monitoring/apisix-config.yaml
  - base/gateway-monitoring/kong-prometheus.yaml

UI Location: Gateway → NGINX, APISIX, Kong

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
