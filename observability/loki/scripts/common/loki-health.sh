#!/bin/bash

# Loki Unified Health Check
# Auto-detects deployment mode and runs appropriate checks
# Works with any deployment: local monolithic, single-binary K8s, simple-scalable, distributed
#
# Usage:
#   ./loki-health.sh                    # Auto-detect mode, full checks
#   ./loki-health.sh --quick            # Quick basic checks only
#   ./loki-health.sh -m monolithic      # Force monolithic mode
#   ./loki-health.sh -m kubernetes      # Force kubernetes mode
#   ./loki-health.sh --deep             # Include debug endpoints

set -euo pipefail

LOKI_URL="${LOKI_URL:-http://127.0.0.1:3100}"
NAMESPACE="${LOKI_NAMESPACE:-loki}"
MODE="${MODE:-auto}"
QUICK=false
DEEP=false
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Loki Unified Health Check - works with any deployment mode.

OPTIONS:
    -u, --url URL        Loki URL (default: http://127.0.0.1:3100)
    -n, --namespace NS   Kubernetes namespace (default: loki)
    -m, --mode MODE      Deployment mode: auto|monolithic|kubernetes (default: auto)
    -q, --quick          Quick checks only (ready + basic API)
    -d, --deep           Deep checks including debug endpoints
    -v, --verbose        Verbose output
    -h, --help           Show this help

EXAMPLES:
    $(basename "$0")                     # Auto-detect, standard checks
    $(basename "$0") --quick             # Fast health check
    $(basename "$0") --deep              # Include debug endpoints
    $(basename "$0") -m kubernetes       # Force K8s mode
    $(basename "$0") -u http://loki:3100 # Custom URL

PREREQUISITES:
    For Kubernetes: kubectl port-forward svc/loki-gateway -n loki 3100:80

EOF
    exit 0
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
        -m|--mode) MODE="$2"; shift 2 ;;
        -q|--quick) QUICK=true; shift ;;
        -d|--deep) DEEP=true; shift ;;
        -v|--verbose) VERBOSE=true; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

# Track overall status
EXIT_CODE=0

detect_mode() {
    log "Detecting deployment mode..."

    # Check for Kubernetes pods
    if command -v kubectl &> /dev/null; then
        local pods=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')
        if [[ "$pods" -gt 0 ]]; then
            info "Detected: Kubernetes ($pods pods in namespace $NAMESPACE)"
            echo "kubernetes"
            return
        fi
    fi

    # Check for local process
    if pgrep -f "loki.*config" &> /dev/null; then
        info "Detected: Monolithic (local process)"
        echo "monolithic"
        return
    fi

    # Fallback: check if API is accessible
    if curl -s -m 3 "$LOKI_URL/ready" &> /dev/null; then
        info "Detected: Monolithic (API accessible)"
        echo "monolithic"
        return
    fi

    warning "Could not detect deployment mode, defaulting to monolithic"
    echo "monolithic"
}

check_ready() {
    log "Checking ready endpoint..."

    local response=$(curl -s -m 5 -w "\n%{http_code}" "$LOKI_URL/ready" 2>/dev/null || echo -e "\n000")
    local body=$(echo "$response" | head -n -1)
    local code=$(echo "$response" | tail -1)

    if [[ "$code" == "200" ]]; then
        success "Ready endpoint responding"
        return 0
    else
        error "Ready endpoint failed (HTTP $code)"
        EXIT_CODE=1
        return 1
    fi
}

