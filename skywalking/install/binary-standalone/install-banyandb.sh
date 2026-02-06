#!/bin/bash
# =============================================================================
# Apache SkyWalking - BanyanDB Installation Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
BANYANDB_VERSION="${BANYANDB_VERSION:-0.9.0}"
BANYANDB_HOME="$PROJECT_DIR/banyandb"
DOWNLOAD_DIR="$PROJECT_DIR/downloads"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Detect OS and Architecture
# =============================================================================
detect_platform() {
    OS_TYPE="$(uname -s)"
    ARCH="$(uname -m)"

    case "$OS_TYPE" in
        Linux*)  OS="linux" ;;
        Darwin*) OS="darwin" ;;
        *)       log_error "Unsupported OS: $OS_TYPE"; exit 1 ;;
    esac

    case "$ARCH" in
        x86_64)  ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        arm64)   ARCH="arm64" ;;
        *)       log_error "Unsupported architecture: $ARCH"; exit 1 ;;
    esac

    log_info "Detected platform: ${OS}-${ARCH}"
}

# =============================================================================
# Download BanyanDB
# =============================================================================
download_banyandb() {
    log_info "Downloading BanyanDB v${BANYANDB_VERSION}..."

    mkdir -p "$DOWNLOAD_DIR"

    DOWNLOAD_URL="https://dlcdn.apache.org/skywalking/banyandb/${BANYANDB_VERSION}/apache-skywalking-banyandb-${BANYANDB_VERSION}-banyand-${OS}-${ARCH}.tar.gz"
    TARBALL="$DOWNLOAD_DIR/banyandb-${BANYANDB_VERSION}.tar.gz"

    if [[ -f "$TARBALL" ]]; then
        log_info "BanyanDB tarball already exists, skipping download"
    else
        log_info "Downloading from: $DOWNLOAD_URL"
        curl -fSL "$DOWNLOAD_URL" -o "$TARBALL"
    fi

    log_info "Download completed"
}

# =============================================================================
# Install BanyanDB
# =============================================================================
install_banyandb() {
    log_info "Installing BanyanDB..."

    TARBALL="$DOWNLOAD_DIR/banyandb-${BANYANDB_VERSION}.tar.gz"

    # Remove existing installation
    if [[ -d "$BANYANDB_HOME" ]]; then
        log_warn "Removing existing BanyanDB installation..."
        rm -rf "$BANYANDB_HOME"
    fi

    # Extract
    mkdir -p "$BANYANDB_HOME"
    tar -xzf "$TARBALL" -C "$BANYANDB_HOME" --strip-components=1

    # Create data directory
    mkdir -p "$PROJECT_DIR/data/banyandb"

    log_info "BanyanDB installed to: $BANYANDB_HOME"
}

# =============================================================================
# Verify Installation
# =============================================================================
verify_installation() {
    log_info "Verifying BanyanDB installation..."

    if [[ -f "$BANYANDB_HOME/banyand" ]]; then
        chmod +x "$BANYANDB_HOME/banyand"
        log_info "BanyanDB binary found and made executable"

        # Show version
        "$BANYANDB_HOME/banyand" --version 2>/dev/null || true

        return 0
    else
        log_error "BanyanDB binary not found!"
        return 1
    fi
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  BanyanDB Installation - v${BANYANDB_VERSION}"
    echo "=============================================="
    echo ""

    detect_platform
    download_banyandb
    install_banyandb
    verify_installation

    echo ""
    log_info "BanyanDB installation completed!"
    echo ""
    echo "BanyanDB Home: $BANYANDB_HOME"
    echo "Data Directory: $PROJECT_DIR/data/banyandb"
    echo ""
    echo "To start BanyanDB standalone:"
    echo "  $BANYANDB_HOME/banyand standalone --data-path=$PROJECT_DIR/data/banyandb"
}

main "$@"
