#!/bin/bash
# =============================================================================
# Apache SkyWalking - Java Agent Installation Script
# =============================================================================
# Downloads and configures the SkyWalking Java Agent for application monitoring

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
AGENT_VERSION="${AGENT_VERSION:-9.5.0}"
AGENT_HOME="$PROJECT_DIR/skywalking-agent"
DOWNLOAD_DIR="$PROJECT_DIR/downloads"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Download Java Agent
# =============================================================================
download_agent() {
    log_info "Downloading SkyWalking Java Agent v${AGENT_VERSION}..."

    mkdir -p "$DOWNLOAD_DIR"

    DOWNLOAD_URL="https://dlcdn.apache.org/skywalking/java-agent/${AGENT_VERSION}/apache-skywalking-java-agent-${AGENT_VERSION}.tar.gz"
    TARBALL="$DOWNLOAD_DIR/skywalking-agent-${AGENT_VERSION}.tar.gz"

    if [[ -f "$TARBALL" ]]; then
        log_info "Agent tarball already exists, skipping download"
    else
        log_info "Downloading from: $DOWNLOAD_URL"
        curl -fSL "$DOWNLOAD_URL" -o "$TARBALL"
    fi
}

# =============================================================================
# Install Java Agent
# =============================================================================
install_agent() {
    log_info "Installing Java Agent..."

    TARBALL="$DOWNLOAD_DIR/skywalking-agent-${AGENT_VERSION}.tar.gz"

    if [[ -d "$AGENT_HOME" ]]; then
        log_warn "Removing existing agent installation..."
        rm -rf "$AGENT_HOME"
    fi

    mkdir -p "$AGENT_HOME"
    tar -xzf "$TARBALL" -C "$AGENT_HOME" --strip-components=1

    log_info "Java Agent installed to: $AGENT_HOME"
}

# =============================================================================
# Configure Agent
# =============================================================================
configure_agent() {
    log_info "Configuring Java Agent..."

    CONFIG_FILE="$AGENT_HOME/config/agent.config"

    # Backup original
    cp "$CONFIG_FILE" "$CONFIG_FILE.bak"

    # Update OAP server address
    if [[ "$(uname)" == "Darwin" ]]; then
        sed -i '' 's/collector.backend_service=.*/collector.backend_service=127.0.0.1:11800/' "$CONFIG_FILE"
    else
        sed -i 's/collector.backend_service=.*/collector.backend_service=127.0.0.1:11800/' "$CONFIG_FILE"
    fi

    log_info "Agent configured to connect to localhost:11800"
}

# =============================================================================
# Print Usage Instructions
# =============================================================================
print_usage() {
    echo ""
    echo "=============================================="
    echo "  Java Agent Usage Instructions"
    echo "=============================================="
    echo ""
    echo "Add the following JVM arguments to your Java application:"
    echo ""
    echo "  -javaagent:$AGENT_HOME/skywalking-agent.jar"
    echo "  -Dskywalking.agent.service_name=YOUR_SERVICE_NAME"
    echo ""
    echo "Example:"
    echo "  java -javaagent:$AGENT_HOME/skywalking-agent.jar \\"
    echo "       -Dskywalking.agent.service_name=my-app \\"
    echo "       -jar your-application.jar"
    echo ""
    echo "For Spring Boot applications, add to JAVA_OPTS:"
    echo "  export JAVA_OPTS=\"-javaagent:$AGENT_HOME/skywalking-agent.jar -Dskywalking.agent.service_name=my-spring-app\""
    echo ""
    echo "Configuration file: $AGENT_HOME/config/agent.config"
    echo ""
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  SkyWalking Java Agent - v${AGENT_VERSION}"
    echo "=============================================="
    echo ""

    download_agent
    install_agent
    configure_agent
    print_usage
}

main "$@"
