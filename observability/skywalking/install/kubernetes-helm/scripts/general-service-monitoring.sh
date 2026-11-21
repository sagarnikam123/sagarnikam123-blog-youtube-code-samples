#!/bin/bash
# =============================================================================
# General Service Monitoring (Demo Instrumented Apps)
# =============================================================================
# Deploys sample applications with SkyWalking agents.
#
# Usage:
#   ./scripts/general-service-monitoring.sh [action] [namespace]
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
    log_header "Enabling General Service (Demo Apps)"
    echo ""

    log_info "Deploying Java demo app..."
    kubectl apply -f "${BASE_DIR}/demos/demo-app-java.yaml" -n "${NAMESPACE}"

    log_info "Deploying Python demo app..."
    kubectl apply -f "${BASE_DIR}/demos/demo-app-python.yaml" -n "${NAMESPACE}"

    log_info "Waiting for apps to be ready..."
    kubectl rollout status deployment/demo-app-java -n "${NAMESPACE}" --timeout=300s || true
    kubectl rollout status deployment/demo-app-python -n "${NAMESPACE}" --timeout=300s || true

    log_success "Demo apps deployed!"
    echo ""
    echo "View in UI: General Service → demo-app-java, demo-app-python"
}

do_disable() {
    log_info "Removing demo apps..."
    kubectl delete -f "${BASE_DIR}/demos/demo-app-java.yaml" -n "${NAMESPACE}" --ignore-not-found
    kubectl delete -f "${BASE_DIR}/demos/demo-app-python.yaml" -n "${NAMESPACE}" --ignore-not-found
    log_success "Demo apps removed!"
}

do_status() {
    echo ""
    log_header "General Service Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app in (demo-app-java, demo-app-python)' 2>/dev/null || echo "No demo apps found"
    echo ""
}

do_info() {
    cat << 'EOF'

General Service Monitoring
==========================

Deploys sample applications instrumented with SkyWalking agents.

Components:
  - demo-app-java   : Spring Petclinic + SkyWalking Java Agent 9.3.0
  - demo-app-python : Flask app + SkyWalking Python Agent 1.1.0

Features:
  - Distributed tracing (Python calls Java)
  - JVM/Runtime metrics
  - Application logs
  - Automatic traffic generation (CronJobs)

UI Location: General Service → demo-app-java, demo-app-python

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
