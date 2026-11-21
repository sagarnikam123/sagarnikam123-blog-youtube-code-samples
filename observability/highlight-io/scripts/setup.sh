#!/usr/bin/env bash
# Highlight.io setup script for benchmarking
# Uses official hobby deployment from GitHub
set -euo pipefail

INSTALL_DIR="./highlight-install"

echo "=== Highlight.io Benchmark Setup ==="

if [ -d "$INSTALL_DIR" ]; then
  echo "Installation directory already exists: $INSTALL_DIR"
  echo "To re-install: rm -rf $INSTALL_DIR && ./setup.sh"
  exit 0
fi

# Clone official repo
echo "Cloning Highlight.io repository..."
git clone --depth 1 --recurse-submodules \
  https://github.com/highlight/highlight.git "$INSTALL_DIR"

cd "$INSTALL_DIR/docker"

echo ""
echo "=== Setup complete ==="
echo ""
echo "To start Highlight.io hobby deployment:"
echo "  cd $INSTALL_DIR/docker"
echo "  docker compose -f compose.hobby.yml up -d"
echo ""
echo "Or use the one-liner from official docs:"
echo "  curl -fsS https://raw.githubusercontent.com/highlight/highlight/main/deploy/hobby.sh | bash"
echo ""
echo "Access: http://localhost:3000 (or http://localhost:8080)"
echo "OTLP gRPC: localhost:4317"
echo "OTLP HTTP: localhost:4318"
