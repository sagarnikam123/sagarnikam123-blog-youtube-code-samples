#!/bin/bash
# =============================================================================
# SkyWalking Minikube Setup Script
# =============================================================================
# Complete setup for testing SkyWalking on local Minikube
#
# Usage:
#   ./scripts/minikube-setup.sh [command]
#
# Commands:
#   start       - Start Minikube and install SkyWalking
#   install     - Install SkyWalking only (Minikube must be running)
#   status      - Show status of all components
#   ui          - Open SkyWalking UI in browser
#   logs        - Show OAP logs
#   uninstall   - Remove SkyWalking
#   stop        - Stop Minikube
#   clean       - Delete Minikube cluster completely
#
# Examples:
#   ./scripts/minikube-setup.sh start
#   ./scripts/minikube-setup.sh ui
#   ./scripts/minikube-setup.sh logs
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
NAMESPACE="skywalking"
RELEASE_NAME="skywalking"
HELM_CHART="oci://registry-1.docker.io/apache/skywalking-helm"
HELM_VERSION="4.8.0"

# Minikube settings
MINIKUBE_CPUS=4
MINIKUBE_MEMORY=8192
MINIKUBE_DRIVER="docker"  # or virtualbox, hyperkit

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v minikube &> /dev/null; then
        log_error "minikube is not installed"
        log_info "Install: brew install minikube (macOS) or see https://minikube.sigs.k8s.io/docs/start/"
        exit 1
    fi

    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        log_info "Install: brew install helm (macOS)"
        exit 1
    fi

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        log_info "Install: brew install kubectl (macOS)"
        exit 1
    fi

    log_success "Prerequisites OK"
}

# Start Minikube
start_minikube() {
    log_info "Starting Minikube..."

    if minikube status &> /dev/null; then
        log_info "Minikube is already running"
    else
        minikube start \
            --cpus=${MINIKUBE_CPUS} \
            --memory=${MINIKUBE_MEMORY} \
            --driver=${MINIKUBE_DRIVER}
    fi

    # Wait for cluster to be ready
    log_info "Waiting for cluster to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=120s

    log_success "Minikube is ready"
    minikube status
}

# Install SkyWalking
install_skywalking() {
    local values_file="${BASE_DIR}/environments/minikube/values.yaml"

    if [[ ! -f "$values_file" ]]; then
        log_error "Minikube values file not found: ${values_file}"
        exit 1
    fi

    # Create namespace
    if ! kubectl get namespace "${NAMESPACE}" &> /dev/null; then
        log_info "Creating namespace: ${NAMESPACE}"
        kubectl create namespace "${NAMESPACE}"
    fi

    # Check if already installed
    if helm status "${RELEASE_NAME}" -n "${NAMESPACE}" &> /dev/null; then
        log_warn "SkyWalking is already installed"
        read -p "Upgrade existing installation? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Upgrading SkyWalking..."
            helm upgrade "${RELEASE_NAME}" "${HELM_CHART}" \
                --version "${HELM_VERSION}" \
                -n "${NAMESPACE}" \
                -f "${values_file}" \
                --wait --timeout=10m
        else
            return 0
        fi
    else
        log_info "Installing SkyWalking..."
        helm install "${RELEASE_NAME}" "${HELM_CHART}" \
            --version "${HELM_VERSION}" \
            -n "${NAMESPACE}" \
            -f "${values_file}" \
            --wait --timeout=10m
    fi

    log_success "SkyWalking installed successfully"
}

# Show status
show_status() {
    echo ""
    echo "=============================================="
    echo "SkyWalking Status"
    echo "=============================================="
    echo ""

    log_info "Minikube Status:"
    minikube status || true
    echo ""

    log_info "Helm Release:"
    helm list -n "${NAMESPACE}" || true
    echo ""

    log_info "Pods:"
    kubectl get pods -n "${NAMESPACE}" -o wide || true
    echo ""

    log_info "Services:"
    kubectl get svc -n "${NAMESPACE}" || true
    echo ""

    log_info "PVCs:"
    kubectl get pvc -n "${NAMESPACE}" || true
    echo ""
}

