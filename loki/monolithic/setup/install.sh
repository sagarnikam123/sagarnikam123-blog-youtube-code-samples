#!/bin/bash

# Loki Stack Setup - Download, Extract & Configure

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Error handler
error_exit() {
    print_error "$1"
    print_error "Installation failed. Check the error above."
    exit 1
}

# Check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        error_exit "Required command '$1' not found. Please install it first."
    fi
}

# Configuration
STACK_DIR="$HOME/loki-stack"
DATA_DIR="$HOME/.loki-data"
ARCHIVE_DIR="$HOME/loki-stack/archive"
LOKI_VERSION="3.5.7"
GRAFANA_VERSION="12.2.1"
PROMETHEUS_VERSION="3.5.0"

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case $ARCH in
    x86_64) ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Check Loki status: installed, downloaded, or not downloaded
check_loki_status() {
    # 1. Check if tool already installed (system-wide)
    if command -v loki &> /dev/null; then
        local system_version=$(loki --version 2>/dev/null | grep -o 'version [0-9]\+\.[0-9]\+\.[0-9]\+' | cut -d' ' -f2 || echo "unknown")
        if [[ "$system_version" == "$LOKI_VERSION" ]]; then
            print_warning "Loki $LOKI_VERSION already installed system-wide, skipping setup"
            return 0
        else
            print_warning "Loki $system_version installed system-wide (need $LOKI_VERSION), proceeding with local setup"
        fi
    fi

    # 2. Check if tool already installed locally
    if [[ -f "$STACK_DIR/loki/loki" ]]; then
        local current_version=$("$STACK_DIR/loki/loki" --version 2>/dev/null | grep -o 'version [0-9]\+\.[0-9]\+\.[0-9]\+' | cut -d' ' -f2 || echo "unknown")
        if [[ "$current_version" == "$LOKI_VERSION" ]]; then
            print_warning "Loki $LOKI_VERSION already installed locally, skipping setup"
            return 0
        else
            print_warning "Loki $current_version installed locally (need $LOKI_VERSION), will reinstall"
        fi
    fi

    # 3. Check if tools already downloaded
    local all_downloaded=true
    for tool in loki logcli loki-canary; do
        local archive_file="$ARCHIVE_DIR/${tool}-${OS}-${ARCH}-v${LOKI_VERSION}.zip"
        if [[ ! -f "$archive_file" ]]; then
            all_downloaded=false
            break
        fi
    done

    if [[ "$all_downloaded" == "true" ]]; then
        print_status "Loki $LOKI_VERSION binaries found in archive, installing from cache"
    else
        print_status "Loki $LOKI_VERSION not found, will download and install"
    fi

    return 1  # Proceed with setup
}

# Check Grafana status: installed, downloaded, or not downloaded
check_grafana_status() {
    # 1. Check if tool already installed (system-wide)
    if command -v grafana &> /dev/null || command -v grafana-server &> /dev/null; then
        local grafana_cmd=$(command -v grafana || command -v grafana-server)
        local system_version=$("$grafana_cmd" --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1 || echo "unknown")
        if [[ "$system_version" == "$GRAFANA_VERSION" ]]; then
            print_warning "Grafana $GRAFANA_VERSION already installed system-wide, skipping setup"
            return 0
        else
            print_warning "Grafana $system_version installed system-wide (need $GRAFANA_VERSION), proceeding with local setup"
        fi
    fi

    # 2. Check if tool already installed locally
    if [[ -f "$STACK_DIR/grafana/bin/grafana" ]]; then
        local current_version=$("$STACK_DIR/grafana/bin/grafana" --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1 || echo "unknown")
        if [[ "$current_version" == "$GRAFANA_VERSION" ]]; then
            print_warning "Grafana $GRAFANA_VERSION already installed locally, skipping setup"
            return 0
        else
            print_warning "Grafana $current_version installed locally (need $GRAFANA_VERSION), will reinstall"
        fi
    fi

    # 3. Check if already downloaded
    local archive_file
    if [[ "$GRAFANA_VERSION" == "12.2.1" ]]; then
        local grafana_build_id="18655849634"
        archive_file="$ARCHIVE_DIR/grafana_${GRAFANA_VERSION}_${grafana_build_id}_${OS}_${ARCH}.tar.gz"
    else
        archive_file="$ARCHIVE_DIR/grafana-${GRAFANA_VERSION}.${OS}-${ARCH}.tar.gz"
    fi

    if [[ -f "$archive_file" ]]; then
        print_status "Grafana $GRAFANA_VERSION binary found in archive, installing from cache"
    else
        print_status "Grafana $GRAFANA_VERSION not found, will download and install"
    fi

    return 1  # Proceed with setup
}

