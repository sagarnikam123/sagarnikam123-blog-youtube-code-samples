#!/bin/bash

################################################################################
# SkyWalking Full Cluster Health Validation Script
#
# This script validates the health of all SkyWalking components in cluster mode
# including pod status, readiness probes, API responsiveness, and cluster
# coordination.
#
# Requirements validated: 9.1-9.13
#
# Usage:
#   ./test-health.sh [OPTIONS]
#
# Options:
#   -n, --namespace NAMESPACE    Kubernetes namespace (default: skywalking)
#   -o, --output FORMAT          Output format: text, json, yaml (default: text)
#   -h, --help                   Display this help message
#
# Exit codes:
#   0 - All health checks passed
#   1 - One or more health checks failed
#   2 - Script error or invalid arguments
#
# Example:
#   ./test-health.sh --namespace skywalking --output json
################################################################################

set -euo pipefail

# Default configuration
NAMESPACE="skywalking"
OUTPUT_FORMAT="text"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_TIME=$(date +%s)
FAILED_CHECKS=0
PASSED_CHECKS=0
WARNING_CHECKS=0

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Health check results storage
declare -A HEALTH_RESULTS
declare -a HEALTH_MESSAGES

################################################################################
# Helper Functions
################################################################################

print_header() {
    if [ "$OUTPUT_FORMAT" = "text" ]; then
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}$1${NC}"
        echo -e "${BLUE}========================================${NC}"
    fi
}

print_section() {
    if [ "$OUTPUT_FORMAT" = "text" ]; then
        echo -e "\n${CYAN}▶ $1${NC}"
        echo "─────────────────────────────────────────────────────────────────"
    fi
}

print_success() {
    if [ "$OUTPUT_FORMAT" = "text" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $1"
    fi
}

print_failure() {
    if [ "$OUTPUT_FORMAT" = "text" ]; then
        echo -e "${RED}✗ FAIL${NC}: $1"
    fi
}

print_warning() {
    if [ "$OUTPUT_FORMAT" = "text" ]; then
        echo -e "${YELLOW}⚠ WARNING${NC}: $1"
    fi
}

print_info() {
    if [ "$OUTPUT_FORMAT" = "text" ]; then
        echo -e "${YELLOW}ℹ INFO${NC}: $1"
    fi
}

usage() {
    sed -n '3,26p' "$0" | sed 's/^# \?//'
    exit 0
}

record_result() {
    local component=$1
    local check=$2
    local status=$3
    local message=$4

    local key="${component}:${check}"
    HEALTH_RESULTS["$key"]="$status"
    HEALTH_MESSAGES+=("$component|$check|$status|$message")

    case $status in
        PASS)
            ((PASSED_CHECKS++))
            print_success "$component - $check: $message"
            ;;
        FAIL)
            ((FAILED_CHECKS++))
            print_failure "$component - $check: $message"
            ;;
        WARNING)
            ((WARNING_CHECKS++))
            print_warning "$component - $check: $message"
            ;;
    esac
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    local missing_tools=()

    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi

    if ! command -v jq &> /dev/null && [ "$OUTPUT_FORMAT" = "json" ]; then
        missing_tools+=("jq (required for JSON output)")
    fi

    if ! command -v yq &> /dev/null && [ "$OUTPUT_FORMAT" = "yaml" ]; then
        missing_tools+=("yq (required for YAML output)")
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

    if [ "$OUTPUT_FORMAT" = "text" ]; then
        print_success "All prerequisites met"
        echo
    fi
}

get_pod_status() {
    local label=$1
    kubectl get pods -n "$NAMESPACE" -l "$label" -o json 2>/dev/null | \
        jq -r '.items[] | "\(.metadata.name)|\(.status.phase)|\(.status.conditions // [] | map(select(.type=="Ready")) | .[0].status // "Unknown")"' 2>/dev/null || echo ""
}

get_service_cluster_ip() {
    local service=$1
    kubectl get service -n "$NAMESPACE" "$service" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo ""
}

get_pod_name() {
    local label=$1
    kubectl get pod -n "$NAMESPACE" -l "$label" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo ""
}

################################################################################
# Component Health Checks
################################################################################

