#!/bin/bash
#
# Prometheus Binary Installer for Linux
# Downloads and installs Prometheus from official releases
#
# Usage: ./install-linux.sh [--version VERSION] [--data-dir PATH] [--config PATH]
#
# Requirements: 1.1, 1.2, 1.5, 1.6, 1.9

set -euo pipefail

# Default values
PROMETHEUS_VERSION="${PROMETHEUS_VERSION:-2.54.1}"
PROMETHEUS_USER="prometheus"
PROMETHEUS_GROUP="prometheus"
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/etc/prometheus"
DATA_DIR="/var/lib/prometheus"
DOWNLOAD_URL="https://github.com/prometheus/prometheus/releases/download"

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
        aarch64|arm64)
            echo "arm64"
            ;;
        armv7l|armv7)
            echo "armv7"
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
    if [[ "$os" != "linux" ]]; then
        log_error "This script is for Linux only. Detected: $os"
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
Prometheus Binary Installer for Linux

Usage: $0 [OPTIONS]

Options:
    --version VERSION    Prometheus version to install (default: $PROMETHEUS_VERSION)
    --data-dir PATH      Data directory path (default: $DATA_DIR)
    --config PATH        Custom prometheus.yml config file path
    --help, -h           Show this help message

Examples:
    $0
    $0 --version 2.54.1
    $0 --data-dir /data/prometheus --config /path/to/prometheus.yml
EOF
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Create prometheus user and group
create_user() {
    log_info "Creating prometheus user and group..."

    if ! getent group "$PROMETHEUS_GROUP" > /dev/null 2>&1; then
        groupadd --system "$PROMETHEUS_GROUP"
        log_info "Created group: $PROMETHEUS_GROUP"
    else
        log_info "Group $PROMETHEUS_GROUP already exists"
    fi

    if ! id "$PROMETHEUS_USER" > /dev/null 2>&1; then
        useradd --system --no-create-home --shell /bin/false \
            -g "$PROMETHEUS_GROUP" "$PROMETHEUS_USER"
        log_info "Created user: $PROMETHEUS_USER"
    else
        log_info "User $PROMETHEUS_USER already exists"
    fi
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
    elif command -v wget &> /dev/null; then
        wget -q "$url" -O "${tmp_dir}/${filename}"
    else
        log_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi

    log_info "Extracting archive..."
    tar -xzf "${tmp_dir}/${filename}" -C "$tmp_dir"

    local extract_dir="${tmp_dir}/prometheus-${PROMETHEUS_VERSION}.${os}-${arch}"

    # Install binaries
    log_info "Installing binaries to $INSTALL_DIR..."
    cp "${extract_dir}/prometheus" "$INSTALL_DIR/"
    cp "${extract_dir}/promtool" "$INSTALL_DIR/"
    chmod 755 "${INSTALL_DIR}/prometheus" "${INSTALL_DIR}/promtool"

    # Install console templates and libraries
    log_info "Installing console templates..."
    mkdir -p "${CONFIG_DIR}/consoles" "${CONFIG_DIR}/console_libraries"
    cp -r "${extract_dir}/consoles/"* "${CONFIG_DIR}/consoles/" 2>/dev/null || true
    cp -r "${extract_dir}/console_libraries/"* "${CONFIG_DIR}/console_libraries/" 2>/dev/null || true

    # Cleanup
    rm -rf "$tmp_dir"

    log_info "Prometheus binaries installed successfully"
}

# Create directories with proper permissions
create_directories() {
    log_info "Creating directories..."

    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"

    chown -R "${PROMETHEUS_USER}:${PROMETHEUS_GROUP}" "$CONFIG_DIR"
    chown -R "${PROMETHEUS_USER}:${PROMETHEUS_GROUP}" "$DATA_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$DATA_DIR"

    log_info "Directories created with proper permissions"
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
# Generated by install-linux.sh

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

    chown "${PROMETHEUS_USER}:${PROMETHEUS_GROUP}" "$config_file"
    chmod 644 "$config_file"

    log_info "Configuration file created at $config_file"
}

# Create systemd service unit
create_systemd_service() {
    local service_file="/etc/systemd/system/prometheus.service"

    log_info "Creating systemd service unit..."

    cat > "$service_file" << SYSTEMD_SERVICE
[Unit]
Description=Prometheus Monitoring System
Documentation=https://prometheus.io/docs/introduction/overview/
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=${PROMETHEUS_USER}
Group=${PROMETHEUS_GROUP}
ExecReload=/bin/kill -HUP \$MAINPID
ExecStart=${INSTALL_DIR}/prometheus \\
    --config.file=${CONFIG_DIR}/prometheus.yml \\
    --storage.tsdb.path=${DATA_DIR} \\
    --web.console.templates=${CONFIG_DIR}/consoles \\
    --web.console.libraries=${CONFIG_DIR}/console_libraries \\
    --web.listen-address=0.0.0.0:9090 \\
    --web.enable-lifecycle

SyslogIdentifier=prometheus
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${DATA_DIR}
PrivateTmp=yes
PrivateDevices=yes

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
SYSTEMD_SERVICE

    chmod 644 "$service_file"

    log_info "Systemd service unit created at $service_file"
}

# Enable and start the service
enable_service() {
    log_info "Reloading systemd daemon..."
    systemctl daemon-reload

    log_info "Enabling prometheus service..."
    systemctl enable prometheus

    log_info "Starting prometheus service..."
    systemctl start prometheus

    # Wait for service to start
    sleep 3

    if systemctl is-active --quiet prometheus; then
        log_info "Prometheus service started successfully"
    else
        log_error "Failed to start Prometheus service"
        systemctl status prometheus --no-pager
        exit 1
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."

    # Check binary version
    local version
    version=$("${INSTALL_DIR}/prometheus" --version 2>&1 | head -1)
    log_info "Installed: $version"

    # Check if service is running
    if systemctl is-active --quiet prometheus; then
        log_info "Service status: running"
    else
        log_warn "Service status: not running"
    fi

    # Check if port 9090 is listening
    if command -v ss &> /dev/null; then
        if ss -tlnp | grep -q ":9090"; then
            log_info "Prometheus is listening on port 9090"
        else
            log_warn "Prometheus is not yet listening on port 9090"
        fi
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
    cat << EOF

${GREEN}========================================${NC}
${GREEN}Prometheus Installation Complete!${NC}
${GREEN}========================================${NC}

Version:        ${PROMETHEUS_VERSION}
Config file:    ${CONFIG_DIR}/prometheus.yml
Data directory: ${DATA_DIR}
Service:        prometheus.service

${YELLOW}Useful commands:${NC}
  Check status:     sudo systemctl status prometheus
  View logs:        sudo journalctl -u prometheus -f
  Restart service:  sudo systemctl restart prometheus
  Reload config:    sudo systemctl reload prometheus

${YELLOW}Access Prometheus:${NC}
  Web UI:           http://localhost:9090
  API:              http://localhost:9090/api/v1/

${YELLOW}Configuration:${NC}
  Edit config:      sudo nano ${CONFIG_DIR}/prometheus.yml
  Validate config:  promtool check config ${CONFIG_DIR}/prometheus.yml

EOF
}

# Main installation function
main() {
    log_info "Starting Prometheus installation..."

    parse_args "$@"
    check_root
    create_user
    download_prometheus
    create_directories
    create_default_config
    create_systemd_service
    enable_service
    verify_installation
    print_info

    log_info "Installation completed successfully!"
}

# Run main function
main "$@"