# Check Prometheus status: installed, downloaded, or not downloaded
check_prometheus_status() {
    # 1. Check if tool already installed (system-wide)
    if command -v prometheus &> /dev/null; then
        local system_version=$(prometheus --version 2>/dev/null | grep -o 'version [0-9]\+\.[0-9]\+\.[0-9]\+' | cut -d' ' -f2 || echo "unknown")
        if [[ "$system_version" == "$PROMETHEUS_VERSION" ]]; then
            print_warning "Prometheus $PROMETHEUS_VERSION already installed system-wide, skipping setup"
            return 0
        else
            print_warning "Prometheus $system_version installed system-wide (need $PROMETHEUS_VERSION), proceeding with local setup"
        fi
    fi

    # 2. Check if tool already installed locally
    if [[ -f "$STACK_DIR/prometheus/prometheus" ]]; then
        local current_version=$("$STACK_DIR/prometheus/prometheus" --version 2>/dev/null | grep -o 'version [0-9]\+\.[0-9]\+\.[0-9]\+' | cut -d' ' -f2 || echo "unknown")
        if [[ "$current_version" == "$PROMETHEUS_VERSION" ]]; then
            print_warning "Prometheus $PROMETHEUS_VERSION already installed locally, skipping setup"
            return 0
        else
            print_warning "Prometheus $current_version installed locally (need $PROMETHEUS_VERSION), will reinstall"
        fi
    fi

    # 3. Check if already downloaded
    local archive_file="$ARCHIVE_DIR/prometheus-${PROMETHEUS_VERSION}.${OS}-${ARCH}.tar.gz"
    if [[ -f "$archive_file" ]]; then
        print_status "Prometheus $PROMETHEUS_VERSION binary found in archive, installing from cache"
    else
        print_status "Prometheus $PROMETHEUS_VERSION not found, will download and install"
    fi

    return 1  # Proceed with setup
}

# Check MinIO status: installed, downloaded, or not downloaded
check_minio_status() {
    # 1. Check if tool already installed (system-wide)
    if command -v minio &> /dev/null; then
        print_warning "MinIO already installed system-wide, skipping setup"
        return 0
    fi

    # 2. Check if tool already installed locally
    if [[ -f "$STACK_DIR/minio/minio" ]]; then
        print_warning "MinIO already installed locally, skipping setup"
        return 0
    fi

    # 3. Check if already downloaded
    local minio_archive="$ARCHIVE_DIR/minio-${OS}-${ARCH}"
    local mc_archive="$ARCHIVE_DIR/mc-${OS}-${ARCH}"

    if [[ -f "$minio_archive" && -f "$mc_archive" ]]; then
        print_status "MinIO binaries found in archive, installing from cache"
    else
        print_status "MinIO not found, will download and install"
    fi

    return 1  # Proceed with setup
}

# Create directory structure
create_directories() {
    print_status "Creating directory structure..."
    mkdir -p "$STACK_DIR"/{loki,grafana,prometheus,minio,configs,scripts,log-scrapers,archive} || error_exit "Failed to create stack directories"
    mkdir -p "$STACK_DIR"/log-scrapers/{fluent-bit,vector,alloy} || error_exit "Failed to create log-scrapers directories"
    mkdir -p "$DATA_DIR"/{loki,grafana,prometheus,minio,logs} || error_exit "Failed to create data directories"
    mkdir -p "$DATA_DIR"/loki/{chunks,index,rules,wal} || error_exit "Failed to create Loki data directories"
}

