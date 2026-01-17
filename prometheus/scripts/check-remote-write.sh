#!/bin/bash

#############################################
# Prometheus Remote Write Status
# Monitor remote_write health and performance
#############################################

# Configuration
NAMESPACE="${NAMESPACE:-prometheus}"
LOCAL_PORT="${LOCAL_PORT:-9090}"
PROM_SVC="${PROM_SVC:-prometheus-kube-prometheus-prometheus}"
PROM_API_PREFIX=""

# Colors
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
NC=$'\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace|-n) NAMESPACE="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --namespace, -n <ns>   Kubernetes namespace (default: prometheus)"
            echo "  --help, -h             Show this help"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Cleanup
cleanup() { [[ -n "$PF_PID" ]] && kill $PF_PID 2>/dev/null; }
trap cleanup EXIT

echo "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo "${GREEN}║   Prometheus Remote Write Status      ║${NC}"
echo "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""

# Setup port-forward
PROM_PORT=$(kubectl get svc -n "$NAMESPACE" "$PROM_SVC" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null || echo "9090")
kubectl port-forward -n "$NAMESPACE" svc/"$PROM_SVC" ${LOCAL_PORT}:${PROM_PORT} >/dev/null 2>&1 &
PF_PID=$!

# Auto-detect API path
for i in {1..30}; do
    if curl -s --connect-timeout 2 "http://localhost:${LOCAL_PORT}/prometheus/api/v1/query?query=up" 2>/dev/null | grep -q '"status":"success"'; then
        PROM_API_PREFIX="/prometheus"
        printf "${GREEN}✓${NC} Connected\n"
        break
    fi
    if curl -s --connect-timeout 2 "http://localhost:${LOCAL_PORT}/api/v1/query?query=up" 2>/dev/null | grep -q '"status":"success"'; then
        PROM_API_PREFIX=""
        printf "${GREEN}✓${NC} Connected\n"
        break
    fi
    sleep 1
    [[ $i -eq 30 ]] && { echo "${RED}✗ Connection failed${NC}"; exit 1; }
done

BASE_URL="http://localhost:${LOCAL_PORT}${PROM_API_PREFIX}"

# Helper function
query_value() {
    local query="$1"
    local encoded=$(echo "$query" | sed 's/ /%20/g; s/(/%28/g; s/)/%29/g; s/{/%7B/g; s/}/%7D/g; s/\[/%5B/g; s/\]/%5D/g; s/"/%22/g; s/=/%3D/g; s/~/%7E/g')
    curl -s --connect-timeout 5 "${BASE_URL}/api/v1/query?query=$encoded" 2>/dev/null | jq -r '.data.result[0].value[1] // empty' 2>/dev/null
}

#############################################
# Check if remote_write is configured
#############################################
printf "\n"
echo "${BLUE}═══ Remote Write Configuration ═══${NC}"

# Check config for remote_write
CONFIG=$(curl -s "${BASE_URL}/api/v1/status/config" 2>/dev/null)
CONFIG_YAML=$(echo "$CONFIG" | jq -r '.data.yaml' 2>/dev/null)

# Check if remote_write section exists and has URLs
RW_URLS=$(echo "$CONFIG_YAML" | grep -A5 "remote_write:" | grep "url:" | sed 's/.*url: *//' | tr -d '"' | tr -d "'" || true)

if [[ -z "$RW_URLS" ]]; then
    echo "  ${YELLOW}⚠ Remote write is NOT configured${NC}"
    printf "\n  To enable remote_write, add to your Prometheus spec:\n"
    echo "  ${CYAN}remoteWrite:${NC}"
    echo "  ${CYAN}  - url: http://mimir-nginx.mimir.svc/api/v1/push${NC}"
    echo "  ${CYAN}    headers:${NC}"
    echo "  ${CYAN}      X-Scope-OrgID: <tenant-id>${NC}"
    printf "\n${GREEN}✓ Remote write check complete${NC}\n"
    exit 0
fi

echo "  ${GREEN}✓ Remote write is configured${NC}"

# Get remote write URLs
printf "\n  Remote write endpoints:\n"
echo "$RW_URLS" | while read -r url; do
    [[ -n "$url" ]] && echo "    - $url"
done

#############################################
# Key Metrics
#############################################
printf "\n"
echo "${BLUE}═══ Remote Write Metrics ═══${NC}"

