#!/bin/bash
# =============================================================================
# SkyWalking Full Cluster Mode Cleanup Script
# =============================================================================
# Safely removes Apache SkyWalking full cluster mode deployment
# Supports multiple environments: minikube, eks-dev, eks-prod
#
# Usage:
#   ./cleanup-skywalking-cluster.sh <environment>
#   ./cleanup-skywalking-cluster.sh minikube
#   ./cleanup-skywalking-cluster.sh eks-prod --delete-pvcs
#   ./cleanup-skywalking-cluster.sh eks-dev --delete-namespace --force
#
# Requirements:
#   - kubectl (configured and connected to target cluster)
#   - helm (v3.0+)
# =============================================================================

set -e  # Exit on error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Configuration
NAMESPACE="skywalking"
RELEASE_NAME="skywalking"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

# Flags
DELETE_PVCS=false
DELETE_NAMESPACE=false
FORCE=false
VERBOSE=false

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────────────"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_usage() {
    cat << EOF
Usage: $(basename "$0") <environment> [options]

Environments:
  minikube    Cleanup from local Minikube cluster
  eks-dev     Cleanup from AWS EKS development environment
  eks-prod    Cleanup from AWS EKS production environment

Options:
  --delete-pvcs       Delete persistent volume claims (WARNING: data loss)
  --delete-namespace  Delete the namespace after cleanup
  --force             Skip confirmation prompts
  --verbose           Enable verbose output
  --help              Display this help message

Examples:
  $(basename "$0") minikube
  $(basename "$0") eks-prod --delete-pvcs
  $(basename "$0") eks-dev --delete-namespace --force

WARNING:
  - Deleting PVCs will result in permanent data loss
  - Use --force flag with caution in production environments

For more information, see: ${PROJECT_ROOT}/README.md
EOF
}

# =============================================================================
# Validation Functions
# =============================================================================

validate_environment() {
    local env="$1"

    case "$env" in
        minikube|eks-dev|eks-prod)
            return 0
            ;;
        *)
            print_error "Invalid environment: $env"
            echo ""
            print_usage
            exit 1
            ;;
    esac
}

check_command() {
    local cmd="$1"

    if command -v "$cmd" &> /dev/null; then
        local version
        case "$cmd" in
            kubectl)
                version=$(kubectl version --client --short 2>/dev/null | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1)
                ;;
            helm)
                version=$(helm version --short 2>/dev/null | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+')
                ;;
        esac
        print_success "$cmd is installed${version:+ ($version)}"
        return 0
    else
        print_error "$cmd is not installed or not in PATH"
        return 1
    fi
}

check_cluster_connectivity() {
    print_section "Checking Cluster Connectivity"

    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        print_info "Please ensure kubectl is configured and cluster is accessible"
        return 1
    fi

    local context
    context=$(kubectl config current-context 2>/dev/null)
    print_success "Connected to cluster (context: $context)"

    return 0
}

check_deployment_exists() {
    print_section "Checking Deployment Status"

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_warning "Namespace '$NAMESPACE' does not exist"
        print_info "Nothing to clean up"
        return 1
    fi

    print_success "Namespace '$NAMESPACE' exists"

    # Check if Helm release exists
    if ! helm list -n "$NAMESPACE" 2>/dev/null | grep -q "$RELEASE_NAME"; then
        print_warning "Helm release '$RELEASE_NAME' not found in namespace '$NAMESPACE'"
        print_info "Will proceed with namespace cleanup if requested"
        return 2  # Partial cleanup needed
    fi

    print_success "Helm release '$RELEASE_NAME' found"

    return 0
}

# =============================================================================
# Confirmation Functions
# =============================================================================

confirm_cleanup() {
    local env="$1"

    if [ "$FORCE" = true ]; then
        print_info "Force mode enabled, skipping confirmation"
        return 0
    fi

    print_section "Cleanup Confirmation"

    echo ""
    print_warning "You are about to remove SkyWalking cluster from: $env"
    echo ""
    echo "This will:"
    echo "  - Uninstall Helm release: $RELEASE_NAME"
    echo "  - Remove all SkyWalking pods and services"

    if [ "$DELETE_PVCS" = true ]; then
        echo -e "  - ${RED}DELETE all persistent volume claims (DATA LOSS)${NC}"
    else
        echo "  - Keep persistent volume claims (data preserved)"
    fi

    if [ "$DELETE_NAMESPACE" = true ]; then
        echo "  - Delete namespace: $NAMESPACE"
    else
        echo "  - Keep namespace: $NAMESPACE"
    fi

    echo ""

    # Get current resources
    local pod_count
    local pvc_count
    pod_count=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
    pvc_count=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)

    echo "Current resources:"
    echo "  - Pods: $pod_count"
    echo "  - PVCs: $pvc_count"

    echo ""
    read -p "Do you want to continue? (yes/no): " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "Cleanup cancelled by user"
        exit 0
    fi

    return 0
}

