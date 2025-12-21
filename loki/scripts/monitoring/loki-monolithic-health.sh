#!/bin/bash

# Loki Basic Health Monitor
# Core system health: process, readiness, ring, config, network

# Configuration
LOKI_HOST="${LOKI_HOST:-127.0.0.1}"
LOKI_PORT="${LOKI_PORT:-3100}"
LOKI_URL="http://${LOKI_HOST}:${LOKI_PORT}"
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -u, --url URL                Loki URL (default: http://${LOKI_HOST}:${LOKI_PORT})"
    echo "  -i, --host HOST               Loki host (default: ${LOKI_HOST})"
    echo "  -p, --port PORT               Loki port (default: ${LOKI_PORT})"
    echo "  -v, --verbose                Verbose output with detailed metrics"
    echo "  -h, --help                   Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  LOKI_HOST                     Loki host (default: 127.0.0.1)"
    echo "  LOKI_PORT                     Loki port (default: 3100)"
}

log() {
    echo -e "${BLUE}$1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            LOKI_URL="$2"
            shift 2
            ;;
        -i|--host)
            LOKI_HOST="$2"
            LOKI_URL="http://${LOKI_HOST}:${LOKI_PORT}"
            shift 2
            ;;
        -p|--port)
            LOKI_PORT="$2"
            LOKI_URL="http://${LOKI_HOST}:${LOKI_PORT}"
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

check_loki_ready() {
    local response=$(curl -s --max-time 5 "$LOKI_URL/ready" 2>/dev/null || echo "timeout")

    if [[ "$response" == "ready" ]]; then
        return 0
    else
        error "Loki not ready: $response"
        return 1
    fi
}

check_loki_process() {
    log "Checking Loki process..."

    local loki_process=$(ps aux | grep -E "loki.*config\.file" | grep -v grep | wc -l)

    if [[ "$loki_process" -gt 0 ]]; then
        success "Loki process is running"
        if [[ "$VERBOSE" == "true" ]]; then
            local process_info=$(ps aux | grep -E "loki.*config\.file" | grep -v grep | head -1)
            echo "  $process_info"
            local loki_pid=$(echo "$process_info" | awk '{print $2}')
            if [[ -n "$loki_pid" ]]; then
                local memory=$(ps -p $loki_pid -o rss= 2>/dev/null | awk '{print int($1/1024)"MB"}' || echo "unknown")
                local cpu=$(ps -p $loki_pid -o %cpu= 2>/dev/null || echo "unknown")
                info "PID: $loki_pid, Memory: $memory, CPU: ${cpu}%"
            fi
        fi
        return 0
    else
        error "Loki process not found"
        return 1
    fi
}

check_config_endpoints() {
    log "Checking configuration endpoints..."
    local config_ok=true

    local config_response=$(curl -s -o /dev/null -w "%{http_code}" "$LOKI_URL/config" 2>/dev/null || echo "000")
    if [[ "$config_response" == "200" ]]; then
        success "Config endpoint accessible ($LOKI_URL/config)"
    else
        error "Config endpoint failed: $config_response ($LOKI_URL/config)"
        config_ok=false
    fi

    local services_response=$(curl -s -o /dev/null -w "%{http_code}" "$LOKI_URL/services" 2>/dev/null || echo "000")
    if [[ "$services_response" == "200" ]]; then
        success "Services endpoint accessible ($LOKI_URL/services)"
    else
        error "Services endpoint failed: $services_response ($LOKI_URL/services)"
        config_ok=false
    fi

    return $([ "$config_ok" = true ] && echo 0 || echo 1)
}

check_network_connectivity() {
    log "Testing network connectivity..."

    if curl -s --max-time 3 "$LOKI_URL/ready" >/dev/null 2>&1; then
        success "Network connectivity OK"

        if [[ "$VERBOSE" == "true" ]]; then
            echo "  Response times:"
            for endpoint in "/ready" "/metrics" "/config"; do
                local response_time=$(curl -s -w "%{time_total}" -o /dev/null --max-time 5 "$LOKI_URL$endpoint" 2>/dev/null || echo "timeout")
                if [[ "$response_time" != "timeout" ]]; then
                    echo "    • $endpoint: ${response_time}s"
                else
                    echo "    • $endpoint: timeout"
                fi
            done
        fi
        return 0
    else
        error "Network connectivity failed"
        return 1
    fi
}

