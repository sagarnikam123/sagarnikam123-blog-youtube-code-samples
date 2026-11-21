#!/bin/bash
# =============================================================================
# Kubernetes Monitoring
# =============================================================================
# Deploys kube-state-metrics, node-exporter, and OTel Collector.
#
# Usage:
#   ./scripts/kubernetes-monitoring.sh [action] [namespace]
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
    log_header "Enabling Kubernetes Monitoring"
    echo ""

    log_info "Deploying kube-state-metrics..."
    kubectl apply -f "${BASE_DIR}/base/k8s-monitoring/kube-state-metrics.yaml"

    log_info "Deploying node-exporter..."
    kubectl apply -f "${BASE_DIR}/base/k8s-monitoring/node-exporter.yaml"

    log_info "Deploying OpenTelemetry Collector..."
    kubectl apply -f "${BASE_DIR}/base/k8s-monitoring/otel-collector.yaml"

    log_info "Waiting for deployments..."
    kubectl rollout status deployment/kube-state-metrics -n "${NAMESPACE}" --timeout=120s
    kubectl rollout status deployment/otel-collector -n "${NAMESPACE}" --timeout=120s
    kubectl rollout status daemonset/node-exporter -n "${NAMESPACE}" --timeout=120s

    log_success "Kubernetes monitoring enabled!"
    echo ""
    echo "View in UI: Kubernetes → Cluster, Service, Node"
}

do_disable() {
    log_info "Removing Kubernetes monitoring..."
    kubectl delete -f "${BASE_DIR}/base/k8s-monitoring/otel-collector.yaml" --ignore-not-found
    kubectl delete -f "${BASE_DIR}/base/k8s-monitoring/node-exporter.yaml" --ignore-not-found
    kubectl delete -f "${BASE_DIR}/base/k8s-monitoring/kube-state-metrics.yaml" --ignore-not-found
    log_success "Kubernetes monitoring removed!"
}

do_status() {
    echo ""
    log_header "Kubernetes Monitoring Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/name in (kube-state-metrics, node-exporter, otel-collector)' 2>/dev/null || echo "No K8s monitoring found"
    echo ""
}

do_info() {
    cat << 'EOF'

Kubernetes Monitoring
=====================

Monitors Kubernetes cluster infrastructure.

Components:
  - kube-state-metrics : Cluster state (pods, deployments, services)
  - node-exporter      : Node-level metrics (CPU, memory, disk)
  - otel-collector     : Scrapes and forwards metrics to OAP

UI Location: Kubernetes → Cluster, Service, Node

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
