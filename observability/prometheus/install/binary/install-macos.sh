#!/bin/bash
#
# Prometheus Binary Installer for macOS
# Downloads and installs Prometheus from official releases
#
# Usage: ./install-macos.sh [--version VERSION] [--data-dir PATH] [--config PATH]
#
# Requirements: 1.3, 1.7, 1.9

set -euo pipefail

# Default values
PROMETHEUS_VERSION="${PROMETHEUS_VERSION:-2.54.1}"
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/usr/local/etc/prometheus"
DATA_DIR="/usr/local/var/prometheus"
LOG_DIR="/usr/local/var/log/prometheus"
DOWNLOAD_URL="https://github.com/prometheus/prometheus/releases/download"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="io.prometheus.prometheus"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect architecture
detect_arch() {
    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64)
            echo "amd64"
            ;;
        arm64)
            echo "arm64"
            ;;
        *)
            log_error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac
}

# Detect OS
detect_os() {
    local os
    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    if [[ "$os" != "darwin" ]]; then
        log_error "This script is for macOS only. Detected: $os"
        exit 1
    fi
    echo "$os"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                PROMETHEUS_VERSION="$2"
                shift 2
                ;;
            --data-dir)
                DATA_DIR="$2"
                shift 2
                ;;
            --config)
                CUSTOM_CONFIG="$2"
                shift 2
                ;;
            --system)
                # Install as system-wide service (requires sudo)
                SYSTEM_INSTALL=true
                PLIST_DIR="/Library/LaunchDaemons"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
Prometheus Binary Installer for macOS

Usage: $0 [OPTIONS]

Options:
    --version VERSION    Prometheus version to install (default: $PROMETHEUS_VERSION)
    --data-dir PATH      Data directory path (default: $DATA_DIR)
    --config PATH        Custom prometheus.yml config file path
    --system             Install as system-wide service (requires sudo)
    --help, -h           Show this help message

Examples:
    $0
    $0 --version 2.54.1
    $0 --data-dir /data/prometheus --config /path/to/prometheus.yml
    sudo $0 --system
EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check for curl or wget
    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        log_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi

    # Check for tar
    if ! command -v tar &> /dev/null; then
        log_error "tar command not found. Please install it."
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Download and extract Prometheus
download_prometheus() {
    local os arch filename url tmp_dir

    os=$(detect_os)
    arch=$(detect_arch)
    filename="prometheus-${PROMETHEUS_VERSION}.${os}-${arch}.tar.gz"
    url="${DOWNLOAD_URL}/v${PROMETHEUS_VERSION}/${filename}"
    tmp_dir=$(mktemp -d)

    log_info "Downloading Prometheus v${PROMETHEUS_VERSION} for ${os}-${arch}..."
    log_info "URL: $url"

    if command -v curl &> /dev/null; then
        curl -fsSL "$url" -o "${tmp_dir}/${filename}"
    else
        wget -q "$url" -O "${tmp_dir}/${filename}"
    fi

    log_info "Extracting archive..."
    tar -xzf "${tmp_dir}/${filename}" -C "$tmp_dir"

    local extract_dir="${tmp_dir}/prometheus-${PROMETHEUS_VERSION}.${os}-${arch}"

    # Install binaries
    log_info "Installing binaries to $INSTALL_DIR..."

    # Create install directory if it doesn't exist
    if [[ ! -d "$INSTALL_DIR" ]]; then
        if [[ "${SYSTEM_INSTALL:-false}" == "true" ]]; then
            sudo mkdir -p "$INSTALL_DIR"
        else
            mkdir -p "$INSTALL_DIR"
        fi
    fi

    if [[ "${SYSTEM_INSTALL:-false}" == "true" ]]; then
        sudo cp "${extract_dir}/prometheus" "$INSTALL_DIR/"
        sudo cp "${extract_dir}/promtool" "$INSTALL_DIR/"
        sudo chmod 755 "${INSTALL_DIR}/prometheus" "${INSTALL_DIR}/promtool"
    else
        cp "${extract_dir}/prometheus" "$INSTALL_DIR/"
        cp "${extract_dir}/promtool" "$INSTALL_DIR/"
        chmod 755 "${INSTALL_DIR}/prometheus" "${INSTALL_DIR}/promtool"
    fi

    # Install console templates and libraries
    log_info "Installing console templates..."
    mkdir -p "${CONFIG_DIR}/consoles" "${CONFIG_DIR}/console_libraries"
    cp -r "${extract_dir}/consoles/"* "${CONFIG_DIR}/consoles/" 2>/dev/null || true
    cp -r "${extract_dir}/console_libraries/"* "${CONFIG_DIR}/console_libraries/" 2>/dev/null || true

    # Cleanup
    rm -rf "$tmp_dir"

    log_info "Prometheus binaries installed successfully"
}

