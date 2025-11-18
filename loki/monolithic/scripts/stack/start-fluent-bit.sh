#!/bin/bash

# Fluent Bit Start Script
# Edit FLUENT_BIT_CONFIG variable below to change configuration

# Get script directory and set working directory to monolithic root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONOLITHIC_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$MONOLITHIC_DIR"

# 🔧 EDIT THIS VARIABLE TO CHANGE CONFIG:
FLUENT_BIT_CONFIG="log-scrapers/fluent-bit/yaml/fluent-bit-loki-minimal.yaml"

# Available options:
# CONF files (recommended):
# log-scrapers/fluent-bit/conf/fluent-bit-loki-minimal.conf              - Minimal Loki configuration
# log-scrapers/fluent-bit/conf/fluent-bit-local-config.conf              - Local file collection
# log-scrapers/fluent-bit/conf/fluent-bit-local-dummy-config.conf        - Dummy data generation
# log-scrapers/fluent-bit/conf/fluent-bit-local-storage-filesystem-config.conf - Filesystem storage
# log-scrapers/fluent-bit/conf/fluent-bit-loki-canary.conf               - Loki Canary monitoring
# log-scrapers/fluent-bit/conf/fluent-bit-production-buffering.conf      - Production buffering
# log-scrapers/fluent-bit/conf/fluent-bit-var-log-loki.conf              - System logs to Loki
#
# YAML files (alternative):
# log-scrapers/fluent-bit/yaml/fluent-bit-json-parsing.yaml              - JSON log parsing
# log-scrapers/fluent-bit/yaml/fluent-bit-filesystem-storage.yaml        - Basic filesystem storage
# log-scrapers/fluent-bit/yaml/fluent-bit-dummy-local-config.yaml        - Dummy data (YAML)
# log-scrapers/fluent-bit/yaml/fluent-bit-loki-minimal.yaml              - Minimal Loki (YAML)

echo "🚀 Starting Fluent Bit with: $FLUENT_BIT_CONFIG"
echo "📊 Metrics available at: http://127.0.0.1:2020/metrics"
echo "🛑 Press Ctrl+C to stop Fluent Bit"
echo ""

fluent-bit --config "$FLUENT_BIT_CONFIG"
