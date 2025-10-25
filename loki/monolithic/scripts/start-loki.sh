#!/bin/bash

# Loki Monolithic Start Script
# Edit LOKI_CONFIG variable below to change configuration

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONOLITHIC_DIR="$(dirname "$SCRIPT_DIR")"
cd "$MONOLITHIC_DIR"

# 🔧 EDIT THIS VARIABLE TO CHANGE CONFIG:
LOKI_CONFIG="v3.x/loki-3.x-most-rings-enabled.yaml"

# Available options:
# v2.x/loki-2.x-prod-local-storage.yaml
# v2.x/loki-2.x-prod-s3-memberlist.yaml
# v3.x/loki-3.x-dev-local-storage.yaml
# v3.x/loki-3.x-prod-s3-storage.yaml
# v3.x/loki-3.x-most-rings-enabled.yaml
# v3.x/loki-3.x-minimal-working.yaml
# v3.x/loki-3.x-simple-working.yaml

export LOKI_ADDR="http://127.0.0.1:3100"
echo "🚀 Starting Loki with: $LOKI_CONFIG"
echo "🌐 Available at: $LOKI_ADDR"
loki-3.5.5 -config.file="$LOKI_CONFIG" -config.expand-env=true