get_ring_metrics() {
    log "Fetching ring metrics..."

    local metrics=$(curl -s --max-time 10 "$LOKI_URL/metrics" 2>/dev/null || echo "timeout")

    if [[ "$metrics" == "timeout" ]]; then
        error "Metrics endpoint timeout"
        return 1
    fi

    echo "$metrics"
}

analyze_ring_status() {
    local metrics="$1"
    local exit_code=0

    echo -e "${BLUE}🔍 LOKI RING STATUS ANALYSIS${NC}"
    echo "Target: $LOKI_URL"
    echo "=========================================="
    echo

    # Get ring members data
    local ring_members=$(echo "$metrics" | grep "loki_ring_members")
    local ring_tokens=$(echo "$metrics" | grep "loki_ring_tokens_total")

    if [[ -z "$ring_members" ]]; then
        error "No ring metrics found"
        return 1
    fi

    # Extract unique ring names
    local rings=$(echo "$ring_members" | grep -o 'name="[^"]*"' | sort -u | sed 's/name="//g' | sed 's/"//g')

    echo -e "${CYAN}📊 ACTIVE RINGS ($LOKI_URL/ring):${NC}"
    echo "------------------------"

    for ring in $rings; do
        local active=$(echo "$ring_members" | grep "name=\"$ring\"" | grep "state=\"ACTIVE\"" | grep -o "} [0-9]*" | awk '{print $2}')
        local joining=$(echo "$ring_members" | grep "name=\"$ring\"" | grep "state=\"JOINING\"" | grep -o "} [0-9]*" | awk '{print $2}')
        local leaving=$(echo "$ring_members" | grep "name=\"$ring\"" | grep "state=\"LEAVING\"" | grep -o "} [0-9]*" | awk '{print $2}')
        local unhealthy=$(echo "$ring_members" | grep "name=\"$ring\"" | grep "state=\"Unhealthy\"" | grep -o "} [0-9]*" | awk '{print $2}')
        local tokens=$(echo "$ring_tokens" | grep "name=\"$ring\"" | grep -o "} [0-9]*" | awk '{print $2}')

        # Default to 0 if empty
        active=${active:-0}
        joining=${joining:-0}
        leaving=${leaving:-0}
        unhealthy=${unhealthy:-0}
        tokens=${tokens:-0}

        echo -n "🔗 ${ring}: "

        if [[ "$active" -gt 0 ]]; then
            success "ACTIVE ($active members, $tokens tokens)"
            if [[ "$joining" -gt 0 ]]; then
                info "  └─ $joining joining"
            fi
            if [[ "$leaving" -gt 0 ]]; then
                warning "  └─ $leaving leaving"
            fi
            if [[ "$unhealthy" -gt 0 ]]; then
                error "  └─ $unhealthy unhealthy"
                exit_code=1
            fi
        else
            if [[ "$tokens" -gt 0 ]]; then
                warning "CONFIGURED but no active members ($tokens tokens)"
                exit_code=1
            else
                error "INACTIVE (0 members, 0 tokens)"
                exit_code=1
            fi
        fi

        if [[ "$VERBOSE" == "true" ]]; then
            echo "    Active: $active | Joining: $joining | Leaving: $leaving | Unhealthy: $unhealthy | Tokens: $tokens"
        fi
    done

    echo

    # Memberlist status
    echo -e "${CYAN}🌐 MEMBERLIST STATUS ($LOKI_URL/memberlist):${NC}"
    echo "State: 0=Alive, 1=Suspect, 2=Dead, 3=Left"
    echo "------------------------"

    # Look for actual memberlist metrics from Loki (exclude HELP and TYPE lines)
    local memberlist_nodes=$(echo "$metrics" | grep "^loki_memberlist_client_cluster_members_count" | awk '{print $2}')
    local memberlist_health=$(echo "$metrics" | grep "^loki_memberlist_client_cluster_node_health_score" | awk '{print $2}')
    local memberlist_cas_success=$(echo "$metrics" | grep "^loki_memberlist_client_cas_success_total" | awk '{print $2}')
    local memberlist_cas_failure=$(echo "$metrics" | grep "^loki_memberlist_client_cas_failure_total" | awk '{print $2}')
    local memberlist_kv_store=$(echo "$metrics" | grep "^loki_memberlist_client_kv_store_count" | awk '{print $2}')



    if [[ -n "$memberlist_nodes" ]]; then
        success "Memberlist active (cluster members: $memberlist_nodes, health state: ${memberlist_health:-0}=Alive, KV store: ${memberlist_kv_store:-0})"

        if [[ "$VERBOSE" == "true" ]]; then
            info "  └─ CAS operations: ${memberlist_cas_success:-0} success, ${memberlist_cas_failure:-0} failures"
            info "  └─ KV store entries: ${memberlist_kv_store:-0}"
        fi
    else
        warning "No memberlist cluster metrics found"
    fi

    echo

    # Services status
    echo -e "${CYAN}🔧 SERVICES STATUS ($LOKI_URL/services):${NC}"
    echo "------------------------"

    local services=$(curl -s --max-time 5 "$LOKI_URL/services" 2>/dev/null || echo "timeout")

    if [[ "$services" != "timeout" ]]; then
        echo "$services" | while read -r line; do
            if [[ -n "$line" ]]; then
                if [[ "$line" == *"Running"* ]]; then
                    success "$line"
                else
                    warning "$line"
                fi
            fi
        done
    else
        error "Services endpoint timeout"
        exit_code=1
    fi

    echo

    # Summary
    local total_active=$(echo "$ring_members" | grep "state=\"ACTIVE\"" | grep -o "} [0-9]*" | awk '{sum += $2} END {print sum+0}')
    local total_unhealthy=$(echo "$ring_members" | grep "state=\"Unhealthy\"" | grep -o "} [0-9]*" | awk '{sum += $2} END {print sum+0}')

    echo -e "${CYAN}📈 SUMMARY ($LOKI_URL/metrics):${NC}"
    echo "------------------------"
    info "Total active ring members: $total_active"
    if [[ "$total_unhealthy" -gt 0 ]]; then
        warning "Total unhealthy ring members: $total_unhealthy"
    else
        success "No unhealthy ring members"
    fi



    return $exit_code
}

