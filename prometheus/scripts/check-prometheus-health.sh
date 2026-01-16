#!/bin/bash

#############################################
# Prometheus Comprehensive Health Check
# Uses HTTP API for deep health inspection
#############################################

# Configuration
NAMESPACE="${NAMESPACE:-prometheus}"
LOCAL_PORT="${LOCAL_PORT:-9090}"
PROM_SVC="${PROM_SVC:-prometheus-kube-prometheus-prometheus}"
PROM_API_PREFIX=""  # Auto-detected

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace|-n)
            NAMESPACE="$2"
            shift 2
            ;;
        --service|-s)
            PROM_SVC="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --namespace, -n <ns>     Kubernetes namespace (default: prometheus)"
            echo "  --service, -s <svc>      Prometheus service name (default: prometheus-kube-prometheus-prometheus)"
            echo "  --help, -h               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Cleanup on exit
cleanup() {
    [[ -n "$PF_PID" ]] && kill $PF_PID 2>/dev/null
}
trap cleanup EXIT

echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════╗
║   Prometheus Health Check             ║
╚═══════════════════════════════════════╝
EOF
echo -e "${NC}"

#############################################
# Setup port-forward with auto-detection
#############################################
echo -e "${BLUE}→${NC} Setting up port-forward to $PROM_SVC..."

# Get service port
PROM_PORT=$(kubectl get svc -n "$NAMESPACE" "$PROM_SVC" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null)
[[ -z "$PROM_PORT" ]] && PROM_PORT=9090

kubectl port-forward -n "$NAMESPACE" svc/"$PROM_SVC" ${LOCAL_PORT}:${PROM_PORT} >/dev/null 2>&1 &
PF_PID=$!

# Wait and auto-detect API path
for i in {1..30}; do
    # Try /prometheus prefix first (common in kube-prometheus-stack)
    if curl -s --connect-timeout 2 "http://localhost:${LOCAL_PORT}/prometheus/api/v1/query?query=up" 2>/dev/null | grep -q '"status":"success"'; then
        PROM_API_PREFIX="/prometheus"
        echo -e "${GREEN}✓${NC} Port-forward ready (took ${i}s) - API path: /prometheus/api/v1"
        break
    fi
    # Try root path
    if curl -s --connect-timeout 2 "http://localhost:${LOCAL_PORT}/api/v1/query?query=up" 2>/dev/null | grep -q '"status":"success"'; then
        PROM_API_PREFIX=""
        echo -e "${GREEN}✓${NC} Port-forward ready (took ${i}s) - API path: /api/v1"
        break
    fi
    sleep 1
    if [[ $i -eq 30 ]]; then
        echo -e "${RED}✗${NC} Port-forward failed after 30s"
        echo -e "${YELLOW}⚠${NC} Check: kubectl get svc -n $NAMESPACE $PROM_SVC"
        exit 1
    fi
done

BASE_URL="http://localhost:${LOCAL_PORT}${PROM_API_PREFIX}"

# Helper function
query_prometheus() {
    local query="$1"
    local encoded=$(echo "$query" | sed 's/ /%20/g; s/(/%28/g; s/)/%29/g; s/{/%7B/g; s/}/%7D/g; s/\[/%5B/g; s/\]/%5D/g; s/"/%22/g; s/=/%3D/g; s/~/%7E/g')
    curl -s --connect-timeout 5 "${BASE_URL}/api/v1/query?query=$encoded" 2>/dev/null
}

HEALTH_SCORE=0
MAX_SCORE=8


#############################################
# 1. Build Info & Version
#############################################
echo -e "\n${BLUE}═══ 1. Build Information ═══${NC}"
BUILD_INFO=$(curl -s "${BASE_URL}/api/v1/status/buildinfo" 2>/dev/null)

