#!/usr/bin/env bash
set -euo pipefail

# Pixie local dev setup with minikube
# Docs: https://docs.px.dev/installing-pixie/setting-up-k8s/minikube-setup/

# ponytail: driver selection — qemu2 on macOS (hyperkit removed from brew, x86-only), kvm2 on Linux
OS="$(uname -s)"
case "$OS" in
  Darwin) DRIVER="qemu2" ;;
  Linux)  DRIVER="kvm2" ;;
  *)      echo "Unsupported OS: $OS"; exit 1 ;;
esac

CLUSTER_NAME="${1:-pixie-dev}"
CPUS="${MINIKUBE_CPUS:-4}"
MEMORY="${MINIKUBE_MEMORY:-8192}"

echo "=== Pixie minikube setup (driver=$DRIVER) ==="

# --- Preflight ---
for cmd in minikube kubectl; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd not found. Install it first."
    exit 1
  fi
done

# --- Create cluster ---
echo "[1/2] Creating minikube cluster '$CLUSTER_NAME'..."
minikube start \
  --driver="$DRIVER" \
  --cpus="$CPUS" \
  --memory="$MEMORY" \
  -p "$CLUSTER_NAME"

echo "[2/2] Verifying cluster..."
kubectl get nodes

echo ""
echo "=== Cluster ready ==="
echo "Next: cd ../cli && ./install.sh"
echo ""
echo "# To delete: minikube delete -p $CLUSTER_NAME"
