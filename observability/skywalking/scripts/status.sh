#!/bin/bash
# =============================================================================
# Apache SkyWalking - Service Status Check
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

PID_DIR="$PROJECT_DIR/pids"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# =============================================================================
# Check Service Status
# =============================================================================
check_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    local health_url=$2
    local port=$3

    printf "%-15s" "$service_name:"

    # Check PID
    if [[ -f "$pid_file" ]]; then
        PID=$(cat "$pid_file")
        if ps -p "$PID" > /dev/null 2>&1; then
            printf "${GREEN}Running${NC} (PID: $PID)"

            # Check health endpoint if provided
            if [[ -n "$health_url" ]]; then
                if curl -s "$health_url" > /dev/null 2>&1; then
                    printf " - ${GREEN}Healthy${NC}"
                else
                    printf " - ${YELLOW}Starting${NC}"
                fi
            fi
            echo ""
            return 0
        fi
    fi

    # Check by port
    if [[ -n "$port" ]]; then
        if lsof -i ":$port" > /dev/null 2>&1; then
            printf "${YELLOW}Running${NC} (port $port in use)"
            echo ""
            return 0
        fi
    fi

    printf "${RED}Stopped${NC}"
    echo ""
    return 1
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  Apache SkyWalking - Service Status"
    echo "=============================================="
    echo ""

    check_service "BanyanDB" "http://localhost:17913/api/healthz" "17912"
    check_service "OAP Server" "http://localhost:12800/healthcheck" "11800"
    check_service "UI" "http://localhost:8080" "8080"

    echo ""
    echo "----------------------------------------------"
    echo "Endpoints:"
    echo "  UI:         http://localhost:8080"
    echo "  OAP gRPC:   localhost:11800"
    echo "  OAP HTTP:   http://localhost:12800"
    echo "  BanyanDB:   localhost:17912"
    echo "----------------------------------------------"
    echo ""
    echo "Logs: $PROJECT_DIR/logs/"
}

main "$@"
