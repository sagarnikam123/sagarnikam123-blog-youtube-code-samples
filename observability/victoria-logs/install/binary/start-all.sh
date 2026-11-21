#!/bin/bash
# =============================================================================
# Start all VictoriaLogs PoC services (binary mode)
# =============================================================================
# Usage: ./start-all.sh
# Stop:  Press Ctrl+C (kills all background processes)
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create data directories
mkdir -p data/vlogs data/vm data/alertmanager data/logs

echo "🚀 Starting VictoriaLogs PoC (binary mode)..."
echo ""

# Track PIDs for cleanup
PIDS=()

cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    echo "✅ All services stopped."
}
trap cleanup EXIT INT TERM

# --- VictoriaLogs ---
echo "📦 Starting VictoriaLogs (port 9428)..."
./bin/victoria-logs-prod \
    -storageDataPath=./data/vlogs \
    -retentionPeriod=7d \
    -httpListenAddr=:9428 \
    > ./data/vlogs.log 2>&1 &
PIDS+=($!)
sleep 2

# --- VictoriaMetrics ---
echo "📦 Starting VictoriaMetrics (port 8428)..."
./bin/victoria-metrics-prod \
    -storageDataPath=./data/vm \
    -retentionPeriod=7d \
    -httpListenAddr=:8428 \
    > ./data/vm.log 2>&1 &
PIDS+=($!)
sleep 2

# --- AlertManager ---
echo "📦 Starting AlertManager (port 9093)..."
alertmanager \
    --config.file=./config/alertmanager.yaml \
    --storage.path=./data/alertmanager \
    > ./data/alertmanager.log 2>&1 &
PIDS+=($!)
sleep 1

# --- vmalert ---
echo "📦 Starting vmalert (port 8880)..."
./bin/vmalert-prod \
    -rule=./config/alert-rules.yaml \
    -datasource.url=http://localhost:9428 \
    -notifier.url=http://localhost:9093 \
    -remoteWrite.url=http://localhost:8428 \
    -remoteRead.url=http://localhost:8428 \
    -rule.defaultRuleType=vlogs \
    -evaluationInterval=30s \
    -httpListenAddr=:8880 \
    > ./data/vmalert.log 2>&1 &
PIDS+=($!)
sleep 1

# --- Fake Log Generator (flog) ---
echo "📦 Starting flog (fake log generator)..."
flog -f json -d 2s -l -w -o ./data/logs/app.log &
PIDS+=($!)
sleep 1

# --- Fluent Bit ---
echo "📦 Starting Fluent Bit..."
fluent-bit -c ./config/fluent-bit.conf \
    > ./data/fluentbit.log 2>&1 &
PIDS+=($!)
sleep 1

# --- Webhook Receiver ---
echo "📦 Starting webhook receiver (port 5001)..."
python3 ./webhook-receiver.py &
PIDS+=($!)

echo ""
echo "=============================================="
echo "✅ All services running!"
echo "=============================================="
echo ""
echo "  VictoriaLogs VMUI:  http://localhost:9428/select/vmui/"
echo "  VictoriaMetrics:    http://localhost:8428/vmui/"
echo "  AlertManager:       http://localhost:9093"
echo "  vmalert:            http://localhost:8880"
echo "  Webhook receiver:   http://localhost:5001"
echo ""
echo "  Logs dir:           ./data/logs/"
echo "  Service logs:       ./data/*.log"
echo ""
echo "  Press Ctrl+C to stop all services"
echo "=============================================="
echo ""

# Wait for all background processes
wait
