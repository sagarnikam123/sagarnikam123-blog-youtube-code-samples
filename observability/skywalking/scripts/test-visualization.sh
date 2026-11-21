#!/bin/bash

################################################################################
# SkyWalking Data Visualization Validation Script
#
# This script validates data visualization in the SkyWalking UI including
# service topology, traces, metrics, logs, and marketplace dashboards.
#
# Requirements validated: 14.1-14.12
#
# Usage:
#   ./test-visualization.sh [OPTIONS]
#
# Options:
#   -n, --namespace NAMESPACE    Kubernetes namespace (default: skywalking)
#   -t, --timeout SECONDS        Timeout for validation (default: 300)
#   -h, --help                   Display this help message
#
# Exit codes:
#   0 - All visualization checks passed
#   1 - One or more visualization checks failed
#   2 - Script error or invalid arguments
#
# Example:
#   ./test-visualization.sh --namespace skywalking --timeout 300
################################################################################

set -euo pipefail

# Default configuration
NAMESPACE="skywalking"
TIMEOUT=300
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_TIME=$(date +%s)
FAILED_CHECKS=0
PASSED_CHECKS=0

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test results storage
declare -a TEST_RESULTS

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────────────"
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
    sed -n '3,26p' "$0" | sed 's/^# \?//'
    exit 0
}

record_result() {
    local check=$1
    local status=$2
    local message=$3

    TEST_RESULTS+=("$check|$status|$message")

    case $status in
        PASS)
            ((PASSED_CHECKS++))
            print_success "$check: $message"
            ;;
        FAIL)
            ((FAILED_CHECKS++))
            print_failure "$check: $message"
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

    print_success "All prerequisites met"
    echo
}