if echo "$BUILD_INFO" | jq -e '.data.version' >/dev/null 2>&1; then
    VERSION=$(echo "$BUILD_INFO" | jq -r '.data.version')
    REVISION=$(echo "$BUILD_INFO" | jq -r '.data.revision' | cut -c1-8)
    GO_VERSION=$(echo "$BUILD_INFO" | jq -r '.data.goVersion')
    echo -e "  Version:    ${GREEN}$VERSION${NC}"
    echo -e "  Revision:   $REVISION"
    echo -e "  Go Version: $GO_VERSION"
    ((HEALTH_SCORE++))
else
    echo -e "  ${RED}✗ Failed to get build info${NC}"
fi

#############################################
# 2. Runtime & Config Status
#############################################
echo -e "\n${BLUE}═══ 2. Runtime Status ═══${NC}"
RUNTIME=$(curl -s "${BASE_URL}/api/v1/status/runtimeinfo" 2>/dev/null)

if echo "$RUNTIME" | jq -e '.data' >/dev/null 2>&1; then
    STORAGE_RETENTION=$(echo "$RUNTIME" | jq -r '.data.storageRetention // "unknown"')
    GOROUTINES=$(echo "$RUNTIME" | jq -r '.data.goroutineCount // "unknown"')
    echo -e "  Storage Retention: ${GREEN}$STORAGE_RETENTION${NC}"
    echo -e "  Goroutines:        $GOROUTINES"
    ((HEALTH_SCORE++))
else
    echo -e "  ${YELLOW}⚠ Runtime info not available${NC}"
fi

#############################################
# 3. TSDB Status
#############################################
echo -e "\n${BLUE}═══ 3. TSDB Status ═══${NC}"
TSDB=$(curl -s "${BASE_URL}/api/v1/status/tsdb" 2>/dev/null)

if echo "$TSDB" | jq -e '.data' >/dev/null 2>&1; then
    HEAD_SERIES=$(echo "$TSDB" | jq -r '.data.headStats.numSeries // 0')
    HEAD_CHUNKS=$(echo "$TSDB" | jq -r '.data.headStats.chunkCount // 0')
    HEAD_MIN_TIME=$(echo "$TSDB" | jq -r '.data.headStats.minTime // 0')
    HEAD_MAX_TIME=$(echo "$TSDB" | jq -r '.data.headStats.maxTime // 0')

    # Format numbers
    HEAD_SERIES_FMT=$(printf "%'d" "$HEAD_SERIES" 2>/dev/null || echo "$HEAD_SERIES")
    HEAD_CHUNKS_FMT=$(printf "%'d" "$HEAD_CHUNKS" 2>/dev/null || echo "$HEAD_CHUNKS")

    echo -e "  Active Series: ${GREEN}$HEAD_SERIES_FMT${NC}"
    echo -e "  Head Chunks:   $HEAD_CHUNKS_FMT"

    # Convert timestamps to human readable
    if [[ "$HEAD_MIN_TIME" != "0" && "$HEAD_MIN_TIME" != "null" ]]; then
        MIN_DATE=$(date -r $((HEAD_MIN_TIME/1000)) "+%Y-%m-%d %H:%M" 2>/dev/null || echo "N/A")
        MAX_DATE=$(date -r $((HEAD_MAX_TIME/1000)) "+%Y-%m-%d %H:%M" 2>/dev/null || echo "N/A")
        echo -e "  Data Range:    $MIN_DATE → $MAX_DATE"
    fi
    ((HEALTH_SCORE++))
else
    echo -e "  ${YELLOW}⚠ TSDB info not available${NC}"
fi

#############################################
# 4. Scrape Targets
#############################################
echo -e "\n${BLUE}═══ 4. Scrape Targets ═══${NC}"
TARGETS=$(curl -s "${BASE_URL}/api/v1/targets" 2>/dev/null)

