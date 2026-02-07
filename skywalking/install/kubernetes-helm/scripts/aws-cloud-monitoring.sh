#!/bin/bash
# =============================================================================
# AWS Cloud Monitoring
# =============================================================================
# Monitors AWS services using YACE CloudWatch Exporter.
#
# Usage:
#   ./scripts/aws-cloud-monitoring.sh [action] [namespace]
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
    log_header "Enabling AWS Cloud Monitoring"
    echo ""

    log_warn "AWS monitoring requires IRSA (IAM Roles for Service Accounts) on EKS."
    echo ""

    log_info "Deploying YACE CloudWatch Exporter..."
    kubectl apply -f "${BASE_DIR}/base/aws-monitoring/yace-exporter.yaml" -n "${NAMESPACE}"

    log_info "Deploying OTel Collector for AWS..."
    kubectl apply -f "${BASE_DIR}/base/aws-monitoring/otel-collector-aws.yaml" -n "${NAMESPACE}"

    log_success "AWS monitoring deployed!"
    echo ""
    echo "View in UI: AWS Cloud → API Gateway, DynamoDB"
    echo ""
    log_warn "Ensure IAM role is configured. See: base/aws-monitoring/iam-policy.json"
}

do_disable() {
    log_info "Removing AWS monitoring..."
    kubectl delete -f "${BASE_DIR}/base/aws-monitoring/otel-collector-aws.yaml" -n "${NAMESPACE}" --ignore-not-found
    kubectl delete -f "${BASE_DIR}/base/aws-monitoring/yace-exporter.yaml" -n "${NAMESPACE}" --ignore-not-found
    log_success "AWS monitoring removed!"
}

do_status() {
    echo ""
    log_header "AWS Cloud Monitoring Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/name in (yace-exporter, otel-collector-aws)' 2>/dev/null || echo "No AWS monitoring found"
    echo ""
}

do_info() {
    cat << 'EOF'

AWS Cloud Monitoring
====================

Monitors AWS managed services using YACE (Yet Another CloudWatch Exporter).

Prerequisites:
  - EKS cluster with IRSA enabled
  - IAM role with CloudWatch read permissions

Supported Services:
  - API Gateway
  - DynamoDB

Setup Steps:
  1. Create IAM policy: base/aws-monitoring/iam-policy.json
  2. Create service account with IRSA
  3. Update region in yace-exporter.yaml
  4. Deploy monitoring

UI Location: AWS Cloud → API Gateway, DynamoDB

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
