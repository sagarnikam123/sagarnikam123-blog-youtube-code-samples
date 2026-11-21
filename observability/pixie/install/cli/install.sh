#!/usr/bin/env bash
set -euo pipefail

# Pixie installation via CLI (recommended)
# Docs: https://docs.px.dev/installing-pixie/install-schemes/cli/

echo "=== Pixie CLI Install ==="

# --- Install the px CLI ---
# Option 1: Install script (easiest)
if ! command -v px &>/dev/null; then
  echo "[1/3] Installing Pixie CLI..."
  bash -c "$(curl -fsSL https://withpixie.ai/install.sh)"
else
  echo "[1/3] Pixie CLI already installed: $(px version)"
fi

# --- Check cluster requirements ---
echo "[2/3] Checking cluster requirements..."
px collect-info || true

# --- Deploy Pixie ---
echo "[3/3] Deploying Pixie to cluster..."
px deploy

echo ""
echo "=== Pixie deployed ==="
echo "Namespaces: pl, px-operator, olm"
echo "Run 'px live' to open the Pixie UI"
