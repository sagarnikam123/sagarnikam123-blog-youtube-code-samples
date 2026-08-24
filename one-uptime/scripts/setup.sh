#!/usr/bin/env bash
# OneUptime setup script for benchmarking
# OneUptime has its own complex docker-compose.yml (many microservices).
# This script clones the official repo and starts it.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
INSTALL_DIR="${PLATFORM_DIR}/install/docker-compose/standalone/oneuptime-install"

echo "=== OneUptime Benchmark Setup ==="

if [ -d "$INSTALL_DIR" ]; then
  echo "Installation directory already exists: $INSTALL_DIR"
  echo "To re-install: rm -rf $INSTALL_DIR && ./scripts/setup.sh"
  exit 0
fi

# Clone official release branch
echo "Cloning OneUptime release branch..."
git clone --depth 1 --single-branch --branch release \
  https://github.com/OneUptime/oneuptime.git "$INSTALL_DIR"

cd "$INSTALL_DIR"

# Copy config
cp config.example.env config.env

# Adjust port if needed (default is port 80)
# sed -i'' "s/HTTP_PORT=80/HTTP_PORT=3400/" config.env

echo ""
echo "=== Setup complete ==="
echo ""
echo "To start OneUptime:"
echo "  cd $INSTALL_DIR"
echo "  npm start"
echo ""
echo "Or without npm:"
echo "  cd $INSTALL_DIR"
echo "  export \$(grep -v '^#' config.env | xargs) && docker compose up --remove-orphans -d"
echo ""
echo "Access: http://localhost (register a new account on first use)"
echo ""
echo "OTLP Endpoint: http://localhost/otlp"
echo "  - gRPC: port 4317 (exposed by the ingest service)"
echo "  - HTTP: port 4318 (exposed by the ingest service)"