# Download and setup Loki
setup_loki() {
    print_status "Setting up Loki $LOKI_VERSION..."

    if check_loki_status; then
        return
    fi

    # Download Loki tools
    for tool in loki logcli loki-canary; do
        archive_file="$ARCHIVE_DIR/${tool}-${OS}-${ARCH}-v${LOKI_VERSION}.zip"

        if [[ ! -f "$archive_file" ]]; then
            print_status "Downloading $tool $LOKI_VERSION for $OS-$ARCH..."
            if ! wget --progress=dot:giga --timeout=30 "https://github.com/grafana/loki/releases/download/v${LOKI_VERSION}/${tool}-${OS}-${ARCH}.zip" -O "$archive_file"; then
                error_exit "Failed to download $tool"
            fi
        else
            print_warning "Using cached $tool binary from archive"
        fi

        cd "$STACK_DIR/loki" || error_exit "Failed to change to loki directory"
        if ! unzip -o -q "$archive_file"; then
            error_exit "Failed to extract $tool archive"
        fi
        chmod +x "${tool}-${OS}-${ARCH}" || error_exit "Failed to make $tool executable"

        # Remove quarantine attribute on macOS to prevent Gatekeeper warnings
        if [[ "$OS" == "darwin" ]]; then
            xattr -d com.apple.quarantine "${tool}-${OS}-${ARCH}" 2>/dev/null || true
        fi

        ln -sf "${tool}-${OS}-${ARCH}" "$tool" || error_exit "Failed to create $tool symlink"
    done

    print_status "Loki tools installed"
}

