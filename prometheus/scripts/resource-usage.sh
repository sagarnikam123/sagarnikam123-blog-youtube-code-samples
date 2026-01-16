#!/bin/bash

#############################################
# Prometheus Resource Usage Analysis
# Shows CPU, memory, storage usage
#############################################

# Configuration
NAMESPACE="${NAMESPACE:-prometheus}"

# Colors - using $'...' syntax for POSIX compatibility
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

echo "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo "${GREEN}║   Prometheus Resource Usage           ║${NC}"
echo "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo "Namespace: ${YELLOW}$NAMESPACE${NC}"
echo ""

# Check namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "${RED}Error: Namespace '$NAMESPACE' not found${NC}"
    exit 1
fi

# Check metrics-server
METRICS_AVAILABLE=true
if ! kubectl top nodes &>/dev/null 2>&1; then
    METRICS_AVAILABLE=false
    echo "${YELLOW}⚠ metrics-server not available - showing allocation only${NC}"
    echo ""
fi

#############################################
# Pod Status Overview
#############################################
echo "${BLUE}═══ Pod Status ═══${NC}"
PODS=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null)
TOTAL=$(echo "$PODS" | wc -l | tr -d ' ')
RUNNING=$(echo "$PODS" | grep -c "Running" || echo "0")
NOT_RUNNING=$((TOTAL - RUNNING))

printf "  Total Pods: $TOTAL\n"
echo "  Running:    ${GREEN}$RUNNING${NC}"
[[ "$NOT_RUNNING" -gt 0 ]] && echo "  Not Running: ${RED}$NOT_RUNNING${NC}"
echo ""

#############################################
# Resource Allocation
#############################################
echo "${BLUE}═══ Resource Allocation ═══${NC}"