confirm_pvc_deletion() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    if [ "$DELETE_PVCS" = false ]; then
        return 0
    fi

    print_section "PVC Deletion Warning"

    echo ""
    print_error "WARNING: You are about to delete persistent volume claims!"
    print_error "This will result in PERMANENT DATA LOSS!"
    echo ""

    # List PVCs
    echo "PVCs to be deleted:"
    kubectl get pvc -n "$NAMESPACE" 2>/dev/null || true

    echo ""
    read -p "Are you absolutely sure you want to delete all PVCs? (yes/no): " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "PVC deletion cancelled, will preserve data"
        DELETE_PVCS=false
        return 0
    fi

    print_warning "PVC deletion confirmed"
    return 0
}

# =============================================================================
# Cleanup Functions
# =============================================================================

uninstall_helm_release() {
    print_section "Uninstalling Helm Release"

    if ! helm list -n "$NAMESPACE" 2>/dev/null | grep -q "$RELEASE_NAME"; then
        print_info "Helm release '$RELEASE_NAME' not found, skipping"
        return 0
    fi

    print_info "Uninstalling Helm release: $RELEASE_NAME"

    local helm_cmd="helm uninstall $RELEASE_NAME --namespace $NAMESPACE"

    if [ "$VERBOSE" = true ]; then
        helm_cmd="$helm_cmd --debug"
    fi

    if eval "$helm_cmd"; then
        print_success "Helm release uninstalled successfully"

        # Wait for pods to terminate
        print_info "Waiting for pods to terminate..."
        local timeout=120
        local interval=5
        local elapsed=0

        while [ $elapsed -lt $timeout ]; do
            local pod_count
            pod_count=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)

            if [ "$pod_count" -eq 0 ]; then
                print_success "All pods terminated"
                break
            fi

            echo -ne "\r  Remaining pods: $pod_count (${elapsed}s elapsed)"
            sleep $interval
            elapsed=$((elapsed + interval))
        done

        echo ""  # New line after progress

        return 0
    else
        print_error "Failed to uninstall Helm release"
        print_info "You may need to manually clean up resources"
        return 1
    fi
}

delete_pvcs() {
    if [ "$DELETE_PVCS" = false ]; then
        print_section "Preserving Persistent Volume Claims"
        print_info "PVCs will be kept for data preservation"
        return 0
    fi

    print_section "Deleting Persistent Volume Claims"

    local pvcs
    pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{print $1}')

    if [ -z "$pvcs" ]; then
        print_info "No PVCs found in namespace '$NAMESPACE'"
        return 0
    fi

    print_warning "Deleting PVCs (this will cause data loss)..."

    local deleted_count=0
    local failed_count=0

    for pvc in $pvcs; do
        if kubectl delete pvc "$pvc" -n "$NAMESPACE" --timeout=60s 2>/dev/null; then
            print_success "Deleted PVC: $pvc"
            deleted_count=$((deleted_count + 1))
        else
            print_error "Failed to delete PVC: $pvc"
            failed_count=$((failed_count + 1))
        fi
    done

    if [ $failed_count -gt 0 ]; then
        print_warning "Some PVCs could not be deleted"
        print_info "You may need to manually delete them later"
    fi

    print_info "Deleted $deleted_count PVC(s), $failed_count failed"

    return 0
}

delete_namespace() {
    if [ "$DELETE_NAMESPACE" = false ]; then
        print_section "Preserving Namespace"
        print_info "Namespace '$NAMESPACE' will be kept"
        return 0
    fi

    print_section "Deleting Namespace"

    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_info "Namespace '$NAMESPACE' does not exist"
        return 0
    fi

    print_info "Deleting namespace: $NAMESPACE"

    if kubectl delete namespace "$NAMESPACE" --timeout=120s; then
        print_success "Namespace deleted successfully"
        return 0
    else
        print_error "Failed to delete namespace"
        print_info "Namespace may be stuck in Terminating state"
        print_info "Check for resources with finalizers:"
        print_info "  kubectl get all -n $NAMESPACE"
        print_info "  kubectl api-resources --verbs=list --namespaced -o name | xargs -n 1 kubectl get --show-kind --ignore-not-found -n $NAMESPACE"
        return 1
    fi
}

# =============================================================================
# Status Reporting Functions
# =============================================================================

