#!/bin/bash

# Fluent Bit Start Script
# Edit FLUENT_BIT_CONFIG variable below to change configuration

# Get script directory and navigate to fluent-bit configs
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONOLITHIC_DIR="$(dirname "$SCRIPT_DIR")"
FLUENT_BIT_DIR="$MONOLITHIC_DIR/log-scrapers/fluent-bit"
cd "$FLUENT_BIT_DIR"

# 🔧 EDIT THIS VARIABLE TO CHANGE CONFIG:
FLUENT_BIT_CONFIG="fluent-bit-json-parsing.yaml"

# Available options:
# fluent-bit-json-parsing.yaml          - JSON log parsing and forwarding
# fluent-bit-filesystem-storage.yaml    - Basic filesystem storage
# fluent-bit-production-buffering.conf  - Production with persistent buffering
# fluent-bit-loki-canary.conf           - Loki Canary log monitoring

echo "🚀 Starting Fluent Bit with: $FLUENT_BIT_CONFIG"
echo "📊 Metrics available at: http://127.0.0.1:2020/metrics"
echo "🛑 Press Ctrl+C to stop Fluent Bit"
echo ""

fluent-bit --config "$FLUENT_BIT_CONFIG"
