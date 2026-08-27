#!/usr/bin/env bash
set -euo pipefail

# Pixie installation via Helm
# Docs: https://docs.px.dev/installing-pixie/install-schemes/helm/

DEPLOY_KEY="${PIXIE_DEPLOY_KEY:-}"

if [[ -z "$DEPLOY_KEY" ]]; then
  echo "ERROR: Set PIXIE_DEPLOY_KEY env var before running."
  echo "  Create one at: https://work.withpixie.ai/admin/deployment-keys"
  echo "  Or via CLI:    px deploy-key create"
  exit 1
fi

echo "=== Pixie Helm Install ==="

# --- Add Pixie Helm repo ---
echo "[1/3] Adding Pixie operator Helm repo..."
helm repo add pixie-operator https://pixie-operator-charts.storage.googleapis.com
helm repo update

# --- Deploy Pixie (operator-managed) ---
echo "[2/3] Deploying Pixie via Helm..."
helm install pixie pixie-operator/pixie-operator-chart \
  --set deployKey="$DEPLOY_KEY" \
  --set clusterName="$(kubectl config current-context)" \
  --namespace pl \
  --create-namespace

echo "[3/3] Waiting for pods..."
kubectl -n pl rollout status daemonset/vizier-pem --timeout=300s || true

echo ""
echo "=== Pixie deployed via Helm ==="
echo "Namespaces: pl, px-operator, olm"
echo ""
echo "# Non-operator alternative:"
echo "# helm install pixie pixie-operator/pixie-operator-chart \\"
echo "#   --set deployKey=\$PIXIE_DEPLOY_KEY \\"
echo "#   --set clusterName=\$(kubectl config current-context) \\"
echo "#   --set deployOLM=false \\"
echo "#   --set useOperator=false \\"
echo "#   --namespace pl --create-namespace"
