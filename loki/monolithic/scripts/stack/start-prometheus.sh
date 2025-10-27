#!/bin/bash

# Prometheus Start Script for Loki Monolithic Stack
# Starts Prometheus with proper configuration

# Get script directory and set working directory to monolithic root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONOLITHIC_DIR="$(dirname "$SCRIPT_DIR")"
cd "$MONOLITHIC_DIR"

# Configuration file
PROMETHEUS_CONFIG="observability/prometheus/configs/prometheus.yml"

# Data directory - use $HOME/data for persistence or /tmp for temporary
PROMETHEUS_DATA_DIR="${PROMETHEUS_DATA_DIR:-$HOME/data/prometheus/data}"

# Create data directory if it doesn't exist
mkdir -p "$PROMETHEUS_DATA_DIR"

echo "🚀 Starting Prometheus..."
echo "📊 Web UI available at: http://127.0.0.1:9090"
echo "📁 Working directory: $(pwd)"
echo "⚙️  Configuration: $PROMETHEUS_CONFIG"
echo "💾 Data directory: $PROMETHEUS_DATA_DIR"
echo "🛑 Press Ctrl+C to stop Prometheus"
echo ""

# Start Prometheus from installed location
cd "$HOME/loki-stack/prometheus"
./prometheus \
  --config.file="$MONOLITHIC_DIR/$PROMETHEUS_CONFIG" \
  --storage.tsdb.path="$PROMETHEUS_DATA_DIR" \
  --storage.tsdb.retention.time=7d \
  --storage.tsdb.retention.size=1GB \
  --web.listen-address="0.0.0.0:9090" \
  --web.enable-lifecycle \
  --web.enable-admin-api \
  --log.level=info