check_oap_server_health() {
    print_section "OAP Server Health Checks"

    local pod_info
    pod_info=$(get_pod_status "app.kubernetes.io/component=oap")

    if [ -z "$pod_info" ]; then
        record_result "OAP_Server" "Pod_Status" "FAIL" "No OAP Server pods found"
        return 1
    fi

    local all_running=true
    local all_ready=true
    local pod_count=0

    while IFS='|' read -r pod_name phase ready_status; do
        [ -z "$pod_name" ] && continue
        ((pod_count++))

        if [ "$phase" != "Running" ]; then
            record_result "OAP_Server" "Pod_${pod_name}" "FAIL" "Pod not running (status: $phase)"
            all_running=false
        fi

        if [ "$ready_status" != "True" ]; then
            record_result "OAP_Server" "Readiness_${pod_name}" "FAIL" "Pod not ready"
            all_ready=false
        fi
    done <<< "$pod_info"

    if [ $pod_count -eq 0 ]; then
        record_result "OAP_Server" "Pod_Count" "FAIL" "No OAP Server pods found"
        return 1
    fi

    if $all_running; then
        record_result "OAP_Server" "Pod_Status" "PASS" "All $pod_count pods running"
    fi

    if $all_ready; then
        record_result "OAP_Server" "Readiness_Probes" "PASS" "All $pod_count pods ready"
    fi

    return 0
}

check_banyandb_liaison_health() {
    print_section "BanyanDB Liaison Health Checks"

    local pod_info
    pod_info=$(get_pod_status "app.kubernetes.io/component=liaison")

    if [ -z "$pod_info" ]; then
        record_result "BanyanDB_Liaison" "Pod_Status" "WARNING" "No liaison pods found (may not be deployed)"
        return 0
    fi

    local all_running=true
    local pod_count=0

    while IFS='|' read -r pod_name phase ready_status; do
        [ -z "$pod_name" ] && continue
        ((pod_count++))

        if [ "$phase" != "Running" ]; then
            record_result "BanyanDB_Liaison" "Pod_${pod_name}" "FAIL" "Pod not running (status: $phase)"
            all_running=false
        fi
    done <<< "$pod_info"

    if $all_running && [ $pod_count -gt 0 ]; then
        record_result "BanyanDB_Liaison" "Pod_Status" "PASS" "All $pod_count liaison pods running"
    fi

    return 0
}

check_banyandb_data_health() {
    print_section "BanyanDB Data Node Health Checks"

    local pod_info
    pod_info=$(get_pod_status "app.kubernetes.io/component=data")

    if [ -z "$pod_info" ]; then
        record_result "BanyanDB_Data" "Pod_Status" "FAIL" "No data node pods found"
        return 1
    fi

    local all_running=true
    local pod_count=0

    while IFS='|' read -r pod_name phase ready_status; do
        [ -z "$pod_name" ] && continue
        ((pod_count++))

        if [ "$phase" != "Running" ]; then
            record_result "BanyanDB_Data" "Pod_${pod_name}" "FAIL" "Pod not running (status: $phase)"
            all_running=false
        fi
    done <<< "$pod_info"

    if $all_running && [ $pod_count -gt 0 ]; then
        record_result "BanyanDB_Data" "Pod_Status" "PASS" "All $pod_count data node pods running"
    fi

    return 0
}

check_satellite_health() {
    print_section "Satellite Health Checks"

    local pod_info
    pod_info=$(get_pod_status "app.kubernetes.io/component=satellite")

    if [ -z "$pod_info" ]; then
        record_result "Satellite" "Pod_Status" "WARNING" "No Satellite pods found (may not be deployed)"
        return 0
    fi

    local all_running=true
    local all_ready=true
    local pod_count=0

    while IFS='|' read -r pod_name phase ready_status; do
        [ -z "$pod_name" ] && continue
        ((pod_count++))

        if [ "$phase" != "Running" ]; then
            record_result "Satellite" "Pod_${pod_name}" "FAIL" "Pod not running (status: $phase)"
            all_running=false
        fi

        if [ "$ready_status" != "True" ]; then
            record_result "Satellite" "Readiness_${pod_name}" "FAIL" "Pod not ready"
            all_ready=false
        fi
    done <<< "$pod_info"

    if $all_running && [ $pod_count -gt 0 ]; then
        record_result "Satellite" "Pod_Status" "PASS" "All $pod_count pods running"
    fi

    if $all_ready && [ $pod_count -gt 0 ]; then
        record_result "Satellite" "Readiness_Probes" "PASS" "All $pod_count pods ready and accepting connections"
    fi

    return 0
}

