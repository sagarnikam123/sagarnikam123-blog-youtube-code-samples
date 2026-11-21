#!/bin/bash
# =============================================================================
# SkyWalking Helm Installation Script for AWS EKS
# =============================================================================
# Usage:
#   ./scripts/install.sh [environment] [options]
#
# Environments:
#   dev         - Development (minimal resources)
#   staging     - Staging (production-like, reduced scale)
#   production  - Production (full HA)
#
# Options:
#   --dry-run   - Show what would be installed without applying
#   --debug     - Enable Helm debug output
#   --wait      - Wait for all pods to be ready
#
# Examples:
#   ./scripts/install.sh dev
#   ./scripts/install.sh production --wait
#   ./scripts/install.sh staging --dry-run
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HELM_CHART="oci://registry-1.docker.io/apache/skywalking-helm"
HELM_VERSION="4.8.0"
RELEASE_NAME="skywalking"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="${1:-dev}"

# Add minikube to valid environments
valid_envs=("dev" "staging" "production" "minikube")
DRY_RUN=""
DEBUG=""
WAIT=""
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
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    if [[ ! " ${valid_envs[*]} " =~ " ${ENVIRONMENT} " ]]; then
        log_error "Invalid environment: ${ENVIRONMENT}"
        log_info "Valid environments: ${valid_envs[*]}"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi

    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check if EBS CSI driver is installed (for production)
    if [[ "$ENVIRONMENT" == "production" ]] || [[ "$ENVIRONMENT" == "staging" ]]; then
        if ! kubectl get storageclass gp3-skywalking &> /dev/null; then
            log_warn "Storage class 'gp3-skywalking' not found"
            log_info "Creating storage classes..."
            kubectl apply -f "${BASE_DIR}/base/storage-class.yaml"
        fi
    fi

    log_success "Prerequisites check passed"
}

# Set namespace based on environment
get_namespace() {
    case $ENVIRONMENT in
        dev)
            echo "skywalking-dev"
            ;;
        staging)
            echo "skywalking-staging"
            ;;
        production)
            echo "skywalking"
            ;;
        minikube)
            echo "skywalking"
            ;;
    esac
}

# Apply base resources
apply_base_resources() {
    local namespace=$(get_namespace)

    log_info "Applying base resources for namespace: ${namespace}..."

    # Create namespace if it doesn't exist
    if ! kubectl get namespace "${namespace}" &> /dev/null; then
        log_info "Creating namespace: ${namespace}"
        kubectl create namespace "${namespace}"
    fi

    # Apply storage classes (idempotent)
    if [[ "$ENVIRONMENT" != "dev" ]]; then
        kubectl apply -f "${BASE_DIR}/base/storage-class.yaml"
    fi

    # Apply service accounts and RBAC
    sed "s/namespace: skywalking/namespace: ${namespace}/g" \
        "${BASE_DIR}/base/service-account.yaml" | kubectl apply -f -

    # Apply network policies (optional, comment out if not using)
    if [[ "$ENVIRONMENT" == "production" ]]; then
        sed "s/namespace: skywalking/namespace: ${namespace}/g" \
            "${BASE_DIR}/base/network-policy.yaml" | kubectl apply -f - || true
    fi

    log_success "Base resources applied"
}

# Install SkyWalking
install_skywalking() {
    local namespace=$(get_namespace)
    local values_file="${BASE_DIR}/environments/${ENVIRONMENT}/values.yaml"

    if [[ ! -f "$values_file" ]]; then
        log_error "Values file not found: ${values_file}"
        exit 1
    fi

    log_info "Installing SkyWalking (${ENVIRONMENT}) in namespace: ${namespace}"
    log_info "Using values file: ${values_file}"
    log_info "Helm chart: ${HELM_CHART}:${HELM_VERSION}"

    # Check if release exists
    if helm status "${RELEASE_NAME}" -n "${namespace}" &> /dev/null; then
        log_warn "Release '${RELEASE_NAME}' already exists. Use upgrade.sh to update."
        read -p "Do you want to upgrade instead? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            helm upgrade "${RELEASE_NAME}" "${HELM_CHART}" \
                --version "${HELM_VERSION}" \
                -n "${namespace}" \
                -f "${values_file}" \
                ${DRY_RUN} ${DEBUG} ${WAIT}
        else
            exit 0
        fi
    else
        helm install "${RELEASE_NAME}" "${HELM_CHART}" \
            --version "${HELM_VERSION}" \
            -n "${namespace}" \
            -f "${values_file}" \
            ${DRY_RUN} ${DEBUG} ${WAIT}
    fi

    log_success "SkyWalking installation completed"
}

# Post-installation info
show_post_install_info() {
    local namespace=$(get_namespace)

    echo ""
    echo "=============================================="
    echo -e "${GREEN}SkyWalking Installation Complete${NC}"
    echo "=============================================="
    echo ""
    echo "Environment: ${ENVIRONMENT}"
    echo "Namespace:   ${namespace}"
    echo ""
    echo "Check pod status:"
    echo "  kubectl get pods -n ${namespace}"
    echo ""
    echo "Access UI (port-forward):"
    echo "  kubectl port-forward svc/${RELEASE_NAME}-ui 8080:80 -n ${namespace}"
    echo "  Open: http://localhost:8080"
    echo ""
    echo "Agent connection endpoints:"
    echo "  gRPC: ${RELEASE_NAME}-oap.${namespace}.svc:11800"
    echo "  HTTP: ${RELEASE_NAME}-oap.${namespace}.svc:12800"
    echo ""

    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "Production Notes:"
        echo "  - Configure ALB Ingress with your domain"
        echo "  - Set up monitoring with Prometheus"
        echo "  - Configure backup for BanyanDB"
        echo ""
    fi
}

# Main execution
main() {
    echo ""
    echo "=============================================="
    echo "SkyWalking Helm Installation"
    echo "=============================================="
    echo ""

    validate_environment
    check_prerequisites
    apply_base_resources
    install_skywalking

    if [[ -z "$DRY_RUN" ]]; then
        show_post_install_info
    fi
}

main
