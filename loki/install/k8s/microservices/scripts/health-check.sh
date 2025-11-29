#!/bin/bash

# Loki Microservices Health Check Script
# Checks API endpoints, ring status, UI, and component health

# Removed set -e to handle errors properly

NAMESPACE="loki"
CONTEXT=""
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -n, --namespace NAMESPACE    Kubernetes namespace (default: loki)"
    echo "  -c, --context CONTEXT        Kubectl context"
    echo "  -v, --verbose                Verbose output"
    echo "  -h, --help                   Show this help"
}

log() {
    echo "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo "${GREEN}✅ $1${NC}"
}

warning() {
    echo "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo "${RED}❌ $1${NC}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -c|--context)
            CONTEXT="--context $2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

KUBECTL="kubectl $CONTEXT -n $NAMESPACE"

check_pods() {
    log "Checking pod status..."

    local components=("distributor" "ingester" "querier" "query-frontend" "query-scheduler" "compactor" "ruler" "index-gateway")
    local all_ready=true

    for component in "${components[@]}"; do
        local pod_status=$($KUBECTL get pods -l app=loki-$component -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")
        local ready_status=$($KUBECTL get pods -l app=loki-$component -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>/dev/null || echo "false")

        if [[ "$pod_status" == "Running" && "$ready_status" == "true" ]]; then
            success "$component pod is running and ready"
        else
            error "$component pod status: $pod_status, ready: $ready_status"
            all_ready=false
        fi
    done

    return $([ "$all_ready" = true ] && echo 0 || echo 1)
}

check_api_endpoints() {
    log "Checking API endpoints..."
    local api_ok=true

    local components=("distributor:3100" "querier:3100" "query-frontend:3100" "compactor:3100" "ruler:3100")

    for component_port in "${components[@]}"; do
        local component=${component_port%:*}
        local port=${component_port#*:}

        local response=$($KUBECTL exec deployment/loki-$component -- wget -q -O /dev/null -S http://localhost:$port/ready 2>&1 | grep -o 'HTTP/1.1 [0-9]*' | cut -d' ' -f2 || echo "000")

        if [[ "$response" == "200" ]]; then
            success "$component API (/ready) is healthy"
        else
            error "$component API (/ready) returned: $response"
            api_ok=false
        fi
    done

    return $([ "$api_ok" = true ] && echo 0 || echo 1)
}

check_ring_status() {
    log "Checking ring status..."
    local ring_ok=true

    # Check distributor ring
    local dist_active=$($KUBECTL exec deployment/loki-distributor -- wget -q -O - http://localhost:3100/ring 2>/dev/null | grep -c "ACTIVE" || echo "0")
    if [[ "$dist_active" -gt 0 ]]; then
        success "Distributor ring has $dist_active ACTIVE instances"
    else
        error "Distributor ring has no ACTIVE instances"
        ring_ok=false
    fi

    # Check ingester ring
    local ing_active=$($KUBECTL exec statefulset/loki-ingester -- wget -q -O - http://localhost:3100/ring 2>/dev/null | grep -c "ACTIVE" || echo "0")
    if [[ "$ing_active" -gt 0 ]]; then
        success "Ingester ring has $ing_active ACTIVE instances"
    else
        error "Ingester ring has no ACTIVE instances"
        ring_ok=false
    fi

    return $([ "$ring_ok" = true ] && echo 0 || echo 1)
}

check_ui_access() {
    log "Checking UI access..."

    # Port forward to query-frontend for UI check
    $KUBECTL port-forward service/query-frontend 3100:3100 >/dev/null 2>&1 &
    local pf_pid=$!
    sleep 2

    local ui_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3100/ui/ 2>/dev/null || echo "000")
    kill $pf_pid 2>/dev/null || true

    if [[ "$ui_response" == "200" ]]; then
        success "Loki UI is accessible"
        return 0
    else
        error "Loki UI returned: $ui_response"
        return 1
    fi
}

check_log_ingestion() {
    log "Testing log ingestion..."

    # Port forward to distributor
    $KUBECTL port-forward service/distributor 3100:3100 >/dev/null 2>&1 &
    local pf_pid=$!
    sleep 2

    local test_log='{"streams": [{"stream": {"job": "health-check"}, "values": [["'$(date +%s%N)'", "Health check test log"]]}]}'
    local push_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$test_log" http://localhost:3100/loki/api/v1/push 2>/dev/null || echo "000")
    kill $pf_pid 2>/dev/null || true

    if [[ "$push_response" == "204" ]]; then
        success "Log ingestion is working"
        return 0
    else
        error "Log ingestion failed: $push_response"
        return 1
    fi
}

check_storage() {
    log "Checking storage connectivity..."

    # Check MinIO connectivity from ingester
    local minio_check=$($KUBECTL exec statefulset/loki-ingester -- wget -q -O /dev/null -S http://minio.loki.svc.cluster.local:9000/minio/health/live 2>&1 | grep -o 'HTTP/1.1 [0-9]*' | cut -d' ' -f2 || echo "000")

    if [[ "$minio_check" == "200" ]]; then
        success "MinIO storage is accessible"
        return 0
    else
        error "MinIO storage check failed: $minio_check"
        return 1
    fi
}

main() {
    echo "${BLUE}🔍 Loki Microservices Health Check${NC}"
    echo "Namespace: $NAMESPACE"
    echo "----------------------------------------"

    local exit_code=0

    check_pods || exit_code=1
    echo

    check_api_endpoints || exit_code=1
    echo

    check_ring_status || exit_code=1
    echo

    check_ui_access || exit_code=1
    echo

    check_log_ingestion || exit_code=1
    echo

    check_storage || exit_code=1
    echo

    if [[ $exit_code -eq 0 ]]; then
        success "All health checks passed! 🎉"
    else
        error "Some health checks failed!"
    fi

    exit $exit_code
}

main "$@"
