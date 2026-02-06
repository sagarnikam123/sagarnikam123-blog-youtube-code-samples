#!/bin/bash
# =============================================================================
# Apache SkyWalking - Prerequisites Installation Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Check Java Installation
# =============================================================================
check_java() {
    log_info "Checking Java installation..."

    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)

        # Handle version format like "11.0.x" or "17.0.x"
        if [[ "$JAVA_VERSION" == "1" ]]; then
            JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f2)
        fi

        if [[ "$JAVA_VERSION" -ge 11 ]]; then
            log_info "Java $JAVA_VERSION found - OK"
            java -version
            return 0
        else
            log_warn "Java version $JAVA_VERSION found, but Java 11+ is required"
            return 1
        fi
    else
        log_error "Java not found"
        return 1
    fi
}

# =============================================================================
# Install Java (if needed)
# =============================================================================
install_java() {
    log_info "Installing Java 17..."

    OS_TYPE="$(uname -s)"

    case "$OS_TYPE" in
        Linux*)
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y openjdk-17-jdk
            elif command -v yum &> /dev/null; then
                sudo yum install -y java-17-openjdk java-17-openjdk-devel
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y java-17-openjdk java-17-openjdk-devel
            else
                log_error "Unsupported package manager. Please install Java 17 manually."
                exit 1
            fi
            ;;
        Darwin*)
            if command -v brew &> /dev/null; then
                brew install openjdk@17
                log_info "Add to your shell profile:"
                echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"'
            else
                log_error "Homebrew not found. Please install Java 17 manually."
                log_info "Download from: https://adoptium.net/temurin/releases/"
                exit 1
            fi
            ;;
        *)
            log_error "Unsupported OS: $OS_TYPE"
            log_info "Please install Java 17 manually from: https://adoptium.net/temurin/releases/"
            exit 1
            ;;
    esac
}

# =============================================================================
# Check System Requirements
# =============================================================================
check_system_requirements() {
    log_info "Checking system requirements..."

    # Check available memory
    OS_TYPE="$(uname -s)"
    case "$OS_TYPE" in
        Linux*)
            TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
            ;;
        Darwin*)
            TOTAL_MEM=$(($(sysctl -n hw.memsize) / 1024 / 1024))
            ;;
    esac

    if [[ "$TOTAL_MEM" -lt 4096 ]]; then
        log_warn "System has ${TOTAL_MEM}MB RAM. Recommended: 4GB+"
    else
        log_info "Memory: ${TOTAL_MEM}MB - OK"
    fi

    # Check disk space
    AVAILABLE_DISK=$(df -m "$PROJECT_DIR" | awk 'NR==2 {print $4}')
    if [[ "$AVAILABLE_DISK" -lt 20480 ]]; then
        log_warn "Available disk: ${AVAILABLE_DISK}MB. Recommended: 20GB+"
    else
        log_info "Disk space: ${AVAILABLE_DISK}MB - OK"
    fi
}

# =============================================================================
# Create Directory Structure
# =============================================================================
create_directories() {
    log_info "Creating directory structure..."

    mkdir -p "$PROJECT_DIR"/{data,logs,downloads}
    mkdir -p "$PROJECT_DIR"/data/{banyandb,skywalking}

    log_info "Directories created successfully"
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  Apache SkyWalking - Prerequisites Check"
    echo "=============================================="
    echo ""

    check_system_requirements
    echo ""

    if ! check_java; then
        echo ""
        read -p "Would you like to install Java 17? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_java
            check_java
        else
            log_error "Java 11+ is required. Please install it manually."
            exit 1
        fi
    fi

    echo ""
    create_directories

    echo ""
    log_info "Prerequisites check completed successfully!"
}

main "$@"
