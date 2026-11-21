#!/bin/bash
# =============================================================================
# Apache SkyWalking Cloud on Kubernetes (SWCK) - Operator Installation
# =============================================================================
# Official docs: https://skywalking.apache.org/docs/skywalking-swck/next/operator
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
SWCK_VERSION="${SWCK_VERSION:-0.9.0}"
CERT_MANAGER_VERSION="${CERT_MANAGER_VERSION:-1.14.0}"

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

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
        exit 1
    fi

    # Check Kubernetes version
    K8S_VERSION=$(kubectl version --short 2>/dev/null | grep "Server" | awk '{print $3}' || echo "unknown")
    log_info "Kubernetes version: $K8S_VERSION"

    log_info "Prerequisites OK"
}

# =============================================================================
# Install cert-manager (Required for SWCK)
# =============================================================================
install_cert_manager() {
    log_info "Checking cert-manager..."

    if kubectl get crd certificates.cert-manager.io &> /dev/null; then
        log_info "cert-manager already installed"
        return 0
    fi

    log_info "Installing cert-manager v${CERT_MANAGER_VERSION}..."

    kubectl apply -f "https://github.com/cert-manager/cert-manager/releases/download/v${CERT_MANAGER_VERSION}/cert-manager.yaml"

    log_info "Waiting for cert-manager to be ready..."

    kubectl wait --for=condition=Available deployment/cert-manager \
        -n cert-manager --timeout=300s
    kubectl wait --for=condition=Available deployment/cert-manager-cainjector \
        -n cert-manager --timeout=300s
    kubectl wait --for=condition=Available deployment/cert-manager-webhook \
        -n cert-manager --timeout=300s

    # Give webhook time to be fully ready
    log_info "Waiting for webhook to be fully ready..."
    sleep 30

    log_info "cert-manager installed successfully"
}

# =============================================================================
# Install SWCK Operator via GitHub Release
# =============================================================================
install_swck_operator() {
    log_info "Installing SWCK Operator v${SWCK_VERSION}..."

    DOWNLOAD_DIR="$SCRIPT_DIR/downloads"
    mkdir -p "$DOWNLOAD_DIR"

    TARBALL="$DOWNLOAD_DIR/skywalking-swck-${SWCK_VERSION}-bin.tgz"
    SWCK_DIR="$DOWNLOAD_DIR/skywalking-swck-${SWCK_VERSION}-bin"

    # Download if not exists
    if [[ ! -f "$TARBALL" ]]; then
        # Try GitHub releases first (usually faster)
        GITHUB_URL="https://github.com/apache/skywalking-swck/releases/download/v${SWCK_VERSION}/skywalking-swck-${SWCK_VERSION}-bin.tgz"
        APACHE_URL="https://dlcdn.apache.org/skywalking/swck/${SWCK_VERSION}/skywalking-swck-${SWCK_VERSION}-bin.tgz"

        log_info "Downloading SWCK from GitHub..."
        if ! curl -fSL --connect-timeout 30 --max-time 300 "$GITHUB_URL" -o "$TARBALL" 2>/dev/null; then
            log_warn "GitHub download failed, trying Apache mirror..."
            curl -fSL --connect-timeout 30 --max-time 300 "$APACHE_URL" -o "$TARBALL" || {
                log_error "Download failed. Please download manually:"
                log_error "  $APACHE_URL"
                exit 1
            }
        fi

        # Extract
        log_info "Extracting SWCK..."
        tar -xzf "$TARBALL" -C "$DOWNLOAD_DIR"
    else
        log_info "Using cached SWCK tarball"
    fi

    # Find the operator-bundle.yaml (tarball extracts directly to downloads/)
    BUNDLE_FILE="$DOWNLOAD_DIR/config/operator-bundle.yaml"

    if [[ ! -f "$BUNDLE_FILE" ]]; then
        log_error "operator-bundle.yaml not found at: $BUNDLE_FILE"
        log_info "Contents of $DOWNLOAD_DIR:"
        ls -la "$DOWNLOAD_DIR" 2>/dev/null || true
        exit 1
    fi

    # Apply the operator bundle
    log_info "Applying operator-bundle.yaml..."
    kubectl apply -f "$BUNDLE_FILE"

    # Wait for operator to be ready
    log_info "Waiting for SWCK operator to be ready..."
    sleep 15

    kubectl wait --for=condition=Available deployment/skywalking-swck-controller-manager \
        -n skywalking-swck-system --timeout=300s || {
        log_warn "Operator may still be starting. Checking status..."
    }

    log_info "SWCK Operator installed!"
}

# =============================================================================
# Verify Installation
# =============================================================================
verify_installation() {
    log_info "Verifying SWCK installation..."

    echo ""
    echo "CRDs installed:"
    kubectl get crd | grep skywalking || echo "  No SkyWalking CRDs found"

    echo ""
    echo "Operator pods:"
    kubectl get pods -n skywalking-swck-system
}

# =============================================================================
# Print Next Steps
# =============================================================================
print_next_steps() {
    echo ""
    echo "=============================================="
    echo "  SWCK Operator Installation Complete!"
    echo "=============================================="
    echo ""
    echo "Operator namespace: skywalking-swck-system"
    echo ""
    echo "Available CRDs:"
    kubectl get crd | grep skywalking | awk '{print "  - " $1}'
    echo ""
    echo "Next steps:"
    echo "  ./deploy-all.sh"
    echo ""
    echo "Or manually:"
    echo "  kubectl create namespace skywalking"
    echo "  kubectl apply -f oap-server.yaml -n skywalking"
    echo "  kubectl apply -f ui.yaml -n skywalking"
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  SWCK Operator Installation - v${SWCK_VERSION}"
    echo "=============================================="
    echo ""

    check_prerequisites
    install_cert_manager
    install_swck_operator
    verify_installation
    print_next_steps
}

main "$@"