# Create directories
create_directories() {
    log_info "Creating directories..."

    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$PLIST_DIR"

    log_info "Directories created"
}


# Create default prometheus.yml configuration
create_default_config() {
    local config_file="${CONFIG_DIR}/prometheus.yml"

    if [[ -n "${CUSTOM_CONFIG:-}" ]] && [[ -f "$CUSTOM_CONFIG" ]]; then
        log_info "Using custom configuration from $CUSTOM_CONFIG"
        cp "$CUSTOM_CONFIG" "$config_file"
    elif [[ -f "$config_file" ]]; then
        log_warn "Configuration file already exists at $config_file, skipping..."
        return
    else
        log_info "Creating default prometheus.yml configuration..."
        cat > "$config_file" << 'PROMETHEUS_CONFIG'
# Prometheus configuration file
# Generated by install-macos.sh

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  # scrape_timeout is set to the global default (10s)

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

# Rule files
rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

# Scrape configurations
scrape_configs:
  # Prometheus self-monitoring
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
        labels:
          instance: "prometheus-server"

  # Node Exporter (uncomment when installed)
  # - job_name: "node"
  #   static_configs:
  #     - targets: ["localhost:9100"]
PROMETHEUS_CONFIG
    fi

    chmod 644 "$config_file"

    log_info "Configuration file created at $config_file"
}

# Create launchd plist
create_launchd_plist() {
    local plist_file="${PLIST_DIR}/${PLIST_NAME}.plist"

    log_info "Creating launchd plist..."

    if [[ "${SYSTEM_INSTALL:-false}" == "true" ]]; then
        # System-wide daemon (runs as root)
        cat > "$plist_file" << LAUNCHD_PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL_DIR}/prometheus</string>
        <string>--config.file=${CONFIG_DIR}/prometheus.yml</string>
        <string>--storage.tsdb.path=${DATA_DIR}</string>
        <string>--web.console.templates=${CONFIG_DIR}/consoles</string>
        <string>--web.console.libraries=${CONFIG_DIR}/console_libraries</string>
        <string>--web.listen-address=0.0.0.0:9090</string>
        <string>--web.enable-lifecycle</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>StandardOutPath</key>
    <string>${LOG_DIR}/prometheus.log</string>

    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/prometheus.error.log</string>

    <key>WorkingDirectory</key>
    <string>${DATA_DIR}</string>

    <key>SoftResourceLimits</key>
    <dict>
        <key>NumberOfFiles</key>
        <integer>65536</integer>
    </dict>

    <key>HardResourceLimits</key>
    <dict>
        <key>NumberOfFiles</key>
        <integer>65536</integer>
    </dict>
</dict>
</plist>
LAUNCHD_PLIST
        sudo chown root:wheel "$plist_file"
        sudo chmod 644 "$plist_file"
    else
        # User agent (runs as current user)
        cat > "$plist_file" << LAUNCHD_PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL_DIR}/prometheus</string>
        <string>--config.file=${CONFIG_DIR}/prometheus.yml</string>
        <string>--storage.tsdb.path=${DATA_DIR}</string>
        <string>--web.console.templates=${CONFIG_DIR}/consoles</string>
        <string>--web.console.libraries=${CONFIG_DIR}/console_libraries</string>
        <string>--web.listen-address=127.0.0.1:9090</string>
        <string>--web.enable-lifecycle</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>StandardOutPath</key>
    <string>${LOG_DIR}/prometheus.log</string>

    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/prometheus.error.log</string>

    <key>WorkingDirectory</key>
    <string>${DATA_DIR}</string>
