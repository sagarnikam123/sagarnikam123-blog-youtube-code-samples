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
echo ""
echo "🔗 Core URLs:"
echo "  • Ready Check: $LOKI_ADDR/ready"
echo "  • Services: $LOKI_ADDR/services"
echo "  • Web UI: $LOKI_ADDR/ui/"
echo "  • Ring Status: $LOKI_ADDR/ring"
echo "  • Configuration: $LOKI_ADDR/config"
echo "  • Metrics: $LOKI_ADDR/metrics"
echo "  • Memberlist: $LOKI_ADDR/memberlist"

echo ""
echo "🔗 API URLs:"
echo "  • Query API: $LOKI_ADDR/loki/api/v1/query_range"
echo "  • Labels API: $LOKI_ADDR/loki/api/v1/labels"
echo "  • Label Values: $LOKI_ADDR/loki/api/v1/label/<label>/values"
echo "  • Push API: $LOKI_ADDR/loki/api/v1/push"
echo ""
echo "🔗 Other UI URLs:"
echo "  • UI Nodes: $LOKI_ADDR/ui/nodes"
echo "  • UI Rings: $LOKI_ADDR/ui/rings"
echo ""
echo "🛑 Press Ctrl+C to stop Loki"
echo ""
loki-3.5.5 -config.file="$LOKI_CONFIG" -config.expand-env=true
