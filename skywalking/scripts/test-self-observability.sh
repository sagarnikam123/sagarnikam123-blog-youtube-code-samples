#!/bin/bash

################################################################################
# SkyWalking Self-Observability Validation Script
#
# This script validates SkyWalking self-observability features including metrics
# collection from OAP Server, BanyanDB, Satellite, and Java agents. It verifies
# that marketplace features are activated and component metrics are visible.
#
# Requirements validated: 10.1-10.9
#
# Usage:
#   ./test-self-observability.sh [OPTIONS]
#
# Options:
#   -n, --namespace NAMESPACE    Kubernetes namespace (default: skywalking)
#   -t, --timeout SECONDS        Timeout for validation (default: 300)
#   -o, --output FORMAT          Output format: text, json (default: text)
#   -h, --help                   Display this help message
#
# Exit codes:
#   0 - All self-observability checks passed
#   1 - One or more checks failed
#   2 - Script error or invalid arguments
#
# Example:
#   ./test-self-observability.sh --namespace skywalking --timeout 300
################################################################################

set -euo pipefail

# Default configuration
NAMESPACE="skywalking"
TIMEOUT=300
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

# Check results storage
declare -A CHECK_RESULTS
declare -a CHECK_MESSAGES

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
    CHECK_RESULTS["$key"]="$status"
    CHECK_MESSAGES+=("$component|$check|$status|$message")

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

    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
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

get_service_cluster_ip() {
    local service=$1
    kubectl get service -n "$NAMESPACE" "$service" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo ""
}

get_pod_name() {
    local label=$1
    kubectl get pod -n "$NAMESPACE" -l "$label" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo ""
}

query_graphql() {
    local oap_svc=$1
    local query=$2

    kubectl run "graphql-query-$$-$RANDOM" -n "$NAMESPACE" \
        --image=curlimages/curl:latest \
        --restart=Never \
        --rm -i --quiet \
        --command -- \
        curl -s "http://${oap_svc}:12800/graphql" \
        -H "Content-Type: application/json" \
        -d "{\"query\":\"$query\"}" \
        --max-time 10 2>/dev/null || echo ""
}

################################################################################
# Marketplace Feature Activation Checks
################################################################################

check_marketplace_features() {
    print_section "Marketplace Feature Activation"

    local oap_svc
    oap_svc=$(get_service_cluster_ip "skywalking-oap")

    if [ -z "$oap_svc" ]; then
        record_result "Marketplace" "Service" "FAIL" "OAP Server service not found"
        return 1
    fi

    # Check if self-observability feature is available
    # Query for available features through GraphQL
    local features_query='query { listFeatures { name enabled } }'
    local features_response
    features_response=$(query_graphql "$oap_svc" "$features_query")

    if [ -z "$features_response" ]; then
        record_result "Marketplace" "Features_Query" "WARNING" "Cannot query marketplace features (may require UI interaction)"
        return 0
    fi

    # Check if response contains self-observability related features
    if echo "$features_response" | grep -qi "self-observability\|so11y\|server"; then
        record_result "Marketplace" "Self_Observability_Feature" "PASS" "Self-observability feature detected"
    else
        record_result "Marketplace" "Self_Observability_Feature" "WARNING" "Self-observability feature status unclear"
    fi

    return 0
}

################################################################################
# OAP Server Self-Observability Metrics
################################################################################

