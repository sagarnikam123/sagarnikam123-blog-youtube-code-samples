#!/bin/bash
# =============================================================================
# Apache SkyWalking - Stop All Services
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

PID_DIR="$PROJECT_DIR/pids"
SKYWALKING_HOME="$PROJECT_DIR/skywalking-oap"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Stop Service by PID file
# =============================================================================
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"

    if [[ -f "$pid_file" ]]; then
        PID=$(cat "$pid_file")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "Stopping $service_name (PID: $PID)..."
            kill "$PID" 2>/dev/null || true

            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    log_info "$service_name stopped"
                    rm -f "$pid_file"
                    return 0
                fi
                sleep 1
            done

            # Force kill if still running
            log_warn "$service_name did not stop gracefully, forcing..."
            kill -9 "$PID" 2>/dev/null || true
            rm -f "$pid_file"
        else
            log_info "$service_name not running (stale PID file)"
            rm -f "$pid_file"
        fi
    else
        log_info "$service_name not running (no PID file)"
    fi
}

# =============================================================================
# Stop by process name (fallback)
# =============================================================================
stop_by_process() {
    local process_pattern=$1
    local service_name=$2

    PIDS=$(pgrep -f "$process_pattern" 2>/dev/null || true)

    if [[ -n "$PIDS" ]]; then
        log_info "Stopping $service_name processes..."
        echo "$PIDS" | xargs kill 2>/dev/null || true
        sleep 2

        # Force kill remaining
        PIDS=$(pgrep -f "$process_pattern" 2>/dev/null || true)
        if [[ -n "$PIDS" ]]; then
            echo "$PIDS" | xargs kill -9 2>/dev/null || true
        fi
    fi
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  Stopping Apache SkyWalking Stack"
    echo "=============================================="
    echo ""

    # Stop UI first
    log_info "Stopping SkyWalking UI..."
    stop_service "ui"
    stop_by_process "skywalking-webapp" "UI"

    # Stop OAP
    log_info "Stopping SkyWalking OAP..."
    stop_service "oap"
    stop_by_process "OAPServerStartUp" "OAP"

    # Stop BanyanDB last
    log_info "Stopping BanyanDB..."
    stop_service "banyandb"
    stop_by_process "banyand" "BanyanDB"

    echo ""
    log_info "All services stopped!"
}

main "$@"