display_cleanup_summary() {
    print_section "Cleanup Summary"

    local context
    context=$(kubectl config current-context 2>/dev/null)

    echo ""
    echo "Cleanup completed for environment: $ENVIRONMENT"
    echo "Cluster context: $context"
    echo ""

    echo "Resources removed:"
    echo "  ✓ Helm release: $RELEASE_NAME"
    echo "  ✓ All SkyWalking pods and services"

    if [ "$DELETE_PVCS" = true ]; then
        echo "  ✓ Persistent volume claims (data deleted)"
    else
        echo "  - Persistent volume claims (preserved)"
    fi

    if [ "$DELETE_NAMESPACE" = true ]; then
        echo "  ✓ Namespace: $NAMESPACE"
    else
        echo "  - Namespace: $NAMESPACE (preserved)"
    fi

    echo ""

    # Check remaining resources
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        local remaining_pods
        local remaining_pvcs
        remaining_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
        remaining_pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)

        if [ "$remaining_pods" -gt 0 ] || [ "$remaining_pvcs" -gt 0 ]; then
            print_warning "Some resources remain in namespace:"
            [ "$remaining_pods" -gt 0 ] && echo "  - Pods: $remaining_pods"
            [ "$remaining_pvcs" -gt 0 ] && echo "  - PVCs: $remaining_pvcs"
            echo ""
        fi
    fi

    if [ "$DELETE_PVCS" = false ]; then
        print_info "To delete PVCs later, run:"
        print_info "  kubectl delete pvc --all -n $NAMESPACE"
    fi

    if [ "$DELETE_NAMESPACE" = false ]; then
        print_info "To delete namespace later, run:"
        print_info "  kubectl delete namespace $NAMESPACE"
    fi

    echo ""
}

# =============================================================================
# Error Handling Functions
# =============================================================================

handle_cleanup_failure() {
    local exit_code="$1"

    print_header "Cleanup Failed"

    print_error "Cleanup encountered an error (exit code: $exit_code)"

    print_section "Current State"

    # Check namespace
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo "Namespace: $NAMESPACE (still exists)"

        # Check Helm release
        if helm list -n "$NAMESPACE" 2>/dev/null | grep -q "$RELEASE_NAME"; then
            echo "Helm release: $RELEASE_NAME (still installed)"
        else
            echo "Helm release: $RELEASE_NAME (removed)"
        fi

        # Check resources
        echo ""
        echo "Remaining resources:"
        kubectl get all -n "$NAMESPACE" 2>/dev/null || true

        echo ""
        echo "Remaining PVCs:"
        kubectl get pvc -n "$NAMESPACE" 2>/dev/null || true
    else
        echo "Namespace: $NAMESPACE (removed)"
    fi

    print_section "Manual Cleanup Steps"

    cat << EOF

If automatic cleanup failed, try these manual steps:

1. Force delete Helm release:
   helm uninstall $RELEASE_NAME -n $NAMESPACE --wait=false

2. Delete all resources in namespace:
   kubectl delete all --all -n $NAMESPACE

3. Delete PVCs (if needed):
   kubectl delete pvc --all -n $NAMESPACE

4. Force delete namespace (if stuck):
   kubectl delete namespace $NAMESPACE --grace-period=0 --force

5. Remove finalizers from stuck resources:
   kubectl patch pvc <pvc-name> -n $NAMESPACE -p '{"metadata":{"finalizers":null}}'

For more help:
  kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'

EOF
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    # Parse arguments
    if [ $# -eq 0 ]; then
        print_error "No environment specified"
        echo ""
        print_usage
        exit 1
    fi

    ENVIRONMENT="$1"
    shift

    # Parse options
    while [ $# -gt 0 ]; do
        case "$1" in
            --delete-pvcs)
                DELETE_PVCS=true
                ;;
            --delete-namespace)
                DELETE_NAMESPACE=true
                ;;
            --force)
                FORCE=true
                ;;
            --verbose)
                VERBOSE=true
                ;;
            --help)
                print_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo ""
                print_usage
                exit 1
                ;;
        esac
        shift
    done

    # Validate environment
    validate_environment "$ENVIRONMENT"

    # Print header
    print_header "SkyWalking Cluster Cleanup - $ENVIRONMENT"

    # Run prerequisite checks
    print_section "Checking Prerequisites"

    local prereq_failed=false

    check_command "kubectl" || prereq_failed=true
    check_command "helm" || prereq_failed=true

    if [ "$prereq_failed" = true ]; then
        print_error "Prerequisite checks failed"
        exit 1
    fi

    # Check cluster connectivity
    check_cluster_connectivity || exit 1

    # Check if deployment exists
    local deployment_status
    check_deployment_exists
    deployment_status=$?

    if [ $deployment_status -eq 1 ]; then
        print_info "Nothing to clean up"
        exit 0
    fi

    print_success "All prerequisite checks passed"

    # Confirm cleanup
    confirm_cleanup "$ENVIRONMENT"

    # Confirm PVC deletion if requested
    confirm_pvc_deletion

    # Execute cleanup steps
    echo ""
    print_info "Starting cleanup process..."

    # Uninstall Helm release
    if ! uninstall_helm_release; then
        handle_cleanup_failure $?
        exit 1
    fi

    # Delete PVCs if requested
    if ! delete_pvcs; then
        handle_cleanup_failure $?
        exit 1
    fi

    # Delete namespace if requested
    if ! delete_namespace; then
        handle_cleanup_failure $?
        exit 1
    fi

    # Display cleanup summary
    display_cleanup_summary

    # Success message
    print_header "Cleanup Complete"

    print_success "SkyWalking cluster cleanup completed successfully"

    exit 0
}

# Trap errors and handle them
trap 'handle_cleanup_failure $?' ERR

# Run main function
main "$@"
