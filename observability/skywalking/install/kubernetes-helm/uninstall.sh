#!/bin/bash
# =============================================================================
# Apache SkyWalking - Kubernetes Helm Uninstall Script
# =============================================================================

set -e

NAMESPACE="${NAMESPACE:-skywalking}"
RELEASE_NAME="${RELEASE_NAME:-skywalking}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo "=============================================="
echo "  SkyWalking Helm Uninstall"
echo "=============================================="
echo ""

log_info "Uninstalling SkyWalking release: $RELEASE_NAME"

# Uninstall Helm release
helm uninstall "$RELEASE_NAME" --namespace "$NAMESPACE" 2>/dev/null || true

# Delete PVCs (optional)
read -p "Delete persistent volume claims? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Deleting PVCs..."
    kubectl delete pvc -l app=skywalking -n "$NAMESPACE" 2>/dev/null || true
fi

# Delete namespace (optional)
read -p "Delete namespace '$NAMESPACE'? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Deleting namespace..."
    kubectl delete namespace "$NAMESPACE" 2>/dev/null || true
fi

echo ""
log_info "Uninstall complete!"
