#!/bin/bash

# Loki Distributed Mode Health Check
# For Loki deployed in distributed/microservices mode with separate components

LOKI_URL="${LOKI_URL:-http://127.0.0.1:3100}"
NAMESPACE="${NAMESPACE:-loki}"
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -u, --url URL        Loki gateway URL (default: http://127.0.0.1:3100)"
    echo "  -n, --namespace NS   Kubernetes namespace (default: loki)"
    echo "  -v, --verbose        Verbose output"
    echo "  -h, --help           Show this help"
}

log() { echo -e "${BLUE}$1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url) LOKI_URL="$2"; shift 2 ;;
        -n|--namespace) NAMESPACE="$2"; shift 2 ;;
        -v|--verbose) VERBOSE=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        error "kubectl not found"
        return 1
    fi
    return 0
}

check_pods() {
    log "Checking pod status in namespace: $NAMESPACE"

    local total=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l | tr -d ' ')
    local running=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')
    local pending=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Pending --no-headers 2>/dev/null | wc -l | tr -d ' ')
    local failed=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed --no-headers 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$total" -eq 0 ]]; then
        error "No pods found in namespace $NAMESPACE"
        return 1
    fi

    if [[ "$running" -eq "$total" ]]; then
        success "All pods running ($running/$total)"
    else
        warning "Pods: $running running, $pending pending, $failed failed (total: $total)"
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        echo ""
        kubectl get pods -n $NAMESPACE
    fi

    return 0
}

check_components() {
    log "Checking microservices components..."

    local components=("distributor" "ingester" "querier" "query-frontend" "compactor" "gateway")
    local all_ok=true

    for component in "${components[@]}"; do
        local count=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/component=$component --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')

        if [[ "$count" -gt 0 ]]; then
            success "$component: $count pod(s) running"
        else
            error "$component: no running pods"
            all_ok=false
        fi
    done

    [[ "$all_ok" == "true" ]] && return 0 || return 1
}

check_gateway_api() {
    log "Checking gateway API endpoints..."

    local buildinfo=$(curl -s -m 5 "$LOKI_URL/loki/api/v1/status/buildinfo" 2>/dev/null)

    if echo "$buildinfo" | grep -q "version"; then
        local version=$(echo "$buildinfo" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        success "Gateway API accessible - Loki v$version"

        if [[ "$VERBOSE" == "true" ]]; then
            echo "$buildinfo" | grep -E "version|revision|branch" | sed 's/^/  /'
        fi
        return 0
    else
        error "Gateway API not accessible"
        return 1
    fi
}

check_ingestion() {
    log "Testing log ingestion..."

    local timestamp=$(date +%s%N)
    local response=$(curl -s -m 5 -o /dev/null -w "%{http_code}" -X POST "$LOKI_URL/loki/api/v1/push" \
        -H "Content-Type: application/json" \
        -d "{\"streams\":[{\"stream\":{\"job\":\"health-check\"},\"values\":[[\"$timestamp\",\"test\"]]}]}" 2>/dev/null)

    if [[ "$response" == "204" ]]; then
        success "Log ingestion working"
        return 0
    elif [[ "$response" == "401" ]]; then
        warning "Log ingestion requires authentication (HTTP 401)"
        return 0
    else
        error "Log ingestion failed (HTTP $response)"
        return 1
    fi
}

check_query() {
    log "Testing query API..."

    local start=$(($(date +%s) - 3600))000000000
    local end=$(date +%s)000000000
    local response=$(curl -s -m 5 -G "$LOKI_URL/loki/api/v1/query_range" \
        --data-urlencode 'query={job="health-check"}' \
        --data-urlencode "start=$start" \
        --data-urlencode "end=$end" \
        --data-urlencode "limit=1" 2>/dev/null)

    if echo "$response" | grep -q '"status":"success"'; then
        success "Query API working"
        return 0
    elif echo "$response" | grep -q "401\|Unauthorized"; then
        warning "Query API requires authentication (HTTP 401)"
        return 0
    else
        warning "Query API accessible but no logs found yet"
        return 0
    fi
}

check_services() {
    log "Checking Kubernetes services..."

    local gateway=$(kubectl get svc -n $NAMESPACE loki-gateway -o jsonpath='{.spec.type}' 2>/dev/null)

    if [[ -n "$gateway" ]]; then
        success "Gateway service: $gateway"

        if [[ "$VERBOSE" == "true" ]]; then
            kubectl get svc -n $NAMESPACE | grep loki
        fi
        return 0
    else
        error "Gateway service not found"
        return 1
    fi
}

main() {
    echo -e "${BLUE}🔍 Loki Distributed Mode Health Check${NC}"
    echo "Target: $LOKI_URL"
    echo "Namespace: $NAMESPACE"
    echo "=========================================="
    echo ""

    local exit_code=0

    # Check kubectl
    check_kubectl || exit_code=1
    echo ""

    # Check pods
    check_pods || exit_code=1
    echo ""

    # Check components
    check_components || exit_code=1
    echo ""

    # Check services
    check_services || exit_code=1
    echo ""

    # Check gateway API
    check_gateway_api || exit_code=1
    echo ""

    # Check ingestion
    check_ingestion || exit_code=1
    echo ""

    # Check query
    check_query || exit_code=1
    echo ""

    if [[ $exit_code -eq 0 ]]; then
        success "All distributed mode checks passed! 🎉"
    else
        error "Some checks failed!"
    fi

    echo ""
    echo "🔗 Useful URLs:"
    echo "  • Build Info: $LOKI_URL/loki/api/v1/status/buildinfo"
    echo "  • Labels: $LOKI_URL/loki/api/v1/labels"
    echo "  • Metrics: $LOKI_URL/metrics"
    echo "  • Config: $LOKI_URL/config"

    exit $exit_code
}

main "$@"
