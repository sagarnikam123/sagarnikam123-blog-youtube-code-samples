#!/bin/bash

# Apply and Validate Network Policies for SkyWalking Cluster
# This script applies network policies and validates they are working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-skywalking}"
NETWORK_POLICY_FILE="${NETWORK_POLICY_FILE:-skywalking/helm-values/network-policies.yaml}"
TIMEOUT="${TIMEOUT:-60}"

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

  # Check if network policy file exists
  if [ ! -f "$NETWORK_POLICY_FILE" ]; then
    print_error "Network policy file not found: $NETWORK_POLICY_FILE"
    exit 1
  fi

  print_info "Prerequisites check passed"
}

# Function to check network plugin support
check_network_plugin() {
  print_info "Checking network plugin support for NetworkPolicy..."

  # Try to get existing network policies
  if kubectl get networkpolicies --all-namespaces &> /dev/null; then
    print_info "Network plugin supports NetworkPolicy"
  else
    print_warn "Cannot verify NetworkPolicy support. Ensure your network plugin supports NetworkPolicy (Calico, Cilium, Weave Net, etc.)"
  fi
}

# Function to verify component labels
verify_component_labels() {
  print_info "Verifying component labels..."

  local components=("oap" "banyandb-liaison" "banyandb-data" "satellite" "ui" "etcd")
  local missing_labels=0

  for component in "${components[@]}"; do
    local pod_count=$(kubectl get pods -n "$NAMESPACE" -l "app=skywalking,component=$component" --no-headers 2>/dev/null | wc -l)

    if [ "$pod_count" -eq 0 ]; then
      print_warn "No pods found with labels: app=skywalking,component=$component"
      missing_labels=$((missing_labels + 1))
    else
      print_info "Found $pod_count pod(s) for component: $component"
    fi
  done

  if [ "$missing_labels" -gt 0 ]; then
    print_warn "Some components are missing expected labels. Network policies may not work correctly."
    print_warn "Verify your Helm values configure the correct labels."
  fi
}

# Function to apply network policies
apply_network_policies() {
  print_info "Applying network policies..."

  if kubectl apply -f "$NETWORK_POLICY_FILE"; then
    print_info "Network policies applied successfully"
  else
    print_error "Failed to apply network policies"
    exit 1
  fi
}

# Function to verify network policies are created
verify_network_policies() {
  print_info "Verifying network policies are created..."

  local expected_policies=(
    "skywalking-oap-server"
    "skywalking-banyandb-liaison"
    "skywalking-banyandb-data"
    "skywalking-satellite"
    "skywalking-ui"
    "skywalking-etcd"
  )

  local missing_policies=0

  for policy in "${expected_policies[@]}"; do
    if kubectl get networkpolicy "$policy" -n "$NAMESPACE" &> /dev/null; then
      print_info "Network policy exists: $policy"
    else
      print_error "Network policy not found: $policy"
      missing_policies=$((missing_policies + 1))
    fi
  done

  if [ "$missing_policies" -gt 0 ]; then
    print_error "$missing_policies network policy(ies) are missing"
    exit 1
  fi

  print_info "All network policies verified"
}

