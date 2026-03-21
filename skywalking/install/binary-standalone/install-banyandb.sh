#!/bin/bash
# =============================================================================
# Apache SkyWalking - BanyanDB Installation Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Configuration — override via argument or env var
BANYANDB_VERSION="${1:-${BANYANDB_VERSION:-0.9.0}}"
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

    # BanyanDB server binaries are only available for Linux.
    # macOS users must build from source or use Docker.
    if [[ "$OS" == "darwin" ]]; then
        log_warn "BanyanDB server binaries are only available for Linux (amd64/arm64)."
        log_warn "The official tarball does not include macOS banyand-server binaries."
        log_warn ""
        log_warn "Options for macOS:"
        log_warn "  1. Use Docker: docker run -d -p 17912:17912 -p 17913:17913 apache/skywalking-banyandb:${BANYANDB_VERSION} standalone"
        log_warn "  2. Build from source: https://skywalking.apache.org/docs/skywalking-banyandb/latest/installation/binaries/"
        log_warn ""
        read -p "Continue downloading the tarball anyway (contains Linux binaries only)? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi

    log_info "Detected platform: ${OS}-${ARCH}"
}

# =============================================================================
# Download BanyanDB
# =============================================================================
download_banyandb() {
    log_info "Downloading BanyanDB v${BANYANDB_VERSION}..."

    mkdir -p "$DOWNLOAD_DIR"

    # Single universal tarball — contains multi-platform binaries inside bin/
    DOWNLOAD_URL="https://dlcdn.apache.org/skywalking/banyandb/${BANYANDB_VERSION}/skywalking-banyandb-${BANYANDB_VERSION}-banyand.tgz"
    TARBALL="$DOWNLOAD_DIR/banyandb-${BANYANDB_VERSION}.tgz"

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

    TARBALL="$DOWNLOAD_DIR/banyandb-${BANYANDB_VERSION}.tgz"

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

    # Select the correct binary for this platform
    # Tarball contains: bin/banyand-server-slim-linux-{amd64,arm64}
    #                    bin/banyand-server-static-linux-{amd64,arm64}
    BINARY_NAME="banyand-server-static-${OS}-${ARCH}"
    BINARY_PATH="$BANYANDB_HOME/bin/$BINARY_NAME"

    if [[ -f "$BINARY_PATH" ]]; then
        chmod +x "$BINARY_PATH"
        # Create a symlink for convenience
        ln -sf "bin/$BINARY_NAME" "$BANYANDB_HOME/banyand"
        log_info "Selected binary: $BINARY_NAME"
    else
        log_warn "Binary $BINARY_NAME not found in tarball."
        log_warn "Available binaries:"
        ls -1 "$BANYANDB_HOME/bin/" 2>/dev/null || echo "  (none)"
    fi

    log_info "BanyanDB installed to: $BANYANDB_HOME"
}

# =============================================================================
# Verify Installation
# =============================================================================
verify_installation() {
    log_info "Verifying BanyanDB installation..."

    if [[ -f "$BANYANDB_HOME/banyand" ]] || [[ -L "$BANYANDB_HOME/banyand" ]]; then
        log_info "BanyanDB binary found and ready"

        # Show version
        "$BANYANDB_HOME/banyand" --version 2>/dev/null || true

        return 0
    else
        log_error "BanyanDB binary not found!"
        log_error "Available files in bin/:"
        ls -1 "$BANYANDB_HOME/bin/" 2>/dev/null || echo "  (none)"
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