</dict>
</plist>
LAUNCHD_PLIST
        chmod 644 "$plist_file"
    fi

    log_info "Launchd plist created at $plist_file"
}

# Load and start the service
start_service() {
    local plist_file="${PLIST_DIR}/${PLIST_NAME}.plist"

    log_info "Loading launchd service..."

    # Unload if already loaded
    if [[ "${SYSTEM_INSTALL:-false}" == "true" ]]; then
        sudo launchctl unload "$plist_file" 2>/dev/null || true
        sudo launchctl load "$plist_file"
    else
        launchctl unload "$plist_file" 2>/dev/null || true
        launchctl load "$plist_file"
    fi

    # Wait for service to start
    sleep 3

    # Check if service is running
    if pgrep -f "prometheus.*--config.file" > /dev/null; then
        log_info "Prometheus service started successfully"
    else
        log_warn "Prometheus may not have started. Check logs at ${LOG_DIR}/prometheus.log"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."

    # Check binary version
    local version
    version=$("${INSTALL_DIR}/prometheus" --version 2>&1 | head -1)
    log_info "Installed: $version"

    # Check if process is running
    if pgrep -f "prometheus.*--config.file" > /dev/null; then
        log_info "Process status: running"
    else
        log_warn "Process status: not running"
    fi

    # Check if port 9090 is listening
    if lsof -i :9090 > /dev/null 2>&1; then
        log_info "Prometheus is listening on port 9090"
    else
        log_warn "Prometheus is not yet listening on port 9090"
    fi

    # Validate configuration
    log_info "Validating configuration..."
    if "${INSTALL_DIR}/promtool" check config "${CONFIG_DIR}/prometheus.yml"; then
        log_info "Configuration is valid"
    else
        log_error "Configuration validation failed"
        exit 1
    fi
}

# Print post-installation information
print_info() {
    local listen_addr
    if [[ "${SYSTEM_INSTALL:-false}" == "true" ]]; then
        listen_addr="0.0.0.0:9090"
    else
        listen_addr="127.0.0.1:9090"
    fi

    cat << EOF

${GREEN}========================================${NC}
${GREEN}Prometheus Installation Complete!${NC}
${GREEN}========================================${NC}

Version:        ${PROMETHEUS_VERSION}
Config file:    ${CONFIG_DIR}/prometheus.yml
Data directory: ${DATA_DIR}
Log directory:  ${LOG_DIR}
Service:        ${PLIST_NAME}

${YELLOW}Useful commands:${NC}
  Check status:     launchctl list | grep prometheus
  View logs:        tail -f ${LOG_DIR}/prometheus.log
  Stop service:     launchctl unload ${PLIST_DIR}/${PLIST_NAME}.plist
  Start service:    launchctl load ${PLIST_DIR}/${PLIST_NAME}.plist
  Restart service:  launchctl unload ${PLIST_DIR}/${PLIST_NAME}.plist && launchctl load ${PLIST_DIR}/${PLIST_NAME}.plist

${YELLOW}Access Prometheus:${NC}
  Web UI:           http://localhost:9090
  API:              http://localhost:9090/api/v1/

${YELLOW}Configuration:${NC}
  Edit config:      nano ${CONFIG_DIR}/prometheus.yml
  Validate config:  promtool check config ${CONFIG_DIR}/prometheus.yml

EOF
}

# Main installation function
main() {
    log_info "Starting Prometheus installation for macOS..."

    parse_args "$@"
    check_prerequisites
    create_directories
    download_prometheus
    create_default_config
    create_launchd_plist
    start_service
    verify_installation
    print_info

    log_info "Installation completed successfully!"
}

# Run main function
main "$@"