# Download and setup Grafana
setup_grafana() {
    print_status "Setting up Grafana $GRAFANA_VERSION..."

    if check_grafana_status; then
        return
    fi

    # Use different URL formats based on version
    if [[ "$GRAFANA_VERSION" == "12.2.1" ]]; then
        # New format for v12.2.1+
        local grafana_build_id="18655849634"
        archive_file="$ARCHIVE_DIR/grafana_${GRAFANA_VERSION}_${grafana_build_id}_${OS}_${ARCH}.tar.gz"
        download_url="https://dl.grafana.com/grafana/release/${GRAFANA_VERSION}/grafana_${GRAFANA_VERSION}_${grafana_build_id}_${OS}_${ARCH}.tar.gz"
        extract_dir="grafana_${GRAFANA_VERSION}_${grafana_build_id}"
    else
        # Old format for older versions
        archive_file="$ARCHIVE_DIR/grafana-${GRAFANA_VERSION}.${OS}-${ARCH}.tar.gz"
        download_url="https://dl.grafana.com/oss/release/grafana-${GRAFANA_VERSION}.${OS}-${ARCH}.tar.gz"
        extract_dir="grafana-v${GRAFANA_VERSION}"
    fi

    if [[ ! -f "$archive_file" ]]; then
        print_status "Downloading Grafana $GRAFANA_VERSION for $OS-$ARCH..."
        if ! wget --progress=dot:giga --timeout=60 "$download_url" -O "$archive_file"; then
            error_exit "Failed to download Grafana"
        fi
    else
        print_warning "Using cached Grafana binary from archive"
    fi

    cd "$STACK_DIR" || error_exit "Failed to change to stack directory"
    if ! tar -xzf "$archive_file"; then
        error_exit "Failed to extract Grafana archive"
    fi

    # Find the actual extracted directory (it might have a different name)
    extracted_dir=$(find . -maxdepth 1 -type d -name "grafana*" | head -1)
    if [[ -z "$extracted_dir" ]]; then
        error_exit "Could not find extracted Grafana directory"
    fi

    # Clean existing grafana directory if it exists
    if [[ -d "grafana" ]]; then
        rm -rf grafana/* || print_warning "Failed to clean existing Grafana directory"
    fi

    if ! mv "$extracted_dir"/* grafana/; then
        error_exit "Failed to move Grafana files"
    fi
    rm -rf "$extracted_dir" || print_warning "Failed to cleanup Grafana temp directory"

    # Remove quarantine attribute on macOS to prevent Gatekeeper warnings
    if [[ "$OS" == "darwin" ]]; then
        find grafana/bin -type f -executable -exec xattr -d com.apple.quarantine {} \; 2>/dev/null || true
    fi

    print_status "Grafana installed"
}

# Download and setup Prometheus
setup_prometheus() {
    print_status "Setting up Prometheus $PROMETHEUS_VERSION..."

    if check_prometheus_status; then
        return
    fi

    archive_file="$ARCHIVE_DIR/prometheus-${PROMETHEUS_VERSION}.${OS}-${ARCH}.tar.gz"

    if [[ ! -f "$archive_file" ]]; then
        print_status "Downloading Prometheus $PROMETHEUS_VERSION for $OS-$ARCH..."
        if ! wget --progress=dot:giga --timeout=60 "https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.${OS}-${ARCH}.tar.gz" -O "$archive_file"; then
            error_exit "Failed to download Prometheus"
        fi
    else
        print_warning "Using cached Prometheus binary from archive"
    fi

    cd "$STACK_DIR" || error_exit "Failed to change to stack directory"
    if ! tar -xzf "$archive_file"; then
        error_exit "Failed to extract Prometheus archive"
    fi
    if ! mv "prometheus-${PROMETHEUS_VERSION}.${OS}-${ARCH}"/* prometheus/; then
        error_exit "Failed to move Prometheus files"
    fi
    rm -rf "prometheus-${PROMETHEUS_VERSION}.${OS}-${ARCH}" || print_warning "Failed to cleanup Prometheus temp directory"

    # Remove quarantine attribute on macOS to prevent Gatekeeper warnings
    if [[ "$OS" == "darwin" ]]; then
        find prometheus -type f -executable -exec xattr -d com.apple.quarantine {} \; 2>/dev/null || true
    fi

    print_status "Prometheus installed"
}

# Download and setup MinIO
setup_minio() {
    print_status "Setting up MinIO..."

    if check_minio_status; then
        return
    fi

    # MinIO Server
    minio_archive="$ARCHIVE_DIR/minio-${OS}-${ARCH}"
    if [[ ! -f "$minio_archive" ]]; then
        print_status "Downloading MinIO server for $OS-$ARCH..."
        if ! wget --progress=dot:giga --timeout=30 "https://dl.min.io/server/minio/release/${OS}-${ARCH}/minio" -O "$minio_archive"; then
            error_exit "Failed to download MinIO server"
        fi
    else
        print_warning "Using cached MinIO server binary from archive"
    fi

    # MinIO Client
    mc_archive="$ARCHIVE_DIR/mc-${OS}-${ARCH}"
    if [[ ! -f "$mc_archive" ]]; then
        print_status "Downloading MinIO client (mc) for $OS-$ARCH..."
        if ! wget --progress=dot:giga --timeout=30 "https://dl.min.io/client/mc/release/${OS}-${ARCH}/mc" -O "$mc_archive"; then
            error_exit "Failed to download MinIO client"
        fi
    else
        print_warning "Using cached MinIO client binary from archive"
    fi

    # Copy to installation directory
    if ! cp "$minio_archive" "$STACK_DIR/minio/minio"; then
        error_exit "Failed to copy MinIO server binary"
    fi
    if ! cp "$mc_archive" "$STACK_DIR/minio/mc"; then
        error_exit "Failed to copy MinIO client binary"
    fi
    if ! chmod +x "$STACK_DIR/minio/minio" "$STACK_DIR/minio/mc"; then
        error_exit "Failed to make MinIO binaries executable"
    fi

    # Remove quarantine attribute on macOS to prevent Gatekeeper warnings
    if [[ "$OS" == "darwin" ]]; then
        xattr -d com.apple.quarantine "$STACK_DIR/minio/minio" 2>/dev/null || true
        xattr -d com.apple.quarantine "$STACK_DIR/minio/mc" 2>/dev/null || true
    fi

    print_status "MinIO installed"
}

# Copy configurations
copy_configs() {
    print_status "Copying configurations..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || error_exit "Failed to determine script directory"

    # Copy Loki configs
    if [[ -d "$SCRIPT_DIR/v2.x" ]]; then
        for config in "$SCRIPT_DIR/v2.x/"*.yaml; do
            if [[ -f "$config" ]]; then
                print_status "  Copying $(basename "$config")"
                cp "$config" "$STACK_DIR/configs/" || print_warning "Failed to copy $(basename "$config")"
            fi
        done
    fi
    if [[ -d "$SCRIPT_DIR/v3.x" ]]; then
        for config in "$SCRIPT_DIR/v3.x/"*.yaml; do
            if [[ -f "$config" ]]; then
                print_status "  Copying $(basename "$config")"
                cp "$config" "$STACK_DIR/configs/" || print_warning "Failed to copy $(basename "$config")"
            fi
        done
    fi

    # Copy log scraper configs if they exist
    if [[ -d "$SCRIPT_DIR/log-scrapers" ]]; then
        print_status "  Copying log scraper configurations"
        if ! cp -r "$SCRIPT_DIR/log-scrapers/"* "$STACK_DIR/log-scrapers/" 2>/dev/null; then
            print_warning "Failed to copy log scraper configs"
        fi
    fi

    # Set default config
    if [[ -f "$STACK_DIR/configs/loki-3.x-dev-local-storage.yaml" ]]; then
        print_status "  Setting default config: loki-3.x-dev-local-storage.yaml"
        if ! ln -sf "loki-3.x-dev-local-storage.yaml" "$STACK_DIR/configs/loki.yaml"; then
            print_warning "Failed to create default config symlink"
        fi
    fi
}

# Copy startup scripts
copy_scripts() {
    print_status "Copying startup scripts..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || error_exit "Failed to determine script directory"

    # Copy scripts if they exist in git repository
    if [[ -d "$SCRIPT_DIR/scripts" ]]; then
        if ! cp "$SCRIPT_DIR/scripts/"*.sh "$STACK_DIR/scripts/" 2>/dev/null; then
            print_warning "No scripts found in git repository or failed to copy"
        else
            print_status "Scripts copied from git repository"
        fi
    else
        print_warning "No scripts directory found in git repository"
    fi

    # Make scripts executable
    if ! chmod +x "$STACK_DIR/scripts/"*.sh 2>/dev/null; then
        print_warning "Failed to make scripts executable or no scripts found"
    fi
}

# Setup fuzzy-train log generator
setup_fuzzy_train() {
    print_status "Setting up fuzzy-train log generator..."

    # Check if fuzzy-train already exists
    if [[ -d "$STACK_DIR/fuzzy-train" ]]; then
        print_warning "fuzzy-train already exists, updating..."
        cd "$STACK_DIR/fuzzy-train" || error_exit "Failed to change to fuzzy-train directory"
        if ! git pull origin main; then
            print_warning "Failed to update fuzzy-train, using existing version"
        else
            print_status "fuzzy-train updated successfully"
        fi
        return
    fi

    # Check if git is available
    if ! command -v git &> /dev/null; then
        print_warning "Git not found, skipping fuzzy-train setup"
        print_warning "Install git and run: git clone https://github.com/sagarnikam123/fuzzy-train.git $STACK_DIR/fuzzy-train"
        return
    fi

    # Clone fuzzy-train repository
    cd "$STACK_DIR" || error_exit "Failed to change to stack directory"
    print_status "Cloning fuzzy-train repository..."
    if ! git clone https://github.com/sagarnikam123/fuzzy-train.git; then
        print_warning "Failed to clone fuzzy-train repository"
        print_warning "You can manually clone it later: git clone https://github.com/sagarnikam123/fuzzy-train.git $STACK_DIR/fuzzy-train"
        return
    fi

    print_status "fuzzy-train log generator installed"
}

# Main setup
main() {
    print_status "Setting up Loki Stack in $STACK_DIR..."

    # Check required commands
    check_command "wget"
    check_command "unzip"
    check_command "tar"

    create_directories
    setup_loki
    setup_grafana
    setup_prometheus
    setup_minio
    setup_fuzzy_train
    copy_configs
    copy_scripts

    print_status "Setup completed!"
    echo ""
    echo "Directory structure:"
    echo "  $STACK_DIR/loki/        - Loki binaries"
    echo "  $STACK_DIR/grafana/     - Grafana installation"
    echo "  $STACK_DIR/prometheus/  - Prometheus installation"
    echo "  $STACK_DIR/minio/       - MinIO binaries"
    echo "  $STACK_DIR/configs/     - Loki configuration files"
    echo "  $STACK_DIR/log-scrapers/ - Log scraper configs (fluent-bit, vector, alloy)"
    echo "  $STACK_DIR/fuzzy-train/ - Log generator tool"
    echo "  $STACK_DIR/scripts/     - Startup scripts"
    echo "  $STACK_DIR/archive/     - Downloaded binaries cache"
    echo "  $DATA_DIR/              - Data storage"
    echo ""
    echo "Usage:"
    echo "  source $STACK_DIR/scripts/setup-env.sh"
    echo "  loki-start"
    echo "  grafana-start"
    echo "  prometheus-start"
    echo "  minio-start"
}

main "$@"
