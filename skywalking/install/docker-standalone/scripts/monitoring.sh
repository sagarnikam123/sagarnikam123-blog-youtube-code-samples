#!/bin/bash
# =============================================================================
# SkyWalking Monitoring Features Management Script
# =============================================================================
# Usage:
#   ./scripts/monitoring.sh status              - Show current status
#   ./scripts/monitoring.sh enable <features>   - Enable monitoring features
#   ./scripts/monitoring.sh disable             - Disable all monitoring
#   ./scripts/monitoring.sh list                - List available features
#
# Examples:
#   ./scripts/monitoring.sh enable mysql redis
#   ./scripts/monitoring.sh enable all
#   ./scripts/monitoring.sh enable kafka postgresql
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Available profiles
AVAILABLE_PROFILES=(
    "mysql"
    "postgresql"
    "redis"
    "mongodb"
    "kafka"
    "rabbitmq"
    "nginx"
    "infrastructure"
)

# =============================================================================
# Helper Functions
# =============================================================================

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

print_header() {
    echo ""
    echo -e "${BLUE}=============================================${NC}"
    echo -e "${BLUE}  SkyWalking Monitoring Manager${NC}"
    echo -e "${BLUE}=============================================${NC}"
    echo ""
}

# =============================================================================
# Commands
# =============================================================================

cmd_list() {
    print_header
    echo "Available monitoring profiles:"
    echo ""
    echo "  Databases:"
    echo "    - mysql         : MySQL/MariaDB monitoring"
    echo "    - postgresql    : PostgreSQL monitoring"
    echo "    - redis         : Redis monitoring"
    echo "    - mongodb       : MongoDB monitoring"
    echo ""
    echo "  Message Queues:"
    echo "    - kafka         : Apache Kafka monitoring"
    echo "    - rabbitmq      : RabbitMQ monitoring"
    echo ""
    echo "  Gateways:"
    echo "    - nginx         : Nginx monitoring"
    echo ""
    echo "  Infrastructure:"
    echo "    - infrastructure: Linux VM monitoring (node-exporter)"
    echo ""
    echo "  Special:"
    echo "    - all           : Enable ALL monitoring features"
    echo "    - monitoring    : Same as 'all'"
    echo ""
}

cmd_status() {
    print_header
    echo "Current container status:"
    echo ""

    cd "$COMPOSE_DIR"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || {
        log_warn "No containers running or docker compose not available"
    }
    echo ""
}

cmd_enable() {
    local features=("$@")

    if [[ ${#features[@]} -eq 0 ]]; then
        log_error "No features specified. Use 'list' to see available features."
        exit 1
    fi

    print_header

    # Build profile arguments
    local profile_args=""

    for feature in "${features[@]}"; do
        case "$feature" in
            all|monitoring)
                profile_args="--profile monitoring"
                log_info "Enabling ALL monitoring features"
                break
                ;;
            mysql|postgresql|redis|mongodb|kafka|rabbitmq|nginx|infrastructure)
                profile_args="$profile_args --profile $feature"
                log_info "Enabling: $feature"
                ;;
            *)
                log_warn "Unknown feature: $feature (skipping)"
                ;;
        esac
    done

    if [[ -z "$profile_args" ]]; then
        log_error "No valid features to enable"
        exit 1
    fi

    echo ""
    log_info "Starting containers..."

    cd "$COMPOSE_DIR"

    # Check if .env exists, if not copy from example
    if [[ ! -f ".env" ]] && [[ -f ".env.example" ]]; then
        log_info "Creating .env from .env.example..."
        cp .env.example .env
    fi

    # Run docker compose with profiles
    docker compose $profile_args up -d

    echo ""
    log_info "Monitoring features enabled!"
    echo ""
    echo "Access SkyWalking UI at: http://localhost:${UI_PORT:-8080}"
    echo ""
    echo "Note: It may take 1-2 minutes for metrics to appear in dashboards."
    echo "      Make sure your target services (MySQL, Redis, etc.) are accessible."
}

cmd_disable() {
    print_header
    log_info "Stopping all monitoring containers..."

    cd "$COMPOSE_DIR"
    docker compose --profile monitoring down

    echo ""
    log_info "All monitoring features disabled"
    echo ""
    echo "Core SkyWalking services are still running."
    echo "To stop everything: docker compose down"
}

cmd_restart() {
    local features=("$@")

    print_header
    log_info "Restarting monitoring services..."

    cd "$COMPOSE_DIR"

    if [[ ${#features[@]} -eq 0 ]] || [[ "${features[0]}" == "all" ]]; then
        docker compose --profile monitoring restart
    else
        for feature in "${features[@]}"; do
            docker compose --profile "$feature" restart
        done
    fi

    log_info "Restart complete"
}

cmd_logs() {
    local service="${1:-otel-collector}"

    cd "$COMPOSE_DIR"
    docker compose logs -f "$service"
}

# =============================================================================
# Usage
# =============================================================================

usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  list                    List available monitoring features"
    echo "  status                  Show current container status"
    echo "  enable <features...>    Enable monitoring features"
    echo "  disable                 Disable all monitoring features"
    echo "  restart [features...]   Restart monitoring services"
    echo "  logs [service]          View logs (default: otel-collector)"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 enable mysql redis"
    echo "  $0 enable all"
    echo "  $0 disable"
    echo "  $0 logs mysqld-exporter"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    local command="${1:-}"
    shift || true

    case "$command" in
        list)
            cmd_list
            ;;
        status)
            cmd_status
            ;;
        enable)
            cmd_enable "$@"
            ;;
        disable)
            cmd_disable
            ;;
        restart)
            cmd_restart "$@"
            ;;
        logs)
            cmd_logs "$@"
            ;;
        -h|--help|help|"")
            usage
            ;;
        *)
            log_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