check_buildinfo() {
    log "Checking build info..."

    local response=$(curl -s -m 5 "$LOKI_URL/loki/api/v1/status/buildinfo" 2>/dev/null)

    if echo "$response" | grep -q "version"; then
        local version=$(echo "$response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        success "Loki v$version"

        if [[ "$VERBOSE" == "true" ]]; then
            echo "$response" | grep -oE '"(version|revision|branch)":"[^"]*"' | sed 's/^/  /'
        fi
        return 0
    else
        error "Could not get build info"
        EXIT_CODE=1
        return 1
    fi
}

check_ingestion() {
    log "Testing log ingestion..."

    local timestamp=$(date +%s%N)
    local response=$(curl -s -m 5 -o /dev/null -w "%{http_code}" -X POST "$LOKI_URL/loki/api/v1/push" \
        -H "Content-Type: application/json" \
        -d "{\"streams\":[{\"stream\":{\"job\":\"health-check\",\"source\":\"loki-health-script\"},\"values\":[[\"$timestamp\",\"Health check test\"]]}]}" 2>/dev/null || echo "000")

    if [[ "$response" == "204" ]]; then
        success "Log ingestion working"
        return 0
    elif [[ "$response" == "401" ]] || [[ "$response" == "403" ]]; then
        warning "Log ingestion requires authentication (HTTP $response)"
        return 0
    else
        error "Log ingestion failed (HTTP $response)"
        EXIT_CODE=1
        return 1
    fi
}

check_query() {
    log "Testing query API..."

    local start=$(($(date +%s) - 3600))000000000
    local end=$(date +%s)000000000
    local response=$(curl -s -m 10 -G "$LOKI_URL/loki/api/v1/query_range" \
        --data-urlencode 'query={job="health-check"}' \
        --data-urlencode "start=$start" \
        --data-urlencode "end=$end" \
        --data-urlencode "limit=1" 2>/dev/null || echo "timeout")

    if [[ "$response" == "timeout" ]]; then
        error "Query API timeout"
        EXIT_CODE=1
        return 1
    elif echo "$response" | grep -q '"status":"success"'; then
        local result_count=$(echo "$response" | grep -o '"result":\[[^]]*\]' | grep -c "stream" || echo "0")
        if [[ "$result_count" -gt 0 ]]; then
            success "Query API working (found logs)"
        else
            success "Query API working (no matching logs)"
        fi
        return 0
    elif echo "$response" | grep -qE "401|Unauthorized"; then
        warning "Query API requires authentication"
        return 0
    else
        warning "Query API returned unexpected response"
        [[ "$VERBOSE" == "true" ]] && echo "  Response: $(echo "$response" | head -c 200)"
        return 0
    fi
}

check_labels() {
    log "Testing labels API..."

    local response=$(curl -s -m 10 "$LOKI_URL/loki/api/v1/labels" 2>/dev/null || echo "timeout")

    if [[ "$response" == "timeout" ]]; then
        warning "Labels API timeout"
        return 0
    elif echo "$response" | grep -q '"status":"success"'; then
        local count=$(echo "$response" | grep -o '"data":\[[^]]*\]' | tr ',' '\n' | grep -c '"' || echo "0")
        count=$((count / 2))
        if [[ "$count" -gt 0 ]]; then
            success "Labels API working ($count labels)"
            if [[ "$VERBOSE" == "true" ]]; then
                echo "$response" | grep -o '"data":\[[^]]*\]' | tr ',' '\n' | grep '"' | head -5 | sed 's/^/  /'
            fi
        else
            success "Labels API working (no labels yet)"
        fi
        return 0
    else
        warning "Labels API returned unexpected response"
        return 0
    fi
}

check_metrics() {
    log "Testing metrics endpoint..."

    local response=$(curl -s -m 5 "$LOKI_URL/metrics" 2>/dev/null || echo "timeout")

    if [[ "$response" == "timeout" ]]; then
        warning "Metrics endpoint timeout"
        return 0
    elif echo "$response" | grep -q "loki_"; then
        local count=$(echo "$response" | grep -c "^loki_" || echo "0")
        success "Metrics endpoint working ($count Loki metrics)"
        return 0
    else
        warning "Metrics not exposed (expected in gateway mode)"
        return 0
    fi
}

check_ui() {
    log "Testing UI endpoint..."

    local response=$(curl -s -m 5 -w "\n%{http_code}" "$LOKI_URL/ui/" 2>/dev/null || echo -e "\n000")
    local code=$(echo "$response" | tail -1)

    if [[ "$code" == "200" ]]; then
        success "UI accessible at /ui/"
        return 0
    elif [[ "$code" == "307" ]] || [[ "$code" == "302" ]]; then
        warning "UI redirecting (may have issues in v3.6.x)"
        return 0
    elif [[ "$code" == "404" ]]; then
        warning "UI not enabled or not available"
        return 0
    else
        warning "UI returned HTTP $code"
        return 0
    fi
}

check_debug_endpoints() {
    log "Testing debug endpoints..."

    local endpoints=("/config" "/services" "/memberlist")

    for endpoint in "${endpoints[@]}"; do
        local response=$(curl -s -m 5 -o /dev/null -w "%{http_code}" "$LOKI_URL$endpoint" 2>/dev/null || echo "000")

        if [[ "$response" == "200" ]]; then
            success "  $endpoint accessible"
        else
            warning "  $endpoint returned HTTP $response"
        fi
    done
}

check_kubernetes_pods() {
    log "Checking Kubernetes pods..."

    local total=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')
    local running=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$total" -eq 0 ]]; then
        error "No pods found in namespace $NAMESPACE"
        EXIT_CODE=1
        return 1
    fi

    if [[ "$running" -eq "$total" ]]; then
        success "All pods running ($running/$total)"
    else
        warning "Pods: $running/$total running"
        EXIT_CODE=1
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        echo ""
        kubectl get pods -n "$NAMESPACE" -o wide 2>/dev/null | head -10
    fi

    return 0
}

check_monolithic_process() {
    log "Checking Loki process..."

    if pgrep -f "loki.*config" &> /dev/null; then
        success "Loki process running"
        return 0
    else
        warning "Loki process not found (may be in container)"
        return 0
    fi
}

main() {
    echo -e "${BLUE}🔍 Loki Health Check${NC}"
    echo "Target: $LOKI_URL"
    echo "=========================================="
    echo ""

    # Detect or use specified mode
    if [[ "$MODE" == "auto" ]]; then
        MODE=$(detect_mode)
    else
        info "Using specified mode: $MODE"
    fi
    echo ""

    # Mode-specific checks
    if [[ "$MODE" == "kubernetes" ]]; then
        check_kubernetes_pods
        echo ""
    else
        check_monolithic_process
        echo ""
    fi

    # Basic checks (always run)
    check_ready
    echo ""

    check_buildinfo
    echo ""

    if [[ "$QUICK" == "true" ]]; then
        # Quick mode - just ready + buildinfo
        echo ""
    else
        # Standard checks
        check_ingestion
        echo ""

        check_query
        echo ""

        check_labels
        echo ""

        if [[ "$DEEP" == "true" ]]; then
            # Deep checks
            check_metrics
            echo ""

            check_ui
            echo ""

            check_debug_endpoints
            echo ""
        fi
    fi

    # Summary
    echo "=========================================="
    if [[ $EXIT_CODE -eq 0 ]]; then
        success "All health checks passed! 🎉"
    else
        error "Some checks failed!"
    fi

    echo ""
    echo "🔗 Useful URLs:"
    echo "  • Ready: $LOKI_URL/ready"
    echo "  • Build Info: $LOKI_URL/loki/api/v1/status/buildinfo"
    echo "  • Labels: $LOKI_URL/loki/api/v1/labels"
    if [[ "$MODE" == "monolithic" ]]; then
        echo "  • Metrics: $LOKI_URL/metrics"
        echo "  • Config: $LOKI_URL/config"
    fi

    exit $EXIT_CODE
}

main "$@"
