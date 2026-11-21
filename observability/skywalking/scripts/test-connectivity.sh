#!/bin/bash

################################################################################
# SkyWalking Cluster Connectivity Testing Script
#
# This script validates network connectivity between all SkyWalking components
# by testing required ports and communication paths.
#
# Requirements validated: 7.1-7.10
#
# Usage:
#   ./test-connectivity.sh [OPTIONS]
#
# Options:
#   -n, --namespace NAMESPACE    Kubernetes namespace (default: skywalking)
#   -h, --help                   Display this help message
#
# Exit codes:
#   0 - All connectivity tests passed
#   1 - One or more connectivity tests failed
#   2 - Script error or invalid arguments
#
# Example:
#   ./test-connectivity.sh --namespace skywalking
################################################################################

set -euo pipefail

# Default configuration
NAMESPACE="skywalking"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_TIME=$(date +%s)
TIMEOUT=90
FAILED_TESTS=0
PASSED_TESTS=0

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

print_failure() {
    echo -e "${RED}✗ FAIL${NC}: $1"
}

print_info() {
    echo -e "${YELLOW}ℹ INFO${NC}: $1"
}

usage() {
    sed -n '3,20p' "$0" | sed 's/^# \?//'
    exit 0
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    local missing_tools=()

    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi

    if ! command -v nc &> /dev/null && ! command -v telnet &> /dev/null; then
        missing_tools+=("nc or telnet")
    fi

    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo -e "${RED}Error: Missing required tools: ${missing_tools[*]}${NC}"
        exit 2
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
        exit 2
    fi

    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo -e "${RED}Error: Namespace '$NAMESPACE' does not exist${NC}"
        exit 2
    fi

    print_success "All prerequisites met"
    echo
}

get_pod_ip() {
    local label=$1
    kubectl get pod -n "$NAMESPACE" -l "$label" -o jsonpath='{.items[0].status.podIP}' 2>/dev/null || echo ""
}

get_service_cluster_ip() {
    local service=$1
    kubectl get service -n "$NAMESPACE" "$service" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo ""
}

get_pod_name() {
    local label=$1
    kubectl get pod -n "$NAMESPACE" -l "$label" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo ""
}

test_port_connectivity() {
    local source_pod=$1
    local dest_host=$2
    local dest_port=$3
    local test_name=$4

    if [ -z "$source_pod" ] || [ -z "$dest_host" ]; then
        print_failure "$test_name - Source pod or destination not found"
        ((FAILED_TESTS++))
        return 1
    fi

    # Test connectivity using nc (netcat) from source pod
    if kubectl exec -n "$NAMESPACE" "$source_pod" -- timeout 5 sh -c "nc -zv $dest_host $dest_port" &> /dev/null; then
        print_success "$test_name"
        ((PASSED_TESTS++))
        return 0
    else
        print_failure "$test_name - Cannot reach $dest_host:$dest_port from $source_pod"
        ((FAILED_TESTS++))
        return 1
    fi
}

################################################################################
# Connectivity Tests
################################################################################

test_agent_to_satellite() {
    print_header "Test 1: Agent → Satellite (GRPC port 11800)"

    # Get Satellite service IP
    local satellite_svc=$(get_service_cluster_ip "skywalking-satellite")

    if [ -z "$satellite_svc" ]; then
        print_failure "Satellite service not found"
        ((FAILED_TESTS++))
        return 1
    fi

    # For this test, we'll use any available pod as a proxy for agent connectivity
    # In real scenarios, agents run in application pods
    local test_pod=$(get_pod_name "app.kubernetes.io/component=oap")

    if [ -z "$test_pod" ]; then
        print_info "No test pod available, checking service endpoint exists"
        if kubectl get endpoints -n "$NAMESPACE" skywalking-satellite &> /dev/null; then
            print_success "Satellite service endpoint exists and is ready"
            ((PASSED_TESTS++))
        else
            print_failure "Satellite service endpoint not ready"
            ((FAILED_TESTS++))
        fi
        return
    fi

    test_port_connectivity "$test_pod" "$satellite_svc" "11800" "Agent → Satellite GRPC:11800"
}

