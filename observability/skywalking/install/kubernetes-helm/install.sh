#!/bin/bash
# =============================================================================
# Apache SkyWalking - Kubernetes Helm Installation Script
# =============================================================================
# Uses BanyanDB as storage backend
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
NAMESPACE="${NAMESPACE:-skywalking}"
RELEASE_NAME="${RELEASE_NAME:-skywalking}"
HELM_CHART_VERSION="${HELM_CHART_VERSION:-4.8.0}"
SKYWALKING_VERSION="${SKYWALKING_VERSION:-10.3.0}"
BANYANDB_VERSION="${BANYANDB_VERSION:-0.9.0}"
MODE="${1:-standalone}"  # standalone or cluster

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Prerequisites Check
# =============================================================================
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl first."
        exit 1
    fi

    if ! command -v helm &> /dev/null; then
        log_error "Helm not found. Please install Helm 3 first."
        log_info "Install: https://helm.sh/docs/intro/install/"
        exit 1
    fi

    # Check Helm version
    HELM_VERSION=$(helm version --short | cut -d'.' -f1 | tr -d 'v')
    if [[ "$HELM_VERSION" -lt 3 ]]; then
        log_error "Helm 3+ required. Found: Helm $HELM_VERSION"
        exit 1
    fi

    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
        exit 1
    fi

    log_info "Prerequisites OK"
}

# =============================================================================
# Create Namespace
# =============================================================================
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
}

# =============================================================================
# Install SkyWalking with BanyanDB
# =============================================================================
install_skywalking() {
    log_info "Installing SkyWalking in $MODE mode with BanyanDB storage..."

    VALUES_FILE="$SCRIPT_DIR/values.yaml"
    if [[ "$MODE" == "cluster" ]]; then
        VALUES_FILE="$SCRIPT_DIR/values-cluster.yaml"
    fi

    log_info "Using values file: $VALUES_FILE"
    log_info "SkyWalking version: $SKYWALKING_VERSION"
    log_info "BanyanDB version: $BANYANDB_VERSION"

    # Install using OCI chart with BanyanDB
    helm upgrade --install "$RELEASE_NAME" \
        oci://registry-1.docker.io/apache/skywalking-helm \
        --version "$HELM_CHART_VERSION" \
        --namespace "$NAMESPACE" \
        --set oap.image.tag="$SKYWALKING_VERSION" \
        --set oap.storageType=banyandb \
        --set ui.image.tag="$SKYWALKING_VERSION" \
        --set elasticsearch.enabled=false \
        --set banyandb.enabled=true \
        --set banyandb.image.tag="$BANYANDB_VERSION" \
        --values "$VALUES_FILE" \
        --wait \
        --timeout 10m

    log_info "SkyWalking installed successfully!"
}

# =============================================================================
# Print Access Information
# =============================================================================
print_access_info() {
    echo ""
    echo "=============================================="
    echo "  SkyWalking Installation Complete!"
    echo "=============================================="
    echo ""
    echo "Namespace: $NAMESPACE"
    echo "Release: $RELEASE_NAME"
    echo "Mode: $MODE"
    echo "Storage: BanyanDB"
    echo ""
    echo "Access the UI:"
    echo ""
    echo "  # Port forward"
    echo "  kubectl port-forward svc/${RELEASE_NAME}-ui 8080:80 -n $NAMESPACE"
    echo ""
    echo "  # Then open: http://localhost:8080"
    echo ""
    echo "  # Or for Minikube:"
    echo "  minikube service ${RELEASE_NAME}-ui -n $NAMESPACE"
    echo ""
    echo "OAP Server endpoints:"
    echo "  gRPC: ${RELEASE_NAME}-oap.$NAMESPACE.svc:11800"
    echo "  HTTP: ${RELEASE_NAME}-oap.$NAMESPACE.svc:12800"
    echo ""
    echo "Check status:"
    echo "  kubectl get pods -n $NAMESPACE"
    echo "  helm status $RELEASE_NAME -n $NAMESPACE"
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  SkyWalking Kubernetes Helm Installation"
    echo "  Storage: BanyanDB"
    echo "=============================================="
    echo ""

    if [[ "$MODE" != "standalone" && "$MODE" != "cluster" ]]; then
        log_error "Invalid mode: $MODE"
        echo "Usage: $0 [standalone|cluster]"
        exit 1
    fi

    check_prerequisites
    create_namespace
    install_skywalking
    print_access_info
}

main "$@"
