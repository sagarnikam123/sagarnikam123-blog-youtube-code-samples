#!/bin/bash
# =============================================================================
# SkyWalking Unified Monitoring Manager
# =============================================================================
# Unified interface to enable/disable all monitoring services.
# Calls individual *-monitoring.sh scripts.
#
# Usage:
#   ./scripts/monitoring.sh <service> [action] [namespace]
#
# Services:
#   general-service, service-mesh, kubernetes, cilium, infrastructure,
#   aws-cloud, browser, gateway, database, message-queue, flink,
#   self-observability, all
#
# Actions:
#   enable  - Deploy monitoring components (default)
#   disable - Remove monitoring components
#   status  - Check component status
#   info    - Show setup instructions
#
# Examples:
#   ./scripts/monitoring.sh all                      # List all services
#   ./scripts/monitoring.sh kubernetes enable        # Enable K8s monitoring
#   ./scripts/monitoring.sh database info            # Show database setup
#   ./scripts/monitoring.sh gateway disable          # Disable gateway
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Handle help flag first
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "help" || -z "${1:-}" ]]; then
    SERVICE="help"
else
    SERVICE="${1:-all}"
fi
ACTION="${2:-enable}"
NAMESPACE="${3:-skywalking}"

show_help() {
    cat << 'EOF'

SkyWalking Unified Monitoring Manager
=====================================

Usage: ./scripts/monitoring.sh <service> [action] [namespace]

Services:
  general-service    - Demo instrumented apps (Java, Python)
  service-mesh       - Istio/Envoy ALS monitoring
  kubernetes         - K8s cluster monitoring
  cilium             - Cilium eBPF networking
  infrastructure     - Linux host monitoring
  aws-cloud          - AWS CloudWatch metrics
  browser            - Browser/RUM monitoring
  gateway            - API Gateway (Nginx, APISIX, Kong)
  database           - Database monitoring
  message-queue      - MQ (Kafka, RabbitMQ, etc.)
  flink              - Apache Flink
  self-observability - SkyWalking self-monitoring
  all                - List all services

Actions:
  enable   - Deploy monitoring (default)
  disable  - Remove monitoring
  status   - Check status
  info     - Show setup info

Examples:
  ./scripts/monitoring.sh all                      # List all services
  ./scripts/monitoring.sh kubernetes enable        # Enable K8s monitoring
  ./scripts/monitoring.sh database info            # Show database setup
  ./scripts/monitoring.sh gateway disable          # Disable gateway

Individual scripts can also be called directly:
  ./scripts/kubernetes-monitoring.sh enable
  ./scripts/database-monitoring.sh disable
  ./scripts/gateway-monitoring.sh status

EOF
}

show_all_services() {
    echo ""
    echo -e "${CYAN}Available Monitoring Services${NC}"
    echo "=============================="
    echo ""
    printf "%-20s %-45s %s\n" "SERVICE" "SCRIPT" "UI MENU"
    printf "%-20s %-45s %s\n" "-------" "------" "-------"
    printf "%-20s %-45s %s\n" "general-service" "general-service-monitoring.sh" "General Service"
    printf "%-20s %-45s %s\n" "service-mesh" "service-mesh-monitoring.sh" "Service Mesh"
    printf "%-20s %-45s %s\n" "kubernetes" "kubernetes-monitoring.sh" "Kubernetes"
    printf "%-20s %-45s %s\n" "cilium" "cilium-monitoring.sh" "Cilium"
    printf "%-20s %-45s %s\n" "infrastructure" "infrastructure-monitoring.sh" "Infrastructure"
    printf "%-20s %-45s %s\n" "aws-cloud" "aws-cloud-monitoring.sh" "AWS Cloud"
    printf "%-20s %-45s %s\n" "browser" "browser-monitoring.sh" "Browser"
    printf "%-20s %-45s %s\n" "gateway" "gateway-monitoring.sh" "Gateway"
    printf "%-20s %-45s %s\n" "database" "database-monitoring.sh" "Database"
    printf "%-20s %-45s %s\n" "message-queue" "message-queue-monitoring.sh" "MQ"
    printf "%-20s %-45s %s\n" "flink" "flink-monitoring.sh" "Flink"
    printf "%-20s %-45s %s\n" "self-observability" "self-observability-monitoring.sh" "SkyWalking"
    echo ""
    echo "Usage:"
    echo "  ./scripts/monitoring.sh <service> [enable|disable|status|info]"
    echo "  ./scripts/<service>-monitoring.sh [enable|disable|status|info]"
    echo ""
}

# Map service name to script
get_script_name() {
    local service="$1"
    case "${service}" in
        general-service)    echo "general-service-monitoring.sh" ;;
        service-mesh)       echo "service-mesh-monitoring.sh" ;;
        kubernetes)         echo "kubernetes-monitoring.sh" ;;
        cilium)             echo "cilium-monitoring.sh" ;;
        infrastructure)     echo "infrastructure-monitoring.sh" ;;
        aws-cloud)          echo "aws-cloud-monitoring.sh" ;;
        browser)            echo "browser-monitoring.sh" ;;
        gateway)            echo "gateway-monitoring.sh" ;;
        database)           echo "database-monitoring.sh" ;;
        message-queue)      echo "message-queue-monitoring.sh" ;;
        flink)              echo "flink-monitoring.sh" ;;
        self-observability) echo "self-observability-monitoring.sh" ;;
        *) echo "" ;;
    esac
}

# Main routing
case "${SERVICE}" in
    all)
        show_all_services
        ;;
    help)
        show_help
        ;;
    general-service|service-mesh|kubernetes|cilium|infrastructure|aws-cloud|browser|gateway|database|message-queue|flink|self-observability)
        script_name="$(get_script_name "${SERVICE}")"
        script_path="${SCRIPT_DIR}/${script_name}"

        if [[ ! -x "${script_path}" ]]; then
            echo -e "${RED}[ERROR]${NC} Script not found or not executable: ${script_path}"
            exit 1
        fi

        # Call the individual script
        exec "${script_path}" "${ACTION}" "${NAMESPACE}"
        ;;
    *)
        echo -e "${RED}[ERROR]${NC} Unknown service: ${SERVICE}"
        echo ""
        echo "Available services:"
        echo "  general-service, service-mesh, kubernetes, cilium, infrastructure,"
        echo "  aws-cloud, browser, gateway, database, message-queue, flink,"
        echo "  self-observability, all"
        echo ""
        exit 1
        ;;
esac