# Function to test connectivity
test_connectivity() {
  print_info "Testing connectivity between components..."

  # Wait for pods to stabilize after applying network policies
  print_info "Waiting 10 seconds for network policies to take effect..."
  sleep 10

  # Check if OAP Server pods are ready
  local oap_ready=$(kubectl get pods -n "$NAMESPACE" -l "app=skywalking,component=oap" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)
  local oap_total=$(kubectl get pods -n "$NAMESPACE" -l "app=skywalking,component=oap" --no-headers | wc -l)

  if [ "$oap_ready" -eq "$oap_total" ] && [ "$oap_total" -gt 0 ]; then
    print_info "OAP Server pods are ready ($oap_ready/$oap_total)"
  else
    print_warn "OAP Server pods are not all ready ($oap_ready/$oap_total)"
  fi

  # Check if Satellite pods are ready
  local sat_ready=$(kubectl get pods -n "$NAMESPACE" -l "app=skywalking,component=satellite" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)
  local sat_total=$(kubectl get pods -n "$NAMESPACE" -l "app=skywalking,component=satellite" --no-headers | wc -l)

  if [ "$sat_ready" -eq "$sat_total" ] && [ "$sat_total" -gt 0 ]; then
    print_info "Satellite pods are ready ($sat_ready/$sat_total)"
  else
    print_warn "Satellite pods are not all ready ($sat_ready/$sat_total)"
  fi

  # Check if BanyanDB liaison pods are ready
  local liaison_ready=$(kubectl get pods -n "$NAMESPACE" -l "app=skywalking,component=banyandb-liaison" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)
  local liaison_total=$(kubectl get pods -n "$NAMESPACE" -l "app=skywalking,component=banyandb-liaison" --no-headers | wc -l)

  if [ "$liaison_ready" -eq "$liaison_total" ] && [ "$liaison_total" -gt 0 ]; then
    print_info "BanyanDB liaison pods are ready ($liaison_ready/$liaison_total)"
  else
    print_warn "BanyanDB liaison pods are not all ready ($liaison_ready/$liaison_total)"
  fi

  # Check if UI pods are ready
  local ui_ready=$(kubectl get pods -n "$NAMESPACE" -l "app=skywalking,component=ui" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)
  local ui_total=$(kubectl get pods -n "$NAMESPACE" -l "app=skywalking,component=ui" --no-headers | wc -l)

  if [ "$ui_ready" -eq "$ui_total" ] && [ "$ui_total" -gt 0 ]; then
    print_info "UI pods are ready ($ui_ready/$ui_total)"
  else
    print_warn "UI pods are not all ready ($ui_ready/$ui_total)"
  fi

  print_info "Connectivity test completed. Check component logs for any connection errors."
}

# Function to show network policy details
show_network_policy_details() {
  print_info "Network Policy Summary:"
  echo ""
  kubectl get networkpolicies -n "$NAMESPACE" -o wide
  echo ""

  print_info "To view detailed network policy configuration:"
  echo "  kubectl describe networkpolicy <policy-name> -n $NAMESPACE"
  echo ""
  print_info "To view network policy in YAML format:"
  echo "  kubectl get networkpolicy <policy-name> -n $NAMESPACE -o yaml"
}

# Function to display usage
usage() {
  cat << EOF
Usage: $0 [OPTIONS]

Apply and validate network policies for SkyWalking cluster.

OPTIONS:
  -n, --namespace NAMESPACE    Kubernetes namespace (default: skywalking)
  -f, --file FILE              Network policy file (default: skywalking/helm-values/network-policies.yaml)
  -t, --timeout TIMEOUT        Timeout in seconds (default: 60)
  --skip-validation            Skip connectivity validation
  -h, --help                   Display this help message

EXAMPLES:
  # Apply network policies to default namespace
  $0

  # Apply network policies to custom namespace
  $0 --namespace my-skywalking

  # Apply custom network policy file
  $0 --file custom-network-policies.yaml

  # Apply without validation
  $0 --skip-validation

ENVIRONMENT VARIABLES:
  NAMESPACE                    Kubernetes namespace (default: skywalking)
  NETWORK_POLICY_FILE          Network policy file path
  TIMEOUT                      Timeout in seconds

EOF
}

# Main function
main() {
  local skip_validation=false

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
      -t|--timeout)
        TIMEOUT="$2"
        shift 2
        ;;
      --skip-validation)
        skip_validation=true
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

  print_info "Starting network policy application..."
  print_info "Namespace: $NAMESPACE"
  print_info "Network Policy File: $NETWORK_POLICY_FILE"
  echo ""

  # Execute steps
  check_prerequisites
  check_network_plugin
  verify_component_labels
  apply_network_policies
  verify_network_policies

  if [ "$skip_validation" = false ]; then
    test_connectivity
  else
    print_info "Skipping connectivity validation"
  fi

  show_network_policy_details

  echo ""
  print_info "Network policies applied successfully!"
  print_info "Review the documentation at: skywalking/helm-values/NETWORK-POLICIES.md"
  print_info "For troubleshooting, check component logs:"
  echo "  kubectl logs -n $NAMESPACE -l app=skywalking,component=oap --tail=50"
  echo "  kubectl logs -n $NAMESPACE -l app=skywalking,component=satellite --tail=50"
}

# Run main function
main "$@"