check_ui_health() {
    print_section "UI Health Checks"

    local pod_info
    pod_info=$(get_pod_status "app.kubernetes.io/component=ui")

    if [ -z "$pod_info" ]; then
        record_result "UI" "Pod_Status" "FAIL" "No UI pods found"
        return 1
    fi

    local all_running=true
    local all_ready=true
    local pod_count=0

    while IFS='|' read -r pod_name phase ready_status; do
        [ -z "$pod_name" ] && continue
        ((pod_count++))

        if [ "$phase" != "Running" ]; then
            record_result "UI" "Pod_${pod_name}" "FAIL" "Pod not running (status: $phase)"
            all_running=false
        fi

        if [ "$ready_status" != "True" ]; then
            record_result "UI" "Readiness_${pod_name}" "FAIL" "Pod not ready"
            all_ready=false
        fi
    done <<< "$pod_info"

    if $all_running && [ $pod_count -gt 0 ]; then
        record_result "UI" "Pod_Status" "PASS" "All $pod_count pods running"
    fi

    if $all_ready && [ $pod_count -gt 0 ]; then
        record_result "UI" "Readiness_Probes" "PASS" "All $pod_count pods ready and accessible"
    fi

    return 0
}

check_etcd_health() {
    print_section "etcd Cluster Health Checks"

    local pod_info
    pod_info=$(get_pod_status "app.kubernetes.io/name=etcd")

    if [ -z "$pod_info" ]; then
        record_result "etcd" "Pod_Status" "WARNING" "No etcd pods found (may not be deployed)"
        return 0
    fi

    local all_running=true
    local all_healthy=true
    local pod_count=0
    local healthy_count=0

    while IFS='|' read -r pod_name phase ready_status; do
        [ -z "$pod_name" ] && continue
        ((pod_count++))

        if [ "$phase" != "Running" ]; then
            record_result "etcd" "Pod_${pod_name}" "FAIL" "Pod not running (status: $phase)"
            all_running=false
        else
            # Check etcd member health
            if kubectl exec -n "$NAMESPACE" "$pod_name" -- etcdctl endpoint health --cluster 2>/dev/null | grep -q "is healthy"; then
                ((healthy_count++))
            else
                record_result "etcd" "Health_${pod_name}" "FAIL" "Member not healthy"
                all_healthy=false
            fi
        fi
    done <<< "$pod_info"

    if $all_running && [ $pod_count -gt 0 ]; then
        record_result "etcd" "Pod_Status" "PASS" "All $pod_count pods running"
    fi

    # Check quorum
    local quorum_size=$(( (pod_count / 2) + 1 ))
    if [ $healthy_count -ge $quorum_size ]; then
        record_result "etcd" "Cluster_Quorum" "PASS" "Cluster has quorum ($healthy_count/$pod_count members healthy)"
    else
        record_result "etcd" "Cluster_Quorum" "FAIL" "Cluster lost quorum ($healthy_count/$pod_count members healthy, need $quorum_size)"
    fi

    return 0
}

check_pvc_health() {
    print_section "Persistent Volume Claims Health Checks"

    local pvcs
    pvcs=$(kubectl get pvc -n "$NAMESPACE" -o json 2>/dev/null | jq -r '.items[] | "\(.metadata.name)|\(.status.phase)"' 2>/dev/null || echo "")

    if [ -z "$pvcs" ]; then
        record_result "PVC" "Status" "WARNING" "No PVCs found (may not be using persistent storage)"
        return 0
    fi

    local all_bound=true
    local pvc_count=0
    local bound_count=0

    while IFS='|' read -r pvc_name phase; do
        [ -z "$pvc_name" ] && continue
        ((pvc_count++))

        if [ "$phase" = "Bound" ]; then
            ((bound_count++))
        else
            record_result "PVC" "PVC_${pvc_name}" "FAIL" "PVC not bound (status: $phase)"
            all_bound=false
        fi
    done <<< "$pvcs"

    if $all_bound && [ $pvc_count -gt 0 ]; then
        record_result "PVC" "Status" "PASS" "All $pvc_count PVCs bound to volumes"
    fi

    return 0
}