main() {
    echo -e "${BLUE}🔍 Loki Basic Health Check${NC}"
    echo "Target: $LOKI_URL"
    echo "=========================================="
    echo

    local exit_code=0

    # Process check
    check_loki_process || exit_code=1
    echo

    # API readiness
    log "Checking API readiness ($LOKI_URL/ready)..."
    if check_loki_ready; then
        success "Loki API is ready ($LOKI_URL/ready)"
    else
        exit_code=1
    fi
    echo

    # Configuration endpoints
    check_config_endpoints || exit_code=1
    echo

    # Network connectivity
    check_network_connectivity || exit_code=1
    echo

    # Get metrics for ring analysis
    local metrics=$(get_ring_metrics)
    if [[ $? -ne 0 ]]; then
        exit_code=1
    else
        # Analyze ring status
        analyze_ring_status "$metrics"
        local ring_result=$?
        if [[ $ring_result -ne 0 ]]; then
            exit_code=1
        fi
    fi

    echo
    if [[ $exit_code -eq 0 ]]; then
        success "All ring & system checks passed! 🎉"
    else
        error "Some checks failed!"
    fi

    echo
    echo "🔗 Core URLs:"
    echo "  • Ring Status: $LOKI_URL/ring"
    echo "  • Configuration: $LOKI_URL/config"
    echo "  • Services: $LOKI_URL/services"
    echo "  • Memberlist: $LOKI_URL/memberlist"
    echo "  • Metrics: $LOKI_URL/metrics"

    exit $exit_code
}

main "$@"
