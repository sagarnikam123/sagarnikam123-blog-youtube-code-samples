#!/bin/bash

#############################################
# Prometheus Resource Usage Analysis
# Shows CPU, memory, storage usage per pod
#############################################

# Configuration
NAMESPACE="${NAMESPACE:-prometheus}"

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
    echo "${YELLOW}⚠ metrics-server not available - utilization % will be empty${NC}"
    echo ""
fi

# Temp files
SPEC_FILE="/tmp/pod_specs_$$"
USAGE_FILE="/tmp/pod_usage_$$"
TOTALS_FILE="/tmp/resource_totals_$$"
trap "rm -f $SPEC_FILE $USAGE_FILE $TOTALS_FILE" EXIT

#############################################
# Get pod resource data
#############################################
echo "${BLUE}═══ Pod Resource Usage ═══${NC}"
echo ""

# Get requests/limits from pod specs
kubectl get pods -n "$NAMESPACE" -o json 2>/dev/null | jq -r '
  .items[] |
  {
    name: .metadata.name,
    cpu_req: ([.spec.containers[].resources.requests.cpu // "0m"] | map(if endswith("m") then (rtrimstr("m") | tonumber) else (tonumber * 1000) end) | add),
    cpu_lim: ([.spec.containers[].resources.limits.cpu // "0m"] | map(if endswith("m") then (rtrimstr("m") | tonumber) else (tonumber * 1000) end) | add),
    mem_req: ([.spec.containers[].resources.requests.memory // "0Mi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber * 1024) elif endswith("Mi") then (rtrimstr("Mi") | tonumber) elif endswith("Ki") then (rtrimstr("Ki") | tonumber / 1024) else 0 end) | add),
    mem_lim: ([.spec.containers[].resources.limits.memory // "0Mi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber * 1024) elif endswith("Mi") then (rtrimstr("Mi") | tonumber) elif endswith("Ki") then (rtrimstr("Ki") | tonumber / 1024) else 0 end) | add)
  } | "\(.name)|\(.cpu_req)|\(.cpu_lim)|\(.mem_req)|\(.mem_lim)"
' > "$SPEC_FILE"

# Get actual usage from metrics-server
if [[ "$METRICS_AVAILABLE" == "true" ]]; then
    kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{
        gsub(/m/, "", $2)
        gsub(/Mi/, "", $3)
        print $1 "|" $2 "|" $3
    }' > "$USAGE_FILE"
fi

# Print header
printf "%-50s │ %8s %8s %6s │ %8s %8s %6s\n" "Pod" "CPU Req" "CPU Lim" "CPU %" "Mem Req" "Mem Lim" "Mem %"
printf "%-50s │ %8s %8s %6s │ %8s %8s %6s\n" "$(printf '%.0s─' {1..50})" "────────" "────────" "──────" "────────" "────────" "──────"

# Process each pod
while IFS='|' read -r name cpu_req cpu_lim mem_req mem_lim; do
    [[ -z "$name" ]] && continue

    # Get actual usage from usage file
    cpu_use=0
    mem_use=0
    if [[ -f "$USAGE_FILE" ]]; then
        usage_line=$(grep "^${name}|" "$USAGE_FILE" 2>/dev/null || true)
        if [[ -n "$usage_line" ]]; then
            cpu_use=$(echo "$usage_line" | cut -d'|' -f2)
            mem_use=$(echo "$usage_line" | cut -d'|' -f3)
        fi
    fi

    # Calculate utilization %
    cpu_req_int=${cpu_req%.*}
    mem_req_int=${mem_req%.*}

    if [[ "$cpu_req_int" -gt 0 && "$METRICS_AVAILABLE" == "true" && "$cpu_use" -gt 0 ]]; then
        cpu_pct=$((cpu_use * 100 / cpu_req_int))
    else
        cpu_pct="-"
    fi

    if [[ "$mem_req_int" -gt 0 && "$METRICS_AVAILABLE" == "true" && "$mem_use" -gt 0 ]]; then
        mem_pct=$((mem_use * 100 / mem_req_int))
    else
        mem_pct="-"
    fi

    # Format memory as Mi
    mem_req_fmt="${mem_req_int}Mi"
    mem_lim_fmt="${mem_lim%.*}Mi"

    # Color utilization
    if [[ "$cpu_pct" != "-" ]]; then
        if [[ "$cpu_pct" -gt 80 ]]; then
            cpu_pct_fmt="${RED}$(printf "%5s" "${cpu_pct}%")${NC}"
        elif [[ "$cpu_pct" -lt 30 ]]; then
            cpu_pct_fmt="${YELLOW}$(printf "%5s" "${cpu_pct}%")${NC}"
        else
            cpu_pct_fmt="${GREEN}$(printf "%5s" "${cpu_pct}%")${NC}"
        fi
    else
        cpu_pct_fmt="$(printf "%5s" "-")"
    fi

    if [[ "$mem_pct" != "-" ]]; then
        if [[ "$mem_pct" -gt 80 ]]; then
            mem_pct_fmt="${RED}$(printf "%5s" "${mem_pct}%")${NC}"
        elif [[ "$mem_pct" -lt 30 ]]; then
            mem_pct_fmt="${YELLOW}$(printf "%5s" "${mem_pct}%")${NC}"
        else
            mem_pct_fmt="${GREEN}$(printf "%5s" "${mem_pct}%")${NC}"
        fi
    else
        mem_pct_fmt="$(printf "%5s" "-")"
    fi

    # Truncate pod name
    name_short="${name:0:48}"

    printf "%-50s │ %8s %8s %s │ %8s %8s %s\n" \
        "$name_short" \
        "${cpu_req_int}m" "${cpu_lim%.*}m" "$cpu_pct_fmt" \
        "$mem_req_fmt" "$mem_lim_fmt" "$mem_pct_fmt"

    # Accumulate totals
    echo "${cpu_req_int} ${cpu_lim%.*} ${cpu_use:-0} ${mem_req_int} ${mem_lim%.*} ${mem_use:-0}" >> "$TOTALS_FILE"

done < "$SPEC_FILE"

# Calculate and print totals
if [[ -f "$TOTALS_FILE" && -s "$TOTALS_FILE" ]]; then
    TOTALS=$(awk '{
        cpu_req+=$1; cpu_lim+=$2; cpu_use+=$3;
        mem_req+=$4; mem_lim+=$5; mem_use+=$6;
        count++
    } END {
        printf "%d %d %d %d %d %d %d", count, cpu_req, cpu_lim, cpu_use, mem_req, mem_lim, mem_use
    }' "$TOTALS_FILE")

    POD_COUNT=$(echo "$TOTALS" | awk '{print $1}')
    TOTAL_CPU_REQ=$(echo "$TOTALS" | awk '{print $2}')
    TOTAL_CPU_LIM=$(echo "$TOTALS" | awk '{print $3}')
    TOTAL_CPU_USE=$(echo "$TOTALS" | awk '{print $4}')
    TOTAL_MEM_REQ=$(echo "$TOTALS" | awk '{print $5}')
    TOTAL_MEM_LIM=$(echo "$TOTALS" | awk '{print $6}')
    TOTAL_MEM_USE=$(echo "$TOTALS" | awk '{print $7}')

    # Calculate total utilization
    if [[ "$TOTAL_CPU_REQ" -gt 0 && "$METRICS_AVAILABLE" == "true" && "$TOTAL_CPU_USE" -gt 0 ]]; then
        TOTAL_CPU_PCT=$((TOTAL_CPU_USE * 100 / TOTAL_CPU_REQ))
    else
        TOTAL_CPU_PCT="-"
    fi

    if [[ "$TOTAL_MEM_REQ" -gt 0 && "$METRICS_AVAILABLE" == "true" && "$TOTAL_MEM_USE" -gt 0 ]]; then
        TOTAL_MEM_PCT=$((TOTAL_MEM_USE * 100 / TOTAL_MEM_REQ))
    else
        TOTAL_MEM_PCT="-"
    fi

    # Format total memory
    TOTAL_MEM_REQ_FMT="${TOTAL_MEM_REQ}Mi"
    TOTAL_MEM_LIM_FMT="${TOTAL_MEM_LIM}Mi"

    # Color total utilization
    if [[ "$TOTAL_CPU_PCT" != "-" ]]; then
        if [[ "$TOTAL_CPU_PCT" -gt 80 ]]; then
            TOTAL_CPU_PCT_FMT="${RED}$(printf "%5s" "${TOTAL_CPU_PCT}%")${NC}"
        elif [[ "$TOTAL_CPU_PCT" -lt 30 ]]; then
            TOTAL_CPU_PCT_FMT="${YELLOW}$(printf "%5s" "${TOTAL_CPU_PCT}%")${NC}"
        else
            TOTAL_CPU_PCT_FMT="${GREEN}$(printf "%5s" "${TOTAL_CPU_PCT}%")${NC}"
        fi
    else
        TOTAL_CPU_PCT_FMT="$(printf "%5s" "-")"
    fi

    if [[ "$TOTAL_MEM_PCT" != "-" ]]; then
        if [[ "$TOTAL_MEM_PCT" -gt 80 ]]; then
            TOTAL_MEM_PCT_FMT="${RED}$(printf "%5s" "${TOTAL_MEM_PCT}%")${NC}"
        elif [[ "$TOTAL_MEM_PCT" -lt 30 ]]; then
            TOTAL_MEM_PCT_FMT="${YELLOW}$(printf "%5s" "${TOTAL_MEM_PCT}%")${NC}"
        else
            TOTAL_MEM_PCT_FMT="${GREEN}$(printf "%5s" "${TOTAL_MEM_PCT}%")${NC}"
        fi
    else
        TOTAL_MEM_PCT_FMT="$(printf "%5s" "-")"
    fi

    printf "%-50s │ %8s %8s %6s │ %8s %8s %6s\n" "$(printf '%.0s─' {1..50})" "────────" "────────" "──────" "────────" "────────" "──────"
    printf "${CYAN}%-50s${NC} │ %8s %8s %s │ %8s %8s %s\n" \
        "Total ($POD_COUNT pods)" \
        "${TOTAL_CPU_REQ}m" "${TOTAL_CPU_LIM}m" "$TOTAL_CPU_PCT_FMT" \
        "$TOTAL_MEM_REQ_FMT" "$TOTAL_MEM_LIM_FMT" "$TOTAL_MEM_PCT_FMT"
fi

echo ""

#############################################
# Storage (PVCs)
#############################################
echo "${BLUE}═══ Storage (PVCs) ═══${NC}"
PVC_DATA=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null)
PVC_COUNT=$(echo "$PVC_DATA" | grep -c . 2>/dev/null || echo "0")

if [[ -z "$PVC_DATA" || "$PVC_COUNT" -eq 0 ]]; then
    echo "  ${YELLOW}No PVCs found (using emptyDir or no persistence)${NC}"
else
    echo ""
    printf "  %-55s %-10s %-10s\n" "PVC Name" "Status" "Size"
    printf "  %-55s %-10s %-10s\n" "$(printf '%.0s─' {1..55})" "──────────" "──────────"

    echo "$PVC_DATA" | while read -r pvc status volume capacity rest; do
        if [[ "$status" == "Bound" ]]; then
            printf "  %-55s ${GREEN}%-10s${NC} %-10s\n" "${pvc:0:55}" "$status" "$capacity"
        else
            printf "  %-55s ${RED}%-10s${NC} %-10s\n" "${pvc:0:55}" "$status" "$capacity"
        fi
    done

    # Total storage
    TOTAL_STORAGE=$(kubectl get pvc -n "$NAMESPACE" -o json 2>/dev/null | jq -r '
      [.items[].spec.resources.requests.storage // "0Gi"] |
      map(if endswith("Gi") then (rtrimstr("Gi") | tonumber) elif endswith("Ti") then (rtrimstr("Ti") | tonumber * 1024) else 0 end) | add
    ')
    printf "  %-55s %-10s ${CYAN}%-10s${NC}\n" "$(printf '%.0s─' {1..55})" "──────────" "──────────"
    printf "  ${CYAN}%-55s${NC} %-10s ${CYAN}%-10s${NC}\n" "Total" "" "${TOTAL_STORAGE}Gi"
fi

echo ""

#############################################
# Efficiency Summary
#############################################
if [[ "$METRICS_AVAILABLE" == "true" && -n "$TOTAL_CPU_PCT" && "$TOTAL_CPU_PCT" != "-" ]]; then
    echo "${BLUE}═══ Efficiency Summary ═══${NC}"

    if [[ "$TOTAL_CPU_PCT" -lt 30 ]]; then
        echo "  ${YELLOW}⚠ CPU: Under-utilized (${TOTAL_CPU_PCT}%) - consider reducing requests${NC}"
    elif [[ "$TOTAL_CPU_PCT" -gt 80 ]]; then
        echo "  ${RED}🔴 CPU: High utilization (${TOTAL_CPU_PCT}%) - consider increasing limits${NC}"
    else
        echo "  ${GREEN}✓ CPU: Good utilization (${TOTAL_CPU_PCT}%)${NC}"
    fi

    if [[ "$TOTAL_MEM_PCT" != "-" ]]; then
        if [[ "$TOTAL_MEM_PCT" -lt 30 ]]; then
            echo "  ${YELLOW}⚠ Memory: Under-utilized (${TOTAL_MEM_PCT}%) - consider reducing requests${NC}"
        elif [[ "$TOTAL_MEM_PCT" -gt 80 ]]; then
            echo "  ${RED}🔴 Memory: High utilization (${TOTAL_MEM_PCT}%) - consider increasing limits${NC}"
        else
            echo "  ${GREEN}✓ Memory: Good utilization (${TOTAL_MEM_PCT}%)${NC}"
        fi
    fi
    echo ""
fi

echo "${GREEN}✓ Resource analysis complete${NC}"