################################################################################
# API Responsiveness Checks
################################################################################

check_oap_api_responsiveness() {
    print_section "OAP Server API Responsiveness"

    local oap_svc
    oap_svc=$(get_service_cluster_ip "skywalking-oap")

    if [ -z "$oap_svc" ]; then
        record_result "OAP_API" "Service" "FAIL" "OAP Server service not found"
        return 1
    fi

    # Test health endpoint
    local start_time=$(date +%s%3N)
    local health_response
    health_response=$(kubectl run "oap-health-check-$$" -n "$NAMESPACE" --image=curlimages/curl:latest --restart=Never --rm -i --quiet -- \
        curl -s -w "\n%{http_code}" "http://${oap_svc}:12800/internal/l7check" --max-time 5 2>/dev/null || echo "000")
    local end_time=$(date +%s%3N)
    local latency=$((end_time - start_time))

    local http_code=$(echo "$health_response" | tail -n1)

    if [ "$http_code" = "200" ] || echo "$health_response" | grep -qi "success\|ok\|healthy"; then
        record_result "OAP_API" "Health_Endpoint" "PASS" "Health endpoint responding (${latency}ms)"
    else
        record_result "OAP_API" "Health_Endpoint" "FAIL" "Health endpoint not responding (HTTP $http_code)"
        return 1
    fi

    # Test GraphQL API
    start_time=$(date +%s%3N)
    local graphql_response
    graphql_response=$(kubectl run "oap-graphql-check-$$" -n "$NAMESPACE" --image=curlimages/curl:latest --restart=Never --rm -i --quiet -- \
        curl -s -w "\n%{http_code}" "http://${oap_svc}:12800/graphql" \
        -H "Content-Type: application/json" \
        -d '{"query":"query { version }"}' \
        --max-time 5 2>/dev/null || echo "000")
    end_time=$(date +%s%3N)
    latency=$((end_time - start_time))

    http_code=$(echo "$graphql_response" | tail -n1)

    if [ "$http_code" = "200" ]; then
        record_result "OAP_API" "GraphQL_API" "PASS" "GraphQL API responding (${latency}ms)"
    else
        record_result "OAP_API" "GraphQL_API" "FAIL" "GraphQL API not responding (HTTP $http_code)"
    fi

    return 0
}

check_banyandb_api_responsiveness() {
    print_section "BanyanDB API Responsiveness"

    local banyandb_svc
    banyandb_svc=$(get_service_cluster_ip "skywalking-banyandb")

    if [ -z "$banyandb_svc" ]; then
        record_result "BanyanDB_API" "Service" "WARNING" "BanyanDB service not found (may not be deployed)"
        return 0
    fi

    # Test HTTP management API
    local start_time=$(date +%s%3N)
    local api_response
    api_response=$(kubectl run "banyandb-api-check-$$" -n "$NAMESPACE" --image=curlimages/curl:latest --restart=Never --rm -i --quiet -- \
        curl -s -w "\n%{http_code}" "http://${banyandb_svc}:17913/api/healthz" --max-time 5 2>/dev/null || echo "000")
    local end_time=$(date +%s%3N)
    local latency=$((end_time - start_time))

    local http_code=$(echo "$api_response" | tail -n1)

    if [ "$http_code" = "200" ] || echo "$api_response" | grep -qi "ok\|healthy"; then
        record_result "BanyanDB_API" "HTTP_API" "PASS" "HTTP API responding (${latency}ms)"
    else
        record_result "BanyanDB_API" "HTTP_API" "WARNING" "HTTP API not responding as expected (HTTP $http_code)"
    fi

    return 0
}

################################################################################
# Cluster Coordination Checks
################################################################################