# Open UI
open_ui() {
    log_info "Opening SkyWalking UI..."

    # Check if pods are ready
    if ! kubectl get pods -n "${NAMESPACE}" -l app=skywalking,component=ui -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q "Running"; then
        log_warn "UI pod is not ready yet. Checking status..."
        kubectl get pods -n "${NAMESPACE}"
        exit 1
    fi

    # Get Minikube service URL
    local url=$(minikube service "${RELEASE_NAME}-ui" -n "${NAMESPACE}" --url 2>/dev/null)

    if [[ -n "$url" ]]; then
        log_success "SkyWalking UI available at: ${url}"

        # Try to open in browser
        if command -v open &> /dev/null; then
            open "$url"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$url"
        else
            log_info "Open this URL in your browser: ${url}"
        fi
    else
        # Fallback to port-forward
        log_info "Using port-forward..."
        log_info "UI will be available at: http://localhost:8080"
        kubectl port-forward svc/${RELEASE_NAME}-ui 8080:80 -n "${NAMESPACE}"
    fi
}

# Show logs
show_logs() {
    local component="${1:-oap}"

    log_info "Showing logs for ${component}..."

    case $component in
        oap)
            kubectl logs -f -l app=skywalking,component=oap -n "${NAMESPACE}" --tail=100
            ;;
        ui)
            kubectl logs -f -l app=skywalking,component=ui -n "${NAMESPACE}" --tail=100
            ;;
        banyandb)
            kubectl logs -f -l app.kubernetes.io/name=banyandb -n "${NAMESPACE}" --tail=100
            ;;
        *)
            log_error "Unknown component: ${component}"
            log_info "Available: oap, ui, banyandb"
            ;;
    esac
}

# Uninstall SkyWalking
uninstall_skywalking() {
    log_info "Uninstalling SkyWalking..."

    helm uninstall "${RELEASE_NAME}" -n "${NAMESPACE}" || true

    # Clean up PVCs
    read -p "Delete PVCs (data will be lost)? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete pvc --all -n "${NAMESPACE}" || true
    fi

    log_success "SkyWalking uninstalled"
}

# Stop Minikube
stop_minikube() {
    log_info "Stopping Minikube..."
    minikube stop
    log_success "Minikube stopped"
}

# Clean everything
clean_all() {
    log_warn "This will delete the entire Minikube cluster!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        minikube delete
        log_success "Minikube cluster deleted"
    fi
}

# Print usage
print_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start Minikube and install SkyWalking"
    echo "  install     - Install SkyWalking only"
    echo "  status      - Show status of all components"
    echo "  ui          - Open SkyWalking UI in browser"
    echo "  logs [comp] - Show logs (oap|ui|banyandb)"
    echo "  uninstall   - Remove SkyWalking"
    echo "  stop        - Stop Minikube"
    echo "  clean       - Delete Minikube cluster"
    echo ""
}

# Main
main() {
    local command="${1:-start}"

    case $command in
        start)
            check_prerequisites
            start_minikube
            install_skywalking
            echo ""
            show_status
            echo ""
            log_success "Setup complete!"
            log_info "Run './scripts/minikube-setup.sh ui' to open the UI"
            ;;
        install)
            check_prerequisites
            install_skywalking
            show_status
            ;;
        status)
            show_status
            ;;
        ui)
            open_ui
            ;;
        logs)
            show_logs "${2:-oap}"
            ;;
        uninstall)
            uninstall_skywalking
            ;;
        stop)
            stop_minikube
            ;;
        clean)
            clean_all
            ;;
        help|--help|-h)
            print_usage
            ;;
        *)
            log_error "Unknown command: ${command}"
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
