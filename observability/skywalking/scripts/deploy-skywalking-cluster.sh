#!/bin/bash
# =============================================================================
# SkyWalking Full Cluster Mode Deployment Script
# =============================================================================
# Deploys Apache SkyWalking full cluster mode with BanyanDB, Satellite, and UI
# Supports multiple environments: minikube, eks-dev, eks-prod
#
# Usage:
#   ./deploy-skywalking-cluster.sh <environment>
#   ./deploy-skywalking-cluster.sh minikube
#   ./deploy-skywalking-cluster.sh eks-prod --dry-run
#
# Requirements:
#   - kubectl (configured and connected to target cluster)
#   - helm (v3.0+)
#   - Sufficient cluster resources (see environment-specific requirements)
# =============================================================================

set -e  # Exit on error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HELM_VALUES_DIR="${PROJECT_ROOT}/helm-values"

# Configuration
NAMESPACE="skywalking"
RELEASE_NAME="skywalking"
CHART_REPO="https://apache.jfrog.io/artifactory/skywalking-helm"
CHART_NAME="skywalking"
TIMEOUT="15m"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

# Flags
DRY_RUN=false
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
  minikube    Deploy to local Minikube cluster (6 CPU, 12GB memory required)
  eks-dev     Deploy to AWS EKS development environment
  eks-prod    Deploy to AWS EKS production environment

Options:
  --dry-run   Preview changes without applying them
  --verbose   Enable verbose output
  --help      Display this help message

Examples:
  $(basename "$0") minikube
  $(basename "$0") eks-prod --dry-run
  $(basename "$0") eks-dev --verbose

Requirements:
  - kubectl installed and configured
  - helm v3.0+ installed
  - Cluster connectivity
  - Sufficient cluster resources

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
    local required="$2"

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
        if [ "$required" = "true" ]; then
            print_error "$cmd is not installed or not in PATH"
            return 1
        else
            print_warning "$cmd is not installed (optional)"
            return 0
        fi
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

    # Get cluster version
    local k8s_version
    k8s_version=$(kubectl version -o json 2>/dev/null | grep -o '"gitVersion":"v[0-9.]*"' | head -1 | cut -d'"' -f4 || echo "unknown")
    if [ "$k8s_version" = "unknown" ]; then
        # Fallback to older method
        k8s_version=$(kubectl version --short 2>/dev/null | grep "Server Version" | grep -oE 'v[0-9]+\.[0-9]+' || echo "unknown")
    fi
    print_info "Kubernetes version: $k8s_version"

    # Validate Kubernetes version (minimum v1.19)
    if [[ "$k8s_version" != "unknown" ]] && [[ "$k8s_version" =~ ^v?[0-9]+\.[0-9]+ ]]; then
        local major minor
        major=$(echo "$k8s_version" | cut -d'.' -f1 | tr -d 'v')
        minor=$(echo "$k8s_version" | cut -d'.' -f2)

        # Validate major and minor are numbers
        if [[ "$major" =~ ^[0-9]+$ ]] && [[ "$minor" =~ ^[0-9]+$ ]]; then
            if [ "$major" -lt 1 ] || ([ "$major" -eq 1 ] && [ "$minor" -lt 19 ]); then
                print_warning "Kubernetes version $k8s_version is below recommended minimum (v1.19)"
                print_info "Some features may not work as expected"
            fi
        fi
    fi

    return 0
}

check_minikube_resources() {
    print_section "Checking Minikube Resources"

    # Check if running in Minikube
    if ! kubectl config current-context 2>/dev/null | grep -q "minikube"; then
        print_warning "Not running in Minikube context, skipping resource check"
        return 0
    fi

    # Get Minikube status
    if ! command -v minikube &> /dev/null; then
        print_warning "minikube command not found, cannot verify resources"
        return 0
    fi

    # Check CPU
    local cpu_count
    cpu_count=$(minikube ssh "nproc" 2>/dev/null | tr -d '\r' || echo "0")

    # Validate cpu_count is a number
    if ! [[ "$cpu_count" =~ ^[0-9]+$ ]]; then
        print_warning "Could not determine CPU count, skipping resource check"
        return 0
    fi

    if [ "$cpu_count" -ge 6 ]; then
        print_success "CPU cores: $cpu_count (minimum 6 required)"
    else
        print_error "Insufficient CPU cores: $cpu_count (minimum 6 required)"
        print_info "Start Minikube with: minikube start --cpus=8 --memory=16384"
        return 1
    fi

    # Check memory
    local memory_mb
    memory_mb=$(minikube ssh "free -m | grep Mem | awk '{print \$2}'" 2>/dev/null | tr -d '\r' || echo "0")

    # Validate memory_mb is a number
    if ! [[ "$memory_mb" =~ ^[0-9]+$ ]]; then
        print_warning "Could not determine memory size, skipping resource check"
        return 0
    fi

    local memory_gb=$((memory_mb / 1024))

    if [ "$memory_mb" -ge 12288 ]; then
        print_success "Memory: ${memory_gb}GB (minimum 12GB required)"
    else
        print_error "Insufficient memory: ${memory_gb}GB (minimum 12GB required)"
        print_info "Start Minikube with: minikube start --cpus=8 --memory=16384"
        return 1
    fi

    return 0
}