if echo "$TARGETS" | jq -e '.data.activeTargets' >/dev/null 2>&1; then
    TOTAL_TARGETS=$(echo "$TARGETS" | jq '.data.activeTargets | length')
    UP_TARGETS=$(echo "$TARGETS" | jq '[.data.activeTargets[] | select(.health == "up")] | length')
    DOWN_TARGETS=$(echo "$TARGETS" | jq '[.data.activeTargets[] | select(.health == "down")] | length')

    echo -e "  Total Targets: $TOTAL_TARGETS"
    echo -e "  Up:            ${GREEN}$UP_TARGETS${NC}"

    if [[ "$DOWN_TARGETS" -gt 0 ]]; then
        echo -e "  Down:          ${RED}$DOWN_TARGETS${NC}"
        echo -e "\n  ${YELLOW}Down targets:${NC}"
        echo "$TARGETS" | jq -r '.data.activeTargets[] | select(.health == "down") | "    - \(.labels.job // "unknown"): \(.lastError)"' | head -5
    else
        echo -e "  Down:          ${GREEN}0${NC}"
        ((HEALTH_SCORE++))
    fi
    ((HEALTH_SCORE++))
else
    echo -e "  ${RED}✗ Failed to get targets${NC}"
fi

#############################################
# 5. Alert Rules
#############################################
echo -e "\n${BLUE}═══ 5. Alert Rules ═══${NC}"
RULES=$(curl -s "${BASE_URL}/api/v1/rules" 2>/dev/null)

if echo "$RULES" | jq -e '.data.groups' >/dev/null 2>&1; then
    TOTAL_GROUPS=$(echo "$RULES" | jq '.data.groups | length')
    TOTAL_RULES=$(echo "$RULES" | jq '[.data.groups[].rules[]] | length')
    ALERTING_RULES=$(echo "$RULES" | jq '[.data.groups[].rules[] | select(.type == "alerting")] | length')
    RECORDING_RULES=$(echo "$RULES" | jq '[.data.groups[].rules[] | select(.type == "recording")] | length')

    echo -e "  Rule Groups:     $TOTAL_GROUPS"
    echo -e "  Total Rules:     $TOTAL_RULES"
    echo -e "  Alerting Rules:  $ALERTING_RULES"
    echo -e "  Recording Rules: $RECORDING_RULES"
    ((HEALTH_SCORE++))
else
    echo -e "  ${YELLOW}⚠ Rules info not available${NC}"
fi

#############################################
# 6. Firing Alerts
#############################################
echo -e "\n${BLUE}═══ 6. Firing Alerts ═══${NC}"
ALERTS=$(curl -s "${BASE_URL}/api/v1/alerts" 2>/dev/null)

if echo "$ALERTS" | jq -e '.data.alerts' >/dev/null 2>&1; then
    TOTAL_ALERTS=$(echo "$ALERTS" | jq '.data.alerts | length')
    FIRING=$(echo "$ALERTS" | jq '[.data.alerts[] | select(.state == "firing")] | length')
    PENDING=$(echo "$ALERTS" | jq '[.data.alerts[] | select(.state == "pending")] | length')

    echo -e "  Total Alerts: $TOTAL_ALERTS"

    if [[ "$FIRING" -gt 0 ]]; then
        echo -e "  Firing:       ${RED}$FIRING${NC}"
        echo -e "\n  ${YELLOW}Firing alerts:${NC}"
        echo "$ALERTS" | jq -r '.data.alerts[] | select(.state == "firing") | "    - \(.labels.alertname): \(.labels.severity // "unknown")"' | head -5
    else
        echo -e "  Firing:       ${GREEN}0${NC}"
        ((HEALTH_SCORE++))
    fi

    if [[ "$PENDING" -gt 0 ]]; then
        echo -e "  Pending:      ${YELLOW}$PENDING${NC}"
    else
        echo -e "  Pending:      ${GREEN}0${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Alerts info not available${NC}"
fi

