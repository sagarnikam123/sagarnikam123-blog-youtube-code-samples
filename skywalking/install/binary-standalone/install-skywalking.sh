#!/bin/bash
# =============================================================================
# Apache SkyWalking OAP + UI Installation Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
SKYWALKING_VERSION="${SKYWALKING_VERSION:-10.3.0}"
SKYWALKING_HOME="$PROJECT_DIR/skywalking-oap"
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
# Check Java
# =============================================================================
check_java() {
    if ! command -v java &> /dev/null; then
        log_error "Java not found. Please run install-prerequisites.sh first."
        exit 1
    fi

    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [[ "$JAVA_VERSION" == "1" ]]; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f2)
    fi

    if [[ "$JAVA_VERSION" -lt 11 ]]; then
        log_error "Java 11+ required. Found: Java $JAVA_VERSION"
        exit 1
    fi

    log_info "Java $JAVA_VERSION detected - OK"
}

# =============================================================================
# Download SkyWalking
# =============================================================================
download_skywalking() {
    log_info "Downloading SkyWalking APM v${SKYWALKING_VERSION}..."

    mkdir -p "$DOWNLOAD_DIR"

    DOWNLOAD_URL="https://dlcdn.apache.org/skywalking/${SKYWALKING_VERSION}/apache-skywalking-apm-${SKYWALKING_VERSION}.tar.gz"
    TARBALL="$DOWNLOAD_DIR/skywalking-${SKYWALKING_VERSION}.tar.gz"

    if [[ -f "$TARBALL" ]]; then
        log_info "SkyWalking tarball already exists, skipping download"
    else
        log_info "Downloading from: $DOWNLOAD_URL"
        curl -fSL "$DOWNLOAD_URL" -o "$TARBALL"
    fi

    log_info "Download completed"
}

# =============================================================================
# Install SkyWalking
# =============================================================================
install_skywalking() {
    log_info "Installing SkyWalking..."

    TARBALL="$DOWNLOAD_DIR/skywalking-${SKYWALKING_VERSION}.tar.gz"

    # Remove existing installation
    if [[ -d "$SKYWALKING_HOME" ]]; then
        log_warn "Removing existing SkyWalking installation..."
        rm -rf "$SKYWALKING_HOME"
    fi

    # Extract
    mkdir -p "$SKYWALKING_HOME"
    tar -xzf "$TARBALL" -C "$SKYWALKING_HOME" --strip-components=1

    # Make scripts executable
    chmod +x "$SKYWALKING_HOME"/bin/*.sh 2>/dev/null || true

    log_info "SkyWalking installed to: $SKYWALKING_HOME"
}

# =============================================================================
# Configure for BanyanDB Storage
# =============================================================================
configure_banyandb_storage() {
    log_info "Configuring SkyWalking for BanyanDB storage..."

    CONFIG_FILE="$SKYWALKING_HOME/config/application.yml"

    # Backup original config
    cp "$CONFIG_FILE" "$CONFIG_FILE.bak"

    # Update storage selector to banyandb
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS sed
        sed -i '' 's/selector: \${SW_STORAGE:h2}/selector: \${SW_STORAGE:banyandb}/' "$CONFIG_FILE"
    else
        # Linux sed
        sed -i 's/selector: \${SW_STORAGE:h2}/selector: \${SW_STORAGE:banyandb}/' "$CONFIG_FILE"
    fi

    log_info "Storage configured to use BanyanDB"

    # Copy custom config if exists
    if [[ -f "$PROJECT_DIR/conf/application.yml" ]]; then
        log_info "Applying custom application.yml..."
        cp "$PROJECT_DIR/conf/application.yml" "$CONFIG_FILE"
    fi

    if [[ -f "$PROJECT_DIR/conf/bydb.yaml" ]]; then
        log_info "Applying custom bydb.yaml..."
        cp "$PROJECT_DIR/conf/bydb.yaml" "$SKYWALKING_HOME/config/bydb.yaml"
    fi
}

# =============================================================================
# Verify Installation
# =============================================================================
verify_installation() {
    log_info "Verifying SkyWalking installation..."

    if [[ -f "$SKYWALKING_HOME/bin/oapService.sh" ]]; then
        log_info "OAP Server script found - OK"
    else
        log_error "OAP Server script not found!"
        return 1
    fi

    if [[ -f "$SKYWALKING_HOME/bin/webappService.sh" ]]; then
        log_info "UI Server script found - OK"
    else
        log_error "UI Server script not found!"
        return 1
    fi

    if [[ -d "$SKYWALKING_HOME/webapp" ]]; then
        log_info "Webapp directory found - OK"
    else
        log_error "Webapp directory not found!"
        return 1
    fi

    return 0
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  SkyWalking APM Installation - v${SKYWALKING_VERSION}"
    echo "=============================================="
    echo ""

    check_java
    download_skywalking
    install_skywalking
    configure_banyandb_storage
    verify_installation

    echo ""
    log_info "SkyWalking installation completed!"
    echo ""
    echo "SkyWalking Home: $SKYWALKING_HOME"
    echo ""
    echo "Configuration files:"
    echo "  - $SKYWALKING_HOME/config/application.yml"
    echo "  - $SKYWALKING_HOME/config/bydb.yaml"
    echo ""
    echo "To start SkyWalking:"
    echo "  1. Start BanyanDB first"
    echo "  2. Run: $SKYWALKING_HOME/bin/startup.sh"
    echo ""
    echo "Or use the unified start script:"
    echo "  ./scripts/start-all.sh"
}

main "$@"
