#!/bin/bash
# =============================================================================
# Apache SkyWalking - Start All Services
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Paths
BANYANDB_HOME="$PROJECT_DIR/banyandb"
SKYWALKING_HOME="$PROJECT_DIR/skywalking-oap"
DATA_DIR="$PROJECT_DIR/data"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create directories
mkdir -p "$LOG_DIR" "$PID_DIR" "$DATA_DIR/banyandb"

# =============================================================================
# Start BanyanDB
# =============================================================================
start_banyandb() {
    log_info "Starting BanyanDB..."

    if [[ ! -f "$BANYANDB_HOME/banyand" ]]; then
        log_error "BanyanDB not installed. Run install/install-banyandb.sh first."
        exit 1
    fi

    # Check if already running
    if [[ -f "$PID_DIR/banyandb.pid" ]]; then
        PID=$(cat "$PID_DIR/banyandb.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warn "BanyanDB already running (PID: $PID)"
            return 0
        fi
    fi

    # Start BanyanDB in standalone mode
    nohup "$BANYANDB_HOME/banyand" standalone \
        --data-path="$DATA_DIR/banyandb" \
        > "$LOG_DIR/banyandb.log" 2>&1 &

    echo $! > "$PID_DIR/banyandb.pid"

    log_info "BanyanDB started (PID: $(cat "$PID_DIR/banyandb.pid"))"
    log_info "Waiting for BanyanDB to be ready..."

    # Wait for BanyanDB to be ready
    for i in {1..30}; do
        if curl -s http://localhost:17913/api/healthz > /dev/null 2>&1; then
            log_info "BanyanDB is ready!"
            return 0
        fi
        sleep 2
    done

    log_warn "BanyanDB may not be fully ready yet. Check logs: $LOG_DIR/banyandb.log"
}

# =============================================================================
# Start SkyWalking OAP
# =============================================================================
start_oap() {
    log_info "Starting SkyWalking OAP Server..."

    if [[ ! -f "$SKYWALKING_HOME/bin/oapService.sh" ]]; then
        log_error "SkyWalking not installed. Run install/install-skywalking.sh first."
        exit 1
    fi

    # Check if already running
    if [[ -f "$PID_DIR/oap.pid" ]]; then
        PID=$(cat "$PID_DIR/oap.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warn "OAP Server already running (PID: $PID)"
            return 0
        fi
    fi

    # Set environment variables
    export SW_STORAGE=banyandb
    export SW_STORAGE_BANYANDB_TARGETS=127.0.0.1:17912

    # Start OAP
    cd "$SKYWALKING_HOME"
    nohup bin/oapService.sh > "$LOG_DIR/oap.log" 2>&1 &

    # Get the actual Java process PID
    sleep 3
    OAP_PID=$(pgrep -f "org.apache.skywalking.oap.server.starter.OAPServerStartUp" | head -1)

    if [[ -n "$OAP_PID" ]]; then
        echo "$OAP_PID" > "$PID_DIR/oap.pid"
        log_info "OAP Server started (PID: $OAP_PID)"
    else
        log_warn "OAP Server starting... Check logs: $LOG_DIR/oap.log"
    fi

    # Wait for OAP to be ready
    log_info "Waiting for OAP Server to be ready..."
    for i in {1..60}; do
        if curl -s http://localhost:12800/healthcheck > /dev/null 2>&1; then
            log_info "OAP Server is ready!"
            return 0
        fi
        sleep 2
    done

    log_warn "OAP Server may not be fully ready yet. Check logs: $LOG_DIR/oap.log"
}

# =============================================================================
# Start SkyWalking UI
# =============================================================================
start_ui() {
    log_info "Starting SkyWalking UI..."

    if [[ ! -f "$SKYWALKING_HOME/bin/webappService.sh" ]]; then
        log_error "SkyWalking UI not found."
        exit 1
    fi

    # Check if already running
    if [[ -f "$PID_DIR/ui.pid" ]]; then
        PID=$(cat "$PID_DIR/ui.pid")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warn "UI already running (PID: $PID)"
            return 0
        fi
    fi

    # Start UI
    cd "$SKYWALKING_HOME"
    nohup bin/webappService.sh > "$LOG_DIR/ui.log" 2>&1 &

    # Get the actual Java process PID
    sleep 3
    UI_PID=$(pgrep -f "skywalking-webapp" | head -1)

    if [[ -n "$UI_PID" ]]; then
        echo "$UI_PID" > "$PID_DIR/ui.pid"
        log_info "UI started (PID: $UI_PID)"
    else
        log_warn "UI starting... Check logs: $LOG_DIR/ui.log"
    fi

    # Wait for UI to be ready
    log_info "Waiting for UI to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8080 > /dev/null 2>&1; then
            log_info "UI is ready!"
            return 0
        fi
        sleep 2
    done

    log_warn "UI may not be fully ready yet. Check logs: $LOG_DIR/ui.log"
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  Starting Apache SkyWalking Stack"
    echo "=============================================="
    echo ""

    start_banyandb
    echo ""

    start_oap
    echo ""

    start_ui
    echo ""

    echo "=============================================="
    echo "  SkyWalking Stack Started!"
    echo "=============================================="
    echo ""
    echo "Services:"
    echo "  - BanyanDB:   http://localhost:17913 (gRPC: 17912)"
    echo "  - OAP Server: gRPC=11800, HTTP=12800"
    echo "  - UI:         http://localhost:8080"
    echo ""
    echo "Logs: $LOG_DIR/"
    echo ""
    echo "To check status: ./scripts/status.sh"
    echo "To stop all:     ./scripts/stop-all.sh"
}

main "$@"
