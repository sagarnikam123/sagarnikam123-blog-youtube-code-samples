#!/bin/bash

#############################################
# Prometheus Alert Rules & Firing Alerts
# Shows alert rules status and active alerts
#############################################

# Configuration
NAMESPACE="${NAMESPACE:-prometheus}"
LOCAL_PORT="${LOCAL_PORT:-9090}"
PROM_SVC="${PROM_SVC:-prometheus-kube-prometheus-prometheus}"
PROM_API_PREFIX=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace|-n) NAMESPACE="$2"; shift 2 ;;
        --firing-only|-f) FIRING_ONLY=true; shift ;;
        --group|-g) FILTER_GROUP="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --namespace, -n <ns>   Kubernetes namespace (default: prometheus)"
            echo "  --firing-only, -f      Show only firing alerts"
            echo "  --group, -g <name>     Filter by rule group name"
            echo "  --help, -h             Show this help"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Cleanup
cleanup() { [[ -n "$PF_PID" ]] && kill $PF_PID 2>/dev/null; }
trap cleanup EXIT

echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Prometheus Alerts & Rules           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""

# Setup port-forward
PROM_PORT=$(kubectl get svc -n "$NAMESPACE" "$PROM_SVC" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null || echo "9090")
kubectl port-forward -n "$NAMESPACE" svc/"$PROM_SVC" ${LOCAL_PORT}:${PROM_PORT} >/dev/null 2>&1 &
PF_PID=$!

# Auto-detect API path
for i in {1..30}; do
    if curl -s --connect-timeout 2 "http://localhost:${LOCAL_PORT}/prometheus/api/v1/rules" 2>/dev/null | grep -q '"status":"success"'; then
        PROM_API_PREFIX="/prometheus"
        echo -e "${GREEN}✓${NC} Connected"
        break
    fi
    if curl -s --connect-timeout 2 "http://localhost:${LOCAL_PORT}/api/v1/rules" 2>/dev/null | grep -q '"status":"success"'; then
        PROM_API_PREFIX=""
        echo -e "${GREEN}✓${NC} Connected"
        break
    fi
    sleep 1
    [[ $i -eq 30 ]] && { echo -e "${RED}✗ Connection failed${NC}"; exit 1; }
done

BASE_URL="http://localhost:${LOCAL_PORT}${PROM_API_PREFIX}"

# Helper function to sanitize JSON (remove control characters)
sanitize_json() {
    tr -d '\000-\011\013-\037' | sed 's/\\u001b\[[0-9;]*m//g'
}

#############################################
# Firing Alerts
#############################################
echo -e "\n${BLUE}═══ Firing Alerts ═══${NC}"
ALERTS=$(curl -s "${BASE_URL}/api/v1/alerts" 2>/dev/null | sanitize_json)

FIRING=$(echo "$ALERTS" | jq '[.data.alerts[] | select(.state == "firing")] | length' 2>/dev/null || echo "0")
PENDING=$(echo "$ALERTS" | jq '[.data.alerts[] | select(.state == "pending")] | length' 2>/dev/null || echo "0")

if [[ "$FIRING" -gt 0 ]]; then
    echo -e "  ${RED}🔥 $FIRING firing alert(s)${NC}"
    echo ""
    echo "$ALERTS" | jq -r '
      .data.alerts[] | select(.state == "firing") |
      "  ● \(.labels.alertname)\n    Severity: \(.labels.severity // "unknown")\n    Namespace: \(.labels.namespace // "N/A")\n    Since: \(.activeAt)\n"
    ' 2>/dev/null | head -30
else
    echo -e "  ${GREEN}✓ No firing alerts${NC}"
fi

if [[ "$PENDING" -gt 0 ]]; then
    echo -e "\n  ${YELLOW}⏳ $PENDING pending alert(s)${NC}"
    if [[ -z "$FIRING_ONLY" ]]; then
        echo "$ALERTS" | jq -r '
          .data.alerts[] | select(.state == "pending") |
          "    - \(.labels.alertname) (\(.labels.severity // "unknown"))"
        ' 2>/dev/null | head -10
    fi