# Samples sent
SENT=$(query_value "sum(prometheus_remote_storage_samples_total)")
if [[ -n "$SENT" ]]; then
    SENT_FMT=$(printf "%'d" "${SENT%.*}" 2>/dev/null || echo "$SENT")
    echo "  Samples Sent:      ${GREEN}$SENT_FMT${NC}"
fi

# Samples pending
PENDING=$(query_value "sum(prometheus_remote_storage_samples_pending)")
if [[ -n "$PENDING" ]]; then
    PENDING_INT="${PENDING%.*}"
    PENDING_FMT=$(printf "%'d" "$PENDING_INT" 2>/dev/null || echo "$PENDING")
    if [[ "$PENDING_INT" -gt 100000 ]]; then
        printf "  Samples Pending:   ${RED}$PENDING_FMT${NC} (queue backing up!)\n"
    elif [[ "$PENDING_INT" -gt 10000 ]]; then
        echo "  Samples Pending:   ${YELLOW}$PENDING_FMT${NC}"
    else
        echo "  Samples Pending:   ${GREEN}$PENDING_FMT${NC}"
    fi
fi

# Samples failed
FAILED=$(query_value "sum(prometheus_remote_storage_samples_failed_total)")
if [[ -n "$FAILED" ]]; then
    FAILED_INT="${FAILED%.*}"
    if [[ "$FAILED_INT" -gt 0 ]]; then
        echo "  Samples Failed:    ${RED}$FAILED_INT${NC}"
    else
        echo "  Samples Failed:    ${GREEN}0${NC}"
    fi
fi

# Samples dropped - check by reason
DROPPED_TOTAL=$(query_value "sum(prometheus_remote_storage_samples_dropped_total)")
DROPPED_RELABEL=$(curl -s --connect-timeout 5 "${BASE_URL}/api/v1/query?query=sum(prometheus_remote_storage_samples_dropped_total%7Breason%3D%22dropped_series%22%7D)" 2>/dev/null | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null)
DROPPED_RELABEL_INT="${DROPPED_RELABEL%.*}"

if [[ -n "$DROPPED_TOTAL" ]]; then
    DROPPED_INT="${DROPPED_TOTAL%.*}"
    DROPPED_ERROR=$((DROPPED_INT - DROPPED_RELABEL_INT))

    if [[ "$DROPPED_INT" -gt 0 ]]; then
        DROPPED_FMT=$(printf "%'d" "$DROPPED_INT" 2>/dev/null || echo "$DROPPED_INT")

        if [[ "$DROPPED_RELABEL_INT" -gt 0 && "$DROPPED_ERROR" -eq 0 ]]; then
            # All drops are from writeRelabelConfigs - this is intentional
            RELABEL_FMT=$(printf "%'d" "$DROPPED_RELABEL_INT" 2>/dev/null || echo "$DROPPED_RELABEL_INT")
            printf "  Samples Dropped:   ${CYAN}$RELABEL_FMT${NC} (writeRelabelConfigs - intentional)\n"
        elif [[ "$DROPPED_ERROR" -gt 0 ]]; then
            # Some drops are errors
            echo "  Samples Dropped:   ${RED}$DROPPED_FMT${NC}"
            [[ "$DROPPED_RELABEL_INT" -gt 0 ]] && printf "    ├─ Relabel drops: ${CYAN}$DROPPED_RELABEL_INT${NC} (intentional)\n"
            echo "    └─ Error drops:   ${RED}$DROPPED_ERROR${NC}"
        else
            echo "  Samples Dropped:   ${RED}$DROPPED_FMT${NC}"
        fi
    else
        echo "  Samples Dropped:   ${GREEN}0${NC}"
    fi
fi

#############################################
# Shards
#############################################
printf "\n"
echo "${BLUE}═══ Shard Status ═══${NC}"

SHARDS=$(query_value "sum(prometheus_remote_storage_shards)")
SHARDS_DESIRED=$(query_value "sum(prometheus_remote_storage_shards_desired)")
SHARDS_MAX=$(query_value "sum(prometheus_remote_storage_shards_max)")
SHARDS_MIN=$(query_value "sum(prometheus_remote_storage_shards_min)")