check_storage_class() {
    local env="$1"
    local storage_class

    case "$env" in
        minikube)
            storage_class="standard"
            ;;
        eks-*)
            storage_class="gp3"
            ;;
    esac

    print_section "Checking Storage Class"

    if kubectl get storageclass "$storage_class" &> /dev/null; then
        print_success "Storage class '$storage_class' exists"
        return 0
    else
        print_error "Storage class '$storage_class' not found"

        if [[ "$env" == "eks-"* ]]; then
            print_info "Create EKS storage class with:"
            print_info "  kubectl apply -f ${HELM_VALUES_DIR}/eks-storage-class.yaml"
        else
            print_info "Available storage classes:"
            kubectl get storageclass --no-headers 2>/dev/null | awk '{print "  - " $1}' || true
        fi

        return 1
    fi
}

validate_helm_values() {
    local env="$1"
    local values_file="${HELM_VALUES_DIR}/${env}-values.yaml"

    print_section "Validating Helm Values"

    if [ ! -f "$values_file" ]; then
        print_error "Helm values file not found: $values_file"
        return 1
    fi

    print_success "Found values file: $(basename "$values_file")"

    # Validate YAML syntax
    if command -v yamllint &> /dev/null; then
        if yamllint -d relaxed "$values_file" &> /dev/null; then
            print_success "YAML syntax is valid"
        else
            print_warning "YAML syntax validation failed (non-critical)"
        fi
    fi

    return 0
}

# =============================================================================
# Deployment Functions
# =============================================================================

create_namespace() {
    print_section "Creating Namespace"

    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_info "Namespace '$NAMESPACE' already exists"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        print_info "[DRY RUN] Would create namespace: $NAMESPACE"
        return 0
    fi

    if kubectl create namespace "$NAMESPACE"; then
        print_success "Created namespace: $NAMESPACE"
        return 0
    else
        print_error "Failed to create namespace: $NAMESPACE"
        return 1
    fi
}

apply_storage_class() {
    local env="$1"

    # Only apply for EKS environments
    if [[ "$env" != "eks-"* ]]; then
        return 0
    fi

    local storage_class_file="${HELM_VALUES_DIR}/eks-storage-class.yaml"

    print_section "Applying Storage Class Configuration"

    if [ ! -f "$storage_class_file" ]; then
        print_warning "Storage class file not found: $storage_class_file"
        print_info "Assuming storage class already exists"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        print_info "[DRY RUN] Would apply storage class from: $(basename "$storage_class_file")"
        return 0
    fi

    if kubectl apply -f "$storage_class_file"; then
        print_success "Applied storage class configuration"
        return 0
    else
        print_error "Failed to apply storage class configuration"
        return 1
    fi
}

