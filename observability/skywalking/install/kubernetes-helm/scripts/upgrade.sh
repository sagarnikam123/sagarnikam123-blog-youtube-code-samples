#!/bin/bash
# =============================================================================
# SkyWalking Helm Upgrade Script
# =============================================================================
# Usage:
#   ./scripts/upgrade.sh [environment] [options]
#
# Options:
#   --dry-run     - Show what would change without applying
#   --debug       - Enable Helm debug output
#   --wait        - Wait for all pods to be ready
#   --version     - Specify Helm chart version (default: 4.8.0)
#   --rollback    - Rollback to previous release
#
# Examples:
#   ./scripts/upgrade.sh production
#   ./scripts/upgrade.sh staging --dry-run
#   ./scripts/upgrade.sh production --rollback
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
HELM_CHART="oci://registry-1.docker.io/apache/skywalking-helm"
HELM_VERSION="4.8.0"
RELEASE_NAME="skywalking"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="${1:-production}"
DRY_RUN=""
DEBUG=""
WAIT=""
ROLLBACK=false
TIMEOUT="600s"

# Parse arguments
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --debug)
            DEBUG="--debug"
            shift
            ;;
        --wait)
            WAIT="--wait --timeout=${TIMEOUT}"
            shift
            ;;
        --version)
            HELM_VERSION="$2"
            shift 2
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

get_namespace() {
    case $ENVIRONMENT in
        dev) echo "skywalking-dev" ;;
        staging) echo "skywalking-staging" ;;
        production) echo "skywalking" ;;
    esac
}

# Show current release info
show_release_info() {
    local namespace=$(get_namespace)

    log_info "Current release information:"
    helm history "${RELEASE_NAME}" -n "${namespace}" --max 5 || true
    echo ""
}

# Perform rollback
do_rollback() {
    local namespace=$(get_namespace)

    log_info "Rolling back to previous release..."
    show_release_info

    read -p "Confirm rollback? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        helm rollback "${RELEASE_NAME}" -n "${namespace}" ${WAIT}
        log_success "Rollback completed"
    else
        log_info "Rollback cancelled"
    fi
}

# Perform upgrade
do_upgrade() {
    local namespace=$(get_namespace)
    local values_file="${BASE_DIR}/environments/${ENVIRONMENT}/values.yaml"

    if [[ ! -f "$values_file" ]]; then
        log_error "Values file not found: ${values_file}"
        exit 1
    fi

    log_info "Upgrading SkyWalking (${ENVIRONMENT}) in namespace: ${namespace}"
    log_info "Chart version: ${HELM_VERSION}"

    # Show diff if possible
    if command -v helm-diff &> /dev/null && [[ -z "$DRY_RUN" ]]; then
        log_info "Showing changes (helm diff):"
        helm diff upgrade "${RELEASE_NAME}" "${HELM_CHART}" \
            --version "${HELM_VERSION}" \
            -n "${namespace}" \
            -f "${values_file}" || true
        echo ""
        read -p "Proceed with upgrade? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Upgrade cancelled"
            exit 0
        fi
    fi

    # Perform upgrade
    helm upgrade "${RELEASE_NAME}" "${HELM_CHART}" \
        --version "${HELM_VERSION}" \
        -n "${namespace}" \
        -f "${values_file}" \
        ${DRY_RUN} ${DEBUG} ${WAIT}

    log_success "Upgrade completed"

    # Show new status
    if [[ -z "$DRY_RUN" ]]; then
        echo ""
        log_info "New release status:"
        helm status "${RELEASE_NAME}" -n "${namespace}"
    fi
}

# Main
main() {
    echo ""
    echo "=============================================="
    echo "SkyWalking Helm Upgrade"
    echo "=============================================="
    echo ""

    local namespace=$(get_namespace)

    # Check if release exists
    if ! helm status "${RELEASE_NAME}" -n "${namespace}" &> /dev/null; then
        log_error "Release '${RELEASE_NAME}' not found in namespace '${namespace}'"
        log_info "Use install.sh to install first"
        exit 1
    fi

    show_release_info

    if [[ "$ROLLBACK" == true ]]; then
        do_rollback
    else
        do_upgrade
    fi
}

main