check_banyandb_metadata_consistency() {
    print_section "BanyanDB Cluster Metadata Consistency"

    # Get all BanyanDB data node pods
    local data_pods
    data_pods=($(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/component=data" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null))

    if [ ${#data_pods[@]} -eq 0 ]; then
        record_result "BanyanDB_Cluster" "Metadata_Consistency" "WARNING" "No data nodes found to check"
        return 0
    fi

    if [ ${#data_pods[@]} -eq 1 ]; then
        record_result "BanyanDB_Cluster" "Metadata_Consistency" "PASS" "Single node deployment (no consistency check needed)"
        return 0
    fi

    # Check if etcd is accessible (BanyanDB uses etcd for coordination)
    local etcd_svc
    etcd_svc=$(get_service_cluster_ip "skywalking-etcd")

    if [ -z "$etcd_svc" ]; then
        record_result "BanyanDB_Cluster" "Metadata_Consistency" "WARNING" "etcd service not found (cannot verify metadata consistency)"
        return 0
    fi

    # Verify etcd has cluster metadata
    local etcd_pod
    etcd_pod=$(get_pod_name "app.kubernetes.io/name=etcd")

    if [ -n "$etcd_pod" ]; then
        if kubectl exec -n "$NAMESPACE" "$etcd_pod" -- etcdctl get --prefix "/banyandb" 2>/dev/null | grep -q "banyandb"; then
            record_result "BanyanDB_Cluster" "Metadata_Consistency" "PASS" "Cluster metadata synchronized in etcd"
        else
            record_result "BanyanDB_Cluster" "Metadata_Consistency" "WARNING" "Cannot verify metadata (may be using different coordination mechanism)"
        fi
    else
        record_result "BanyanDB_Cluster" "Metadata_Consistency" "WARNING" "Cannot access etcd to verify metadata"
    fi

    return 0
}

check_oap_cluster_coordination() {
    print_section "OAP Server Cluster Coordination"

    # Get all OAP Server pods
    local oap_pods
    oap_pods=($(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/component=oap" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null))

    if [ ${#oap_pods[@]} -eq 0 ]; then
        record_result "OAP_Cluster" "Coordination" "FAIL" "No OAP Server pods found"
        return 1
    fi

    if [ ${#oap_pods[@]} -eq 1 ]; then
        record_result "OAP_Cluster" "Coordination" "PASS" "Single node deployment (no coordination check needed)"
        return 0
    fi

    # Check if OAP pods can see each other via service discovery
    local oap_svc
    oap_svc=$(get_service_cluster_ip "skywalking-oap")

    if [ -z "$oap_svc" ]; then
        record_result "OAP_Cluster" "Coordination" "FAIL" "OAP Server service not found"
        return 1
    fi

    # Check service endpoints
    local endpoint_count
    endpoint_count=$(kubectl get endpoints -n "$NAMESPACE" skywalking-oap -o json 2>/dev/null | \
        jq -r '.subsets[].addresses | length' 2>/dev/null || echo "0")

    if [ "$endpoint_count" -ge "${#oap_pods[@]}" ]; then
        record_result "OAP_Cluster" "Coordination" "PASS" "All ${#oap_pods[@]} OAP Server replicas registered in service discovery"
    else
        record_result "OAP_Cluster" "Coordination" "WARNING" "Only $endpoint_count/${#oap_pods[@]} OAP Server replicas in service endpoints"
    fi

    # Check cluster mode configuration
    local oap_pod="${oap_pods[0]}"
    if kubectl logs -n "$NAMESPACE" "$oap_pod" --tail=100 2>/dev/null | grep -qi "cluster\|coordinator"; then
        record_result "OAP_Cluster" "Cluster_Mode" "PASS" "Cluster mode enabled"
    else
        record_result "OAP_Cluster" "Cluster_Mode" "WARNING" "Cannot confirm cluster mode from logs"
    fi

    return 0
}

################################################################################
# Output Formatting
################################################################################

output_json() {
    local total_checks=$((PASSED_CHECKS + FAILED_CHECKS + WARNING_CHECKS))

    echo "{"
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"namespace\": \"$NAMESPACE\","
    echo "  \"summary\": {"
    echo "    \"total_checks\": $total_checks,"
    echo "    \"passed\": $PASSED_CHECKS,"
    echo "    \"failed\": $FAILED_CHECKS,"
    echo "    \"warnings\": $WARNING_CHECKS,"
    echo "    \"status\": \"$([ $FAILED_CHECKS -eq 0 ] && echo "HEALTHY" || echo "UNHEALTHY")\""
    echo "  },"
    echo "  \"checks\": ["

    local first=true
    for message in "${HEALTH_MESSAGES[@]}"; do
        IFS='|' read -r component check status msg <<< "$message"

        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi

        echo -n "    {"
        echo -n "\"component\": \"$component\", "
        echo -n "\"check\": \"$check\", "
        echo -n "\"status\": \"$status\", "
        echo -n "\"message\": \"$msg\""
        echo -n "}"
    done

    echo ""
    echo "  ]"
    echo "}"
}

output_yaml() {
    local total_checks=$((PASSED_CHECKS + FAILED_CHECKS + WARNING_CHECKS))

    echo "timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "namespace: $NAMESPACE"
    echo "summary:"
    echo "  total_checks: $total_checks"
    echo "  passed: $PASSED_CHECKS"
    echo "  failed: $FAILED_CHECKS"
    echo "  warnings: $WARNING_CHECKS"
    echo "  status: $([ $FAILED_CHECKS -eq 0 ] && echo "HEALTHY" || echo "UNHEALTHY")"
    echo "checks:"

    for message in "${HEALTH_MESSAGES[@]}"; do
        IFS='|' read -r component check status msg <<< "$message"
        echo "  - component: $component"
        echo "    check: $check"
        echo "    status: $status"
        echo "    message: \"$msg\""
    done
}

output_text_summary() {
    local total_checks=$((PASSED_CHECKS + FAILED_CHECKS + WARNING_CHECKS))
    local end_time=$(date +%s)
    local execution_time=$((end_time - START_TIME))

    print_header "Health Check Summary"
    echo "Namespace: $NAMESPACE"
    echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "Execution time: ${execution_time}s"
    echo ""
    echo "Total checks: $total_checks"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${YELLOW}Warnings: $WARNING_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo ""

    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}✓ All critical health checks PASSED${NC}"
        echo "SkyWalking cluster is HEALTHY"
    else
        echo -e "${RED}✗ Some health checks FAILED${NC}"
        echo "SkyWalking cluster is UNHEALTHY"
        echo ""
        echo "Failed checks:"
        for message in "${HEALTH_MESSAGES[@]}"; do
            IFS='|' read -r component check status msg <<< "$message"
            if [ "$status" = "FAIL" ]; then
                echo -e "  ${RED}✗${NC} $component - $check: $msg"
            fi
        done
    fi
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
            -o|--output)
                OUTPUT_FORMAT="$2"
                if [[ ! "$OUTPUT_FORMAT" =~ ^(text|json|yaml)$ ]]; then
                    echo -e "${RED}Error: Invalid output format. Must be: text, json, or yaml${NC}"
                    exit 2
                fi
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

    # Check prerequisites
    check_prerequisites

    if [ "$OUTPUT_FORMAT" = "text" ]; then
        echo
        print_header "SkyWalking Full Cluster Health Validation"
        echo "Namespace: $NAMESPACE"
        echo "Output format: $OUTPUT_FORMAT"
        echo
    fi

    # Run all health checks
    check_oap_server_health
    echo

    check_banyandb_liaison_health
    echo

    check_banyandb_data_health
    echo

    check_satellite_health
    echo

    check_ui_health
    echo

    check_etcd_health
    echo

    check_pvc_health
    echo

    check_oap_api_responsiveness
    echo

    check_banyandb_api_responsiveness
    echo

    check_banyandb_metadata_consistency
    echo

    check_oap_cluster_coordination
    echo

    # Output results in requested format
    case $OUTPUT_FORMAT in
        json)
            output_json
            ;;
        yaml)
            output_yaml
            ;;
        text)
            output_text_summary
            ;;
    esac

    # Exit with appropriate code
    if [ $FAILED_CHECKS -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
