#!/usr/bin/env bash
set -euo pipefail

# Pixie installation via extracted YAML manifests
# Docs: https://docs.px.dev/installing-pixie/install-schemes/yaml/

DEPLOY_KEY="${PIXIE_DEPLOY_KEY:-}"
EXTRACT_DIR="${1:-./pixie-yamls}"

if [[ -z "$DEPLOY_KEY" ]]; then
  echo "ERROR: Set PIXIE_DEPLOY_KEY env var before running."
  echo "  Create one at: https://work.withpixie.ai/admin/deployment-keys"
  echo "  Or via CLI:    px deploy-key create"
  exit 1
fi

# Ensure px CLI is installed
if ! command -v px &>/dev/null; then
  echo "ERROR: px CLI required. Run: bash -c \"\$(curl -fsSL https://withpixie.ai/install.sh)\""
  exit 1
fi

echo "=== Pixie YAML Install ==="

# --- Extract manifests ---
echo "[1/3] Extracting Pixie manifests to $EXTRACT_DIR..."
px deploy \
  --extract_yaml "$EXTRACT_DIR" \
  --deploy_key "$DEPLOY_KEY"

echo "[2/3] Manifests extracted. Review before applying:"
ls -la "$EXTRACT_DIR"

# --- Apply manifests ---
echo "[3/3] Applying manifests..."
kubectl apply --recursive -f "$EXTRACT_DIR"

echo ""
echo "=== Pixie deployed via YAML ==="
echo "Namespaces: pl, px-operator, olm"
echo "Verify: px get viziers"
