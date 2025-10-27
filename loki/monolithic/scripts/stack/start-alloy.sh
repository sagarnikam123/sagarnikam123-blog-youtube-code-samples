#!/bin/bash

# Grafana Alloy Start Script for Loki Monolithic Stack
# Starts Alloy with local configuration

# Get script directory and set working directory to monolithic root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONOLITHIC_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$MONOLITHIC_DIR"

# Configuration file
ALLOY_CONFIG="log-scrapers/alloy/alloy-monolithic-local.alloy"

# Data directory
ALLOY_DATA_DIR="${ALLOY_DATA_DIR:-$HOME/data/alloy}"
mkdir -p "$ALLOY_DATA_DIR"

echo "🚀 Starting Grafana Alloy..."
echo "📁 Working directory: $(pwd)"
echo "⚙️  Configuration: $ALLOY_CONFIG"
echo "💾 Data directory: $ALLOY_DATA_DIR"
echo "🛑 Press Ctrl+C to stop Alloy"
echo ""

# Check if Alloy is installed
if ! command -v alloy &> /dev/null; then
    echo "❌ Grafana Alloy not found. Please install it first:"
    echo "   See: log-scrapers/alloy/INSTALL.md"
    exit 1
fi

# Start Alloy
alloy run \
  --config.file="$ALLOY_CONFIG" \
  --storage.path="$ALLOY_DATA_DIR" \
  --server.http.listen-addr="127.0.0.1:12345"
