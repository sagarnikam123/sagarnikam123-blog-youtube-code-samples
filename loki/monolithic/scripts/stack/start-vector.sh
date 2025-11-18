#!/bin/bash

# Vector Start Script for Loki Monolithic Stack
# Starts Vector with local configuration

# Get script directory and set working directory to monolithic root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONOLITHIC_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$MONOLITHIC_DIR"

# Configuration file
VECTOR_CONFIG="log-scrapers/vector/vector-local-fs-json-loki.yaml"

# Data directory
VECTOR_DATA_DIR="${VECTOR_DATA_DIR:-$HOME/data/vector}"
mkdir -p "$VECTOR_DATA_DIR/buffer" "$VECTOR_DATA_DIR/data"

echo "🚀 Starting Vector..."
echo "⚙️  Configuration: $VECTOR_CONFIG"
echo "💾 Data directory: $VECTOR_DATA_DIR"
echo "🌐 API available at: http://127.0.0.1:8686"
echo "🛑 Press Ctrl+C to stop Vector"
echo ""

# Check if Vector is installed
if ! command -v vector &> /dev/null; then
    echo "❌ Vector not found. Please install it first:"
    echo "   See: log-scrapers/vector/INSTALL.md"
    exit 1
fi

# Start Vector
vector \
  --config "$VECTOR_CONFIG" \
  --require-healthy
