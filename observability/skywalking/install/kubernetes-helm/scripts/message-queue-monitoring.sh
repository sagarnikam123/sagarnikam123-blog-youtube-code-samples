#!/bin/bash
# =============================================================================
# Message Queue Monitoring
# =============================================================================
# Monitors message queues using Prometheus exporters.
#
# Usage:
#   ./scripts/message-queue-monitoring.sh [action] [namespace]
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
    log_header "Enabling Message Queue Monitoring"
    echo ""

    log_info "Deploying OTel Collector for message queues..."
    kubectl apply -f "${BASE_DIR}/base/mq-monitoring/otel-collector-mq.yaml" -n "${NAMESPACE}"

    log_success "MQ collector deployed!"
    echo ""
    echo "Next steps - deploy exporters for your MQ:"
    echo "  - Kafka:    kubectl apply -f base/mq-monitoring/kafka-exporter.yaml"
    echo "  - RabbitMQ: Enable prometheus plugin (see rabbitmq-config.yaml)"
    echo "  - Pulsar:   Enable prometheus (see pulsar-config.yaml)"
    echo "  - ActiveMQ: kubectl apply -f base/mq-monitoring/activemq-exporter.yaml"
    echo "  - RocketMQ: kubectl apply -f base/mq-monitoring/rocketmq-exporter.yaml"
    echo ""
    echo "View in UI: MQ → Kafka, RabbitMQ, Pulsar, etc."
}

do_disable() {
    log_info "Removing message queue monitoring..."
    kubectl delete -f "${BASE_DIR}/base/mq-monitoring/otel-collector-mq.yaml" -n "${NAMESPACE}" --ignore-not-found
    log_success "MQ monitoring removed!"
    log_warn "Note: Individual exporters need to be removed separately."
}

do_status() {
    echo ""
    log_header "Message Queue Monitoring Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/name=otel-collector-mq' 2>/dev/null || echo "No MQ collector found"
    echo ""
}

do_info() {
    cat << 'EOF'

Message Queue Monitoring
========================

Monitors message queues using Prometheus exporters.

Supported Message Queues:
  - Kafka    : kafka_exporter (port 9308)
  - RabbitMQ : Built-in Prometheus (port 15692)
  - Pulsar   : Built-in Prometheus (port 8080)
  - ActiveMQ : JMX Exporter (port 9404)
  - RocketMQ : rocketmq_exporter (port 5557)

Setup:
  1. Deploy OTel Collector for MQ
  2. Deploy exporter or enable Prometheus on your MQ
  3. Add MQ rules to OAP:
     SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,kafka,rabbitmq,pulsar,..."

Configuration files in: base/mq-monitoring/

UI Location: MQ → Kafka, RabbitMQ, Pulsar, etc.

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
