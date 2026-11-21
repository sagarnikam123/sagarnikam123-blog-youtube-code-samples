#!/bin/bash
# =============================================================================
# Database Monitoring
# =============================================================================
# Monitors databases using Prometheus exporters.
#
# Usage:
#   ./scripts/database-monitoring.sh [action] [namespace]
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
    log_header "Enabling Database Monitoring"
    echo ""

    # Check if otel-collector-database.yaml is a deployable resource
    if ! grep -q "^apiVersion:" "${BASE_DIR}/base/database-monitoring/otel-collector-database.yaml" 2>/dev/null; then
        log_warn "Database monitoring requires manual configuration."
        echo ""
        do_info
        return 0
    fi

    log_info "Deploying OTel Collector for databases..."
    kubectl apply -f "${BASE_DIR}/base/database-monitoring/otel-collector-database.yaml" -n "${NAMESPACE}"

    log_success "Database collector deployed!"
    echo ""
    echo "Next steps - deploy exporters for your databases:"
    echo "  - MySQL:         kubectl apply -f base/database-monitoring/mysql-exporter.yaml"
    echo "  - PostgreSQL:    kubectl apply -f base/database-monitoring/postgresql-exporter.yaml"
    echo "  - Redis:         kubectl apply -f base/database-monitoring/redis-exporter.yaml"
    echo "  - MongoDB:       kubectl apply -f base/database-monitoring/mongodb-exporter.yaml"
    echo "  - Elasticsearch: kubectl apply -f base/database-monitoring/elasticsearch-exporter.yaml"
    echo ""
    echo "View in UI: Database → MySQL, PostgreSQL, Redis, etc."
}

do_disable() {
    log_info "Removing database monitoring..."
    kubectl delete -f "${BASE_DIR}/base/database-monitoring/otel-collector-database.yaml" -n "${NAMESPACE}" --ignore-not-found
    log_success "Database monitoring removed!"
    log_warn "Note: Individual exporters need to be removed separately."
}

do_status() {
    echo ""
    log_header "Database Monitoring Status"
    kubectl get pods -n "${NAMESPACE}" -l 'app.kubernetes.io/name=otel-collector-database' 2>/dev/null || echo "No database collector found"
    echo ""
}

do_info() {
    cat << 'EOF'

Database Monitoring
===================

Monitors databases using Prometheus exporters.

Supported Databases:
  - MySQL/MariaDB    : mysqld_exporter (port 9104)
  - PostgreSQL       : postgres_exporter (port 9187)
  - Redis            : redis_exporter (port 9121)
  - MongoDB          : mongodb_exporter (port 9216)
  - Elasticsearch    : elasticsearch_exporter (port 9114)
  - ClickHouse       : clickhouse_exporter (port 9363)
  - BookKeeper       : Built-in Prometheus (port 8000)

Setup:
  1. Deploy OTel Collector for databases
  2. Deploy exporter for your database (as sidecar or separate pod)
  3. Add database rules to OAP:
     SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,mysql,postgresql,redis,..."

Configuration files in: base/database-monitoring/

UI Location: Database → MySQL, PostgreSQL, Redis, etc.

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