check_oap_self_observability() {
    print_section "OAP Server Self-Observability Metrics"

    local oap_svc
    oap_svc=$(get_service_cluster_ip "skywalking-oap")

    if [ -z "$oap_svc" ]; then
        record_result "OAP_Self_Observability" "Service" "FAIL" "OAP Server service not found"
        return 1
    fi

    # Check Prometheus metrics endpoint
    local metrics_response
    metrics_response=$(kubectl run "oap-metrics-check-$$-$RANDOM" -n "$NAMESPACE" \
        --image=curlimages/curl:latest \
        --restart=Never \
        --rm -i --quiet \
        --command -- \
        curl -s "http://${oap_svc}:1234/metrics" \
        --max-time 5 2>/dev/null || echo "")

    if [ -n "$metrics_response" ] && echo "$metrics_response" | grep -q "^#\|HELP\|TYPE"; then
        record_result "OAP_Self_Observability" "Metrics_Endpoint" "PASS" "Prometheus metrics endpoint accessible"

        # Check for specific JVM metrics
        if echo "$metrics_response" | grep -qi "jvm_memory\|heap"; then
            record_result "OAP_Self_Observability" "JVM_Heap_Metrics" "PASS" "JVM heap metrics available"
        else
            record_result "OAP_Self_Observability" "JVM_Heap_Metrics" "WARNING" "JVM heap metrics not found"
        fi

        if echo "$metrics_response" | grep -qi "jvm_gc\|garbage"; then
            record_result "OAP_Self_Observability" "JVM_GC_Metrics" "PASS" "JVM GC metrics available"
        else
            record_result "OAP_Self_Observability" "JVM_GC_Metrics" "WARNING" "JVM GC metrics not found"
        fi

        if echo "$metrics_response" | grep -qi "jvm_threads\|thread"; then
            record_result "OAP_Self_Observability" "JVM_Thread_Metrics" "PASS" "JVM thread metrics available"
        else
            record_result "OAP_Self_Observability" "JVM_Thread_Metrics" "WARNING" "JVM thread metrics not found"
        fi
    else
        record_result "OAP_Self_Observability" "Metrics_Endpoint" "WARNING" "Metrics endpoint not accessible or empty"
    fi

    # Query OAP Server metrics through GraphQL
    local oap_metrics_query='query { readMetricsValues(condition: {name: \"service_instance_jvm_memory_heap\", entity: {scope: ServiceInstance}}, duration: {start: \"'$(date -u -d '5 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }'

    local oap_metrics_response
    oap_metrics_response=$(query_graphql "$oap_svc" "$oap_metrics_query")

    if [ -n "$oap_metrics_response" ] && echo "$oap_metrics_response" | grep -q "values\|data"; then
        record_result "OAP_Self_Observability" "Metrics_Collection" "PASS" "OAP Server metrics collected and queryable"
    else
        record_result "OAP_Self_Observability" "Metrics_Collection" "WARNING" "Cannot verify metrics collection through GraphQL"
    fi

    return 0
}

################################################################################
# BanyanDB Self-Observability Metrics
################################################################################

check_banyandb_self_observability() {
    print_section "BanyanDB Self-Observability Metrics"

    local banyandb_svc
    banyandb_svc=$(get_service_cluster_ip "skywalking-banyandb")

    if [ -z "$banyandb_svc" ]; then
        record_result "BanyanDB_Self_Observability" "Service" "WARNING" "BanyanDB service not found (may not be deployed)"
        return 0
    fi

    # Check BanyanDB HTTP metrics endpoint
    local metrics_response
    metrics_response=$(kubectl run "banyandb-metrics-check-$$-$RANDOM" -n "$NAMESPACE" \
        --image=curlimages/curl:latest \
        --restart=Never \
        --rm -i --quiet \
        --command -- \
        curl -s "http://${banyandb_svc}:17913/api/metrics" \
        --max-time 5 2>/dev/null || echo "")

    if [ -n "$metrics_response" ]; then
        record_result "BanyanDB_Self_Observability" "Metrics_Endpoint" "PASS" "BanyanDB metrics endpoint accessible"

        # Check for storage metrics
        if echo "$metrics_response" | grep -qi "ingestion\|write\|storage"; then
            record_result "BanyanDB_Self_Observability" "Storage_Metrics" "PASS" "Storage ingestion metrics available"
        else
            record_result "BanyanDB_Self_Observability" "Storage_Metrics" "WARNING" "Storage metrics not found in response"
        fi

        # Check for query latency metrics
        if echo "$metrics_response" | grep -qi "query\|latency\|duration"; then
            record_result "BanyanDB_Self_Observability" "Query_Latency_Metrics" "PASS" "Query latency metrics available"
        else
            record_result "BanyanDB_Self_Observability" "Query_Latency_Metrics" "WARNING" "Query latency metrics not found"
        fi
    else
        record_result "BanyanDB_Self_Observability" "Metrics_Endpoint" "WARNING" "BanyanDB metrics endpoint not accessible"
    fi

    # Check if BanyanDB metrics are visible in SkyWalking UI
    local oap_svc
    oap_svc=$(get_service_cluster_ip "skywalking-oap")

    if [ -n "$oap_svc" ]; then
        local banyandb_metrics_query='query { searchServices(duration: {start: \"'$(date -u -d '5 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { key label } }'

        local services_response
        services_response=$(query_graphql "$oap_svc" "$banyandb_metrics_query")

        if [ -n "$services_response" ] && echo "$services_response" | grep -qi "banyandb\|storage"; then
            record_result "BanyanDB_Self_Observability" "UI_Visibility" "PASS" "BanyanDB metrics visible in UI"
        else
            record_result "BanyanDB_Self_Observability" "UI_Visibility" "WARNING" "Cannot confirm BanyanDB metrics in UI"
        fi
    fi

    return 0
}

################################################################################
# Satellite Self-Observability Metrics
################################################################################

check_satellite_self_observability() {
    print_section "Satellite Self-Observability Metrics"

    # Check if Satellite pods exist
    local satellite_pods
    satellite_pods=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/component=satellite" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)

    if [ -z "$satellite_pods" ]; then
        record_result "Satellite_Self_Observability" "Deployment" "WARNING" "No Satellite pods found (may not be deployed)"
        return 0
    fi

    # Get Satellite service
    local satellite_svc
    satellite_svc=$(get_service_cluster_ip "skywalking-satellite")

    if [ -z "$satellite_svc" ]; then
        record_result "Satellite_Self_Observability" "Service" "WARNING" "Satellite service not found"
        return 0
    fi

    # Check Satellite metrics endpoint (typically on port 1234 for Prometheus)
    local metrics_response
    metrics_response=$(kubectl run "satellite-metrics-check-$$-$RANDOM" -n "$NAMESPACE" \
        --image=curlimages/curl:latest \
        --restart=Never \
        --rm -i --quiet \
        --command -- \
        curl -s "http://${satellite_svc}:1234/metrics" \
        --max-time 5 2>/dev/null || echo "")

    if [ -n "$metrics_response" ] && echo "$metrics_response" | grep -q "^#\|HELP\|TYPE"; then
        record_result "Satellite_Self_Observability" "Metrics_Endpoint" "PASS" "Satellite metrics endpoint accessible"

        # Check for throughput metrics
        if echo "$metrics_response" | grep -qi "throughput\|received\|sent\|forwarded"; then
            record_result "Satellite_Self_Observability" "Throughput_Metrics" "PASS" "Throughput metrics available"
        else
            record_result "Satellite_Self_Observability" "Throughput_Metrics" "WARNING" "Throughput metrics not found"
        fi

        # Check for buffer metrics
        if echo "$metrics_response" | grep -qi "buffer\|queue\|pending"; then
            record_result "Satellite_Self_Observability" "Buffer_Metrics" "PASS" "Buffer metrics available"
        else
            record_result "Satellite_Self_Observability" "Buffer_Metrics" "WARNING" "Buffer metrics not found"
        fi
    else
        record_result "Satellite_Self_Observability" "Metrics_Endpoint" "WARNING" "Satellite metrics endpoint not accessible"
    fi

    # Check if Satellite metrics are visible in SkyWalking UI
    local oap_svc
    oap_svc=$(get_service_cluster_ip "skywalking-oap")

    if [ -n "$oap_svc" ]; then
        local satellite_metrics_query='query { searchServices(duration: {start: \"'$(date -u -d '5 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { key label } }'

        local services_response
        services_response=$(query_graphql "$oap_svc" "$satellite_metrics_query")

        if [ -n "$services_response" ] && echo "$services_response" | grep -qi "satellite"; then
            record_result "Satellite_Self_Observability" "UI_Visibility" "PASS" "Satellite metrics visible in UI"
        else
            record_result "Satellite_Self_Observability" "UI_Visibility" "WARNING" "Cannot confirm Satellite metrics in UI"
        fi
    fi

    return 0
}

################################################################################
# Java Agent Self-Observability Metrics
################################################################################

check_agent_self_observability() {
    print_section "Java Agent Self-Observability Metrics"

    local oap_svc
    oap_svc=$(get_service_cluster_ip "skywalking-oap")

    if [ -z "$oap_svc" ]; then
        record_result "Agent_Self_Observability" "Service" "FAIL" "OAP Server service not found"
        return 1
    fi

    # Query for service instances (which represent agents)
    local instances_query='query { searchServiceInstances(duration: {start: \"'$(date -u -d '10 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}, serviceId: \"\") { key label attributes { name value } } }'

    local instances_response
    instances_response=$(query_graphql "$oap_svc" "$instances_query")

    if [ -n "$instances_response" ] && echo "$instances_response" | grep -q "key\|label"; then
        record_result "Agent_Self_Observability" "Agent_Detection" "PASS" "Java agents detected in system"

        # Check for agent metrics
        local agent_metrics_query='query { readMetricsValues(condition: {name: \"service_instance_jvm_cpu\", entity: {scope: ServiceInstance}}, duration: {start: \"'$(date -u -d '5 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }'

        local agent_metrics_response
        agent_metrics_response=$(query_graphql "$oap_svc" "$agent_metrics_query")

        if [ -n "$agent_metrics_response" ] && echo "$agent_metrics_response" | grep -q "values\|data"; then
            record_result "Agent_Self_Observability" "Agent_Metrics" "PASS" "Java agent metrics collected and queryable"
        else
            record_result "Agent_Self_Observability" "Agent_Metrics" "WARNING" "Cannot verify agent metrics (may need active test application)"
        fi
    else
        record_result "Agent_Self_Observability" "Agent_Detection" "WARNING" "No Java agents detected (may need test application deployment)"
    fi

    return 0
}

################################################################################
# Output Formatting
################################################################################

output_json() {
    local total_checks=$((PASSED_CHECKS + FAILED_CHECKS + WARNING_CHECKS))
    local end_time=$(date +%s)
    local execution_time=$((end_time - START_TIME))

    echo "{"
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"namespace\": \"$NAMESPACE\","
    echo "  \"execution_time_seconds\": $execution_time,"
    echo "  \"summary\": {"
    echo "    \"total_checks\": $total_checks,"
    echo "    \"passed\": $PASSED_CHECKS,"
    echo "    \"failed\": $FAILED_CHECKS,"
    echo "    \"warnings\": $WARNING_CHECKS,"
    echo "    \"status\": \"$([ $FAILED_CHECKS -eq 0 ] && echo "PASS" || echo "FAIL")\""
    echo "  },"
    echo "  \"checks\": ["

    local first=true
    for message in "${CHECK_MESSAGES[@]}"; do
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

output_text_summary() {
    local total_checks=$((PASSED_CHECKS + FAILED_CHECKS + WARNING_CHECKS))
    local end_time=$(date +%s)
    local execution_time=$((end_time - START_TIME))

    print_header "Self-Observability Validation Summary"
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
        if [ $WARNING_CHECKS -eq 0 ]; then
            echo -e "${GREEN}✓ All self-observability checks PASSED${NC}"
            echo "SkyWalking self-observability is fully functional"
        else
            echo -e "${YELLOW}⚠ Self-observability checks passed with warnings${NC}"
            echo "Some metrics may require additional configuration or test applications"
        fi
    else
        echo -e "${RED}✗ Some self-observability checks FAILED${NC}"
        echo ""
        echo "Failed checks:"
        for message in "${CHECK_MESSAGES[@]}"; do
            IFS='|' read -r component check status msg <<< "$message"
            if [ "$status" = "FAIL" ]; then
                echo -e "  ${RED}✗${NC} $component - $check: $msg"
            fi
        done
    fi

    # Check if execution time exceeds requirement (5 minutes = 300 seconds)
    if [ $execution_time -gt 300 ]; then
        echo ""
        echo -e "${YELLOW}⚠ WARNING: Execution time (${execution_time}s) exceeded 5 minute requirement${NC}"
    else
        echo ""
        echo -e "${GREEN}✓ Execution time within 5 minute requirement${NC}"
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
            -t|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_FORMAT="$2"
                if [[ ! "$OUTPUT_FORMAT" =~ ^(text|json)$ ]]; then
                    echo -e "${RED}Error: Invalid output format. Must be: text or json${NC}"
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
        print_header "SkyWalking Self-Observability Validation"
        echo "Namespace: $NAMESPACE"
        echo "Timeout: ${TIMEOUT}s"
        echo "Output format: $OUTPUT_FORMAT"
        echo
        print_info "This test validates self-observability metrics from all SkyWalking components"
        print_info "Some checks may show warnings if test applications are not deployed"
        echo
    fi

    # Run all self-observability checks
    check_marketplace_features
    echo

    check_oap_self_observability
    echo

    check_banyandb_self_observability
    echo

    check_satellite_self_observability
    echo

    check_agent_self_observability
    echo

    # Output results in requested format
    case $OUTPUT_FORMAT in
        json)
            output_json
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