deploy_skywalking() {
    local env="$1"
    local base_values="${HELM_VALUES_DIR}/base-values.yaml"
    local env_values="${HELM_VALUES_DIR}/${env}-values.yaml"

    print_section "Deploying SkyWalking Cluster"

    # Add Helm repository if not using OCI
    if [[ ! "$CHART_REPO" =~ ^oci:// ]]; then
        print_info "Adding Helm repository..."
        if helm repo add skywalking "$CHART_REPO" 2>/dev/null || helm repo add skywalking "$CHART_REPO" --force-update; then
            print_success "Helm repository added"
            helm repo update skywalking
        else
            print_warning "Could not add Helm repository, will try direct install"
        fi
    fi

    # Build helm command
    local helm_cmd
    if [[ "$CHART_REPO" =~ ^oci:// ]]; then
        # For OCI registries, use full path
        helm_cmd="helm upgrade --install $RELEASE_NAME ${CHART_REPO}/${CHART_NAME}"
    else
        # For traditional repos, use repo/chart format
        helm_cmd="helm upgrade --install $RELEASE_NAME skywalking/$CHART_NAME"
    fi

    helm_cmd="$helm_cmd --namespace $NAMESPACE"

    # Add values files if they exist
    if [ -f "$base_values" ]; then
        helm_cmd="$helm_cmd --values $base_values"
        print_info "Using base values: $(basename "$base_values")"
    fi

    helm_cmd="$helm_cmd --values $env_values"
    print_info "Using environment values: $(basename "$env_values")"

    # Disable Elasticsearch subchart (using BanyanDB instead)
    helm_cmd="$helm_cmd --set elasticsearch.enabled=false"

    # Add flags
    helm_cmd="$helm_cmd --timeout $TIMEOUT"
    helm_cmd="$helm_cmd --wait"
    helm_cmd="$helm_cmd --create-namespace"

    if [ "$DRY_RUN" = true ]; then
        helm_cmd="$helm_cmd --dry-run"
        print_info "[DRY RUN] Helm command:"
        echo "  $helm_cmd"
    fi

    if [ "$VERBOSE" = true ]; then
        helm_cmd="$helm_cmd --debug"
    fi

    print_info "Installing SkyWalking components..."
    print_info "This may take up to 15 minutes..."

    # Execute helm command
    if eval "$helm_cmd"; then
        if [ "$DRY_RUN" = true ]; then
            print_success "[DRY RUN] Deployment validation successful"
        else
            print_success "SkyWalking deployed successfully"
        fi
        return 0
    else
        print_error "Helm deployment failed"
        return 1
    fi
}

wait_for_pods() {
    if [ "$DRY_RUN" = true ]; then
        print_info "[DRY RUN] Would wait for pods to be ready"
        return 0
    fi

    print_section "Waiting for Pods to be Ready"

    local timeout=900  # 15 minutes
    local interval=10
    local elapsed=0

    print_info "Waiting for all pods to reach Running state (timeout: ${timeout}s)..."

    while [ $elapsed -lt $timeout ]; do
        local total_pods
        local ready_pods

        total_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
        ready_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | grep -c "Running" || echo "0")

        if [ "$total_pods" -gt 0 ] && [ "$ready_pods" -eq "$total_pods" ]; then
            # Check if all pods are actually ready (not just Running)
            local not_ready
            not_ready=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | grep -v "Running" | wc -l)

            if [ "$not_ready" -eq 0 ]; then
                print_success "All $total_pods pods are ready"
                return 0
            fi
        fi

        echo -ne "\r  Pods ready: $ready_pods/$total_pods (${elapsed}s elapsed)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    echo ""  # New line after progress
    print_error "Timeout waiting for pods to be ready"
    print_info "Current pod status:"
    kubectl get pods -n "$NAMESPACE" 2>/dev/null || true
    return 1
}

# =============================================================================
# Status Reporting Functions
# =============================================================================

display_deployment_status() {
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi

    print_section "Deployment Status"

    # Pod status
    echo "Pods:"
    kubectl get pods -n "$NAMESPACE" -o wide 2>/dev/null || print_error "Failed to get pod status"

    echo ""
    echo "Services:"
    kubectl get svc -n "$NAMESPACE" 2>/dev/null || print_error "Failed to get service status"

    echo ""
    echo "Persistent Volume Claims:"
    kubectl get pvc -n "$NAMESPACE" 2>/dev/null || print_error "Failed to get PVC status"
}

display_connection_info() {
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi

    print_section "Connection Information"

    local context
    context=$(kubectl config current-context 2>/dev/null)

    cat << EOF

SkyWalking UI:
  Service: skywalking-ui
  Port: 8080

  Access via port-forward:
    kubectl port-forward -n $NAMESPACE svc/skywalking-ui 8080:8080
    Open: http://localhost:8080

OAP Server:
  Service: skywalking-oap
  GRPC Port: 11800 (for agents via Satellite)
  REST API Port: 12800 (for UI and queries)

  Access REST API:
    kubectl port-forward -n $NAMESPACE svc/skywalking-oap 12800:12800
    Open: http://localhost:12800

Satellite:
  Service: skywalking-satellite
  GRPC Port: 11800 (for agent connections)

  Agent connection string:
    skywalking-satellite.$NAMESPACE.svc.cluster.local:11800

BanyanDB:
  Liaison Service: skywalking-banyandb-liaison
  GRPC Port: 17912
  HTTP Port: 17913

Cluster Context: $context
Namespace: $NAMESPACE

EOF
}

# =============================================================================
# Error Handling Functions
# =============================================================================

handle_deployment_failure() {
    local exit_code="$1"

    print_header "Deployment Failed"

    print_error "Deployment encountered an error (exit code: $exit_code)"

    print_section "Diagnostic Information"

    # Check pod status
    echo "Pod Status:"
    kubectl get pods -n "$NAMESPACE" 2>/dev/null || print_error "Cannot retrieve pod status"

    echo ""

    # Check for failed pods
    local failed_pods
    failed_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | grep -v "Running" | awk '{print $1}' || echo "")

    if [ -n "$failed_pods" ]; then
        print_section "Failed Pod Details"

        for pod in $failed_pods; do
            echo ""
            echo "Pod: $pod"
            echo "Status:"
            kubectl describe pod "$pod" -n "$NAMESPACE" 2>/dev/null | grep -A 10 "^Status:" || true

            echo ""
            echo "Events:"
            kubectl describe pod "$pod" -n "$NAMESPACE" 2>/dev/null | grep -A 20 "^Events:" || true

            echo ""
            echo "Recent Logs:"
            kubectl logs "$pod" -n "$NAMESPACE" --tail=50 2>/dev/null || print_warning "Cannot retrieve logs for $pod"
            echo "─────────────────────────────────────────────────────────────────"
        done
    fi

    print_section "Rollback Instructions"

    cat << EOF

To rollback this deployment:
  helm rollback $RELEASE_NAME -n $NAMESPACE

To completely remove the deployment:
  helm uninstall $RELEASE_NAME -n $NAMESPACE

To retry deployment after fixing issues:
  $(basename "$0") $ENVIRONMENT

For more troubleshooting:
  kubectl describe pods -n $NAMESPACE
  kubectl logs <pod-name> -n $NAMESPACE
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
            --dry-run)
                DRY_RUN=true
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
    if [ "$DRY_RUN" = true ]; then
        print_header "SkyWalking Cluster Deployment (DRY RUN) - $ENVIRONMENT"
    else
        print_header "SkyWalking Cluster Deployment - $ENVIRONMENT"
    fi

    # Run prerequisite checks
    print_section "Checking Prerequisites"

    local prereq_failed=false

    check_command "kubectl" "true" || prereq_failed=true
    check_command "helm" "true" || prereq_failed=true
    check_command "yamllint" "false"

    if [ "$prereq_failed" = true ]; then
        print_error "Prerequisite checks failed"
        exit 1
    fi

    # Check cluster connectivity
    check_cluster_connectivity || exit 1

    # Check Minikube resources if applicable
    if [ "$ENVIRONMENT" = "minikube" ]; then
        check_minikube_resources || exit 1
    fi

    # Check storage class
    check_storage_class "$ENVIRONMENT" || exit 1

    # Validate Helm values
    validate_helm_values "$ENVIRONMENT" || exit 1

    print_success "All prerequisite checks passed"

    # Execute deployment steps
    if [ "$DRY_RUN" = false ]; then
        echo ""
        print_warning "This will deploy SkyWalking cluster to: $ENVIRONMENT"
        print_info "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
        sleep 5
    fi

    # Create namespace
    create_namespace || exit 1

    # Apply storage class (EKS only)
    apply_storage_class "$ENVIRONMENT" || exit 1

    # Deploy SkyWalking
    if ! deploy_skywalking "$ENVIRONMENT"; then
        handle_deployment_failure $?
        exit 1
    fi

    # Wait for pods (skip in dry-run)
    if [ "$DRY_RUN" = false ]; then
        if ! wait_for_pods; then
            handle_deployment_failure $?
            exit 1
        fi
    fi

    # Display status and connection info
    display_deployment_status
    display_connection_info

    # Success message
    print_header "Deployment Complete"

    if [ "$DRY_RUN" = true ]; then
        print_success "Dry run completed successfully"
        print_info "No changes were made to the cluster"
    else
        print_success "SkyWalking cluster deployed successfully to $ENVIRONMENT"
        print_info "Access the UI using the connection information above"
    fi

    exit 0
}

# Trap errors and handle them
trap 'handle_deployment_failure $?' ERR

# Run main function
main "$@"
