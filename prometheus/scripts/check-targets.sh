#!/bin/bash

#############################################
# Prometheus Scrape Targets Analysis
# Shows detailed target status and health
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
NC=$'\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace|-n) NAMESPACE="$2"; shift 2 ;;
        --job|-j) FILTER_JOB="$2"; shift 2 ;;
        --down-only|-d) DOWN_ONLY=true; shift ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --namespace, -n <ns>   Kubernetes namespace (default: prometheus)"
            echo "  --job, -j <job>        Filter by job name"
            echo "  --down-only, -d        Show only down targets"
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
echo "${GREEN}║   Prometheus Scrape Targets           ║${NC}"
echo "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""

# Setup port-forward
PROM_PORT=$(kubectl get svc -n "$NAMESPACE" "$PROM_SVC" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null || echo "9090")
kubectl port-forward -n "$NAMESPACE" svc/"$PROM_SVC" ${LOCAL_PORT}:${PROM_PORT} >/dev/null 2>&1 &
PF_PID=$!

# Auto-detect API path
for i in {1..30}; do
    if curl -s --connect-timeout 2 "http://localhost:${LOCAL_PORT}/prometheus/api/v1/targets" 2>/dev/null | grep -q '"status":"success"'; then
        PROM_API_PREFIX="/prometheus"
        printf "${GREEN}✓${NC} Connected (API: /prometheus/api/v1)\n"
        break
    fi
    if curl -s --connect-timeout 2 "http://localhost:${LOCAL_PORT}/api/v1/targets" 2>/dev/null | grep -q '"status":"success"'; then
        PROM_API_PREFIX=""
        printf "${GREEN}✓${NC} Connected (API: /api/v1)\n"
        break
    fi
    sleep 1
    [[ $i -eq 30 ]] && { echo "${RED}✗ Connection failed${NC}"; exit 1; }
done

BASE_URL="http://localhost:${LOCAL_PORT}${PROM_API_PREFIX}"

# Helper function to sanitize JSON (remove control characters)
sanitize_json() {
    tr -d '\000-\011\013-\037' | sed 's/\\u001b\[[0-9;]*m//g'
}

TARGETS=$(curl -s "${BASE_URL}/api/v1/targets" 2>/dev/null | sanitize_json)

#############################################
# Summary
#############################################
printf "\n"
echo "${BLUE}═══ Target Summary ═══${NC}"
TOTAL=$(echo "$TARGETS" | jq '.data.activeTargets | length' 2>/dev/null || echo "0")
UP=$(echo "$TARGETS" | jq '[.data.activeTargets[] | select(.health == "up")] | length' 2>/dev/null || echo "0")
DOWN=$(echo "$TARGETS" | jq '[.data.activeTargets[] | select(.health == "down")] | length' 2>/dev/null || echo "0")
UNKNOWN=$(echo "$TARGETS" | jq '[.data.activeTargets[] | select(.health == "unknown")] | length' 2>/dev/null || echo "0")

printf "  Total:   $TOTAL\n"
echo "  Up:      ${GREEN}$UP${NC}"
[[ "$DOWN" -gt 0 ]] && echo "  Down:    ${RED}$DOWN${NC}" || echo "  Down:    ${GREEN}0${NC}"
[[ "$UNKNOWN" -gt 0 ]] && echo "  Unknown: ${YELLOW}$UNKNOWN${NC}"

#############################################
# By Job
#############################################
printf "\n"
echo "${BLUE}═══ Targets by Job ═══${NC}"
printf "%-40s %6s %6s %6s\n" "Job" "Total" "Up" "Down"
printf "%-40s %6s %6s %6s\n" "---" "-----" "----" "----"

echo "$TARGETS" | jq -r '
  .data.activeTargets | group_by(.labels.job) | .[] |
  {
    job: .[0].labels.job,
    total: length,
    up: [.[] | select(.health == "up")] | length,
    down: [.[] | select(.health == "down")] | length
  } | "\(.job) \(.total) \(.up) \(.down)"
' 2>/dev/null | sort | while read job total up down; do
    if [[ -n "$FILTER_JOB" && "$job" != *"$FILTER_JOB"* ]]; then
        continue
    fi
    if [[ "$down" -gt 0 ]]; then
        printf "%-40s %6s ${GREEN}%6s${NC} ${RED}%6s${NC}\n" "$job" "$total" "$up" "$down"
    else
        printf "%-40s %6s ${GREEN}%6s${NC} %6s\n" "$job" "$total" "$up" "$down"
    fi
done

#############################################
# Down Targets Detail
#############################################
if [[ "$DOWN" -gt 0 ]]; then
    printf "\n"
echo "${BLUE}═══ Down Targets (Details) ═══${NC}"
    echo "$TARGETS" | jq -r '
      .data.activeTargets[] | select(.health == "down") |
      "Job: \(.labels.job)\n  Instance: \(.labels.instance)\n  Error: \(.lastError)\n  Last Scrape: \(.lastScrape)\n"
    ' 2>/dev/null | head -50
fi

#############################################
# Scrape Duration Stats
#############################################
if [[ -z "$DOWN_ONLY" ]]; then
    printf "\n"
echo "${BLUE}═══ Scrape Duration (Top 10 Slowest) ═══${NC}"
    printf "%-40s %-20s %12s\n" "Job" "Instance" "Duration"
    printf "%-40s %-20s %12s\n" "---" "--------" "--------"

    echo "$TARGETS" | jq -r '
      .data.activeTargets | sort_by(.lastScrapeDuration) | reverse | .[0:10][] |
      "\(.labels.job) \(.labels.instance) \(.lastScrapeDuration)"
    ' 2>/dev/null | while read job instance duration; do
        duration_ms=$(echo "$duration" | awk '{printf "%.2f", $1 * 1000}')
        printf "%-40s %-20s %10sms\n" "${job:0:40}" "${instance:0:20}" "$duration_ms"
    done
fi

printf "\n"
echo "${GREEN}✓ Target analysis complete${NC}"