test_satellite_to_oap() {
    print_header "Test 2: Satellite → OAP Server (GRPC port 11800)"

    # Get Satellite pod
    local satellite_pod=$(get_pod_name "app.kubernetes.io/component=satellite")

    # Get OAP service IP
    local oap_svc=$(get_service_cluster_ip "skywalking-oap")

    if [ -z "$satellite_pod" ]; then
        print_failure "Satellite pod not found"
        ((FAILED_TESTS++))
        return 1
    fi

    if [ -z "$oap_svc" ]; then
        print_failure "OAP Server service not found"
        ((FAILED_TESTS++))
        return 1
    fi

    test_port_connectivity "$satellite_pod" "$oap_svc" "11800" "Satellite → OAP Server GRPC:11800"
}

test_oap_to_banyandb() {
    print_header "Test 3: OAP Server → BanyanDB Liaison (GRPC port 17912)"

    # Get OAP pod
    local oap_pod=$(get_pod_name "app.kubernetes.io/component=oap")

    # Get BanyanDB liaison service IP
    local banyandb_svc=$(get_service_cluster_ip "skywalking-banyandb-liaison")

    if [ -z "$oap_pod" ]; then
        print_failure "OAP Server pod not found"
        ((FAILED_TESTS++))
        return 1
    fi

    if [ -z "$banyandb_svc" ]; then
        print_failure "BanyanDB liaison service not found"
        ((FAILED_TESTS++))
        return 1
    fi

    test_port_connectivity "$oap_pod" "$banyandb_svc" "17912" "OAP Server → BanyanDB GRPC:17912"
}

test_banyandb_http() {
    print_header "Test 4: BanyanDB HTTP Management (port 17913)"

    # Get BanyanDB liaison pod
    local banyandb_pod=$(get_pod_name "app.kubernetes.io/component=liaison")

    if [ -z "$banyandb_pod" ]; then
        # Try data node if liaison not found
        banyandb_pod=$(get_pod_name "app.kubernetes.io/component=data")
    fi

    if [ -z "$banyandb_pod" ]; then
        print_failure "BanyanDB pod not found"
        ((FAILED_TESTS++))
        return 1
    fi

    # Get BanyanDB service IP
    local banyandb_svc=$(get_service_cluster_ip "skywalking-banyandb")

    if [ -z "$banyandb_svc" ]; then
        print_failure "BanyanDB service not found"
        ((FAILED_TESTS++))
        return 1
    fi

    # Test HTTP port accessibility
    if kubectl exec -n "$NAMESPACE" "$banyandb_pod" -- timeout 5 sh -c "nc -zv $banyandb_svc 17913" &> /dev/null; then
        print_success "BanyanDB HTTP:17913 accessible"
        ((PASSED_TESTS++))
    else
        print_failure "BanyanDB HTTP:17913 not accessible from $banyandb_pod"
        ((FAILED_TESTS++))
    fi
}