fi

[[ "$FIRING_ONLY" == "true" ]] && { echo ""; exit 0; }

#############################################
# Rule Groups Summary
#############################################
echo -e "\n${BLUE}═══ Rule Groups ═══${NC}"
RULES=$(curl -s "${BASE_URL}/api/v1/rules" 2>/dev/null | sanitize_json)

TOTAL_GROUPS=$(echo "$RULES" | jq '.data.groups | length' 2>/dev/null || echo "0")
TOTAL_ALERTING=$(echo "$RULES" | jq '[.data.groups[].rules[] | select(.type == "alerting")] | length' 2>/dev/null || echo "0")
TOTAL_RECORDING=$(echo "$RULES" | jq '[.data.groups[].rules[] | select(.type == "recording")] | length' 2>/dev/null || echo "0")

echo -e "  Total Groups:    $TOTAL_GROUPS"
echo -e "  Alerting Rules:  $TOTAL_ALERTING"
echo -e "  Recording Rules: $TOTAL_RECORDING"

#############################################
# Rules by Group
#############################################
echo -e "\n${BLUE}═══ Rules by Group ═══${NC}"
printf "%-45s %8s %8s %8s\n" "Group" "Alerting" "Recording" "Interval"
printf "%-45s %8s %8s %8s\n" "-----" "--------" "---------" "--------"

echo "$RULES" | jq -r '
  .data.groups[] |
  {
    name: .name,
    interval: .interval,
    alerting: [.rules[] | select(.type == "alerting")] | length,
    recording: [.rules[] | select(.type == "recording")] | length
  } | "\(.name) \(.alerting) \(.recording) \(.interval)"
' 2>/dev/null | sort | while read name alerting recording interval; do
    if [[ -n "$FILTER_GROUP" && "$name" != *"$FILTER_GROUP"* ]]; then
        continue
    fi
    printf "%-45s %8s %8s %8s\n" "${name:0:45}" "$alerting" "$recording" "$interval"
done

#############################################
# Alert Rules by Severity
#############################################
echo -e "\n${BLUE}═══ Alert Rules by Severity ═══${NC}"
echo "$RULES" | jq -r '
  [.data.groups[].rules[] | select(.type == "alerting")] |
  group_by(.labels.severity) | .[] |
  "\(.[0].labels.severity // "none"): \(length)"
' 2>/dev/null | while read line; do
    severity=$(echo "$line" | cut -d: -f1)
    count=$(echo "$line" | cut -d: -f2 | tr -d ' ')
    case "$severity" in
        critical) echo -e "  ${RED}$severity: $count${NC}" ;;
        warning)  echo -e "  ${YELLOW}$severity: $count${NC}" ;;
        info)     echo -e "  ${CYAN}$severity: $count${NC}" ;;
        *)        echo -e "  $severity: $count" ;;
    esac
done

#############################################
# Unhealthy Rules
#############################################
echo -e "\n${BLUE}═══ Unhealthy Rules ═══${NC}"
UNHEALTHY=$(echo "$RULES" | jq '[.data.groups[].rules[] | select(.health != "ok" and .health != null)] | length' 2>/dev/null || echo "0")

if [[ "$UNHEALTHY" -gt 0 && "$UNHEALTHY" != "null" ]]; then
    echo -e "  ${RED}⚠ $UNHEALTHY unhealthy rule(s)${NC}"
    echo "$RULES" | jq -r '
      .data.groups[].rules[] | select(.health != "ok" and .health != null) |
      "    - \(.name): \(.health) - \(.lastError // "no error")"
    ' 2>/dev/null | head -10
else
    echo -e "  ${GREEN}✓ All rules healthy${NC}"
fi

echo -e "\n${GREEN}✓ Alert analysis complete${NC}\n"
