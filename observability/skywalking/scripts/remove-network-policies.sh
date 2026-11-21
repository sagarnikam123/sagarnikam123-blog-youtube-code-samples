#!/bin/bash

# Remove Network Policies for SkyWalking Cluster
# This script removes network policies from the cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-skywalking}"
NETWORK_POLICY_FILE="${NETWORK_POLICY_FILE:-skywalking/helm-values/network-policies.yaml}"

# Function to print colored output
print_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
  print_info "Checking prerequisites..."

  # Check kubectl
  if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
  fi

  # Check cluster connectivity
  if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster"
    exit 1
  fi

  # Check if namespace exists
  if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    print_error "Namespace '$NAMESPACE' does not exist"
    exit 1
  fi

  print_info "Prerequisites check passed"
}

# Function to confirm deletion
confirm_deletion() {
  if [ "$FORCE" = true ]; then
    return 0
  fi

  echo ""
  print_warn "This will remove all network policies from namespace: $NAMESPACE"
  print_warn "After removal, all network traffic will be allowed (default Kubernetes behavior)"
  echo ""
  read -p "Are you sure you want to continue? (yes/no): " -r
  echo ""

  if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_info "Operation cancelled"
    exit 0
  fi
}

# Function to remove network policies
remove_network_policies() {
  print_info "Removing network policies..."

  if [ -f "$NETWORK_POLICY_FILE" ]; then
    if kubectl delete -f "$NETWORK_POLICY_FILE" --ignore-not-found=true; then
      print_info "Network policies removed successfully"
    else
      print_error "Failed to remove network policies"
      exit 1
    fi
  else
    print_warn "Network policy file not found: $NETWORK_POLICY_FILE"
    print_info "Attempting to remove network policies by name..."

    local policies=(
      "skywalking-oap-server"
      "skywalking-banyandb-liaison"
      "skywalking-banyandb-data"
      "skywalking-satellite"
      "skywalking-ui"
      "skywalking-etcd"
    )

    for policy in "${policies[@]}"; do
      if kubectl delete networkpolicy "$policy" -n "$NAMESPACE" --ignore-not-found=true; then
        print_info "Removed network policy: $policy"
      fi
    done
  fi
}

# Function to verify removal
verify_removal() {
  print_info "Verifying network policies are removed..."

  local remaining=$(kubectl get networkpolicies -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)

  if [ "$remaining" -eq 0 ]; then
    print_info "All network policies removed successfully"
  else
    print_warn "Some network policies still exist in namespace $NAMESPACE:"
    kubectl get networkpolicies -n "$NAMESPACE"
  fi
}

# Function to display usage
usage() {
  cat << EOF
Usage: $0 [OPTIONS]

Remove network policies from SkyWalking cluster.

OPTIONS:
  -n, --namespace NAMESPACE    Kubernetes namespace (default: skywalking)
  -f, --file FILE              Network policy file (default: skywalking/helm-values/network-policies.yaml)
  --force                      Skip confirmation prompt
  -h, --help                   Display this help message

EXAMPLES:
  # Remove network policies from default namespace
  $0

  # Remove network policies from custom namespace
  $0 --namespace my-skywalking

  # Remove without confirmation
  $0 --force

ENVIRONMENT VARIABLES:
  NAMESPACE                    Kubernetes namespace (default: skywalking)
  NETWORK_POLICY_FILE          Network policy file path

NOTES:
  After removing network policies, all network traffic will be allowed
  (default Kubernetes behavior). This may reduce security posture.

EOF
}

# Main function
main() {
  local FORCE=false

  # Parse command-line arguments
  while [[ $# -gt 0 ]]; do
    case $1 in
      -n|--namespace)
        NAMESPACE="$2"
        shift 2
        ;;
      -f|--file)
        NETWORK_POLICY_FILE="$2"
        shift 2
        ;;
      --force)
        FORCE=true
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        print_error "Unknown option: $1"
        usage
        exit 1
        ;;
    esac
  done

  print_info "Starting network policy removal..."
  print_info "Namespace: $NAMESPACE"
  echo ""

  # Execute steps
  check_prerequisites
  confirm_deletion
  remove_network_policies
  verify_removal

  echo ""
  print_info "Network policies removed successfully!"
  print_warn "All network traffic is now allowed (default Kubernetes behavior)"
  print_info "To re-apply network policies, run:"
  echo "  ./skywalking/scripts/apply-network-policies.sh"
}

# Run main function
main "$@"