if [[ -n "$SHARDS" ]]; then
    printf "  Current Shards:  $SHARDS\n"
    [[ -n "$SHARDS_DESIRED" ]] && printf "  Desired Shards:  $SHARDS_DESIRED\n"
    [[ -n "$SHARDS_MIN" ]] && printf "  Min Shards:      $SHARDS_MIN\n"
    [[ -n "$SHARDS_MAX" ]] && printf "  Max Shards:      $SHARDS_MAX\n"

    if [[ -n "$SHARDS_MAX" && "$SHARDS" == "$SHARDS_MAX" ]]; then
        printf "\n"
echo "  ${YELLOW}⚠ Shards at maximum - consider increasing maxShards${NC}"
    fi
fi

#############################################
# Lag
#############################################
printf "\n"
echo "${BLUE}═══ Remote Write Lag ═══${NC}"

HIGHEST_SENT=$(query_value "prometheus_remote_storage_queue_highest_sent_timestamp_seconds")
if [[ -n "$HIGHEST_SENT" ]]; then
    CURRENT_TIME=$(date +%s)
    LAG=$((CURRENT_TIME - ${HIGHEST_SENT%.*}))

    if [[ "$LAG" -gt 300 ]]; then
        printf "  Lag: ${RED}${LAG}s${NC} (>5min behind!)\n"
    elif [[ "$LAG" -gt 60 ]]; then
        echo "  Lag: ${YELLOW}${LAG}s${NC}"
    else
        echo "  Lag: ${GREEN}${LAG}s${NC}"
    fi
else
    echo "  ${YELLOW}Lag metric not available${NC}"
fi

#############################################
# Throughput
#############################################
printf "\n"
echo "${BLUE}═══ Throughput (5m rate) ═══${NC}"

RATE=$(query_value "sum(rate(prometheus_remote_storage_samples_total[5m]))")
if [[ -n "$RATE" ]]; then
    RATE_FMT=$(printf "%.0f" "$RATE" 2>/dev/null || echo "$RATE")
    echo "  Samples/sec: ${CYAN}$RATE_FMT${NC}"
fi

BYTES_RATE=$(query_value "sum(rate(prometheus_remote_storage_sent_bytes_total[5m]))")
if [[ -n "$BYTES_RATE" ]]; then
    BYTES_MB=$(awk "BEGIN {printf \"%.2f\", $BYTES_RATE / 1024 / 1024}")
    echo "  Throughput:  ${CYAN}${BYTES_MB} MB/s${NC}"
fi

#############################################
# Health Summary
#############################################
printf "\n"
echo "${BLUE}═══ Health Summary ═══${NC}"

HEALTHY=true
ISSUES=""

if [[ -n "$PENDING" && "${PENDING%.*}" -gt 100000 ]]; then
    HEALTHY=false
    ISSUES="$ISSUES\n  - Queue backing up (${PENDING%.*} pending)"
fi

if [[ -n "$FAILED" && "${FAILED%.*}" -gt 0 ]]; then
    HEALTHY=false
    ISSUES="$ISSUES\n  - Samples failing (${FAILED%.*} failed)"
fi

# Only flag drops as issues if they're NOT from writeRelabelConfigs
if [[ -n "$DROPPED_ERROR" && "$DROPPED_ERROR" -gt 0 ]]; then
    HEALTHY=false
    ISSUES="$ISSUES\n  - Samples being dropped due to errors ($DROPPED_ERROR dropped)"
fi

if [[ -n "$LAG" && "$LAG" -gt 300 ]]; then
    HEALTHY=false
    ISSUES="$ISSUES\n  - High lag (${LAG}s behind)"
fi

if [[ "$HEALTHY" == "true" ]]; then
    echo "  ${GREEN}✓ Remote write is healthy${NC}"
    if [[ -n "$DROPPED_RELABEL_INT" && "$DROPPED_RELABEL_INT" -gt 0 ]]; then
        RELABEL_FMT=$(printf "%'d" "$DROPPED_RELABEL_INT" 2>/dev/null || echo "$DROPPED_RELABEL_INT")
        printf "  ${CYAN}ℹ${NC} $RELABEL_FMT samples filtered by writeRelabelConfigs (intentional)\n"
    fi
else
    echo "  ${RED}✗ Remote write has issues:${NC}"
    printf "$ISSUES\n"
fi

printf "\n"
echo "${GREEN}✓ Remote write analysis complete${NC}"
