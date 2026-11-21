#!/bin/bash

# Loki Monolithic Start Script
# Edit LOKI_CONFIG variable below to change configuration

# Get script directory and calculate paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# install/binary -> loki root
LOKI_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 🔧 EDIT THIS VARIABLE TO CHANGE CONFIG:
LOKI_CONFIG="$LOKI_ROOT/configs/v3.x/v3.7.x/loki-3.7.x-ui-filesystem-inmemory.yaml"

# Available configs in configs/v3.x/v3.6.x/:
#
# Filesystem storage (no external dependencies):
#   loki-3.6.x-ui-filesystem-inmemory.yaml     - UI + filesystem + inmemory KV
#   loki-3.6.x-minimal-ui-only.yaml            - Minimal with UI enabled
#   loki-3.6.x-minimal-official-github.yaml    - Minimal from official docs
#
# MinIO storage (native client):
#   loki-3.6.x-ui-minio-inmemory.yaml          - UI + MinIO + inmemory KV
#   loki-3.6.x-ui-minio-memberlist.yaml        - UI + MinIO + memberlist (multi-node ready)
#
# MinIO storage (Thanos objstore - recommended):
#   loki-3.6.x-ui-minio-thanos-inmemory.yaml   - UI + MinIO + Thanos + inmemory KV
#   loki-3.6.x-ui-minio-thanos-memberlist.yaml - UI + MinIO + Thanos + memberlist
#
# AWS S3 storage (Thanos objstore):
#   loki-3.6.x-ui-s3-thanos-inmemory.yaml      - UI + AWS S3 + Thanos + inmemory KV
#   loki-3.6.x-ui-s3-thanos-memberlist.yaml    - UI + AWS S3 + Thanos + memberlist

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

# Check if config exists
if [ ! -f "$LOKI_CONFIG" ]; then
    echo "❌ Config not found: $LOKI_CONFIG"
    echo "Available configs:"
    ls -1 "$LOKI_ROOT/configs/v3.x/v3.7.x/"
    exit 1
fi

# Check if loki binary exists
if command -v loki-3.6.3 &> /dev/null; then
    LOKI_BIN="loki-3.6.3"
elif command -v loki &> /dev/null; then
    LOKI_BIN="loki"
elif [[ -x "$HOME/loki-stack/loki/loki" ]]; then
    LOKI_BIN="$HOME/loki-stack/loki/loki"
else
    echo "❌ Loki binary not found. Install with:"
    echo "   ./install.sh"
    echo "   # or: brew install loki"
    echo "   # or download from https://github.com/grafana/loki/releases"
    exit 1
fi

$LOKI_BIN -config.file="$LOKI_CONFIG" -config.expand-env=true