# Calculate requests and limits
REQUESTS=$(kubectl get pods -n "$NAMESPACE" -o json 2>/dev/null | jq -r '
  [.items[].spec.containers[].resources.requests // {}] |
  {
    cpu: ([.[].cpu // "0m"] | map(if endswith("m") then (rtrimstr("m") | tonumber) else (tonumber * 1000) end) | add),
    memory: ([.[].memory // "0Mi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber * 1024) elif endswith("Mi") then (rtrimstr("Mi") | tonumber) elif endswith("Ki") then (rtrimstr("Ki") | tonumber / 1024) else 0 end) | add)
  }
')

LIMITS=$(kubectl get pods -n "$NAMESPACE" -o json 2>/dev/null | jq -r '
  [.items[].spec.containers[].resources.limits // {}] |
  {
    cpu: ([.[].cpu // "0m"] | map(if endswith("m") then (rtrimstr("m") | tonumber) else (tonumber * 1000) end) | add),
    memory: ([.[].memory // "0Mi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber * 1024) elif endswith("Mi") then (rtrimstr("Mi") | tonumber) elif endswith("Ki") then (rtrimstr("Ki") | tonumber / 1024) else 0 end) | add)
  }
')

CPU_REQ=$(echo "$REQUESTS" | jq -r '.cpu')
MEM_REQ=$(echo "$REQUESTS" | jq -r '.memory')
CPU_LIM=$(echo "$LIMITS" | jq -r '.cpu')
MEM_LIM=$(echo "$LIMITS" | jq -r '.memory')

# Convert memory to Gi for display
MEM_REQ_GI=$(awk "BEGIN {printf \"%.2f\", $MEM_REQ / 1024}")
MEM_LIM_GI=$(awk "BEGIN {printf \"%.2f\", $MEM_LIM / 1024}")

printf "%-12s %12s %12s\n" "Resource" "Requests" "Limits"
printf "%-12s %12s %12s\n" "--------" "--------" "------"
printf "%-12s %11sm %11sm\n" "CPU" "$CPU_REQ" "$CPU_LIM"
printf "%-12s %10sGi %10sGi\n" "Memory" "$MEM_REQ_GI" "$MEM_LIM_GI"
echo ""

#############################################
# Actual Usage (if metrics available)
#############################################
if [[ "$METRICS_AVAILABLE" == "true" ]]; then
    echo "${BLUE}═══ Actual Resource Usage ═══${NC}"

    ACTUAL_CPU=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{gsub(/m/,"",$2); sum+=$2} END {print sum}')
    ACTUAL_MEM=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{gsub(/Mi/,"",$3); sum+=$3} END {print sum}')

    ACTUAL_CPU=${ACTUAL_CPU:-0}
    ACTUAL_MEM=${ACTUAL_MEM:-0}
    ACTUAL_MEM_GI=$(awk "BEGIN {printf \"%.2f\", $ACTUAL_MEM / 1024}")

    # Calculate utilization
    CPU_UTIL=$(awk "BEGIN {printf \"%.1f\", ($CPU_REQ > 0) ? ($ACTUAL_CPU / $CPU_REQ) * 100 : 0}")
    MEM_UTIL=$(awk "BEGIN {printf \"%.1f\", ($MEM_REQ > 0) ? ($ACTUAL_MEM / $MEM_REQ) * 100 : 0}")

    printf "%-12s %12s %12s %12s\n" "Resource" "Usage" "Requested" "Utilization"
    printf "%-12s %12s %12s %12s\n" "--------" "-----" "---------" "-----------"
    printf "%-12s %11sm %11sm %11s%%\n" "CPU" "$ACTUAL_CPU" "$CPU_REQ" "$CPU_UTIL"
    printf "%-12s %10sGi %10sGi %11s%%\n" "Memory" "$ACTUAL_MEM_GI" "$MEM_REQ_GI" "$MEM_UTIL"
    echo ""

    # Efficiency indicators
    echo "${BLUE}═══ Resource Efficiency ═══${NC}"
    if (( $(echo "$CPU_UTIL < 30" | bc -l 2>/dev/null || echo 0) )); then
        echo "  ${YELLOW}⚠ CPU: Under-utilized (${CPU_UTIL}%)${NC}"
    elif (( $(echo "$CPU_UTIL > 80" | bc -l 2>/dev/null || echo 0) )); then
        echo "  ${RED}🔴 CPU: High utilization (${CPU_UTIL}%)${NC}"
    else
        echo "  ${GREEN}✓ CPU: Good utilization (${CPU_UTIL}%)${NC}"
    fi

    if (( $(echo "$MEM_UTIL < 40" | bc -l 2>/dev/null || echo 0) )); then
        echo "  ${YELLOW}⚠ Memory: Under-utilized (${MEM_UTIL}%)${NC}"
    elif (( $(echo "$MEM_UTIL > 80" | bc -l 2>/dev/null || echo 0) )); then
        echo "  ${RED}🔴 Memory: High utilization (${MEM_UTIL}%)${NC}"
    else
        echo "  ${GREEN}✓ Memory: Good utilization (${MEM_UTIL}%)${NC}"
    fi
    echo ""
fi

#############################################
# Storage (PVCs)
#############################################
echo "${BLUE}═══ Storage (PVCs) ═══${NC}"
PVC_COUNT=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')

if [[ "$PVC_COUNT" -eq 0 ]]; then
    echo "  ${YELLOW}No PVCs found${NC}"
else
    printf "  Total PVCs: $PVC_COUNT\n"
    echo ""
    printf "  %-50s %-10s %-12s\n" "PVC Name" "Status" "Capacity"
    printf "  %-50s %-10s %-12s\n" "--------" "------" "--------"

    kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | while read pvc status volume capacity rest; do
        if [[ "$status" == "Bound" ]]; then
            printf "  %-50s ${GREEN}%-10s${NC} %-12s\n" "${pvc:0:50}" "$status" "$capacity"
        else
            printf "  %-50s ${RED}%-10s${NC} %-12s\n" "${pvc:0:50}" "$status" "$capacity"
        fi
    done

    # Total storage
    TOTAL_STORAGE=$(kubectl get pvc -n "$NAMESPACE" -o json 2>/dev/null | jq -r '
      [.items[].spec.resources.requests.storage // "0Gi"] |
      map(if endswith("Gi") then (rtrimstr("Gi") | tonumber) elif endswith("Ti") then (rtrimstr("Ti") | tonumber * 1024) else 0 end) | add
    ')
    echo ""
    echo "  Total Storage: ${CYAN}${TOTAL_STORAGE}Gi${NC}"
fi
echo ""

#############################################
# Pod-level Breakdown
#############################################
echo "${BLUE}═══ Pod Resource Breakdown ═══${NC}"

if [[ "$METRICS_AVAILABLE" == "true" ]]; then
    printf "  %-55s %10s %10s\n" "Pod" "CPU" "Memory"
    printf "  %-55s %10s %10s\n" "---" "---" "------"

    kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | sort -k2 -rn | while read pod cpu mem; do
        printf "  %-55s %10s %10s\n" "${pod:0:55}" "$cpu" "$mem"
    done
else
    printf "  %-55s %10s %10s\n" "Pod" "CPU Req" "Mem Req"
    printf "  %-55s %10s %10s\n" "---" "-------" "-------"

    kubectl get pods -n "$NAMESPACE" -o json 2>/dev/null | jq -r '
      .items[] |
      {
        name: .metadata.name,
        cpu: ([.spec.containers[].resources.requests.cpu // "0m"] | map(rtrimstr("m") | tonumber) | add),
        mem: ([.spec.containers[].resources.requests.memory // "0Mi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber * 1024) elif endswith("Mi") then (rtrimstr("Mi") | tonumber) else 0 end) | add)
      } | "\(.name) \(.cpu)m \(.mem)Mi"
    ' | while read pod cpu mem; do
        printf "  %-55s %10s %10s\n" "${pod:0:55}" "$cpu" "$mem"
    done
fi

echo "\n${GREEN}✓ Resource analysis complete${NC}"