#############################################
# 7. Remote Write Status
#############################################
echo -e "\n${BLUE}═══ 7. Remote Write Status ═══${NC}"
RW_PENDING=$(query_prometheus "prometheus_remote_storage_samples_pending" | jq -r '.data.result[0].value[1] // empty' 2>/dev/null)
RW_FAILED=$(query_prometheus "prometheus_remote_storage_samples_failed_total" | jq -r '.data.result[0].value[1] // empty' 2>/dev/null)
RW_SENT=$(query_prometheus "prometheus_remote_storage_samples_total" | jq -r '.data.result[0].value[1] // empty' 2>/dev/null)

if [[ -n "$RW_SENT" ]]; then
    RW_SENT_FMT=$(printf "%'d" "${RW_SENT%.*}" 2>/dev/null || echo "$RW_SENT")
    echo -e "  Samples Sent:    ${GREEN}$RW_SENT_FMT${NC}"

    if [[ -n "$RW_PENDING" ]]; then
        RW_PENDING_FMT=$(printf "%'d" "${RW_PENDING%.*}" 2>/dev/null || echo "$RW_PENDING")
        if [[ "${RW_PENDING%.*}" -gt 100000 ]]; then
            echo -e "  Samples Pending: ${RED}$RW_PENDING_FMT${NC}"
        else
            echo -e "  Samples Pending: ${GREEN}$RW_PENDING_FMT${NC}"
        fi
    fi

    if [[ -n "$RW_FAILED" && "${RW_FAILED%.*}" -gt 0 ]]; then
        echo -e "  Samples Failed:  ${RED}$RW_FAILED${NC}"
    else
        echo -e "  Samples Failed:  ${GREEN}0${NC}"
        ((HEALTH_SCORE++))
    fi
else
    echo -e "  ${YELLOW}ℹ Remote write not configured or no data${NC}"
    ((HEALTH_SCORE++))  # Not a failure if not configured
fi

#############################################
# 8. Pod Health Summary
#############################################
echo -e "\n${BLUE}═══ 8. Pod Health Summary ═══${NC}"
TOTAL_PODS=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=prometheus --no-headers 2>/dev/null | wc -l | tr -d ' ')
RUNNING_PODS=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=prometheus --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')

if [[ "$TOTAL_PODS" -gt 0 ]]; then
    echo -e "  Total Pods:   $TOTAL_PODS"
    echo -e "  Running:      ${GREEN}$RUNNING_PODS${NC}"

    if [[ "$RUNNING_PODS" -eq "$TOTAL_PODS" ]]; then
        echo -e "  ${GREEN}✓ All pods healthy${NC}"
    else
        echo -e "  ${YELLOW}⚠ Some pods not running${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ No Prometheus pods found with label app.kubernetes.io/name=prometheus${NC}"
fi

#############################################
# 9. Overall Health Score
#############################################
echo -e "\n${BLUE}═══ 9. Overall Health Score ═══${NC}"
PERCENTAGE=$((HEALTH_SCORE * 100 / MAX_SCORE))

if [[ $PERCENTAGE -ge 80 ]]; then
    echo -e "  Health Score: ${GREEN}$HEALTH_SCORE/$MAX_SCORE ($PERCENTAGE%)${NC}"
    echo -e "  Status: ${GREEN}✓ HEALTHY${NC}"
elif [[ $PERCENTAGE -ge 50 ]]; then
    echo -e "  Health Score: ${YELLOW}$HEALTH_SCORE/$MAX_SCORE ($PERCENTAGE%)${NC}"
    echo -e "  Status: ${YELLOW}⚠ DEGRADED${NC}"
else
    echo -e "  Health Score: ${RED}$HEALTH_SCORE/$MAX_SCORE ($PERCENTAGE%)${NC}"
    echo -e "  Status: ${RED}✗ UNHEALTHY${NC}"
fi

echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
echo -e "${GREEN}Health Check Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}\n"

# Exit code based on health
[[ $PERCENTAGE -ge 80 ]] && exit 0 || exit 1