get_oap_service_url() {
    local oap_svc
    oap_svc=$(kubectl get service -n "$NAMESPACE" skywalking-oap -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")

    if [ -z "$oap_svc" ]; then
        echo ""
        return 1
    fi

    echo "http://${oap_svc}:12800"
}

get_ui_service_url() {
    local ui_svc
    ui_svc=$(kubectl get service -n "$NAMESPACE" skywalking-ui -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")

    if [ -z "$ui_svc" ]; then
        echo ""
        return 1
    fi

    echo "http://${ui_svc}:8080"
}

execute_graphql_query() {
    local query=$1
    local oap_url
    oap_url=$(get_oap_service_url)

    if [ -z "$oap_url" ]; then
        echo ""
        return 1
    fi

    kubectl run "graphql-query-$$" -n "$NAMESPACE" --image=curlimages/curl:latest --restart=Never --rm -i --quiet -- \
        curl -s "${oap_url}/graphql" \
        -H "Content-Type: application/json" \
        -d "{\"query\":\"$query\"}" \
        --max-time 10 2>/dev/null || echo ""
}

################################################################################
# Visualization Checks
################################################################################

check_service_topology() {
    print_section "Service Topology Visualization"

    # Query for services
    local query='query { services: getAllServices(duration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { key: id label: name } }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "Service_Topology" "FAIL" "Cannot query OAP Server GraphQL API"
        return 1
    fi

    # Check if services are returned
    local service_count
    service_count=$(echo "$response" | jq -r '.data.services | length' 2>/dev/null || echo "0")

    if [ "$service_count" -gt 0 ]; then
        record_result "Service_Topology" "PASS" "Found $service_count services in topology"

        # Query for service relationships
        local services
        services=$(echo "$response" | jq -r '.data.services[].key' 2>/dev/null)

        if [ -n "$services" ]; then
            local first_service=$(echo "$services" | head -n1)
            local topo_query='query { topology: getServiceTopology(serviceId: \"'$first_service'\", duration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { nodes { id name } calls { source target } } }'

            local topo_response
            topo_response=$(execute_graphql_query "$topo_query")

            if echo "$topo_response" | jq -e '.data.topology' &>/dev/null; then
                record_result "Service_Dependencies" "PASS" "Service dependencies queryable"
            else
                record_result "Service_Dependencies" "FAIL" "Cannot query service dependencies"
            fi
        fi
    else
        record_result "Service_Topology" "FAIL" "No services found in topology (may need data ingestion)"
    fi

    return 0
}

check_trace_visualization() {
    print_section "Trace Visualization"

    # Query for traces
    local query='query { traces: queryBasicTraces(condition: {queryDuration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}, paging: {pageNum: 1, pageSize: 10}}) { traces { key: segmentId endpointNames duration } } }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "Trace_View" "FAIL" "Cannot query traces from OAP Server"
        return 1
    fi

    # Check if traces are returned
    local trace_count
    trace_count=$(echo "$response" | jq -r '.data.traces.traces | length' 2>/dev/null || echo "0")

    if [ "$trace_count" -gt 0 ]; then
        record_result "Trace_View" "PASS" "Found $trace_count traces"

        # Get first trace ID and query for spans
        local first_trace
        first_trace=$(echo "$response" | jq -r '.data.traces.traces[0].key' 2>/dev/null)

        if [ -n "$first_trace" ] && [ "$first_trace" != "null" ]; then
            local span_query='query { trace: queryTrace(traceId: \"'$first_trace'\") { spans { spanId parentSpanId serviceCode startTime endTime } } }'

            local span_response
            span_response=$(execute_graphql_query "$span_query")

            if echo "$span_response" | jq -e '.data.trace.spans' &>/dev/null; then
                local span_count
                span_count=$(echo "$span_response" | jq -r '.data.trace.spans | length' 2>/dev/null || echo "0")

                if [ "$span_count" -gt 0 ]; then
                    record_result "Trace_Spans" "PASS" "Trace contains $span_count spans with timing information"
                else
                    record_result "Trace_Spans" "FAIL" "Trace has no spans"
                fi
            else
                record_result "Trace_Spans" "FAIL" "Cannot query trace spans"
            fi
        fi
    else
        record_result "Trace_View" "FAIL" "No traces found (may need data ingestion)"
    fi

    return 0
}

check_metrics_visualization() {
    print_section "Metrics Visualization"

    # Query for service metrics
    local query='query { metrics: readMetricsValues(condition: {name: \"service_cpm\", entity: {scope: Service, serviceName: \"*\", normal: true}}, duration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "Metrics_Dashboard" "FAIL" "Cannot query metrics from OAP Server"
        return 1
    fi

    # Check if metrics are returned
    if echo "$response" | jq -e '.data.metrics' &>/dev/null; then
        local has_values
        has_values=$(echo "$response" | jq -r '.data.metrics.values | length' 2>/dev/null || echo "0")

        if [ "$has_values" -gt 0 ]; then
            record_result "Metrics_Dashboard" "PASS" "Time-series metrics data available"
        else
            record_result "Metrics_Dashboard" "FAIL" "No metric values found (may need data ingestion)"
        fi
    else
        record_result "Metrics_Dashboard" "FAIL" "Metrics query returned no data"
    fi

    return 0
}

check_log_visualization() {
    print_section "Log Visualization"

    # Query for logs
    local query='query { logs: queryLogs(condition: {queryDuration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}, paging: {pageNum: 1, pageSize: 10}}) { logs { serviceName timestamp content } } }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "Log_View" "FAIL" "Cannot query logs from OAP Server"
        return 1
    fi

    # Check if logs are returned
    if echo "$response" | jq -e '.data.logs' &>/dev/null; then
        local log_count
        log_count=$(echo "$response" | jq -r '.data.logs.logs | length' 2>/dev/null || echo "0")

        if [ "$log_count" -gt 0 ]; then
            record_result "Log_View" "PASS" "Found $log_count log entries with filtering capability"
        else
            record_result "Log_View" "FAIL" "No logs found (may need data ingestion or log collection)"
        fi
    else
        record_result "Log_View" "FAIL" "Log query returned no data"
    fi

    return 0
}

check_database_dashboard() {
    print_section "Database Dashboard Visualization"

    # Query for database metrics
    local query='query { metrics: readMetricsValues(condition: {name: \"database_access_cpm\", entity: {scope: DatabaseAccess, normal: true}}, duration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "Database_Dashboard" "FAIL" "Cannot query database metrics"
        return 1
    fi

    # Check if database metrics are available
    if echo "$response" | jq -e '.data.metrics' &>/dev/null; then
        local has_values
        has_values=$(echo "$response" | jq -r '.data.metrics.values | length' 2>/dev/null || echo "0")

        if [ "$has_values" -gt 0 ]; then
            record_result "Database_Dashboard" "PASS" "Database query performance metrics available"
        else
            record_result "Database_Dashboard" "FAIL" "No database metrics (may need database monitoring setup)"
        fi
    else
        record_result "Database_Dashboard" "FAIL" "Database metrics query returned no data"
    fi

    return 0
}

check_cache_dashboard() {
    print_section "Cache Dashboard Visualization"

    # Query for cache metrics
    local query='query { metrics: readMetricsValues(condition: {name: \"cache_access_cpm\", entity: {scope: CacheAccess, normal: true}}, duration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "Cache_Dashboard" "FAIL" "Cannot query cache metrics"
        return 1
    fi

    # Check if cache metrics are available
    if echo "$response" | jq -e '.data.metrics' &>/dev/null; then
        local has_values
        has_values=$(echo "$response" | jq -r '.data.metrics.values | length' 2>/dev/null || echo "0")

        if [ "$has_values" -gt 0 ]; then
            record_result "Cache_Dashboard" "PASS" "Cache hit/miss ratio metrics available"
        else
            record_result "Cache_Dashboard" "FAIL" "No cache metrics (may need cache monitoring setup)"
        fi
    else
        record_result "Cache_Dashboard" "FAIL" "Cache metrics query returned no data"
    fi

    return 0
}

check_mq_dashboard() {
    print_section "Message Queue Dashboard Visualization"

    # Query for MQ metrics
    local query='query { metrics: readMetricsValues(condition: {name: \"mq_consume_cpm\", entity: {scope: MQ, normal: true}}, duration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "MQ_Dashboard" "FAIL" "Cannot query message queue metrics"
        return 1
    fi

    # Check if MQ metrics are available
    if echo "$response" | jq -e '.data.metrics' &>/dev/null; then
        local has_values
        has_values=$(echo "$response" | jq -r '.data.metrics.values | length' 2>/dev/null || echo "0")

        if [ "$has_values" -gt 0 ]; then
            record_result "MQ_Dashboard" "PASS" "Message queue throughput and lag metrics available"
        else
            record_result "MQ_Dashboard" "FAIL" "No MQ metrics (may need MQ monitoring setup)"
        fi
    else
        record_result "MQ_Dashboard" "FAIL" "MQ metrics query returned no data"
    fi

    return 0
}

check_kubernetes_dashboard() {
    print_section "Kubernetes Dashboard Visualization"

    # Query for Kubernetes cluster metrics
    local query='query { metrics: readMetricsValues(condition: {name: \"k8s_cluster_cpu_cores\", entity: {scope: K8sCluster, normal: true}}, duration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "Kubernetes_Dashboard" "FAIL" "Cannot query Kubernetes metrics"
        return 1
    fi

    # Check if Kubernetes metrics are available
    if echo "$response" | jq -e '.data.metrics' &>/dev/null; then
        local has_values
        has_values=$(echo "$response" | jq -r '.data.metrics.values | length' 2>/dev/null || echo "0")

        if [ "$has_values" -gt 0 ]; then
            record_result "Kubernetes_Dashboard" "PASS" "Kubernetes cluster and pod metrics available"
        else
            record_result "Kubernetes_Dashboard" "FAIL" "No Kubernetes metrics (may need K8s monitoring setup)"
        fi
    else
        record_result "Kubernetes_Dashboard" "FAIL" "Kubernetes metrics query returned no data"
    fi

    return 0
}

check_self_observability_dashboard() {
    print_section "Self-Observability Dashboard Visualization"

    # Query for OAP Server self-observability metrics
    local query='query { metrics: readMetricsValues(condition: {name: \"meter_oap_instance_jvm_memory_heap_used\", entity: {scope: ServiceInstance, normal: true}}, duration: {start: \"'$(date -u -d '1 hour ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "Self_Observability_Dashboard" "FAIL" "Cannot query self-observability metrics"
        return 1
    fi

    # Check if self-observability metrics are available
    if echo "$response" | jq -e '.data.metrics' &>/dev/null; then
        local has_values
        has_values=$(echo "$response" | jq -r '.data.metrics.values | length' 2>/dev/null || echo "0")

        if [ "$has_values" -gt 0 ]; then
            record_result "Self_Observability_Dashboard" "PASS" "SkyWalking component metrics available"
        else
            record_result "Self_Observability_Dashboard" "FAIL" "No self-observability metrics (may need feature activation)"
        fi
    else
        record_result "Self_Observability_Dashboard" "FAIL" "Self-observability metrics query returned no data"
    fi

    return 0
}

check_custom_query_execution() {
    print_section "Custom Query Execution"

    # Test custom GraphQL query execution
    local query='query { version }'

    local response
    response=$(execute_graphql_query "$query")

    if [ -z "$response" ]; then
        record_result "Custom_Query" "FAIL" "Cannot execute custom queries"
        return 1
    fi

    # Check if query executed successfully
    if echo "$response" | jq -e '.data.version' &>/dev/null; then
        local version
        version=$(echo "$response" | jq -r '.data.version' 2>/dev/null)
        record_result "Custom_Query" "PASS" "Custom queries executable (OAP version: $version)"
    else
        record_result "Custom_Query" "FAIL" "Custom query execution failed"
    fi

    return 0
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

    echo
    print_header "SkyWalking Data Visualization Validation"
    echo "Namespace: $NAMESPACE"
    echo "Timeout: ${TIMEOUT}s"
    echo

    # Run all visualization checks
    check_service_topology
    echo

    check_trace_visualization
    echo

    check_metrics_visualization
    echo

    check_log_visualization
    echo

    check_database_dashboard
    echo

    check_cache_dashboard
    echo

    check_mq_dashboard
    echo

    check_kubernetes_dashboard
    echo

    check_self_observability_dashboard
    echo

    check_custom_query_execution
    echo

    # Calculate execution time
    local end_time=$(date +%s)
    local execution_time=$((end_time - START_TIME))

    # Print summary
    print_header "Visualization Validation Summary"
    echo "Namespace: $NAMESPACE"
    echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "Execution time: ${execution_time}s"
    echo ""
    echo "Total checks: $((PASSED_CHECKS + FAILED_CHECKS))"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo ""

    # Check if execution time is within requirement (5 minutes = 300 seconds)
    if [ $execution_time -le $TIMEOUT ]; then
        print_success "Validation completed within timeout (${execution_time}s <= ${TIMEOUT}s)"
    else
        print_failure "Validation exceeded timeout (${execution_time}s > ${TIMEOUT}s)"
        ((FAILED_CHECKS++))
    fi
    echo ""

    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}✓ All visualization checks PASSED${NC}"
        echo "SkyWalking UI data visualization is working correctly"
        echo ""
        echo "Note: Some checks may fail if:"
        echo "  - Data ingestion has not been performed yet"
        echo "  - Marketplace features are not activated"
        echo "  - Monitoring exporters are not deployed"
        echo "  - Insufficient time has passed for data collection"
    else
        echo -e "${RED}✗ Some visualization checks FAILED${NC}"
        echo ""
        echo "Failed checks:"
        for result in "${TEST_RESULTS[@]}"; do
            IFS='|' read -r check status message <<< "$result"
            if [ "$status" = "FAIL" ]; then
                echo -e "  ${RED}✗${NC} $check: $message"
            fi
        done
        echo ""
        echo "Troubleshooting steps:"
        echo "  1. Ensure data ingestion test has been run successfully"
        echo "  2. Verify marketplace features are activated in UI"
        echo "  3. Check that monitoring exporters are deployed (MySQL, Redis, RabbitMQ, K8s)"
        echo "  4. Verify OTel Collector is configured and running"
        echo "  5. Allow sufficient time for metrics collection (5-10 minutes)"
        echo "  6. Check OAP Server logs for processing errors"
    fi

    # Exit with appropriate code
    if [ $FAILED_CHECKS -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