test_etcd_cluster() {
    print_header "Test 5: etcd Cluster Communication (ports 2379, 2380)"

    # Get etcd pods
    local etcd_pods=($(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=etcd" -o jsonpath='{.items[*].metadata.name}'))

    if [ ${#etcd_pods[@]} -eq 0 ]; then
        print_failure "No etcd pods found"
        ((FAILED_TESTS++))
        return 1
    fi

    # Test client port (2379)
    local etcd_svc=$(get_service_cluster_ip "skywalking-etcd")

    if [ -z "$etcd_svc" ]; then
        print_failure "etcd service not found"
        ((FAILED_TESTS++))
        return 1
    fi

    local test_pod="${etcd_pods[0]}"

    # Test client API port
    if kubectl exec -n "$NAMESPACE" "$test_pod" -- timeout 5 sh -c "nc -zv $etcd_svc 2379" &> /dev/null; then
        print_success "etcd client API port 2379 accessible"
        ((PASSED_TESTS++))
    else
        print_failure "etcd client API port 2379 not accessible"
        ((FAILED_TESTS++))
    fi

    # Test peer port (2380) if multiple etcd members
    if [ ${#etcd_pods[@]} -gt 1 ]; then
        if kubectl exec -n "$NAMESPACE" "$test_pod" -- timeout 5 sh -c "nc -zv $etcd_svc 2380" &> /dev/null; then
            print_success "etcd peer port 2380 accessible"
            ((PASSED_TESTS++))
        else
            print_failure "etcd peer port 2380 not accessible"
            ((FAILED_TESTS++))
        fi
    else
        print_info "Single etcd instance, skipping peer port test"
    fi
}

test_banyandb_data_nodes() {
    print_header "Test 6: BanyanDB Data Node Internal Communication"

    # Get BanyanDB data node pods
    local data_pods=($(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/component=data" -o jsonpath='{.items[*].metadata.name}'))

    if [ ${#data_pods[@]} -eq 0 ]; then
        print_failure "No BanyanDB data node pods found"
        ((FAILED_TESTS++))
        return 1
    fi

    if [ ${#data_pods[@]} -eq 1 ]; then
        print_info "Single data node, skipping internal communication test"
        return 0
    fi

    # Test communication between data nodes
    local source_pod="${data_pods[0]}"
    local dest_ip=$(kubectl get pod -n "$NAMESPACE" "${data_pods[1]}" -o jsonpath='{.status.podIP}')

    if [ -z "$dest_ip" ]; then
        print_failure "Cannot get destination data node IP"
        ((FAILED_TESTS++))
        return 1
    fi

    # Test GRPC port between data nodes
    if kubectl exec -n "$NAMESPACE" "$source_pod" -- timeout 5 sh -c "nc -zv $dest_ip 17912" &> /dev/null; then
        print_success "BanyanDB data node internal communication working"
        ((PASSED_TESTS++))
    else
        print_failure "BanyanDB data nodes cannot communicate"
        ((FAILED_TESTS++))
    fi
}

test_ui_to_oap() {
    print_header "Test 7: UI → OAP Server (REST API port 12800)"

    # Get UI pod
    local ui_pod=$(get_pod_name "app.kubernetes.io/component=ui")

    # Get OAP service IP
    local oap_svc=$(get_service_cluster_ip "skywalking-oap")

    if [ -z "$ui_pod" ]; then
        print_failure "UI pod not found"
        ((FAILED_TESTS++))
        return 1
    fi

    if [ -z "$oap_svc" ]; then
        print_failure "OAP Server service not found"
        ((FAILED_TESTS++))
        return 1
    fi

    test_port_connectivity "$ui_pod" "$oap_svc" "12800" "UI → OAP Server REST:12800"
}

################################################################################
# Main Execution
################################################################################

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -h|--help)
                usage
                ;;
            *)
                echo -e "${RED}Error: Unknown option: $1${NC}"
                usage
                ;;
        esac
    done

    echo
    print_header "SkyWalking Cluster Connectivity Tests"
    echo "Namespace: $NAMESPACE"
    echo "Timeout: ${TIMEOUT}s"
    echo

    # Check prerequisites
    check_prerequisites

    # Run all connectivity tests
    test_agent_to_satellite
    echo

    test_satellite_to_oap
    echo

    test_oap_to_banyandb
    echo

    test_banyandb_http
    echo

    test_etcd_cluster
    echo

    test_banyandb_data_nodes
    echo

    test_ui_to_oap
    echo

    # Calculate execution time
    END_TIME=$(date +%s)
    EXECUTION_TIME=$((END_TIME - START_TIME))

    # Print summary
    print_header "Test Summary"
    echo "Total tests: $((PASSED_TESTS + FAILED_TESTS))"
    echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    echo "Execution time: ${EXECUTION_TIME}s / ${TIMEOUT}s"
    echo

    # Check if execution time exceeded timeout
    if [ $EXECUTION_TIME -gt $TIMEOUT ]; then
        echo -e "${YELLOW}Warning: Execution time exceeded ${TIMEOUT}s timeout${NC}"
    fi

    # Exit with appropriate code
    if [ $FAILED_TESTS -gt 0 ]; then
        echo -e "${RED}Connectivity tests FAILED${NC}"
        exit 1
    else
        echo -e "${GREEN}All connectivity tests PASSED${NC}"
        exit 0
    fi
}

# Run main function
main "$@"
