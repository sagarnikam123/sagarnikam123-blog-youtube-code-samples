#!/bin/bash

# Loki Monolithic Start Script
# Edit LOKI_CONFIG variable below to change configuration

# Get script directory and set working directory to monolithic root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONOLITHIC_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$MONOLITHIC_DIR"

# 🔧 EDIT THIS VARIABLE TO CHANGE CONFIG:
LOKI_CONFIG="configs/v3.x/v3.5.x/loki-3.5.x-ui-minio-thanos-memberlist.yaml"

# Available options:
# configs/v3.x/v3.5.x/loki-3.5.x-minimal-official-github.yaml
# configs/v3.x/v3.5.x/loki-3.5.x-minimal-ui-only.yaml
# configs/v3.x/v3.5.x/loki-3.5.x-ui-filesystem-inmemory.yaml
# configs/v3.x/v3.5.x/loki-3.5.x-ui-minio-thanos-memberlist.yaml

# configs/v3.x/v3.5.x/loki-3.5.x-most-rings-enabled.yaml
# configs/v3.x/v3.5.x/loki-3.x-prod-minio-memberlist.yaml
# configs/v3.x/v3.5.x/loki-3.5.x-prod-s3-storage.yaml


export LOKI_ADDR="http://127.0.0.1:3100"
echo "🚀 Starting Loki with: $LOKI_CONFIG"
echo "🌐 Web UI: $LOKI_ADDR/ui"
echo "🔍 Ring Status: $LOKI_ADDR/ring"
echo "⚙️  Config: $LOKI_ADDR/config"
echo "📈 Metrics: $LOKI_ADDR/metrics"
echo "🛑 Press Ctrl+C to stop Loki"
echo ""
loki-3.5.5 -config.file="$LOKI_CONFIG" -config.expand-env=true
