#!/bin/bash

# Fluent Bit Start Script
# Edit FLUENT_BIT_CONFIG variable below to change configuration

# Get script directory and calculate paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# install/binary -> loki root
LOKI_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 🔧 EDIT THIS VARIABLE TO CHANGE CONFIG:
FLUENT_BIT_CONFIG="$LOKI_ROOT/log-scrapers/fluent-bit/yaml/fluent-bit-fuzzy-train-loki.yaml"

# Available configs in log-scrapers/fluent-bit/:
#
# YAML files (recommended):
#   yaml/fluent-bit-fuzzy-train-loki.yaml          - Fuzzy-train logs to Loki (JSON, logfmt, Apache)
#   yaml/fluent-bit-loki-minimal.yaml              - Minimal Loki configuration
#   yaml/fluent-bit-json-parsing.yaml              - JSON log parsing
#   yaml/fluent-bit-filesystem-buffering.yaml      - Filesystem buffering
#   yaml/fluent-bit-dummy-stdout-config.yaml       - Dummy data to stdout
#
# CONF files (classic format):
#   conf/fluent-bit-loki-minimal.conf              - Minimal Loki configuration
#   conf/fluent-bit-local-config.conf              - Local file collection
#   conf/fluent-bit-local-dummy-config.conf        - Dummy data generation
#   conf/fluent-bit-loki-canary.conf               - Loki Canary monitoring
#   conf/fluent-bit-production-buffering.conf      - Production buffering
#   conf/fluent-bit-var-log-loki.conf              - System logs to Loki

echo "🚀 Starting Fluent Bit with: $FLUENT_BIT_CONFIG"
echo "📊 Metrics available at: http://127.0.0.1:2020/metrics"
echo "🛑 Press Ctrl+C to stop Fluent Bit"
echo ""

# Check if config exists
if [ ! -f "$FLUENT_BIT_CONFIG" ]; then
    echo "❌ Config not found: $FLUENT_BIT_CONFIG"
    echo "Available configs:"
    ls -1 "$LOKI_ROOT/log-scrapers/fluent-bit/yaml/" 2>/dev/null
    ls -1 "$LOKI_ROOT/log-scrapers/fluent-bit/conf/" 2>/dev/null
    exit 1
fi

# Check if fluent-bit binary exists
if ! command -v fluent-bit &> /dev/null; then
    echo "❌ Fluent Bit not found. Install with:"
    echo "   brew install fluent-bit"
    exit 1
fi

fluent-bit --config "$FLUENT_BIT_CONFIG"
