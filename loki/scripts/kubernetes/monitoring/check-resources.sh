#!/bin/bash

# Minikube & Pod Resource Monitoring Script
# Shows resource allocation, usage, availability, and pressure indicators

set -euo pipefail

# Configuration
NAMESPACE="${LOKI_NAMESPACE:-loki}"
COMPONENT=""
HIGH_CPU_THRESHOLD=80
HIGH_MEM_THRESHOLD=80

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Function to get available components from cluster
get_available_components() {
    local k8s_components=$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.labels.app\.kubernetes\.io/component}' 2>/dev/null | tr ' ' '\n' | sort -u | grep -v '^$' || echo "")
    local app_components=$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.labels.app}' 2>/dev/null | tr ' ' '\n' | sort -u | grep -v '^$' | grep -v '^loki$' || echo "")
    echo -e "${k8s_components}\n${app_components}" | sort -u | grep -v '^$'
}

# Usage function
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Monitor Minikube cluster and pod resource usage with pressure indicators.

OPTIONS:
    -n, --namespace NAME     Kubernetes namespace (default: loki)
    -c, --component NAME     Filter by component (e.g., ingester, distributor)
    --list-components        List available components
    --cpu-threshold PCT      High CPU usage threshold (default: 80)
    --mem-threshold PCT      High memory usage threshold (default: 80)
    -h, --help               Display this help message

EXAMPLES:
    $(basename "$0")                        # Full resource report
    $(basename "$0") -c ingester            # Resources for ingester only
    $(basename "$0") --list-components      # List available components
    $(basename "$0") --cpu-threshold 70     # Custom CPU threshold

EOF
    exit 0
}

# List components function
list_components() {
    echo -e "${BLUE}Available Components in namespace '${NAMESPACE}':${NC}"
    echo ""

    local components=$(get_available_components)

    if [ -z "$components" ]; then
        echo -e "${YELLOW}No components found in namespace '${NAMESPACE}'${NC}"
        exit 1
    fi

    for comp in $components; do
        local pod_count=$(kubectl get pods -n "${NAMESPACE}" -l "app.kubernetes.io/component=${comp}" -o name 2>/dev/null | wc -l | tr -d ' ')
        if [ "$pod_count" -eq 0 ]; then
            pod_count=$(kubectl get pods -n "${NAMESPACE}" -l "app=${comp}" -o name 2>/dev/null | wc -l | tr -d ' ')
        fi
        echo -e "  ${GREEN}${comp}${NC} (${pod_count} pod(s))"
    done
    echo ""
    echo -e "Use with: ${CYAN}$(basename "$0") -c <component>${NC}"
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -c|--component)
            COMPONENT="$2"
            shift 2
            ;;
        --list-components)
            list_components
            ;;
        --cpu-threshold)
            HIGH_CPU_THRESHOLD="$2"
            shift 2
            ;;
        --mem-threshold)
            HIGH_MEM_THRESHOLD="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Get pods based on component filter
get_pods_selector() {
    if [ -n "$COMPONENT" ]; then
        local pods=$(kubectl get pods -n "${NAMESPACE}" -l "app.kubernetes.io/component=${COMPONENT}" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)
        if [ -z "$pods" ]; then
            pods=$(kubectl get pods -n "${NAMESPACE}" -l "app=${COMPONENT}" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)
        fi
        echo "$pods"
    else
        kubectl get pods -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null
    fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Resource Monitoring${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Namespace: ${GREEN}${NAMESPACE}${NC}"
echo -e "Timestamp (UTC): ${GREEN}$(date -u '+%Y-%m-%d %H:%M:%S')${NC}"
if [ -n "$COMPONENT" ]; then
    echo -e "Component: ${GREEN}${COMPONENT}${NC}"
fi
echo ""

# Initialize warning counters
WARNINGS=()

# 1. Cluster Node Resources
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}1. Cluster Node Resources${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}Nodes:${NC}"
kubectl get nodes -o custom-columns=\
NAME:.metadata.name,\
STATUS:.status.conditions[-1].type,\
CPU:.status.capacity.cpu,\
MEMORY:.status.capacity.memory 2>/dev/null

echo ""

# Check for node conditions (pressure)
echo -e "${BLUE}Node Conditions:${NC}"
NODE_PRESSURE=$(kubectl get nodes -o json 2>/dev/null | jq -r '.items[] | .metadata.name as $name | .status.conditions[] | select(.type != "Ready") | select(.status == "True") | "\($name): \(.type)"')
if [ -n "$NODE_PRESSURE" ]; then
    echo -e "${RED}⚠ Node pressure detected:${NC}"
    echo "$NODE_PRESSURE" | while read line; do
        echo -e "  ${RED}${line}${NC}"
        WARNINGS+=("Node pressure: $line")
    done
else
    echo -e "${GREEN}✓ No node pressure conditions${NC}"
fi

echo ""

# Node resource usage
echo -e "${BLUE}Node Resource Usage:${NC}"
if kubectl top nodes 2>/dev/null; then
    # Check for high node usage
    kubectl top nodes --no-headers 2>/dev/null | while read node cpu cpu_pct mem mem_pct; do
        cpu_val=${cpu_pct%\%}
        mem_val=${mem_pct%\%}
        if [ "$cpu_val" -ge "$HIGH_CPU_THRESHOLD" ] 2>/dev/null; then
            echo -e "${RED}  ⚠ Node $node CPU usage high: ${cpu_pct}${NC}"
        fi
        if [ "$mem_val" -ge "$HIGH_MEM_THRESHOLD" ] 2>/dev/null; then
            echo -e "${RED}  ⚠ Node $node Memory usage high: ${mem_pct}${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠ Metrics server not available${NC}"
fi

echo ""

# 2. Resource Pressure Indicators
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}2. Resource Pressure Indicators${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Get pods for analysis (filtered by component if specified)
if [ -n "$COMPONENT" ]; then
    PODS_JSON=$(kubectl get pods -n "${NAMESPACE}" -l "app.kubernetes.io/component=${COMPONENT}" -o json 2>/dev/null)
    POD_COUNT=$(echo "$PODS_JSON" | jq '.items | length' 2>/dev/null || echo "0")
    if [ "$POD_COUNT" -eq 0 ]; then
        PODS_JSON=$(kubectl get pods -n "${NAMESPACE}" -l "app=${COMPONENT}" -o json 2>/dev/null)
    fi
else
    PODS_JSON=$(kubectl get pods -n "${NAMESPACE}" -o json 2>/dev/null)
fi

# Pods with high restarts (indicates OOM or crashes)
echo -e "${BLUE}Pods with High Restarts (>3):${NC}"
HIGH_RESTART_PODS=$(echo "$PODS_JSON" | jq -r '.items[] | select(.status.containerStatuses != null) | select(.status.containerStatuses[].restartCount > 3) | "\(.metadata.name): \(.status.containerStatuses[0].restartCount) restarts"' 2>/dev/null)
if [ -n "$HIGH_RESTART_PODS" ]; then
    echo "$HIGH_RESTART_PODS" | while read line; do
        echo -e "  ${RED}${line}${NC}"
    done
    WARNINGS+=("Pods with high restarts detected")
else
    echo -e "  ${GREEN}✓ No pods with high restart counts${NC}"
fi

echo ""

# OOMKilled pods
echo -e "${BLUE}OOMKilled Containers:${NC}"
OOM_PODS=$(echo "$PODS_JSON" | jq -r '.items[] | select(.status.containerStatuses != null) | .metadata.name as $pod | .status.containerStatuses[] | select(.lastState.terminated.reason == "OOMKilled") | "\($pod): OOMKilled"' 2>/dev/null)
if [ -n "$OOM_PODS" ]; then
    echo "$OOM_PODS" | while read line; do
        echo -e "  ${RED}${line}${NC}"
    done
    WARNINGS+=("OOMKilled containers detected")
else
    echo -e "  ${GREEN}✓ No OOMKilled containers${NC}"
fi

echo ""

# Pods without resource limits
echo -e "${BLUE}Pods Without Resource Limits:${NC}"
NO_LIMITS=$(echo "$PODS_JSON" | jq -r '.items[] | select(.spec.containers[].resources.limits == null or .spec.containers[].resources.limits == {}) | .metadata.name' 2>/dev/null | sort -u)
if [ -n "$NO_LIMITS" ]; then
    NO_LIMITS_COUNT=$(echo "$NO_LIMITS" | wc -l | tr -d ' ')
    echo -e "  ${YELLOW}⚠ ${NO_LIMITS_COUNT} pod(s) without limits:${NC}"
    echo "$NO_LIMITS" | head -5 | while read pod; do
        echo -e "    ${YELLOW}${pod}${NC}"
    done
    if [ "$NO_LIMITS_COUNT" -gt 5 ]; then
        echo -e "    ${YELLOW}... and $((NO_LIMITS_COUNT - 5)) more${NC}"
    fi
    WARNINGS+=("$NO_LIMITS_COUNT pods without resource limits")
else
    echo -e "  ${GREEN}✓ All pods have resource limits${NC}"
fi

echo ""

# Pending pods
echo -e "${BLUE}Pending/Problem Pods:${NC}"
if [ -n "$COMPONENT" ]; then
    # Try app.kubernetes.io/component label first
    PROBLEM_PODS=$(kubectl get pods -n "${NAMESPACE}" -l "app.kubernetes.io/component=${COMPONENT}" --field-selector=status.phase!=Running,status.phase!=Succeeded -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,REASON:.status.reason --no-headers 2>/dev/null)
    if [ -z "$PROBLEM_PODS" ]; then
        # Try app label
        PROBLEM_PODS=$(kubectl get pods -n "${NAMESPACE}" -l "app=${COMPONENT}" --field-selector=status.phase!=Running,status.phase!=Succeeded -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,REASON:.status.reason --no-headers 2>/dev/null)
    fi
else
    PROBLEM_PODS=$(kubectl get pods -n "${NAMESPACE}" --field-selector=status.phase!=Running,status.phase!=Succeeded -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,REASON:.status.reason --no-headers 2>/dev/null)
fi
if [ -n "$PROBLEM_PODS" ]; then
    echo -e "${RED}$PROBLEM_PODS${NC}" | sed 's/^/  /'
    WARNINGS+=("Pending or problem pods detected")
else
    echo -e "  ${GREEN}✓ All pods running${NC}"
fi

echo ""

# 3. Pod Resource Usage vs Configured
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}3. Pod Resource Usage vs Configured${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

PODS_LIST=$(get_pods_selector)
METRICS_AVAILABLE=false

# Check if metrics server is available
if kubectl top pods -n "${NAMESPACE}" --no-headers 2>/dev/null | head -1 > /dev/null 2>&1; then
    METRICS_AVAILABLE=true
fi

if [ -n "$PODS_LIST" ]; then
    echo ""
    if [ "$METRICS_AVAILABLE" = true ]; then
        printf "%-40s %8s %8s %8s %8s %8s %8s\n" "POD" "CPU_USE" "CPU_REQ" "CPU_LIM" "MEM_USE" "MEM_REQ" "MEM_LIM"
        printf "%-40s %8s %8s %8s %8s %8s %8s\n" "---" "-------" "-------" "-------" "-------" "-------" "-------"
    else
        echo -e "${YELLOW}⚠ Metrics server not available - showing configured values only${NC}"
        echo -e "${YELLOW}  Enable with: minikube addons enable metrics-server${NC}"
        echo ""
        printf "%-40s %8s %8s %8s %8s\n" "POD" "CPU_REQ" "CPU_LIM" "MEM_REQ" "MEM_LIM"
        printf "%-40s %8s %8s %8s %8s\n" "---" "-------" "-------" "-------" "-------"
    fi

    for pod in $PODS_LIST; do
        # Get configured resources
        POD_JSON=$(kubectl get pod "$pod" -n "${NAMESPACE}" -o json 2>/dev/null)

        CPU_REQ=$(echo "$POD_JSON" | jq -r '.spec.containers[0].resources.requests.cpu // "-"' 2>/dev/null)
        CPU_LIM=$(echo "$POD_JSON" | jq -r '.spec.containers[0].resources.limits.cpu // "-"' 2>/dev/null)
        MEM_REQ=$(echo "$POD_JSON" | jq -r '.spec.containers[0].resources.requests.memory // "-"' 2>/dev/null)
        MEM_LIM=$(echo "$POD_JSON" | jq -r '.spec.containers[0].resources.limits.memory // "-"' 2>/dev/null)

        # Normalize empty to dash
        [ "$CPU_REQ" = "null" ] || [ -z "$CPU_REQ" ] && CPU_REQ="-"
        [ "$CPU_LIM" = "null" ] || [ -z "$CPU_LIM" ] && CPU_LIM="-"
        [ "$MEM_REQ" = "null" ] || [ -z "$MEM_REQ" ] && MEM_REQ="-"
        [ "$MEM_LIM" = "null" ] || [ -z "$MEM_LIM" ] && MEM_LIM="-"

        if [ "$METRICS_AVAILABLE" = true ]; then
            # Get current usage
            METRICS=$(kubectl top pod "$pod" -n "${NAMESPACE}" --no-headers 2>/dev/null || echo "")
            if [ -n "$METRICS" ]; then
                CPU_USE=$(echo "$METRICS" | awk '{print $2}')
                MEM_USE=$(echo "$METRICS" | awk '{print $3}')
            else
                CPU_USE="-"
                MEM_USE="-"
            fi

            # Color code based on usage vs limits
            CPU_USE_VAL=$(echo "$CPU_USE" | sed 's/m$//' | grep -E '^[0-9]+$' || echo "0")
            CPU_LIM_VAL=$(echo "$CPU_LIM" | sed 's/m$//' | grep -E '^[0-9]+$' || echo "0")

            if [ "$CPU_LIM_VAL" -gt 0 ] 2>/dev/null; then
                CPU_PCT=$(awk "BEGIN {printf \"%.0f\", ($CPU_USE_VAL/$CPU_LIM_VAL)*100}")
                if [ "$CPU_PCT" -ge "$HIGH_CPU_THRESHOLD" ] 2>/dev/null; then
                    printf "${RED}%-40s %8s %8s %8s %8s %8s %8s${NC}\n" "$pod" "$CPU_USE" "$CPU_REQ" "$CPU_LIM" "$MEM_USE" "$MEM_REQ" "$MEM_LIM"
                    continue
                fi
            fi

            # Check if no limits defined (warning)
            if [ "$CPU_LIM" = "-" ] || [ "$MEM_LIM" = "-" ]; then
                printf "${YELLOW}%-40s %8s %8s %8s %8s %8s %8s${NC}\n" "$pod" "$CPU_USE" "$CPU_REQ" "$CPU_LIM" "$MEM_USE" "$MEM_REQ" "$MEM_LIM"
            else
                printf "%-40s %8s %8s %8s %8s %8s %8s\n" "$pod" "$CPU_USE" "$CPU_REQ" "$CPU_LIM" "$MEM_USE" "$MEM_REQ" "$MEM_LIM"
            fi
        else
            # No metrics - just show configured
            if [ "$CPU_LIM" = "-" ] || [ "$MEM_LIM" = "-" ]; then
                printf "${YELLOW}%-40s %8s %8s %8s %8s${NC}\n" "$pod" "$CPU_REQ" "$CPU_LIM" "$MEM_REQ" "$MEM_LIM"
            else
                printf "%-40s %8s %8s %8s %8s\n" "$pod" "$CPU_REQ" "$CPU_LIM" "$MEM_REQ" "$MEM_LIM"
            fi
        fi
    done

    echo ""
    echo -e "${BLUE}Legend:${NC} ${YELLOW}Yellow = no limits defined${NC}, ${RED}Red = high usage (>${HIGH_CPU_THRESHOLD}%)${NC}"
else
    echo -e "${YELLOW}No pods found${NC}"
fi

echo ""

# 4. Per-Component Resource Breakdown
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}4. Per-Component Resource Breakdown${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# If component filter is set, only show that component
if [ -n "$COMPONENT" ]; then
    COMPONENTS="$COMPONENT"
else
    COMPONENTS=$(get_available_components)
fi

if [ -n "$COMPONENTS" ]; then
    printf "%-20s %6s %12s %12s %12s %12s\n" "COMPONENT" "PODS" "CPU_REQ" "CPU_LIM" "MEM_REQ" "MEM_LIM"
    printf "%-20s %6s %12s %12s %12s %12s\n" "---------" "----" "-------" "-------" "-------" "-------"

    TOTAL_CPU_REQ=0
    TOTAL_CPU_LIM=0
    TOTAL_MEM_REQ=0
    TOTAL_MEM_LIM=0

    for comp in $COMPONENTS; do
        # Get pods for this component
        COMP_PODS=$(kubectl get pods -n "${NAMESPACE}" -l "app.kubernetes.io/component=${comp}" -o json 2>/dev/null)
        POD_COUNT=$(echo "$COMP_PODS" | jq '.items | length' 2>/dev/null || echo "0")

        if [ "$POD_COUNT" -eq 0 ]; then
            COMP_PODS=$(kubectl get pods -n "${NAMESPACE}" -l "app=${comp}" -o json 2>/dev/null)
            POD_COUNT=$(echo "$COMP_PODS" | jq '.items | length' 2>/dev/null || echo "0")
        fi

        if [ "$POD_COUNT" -gt 0 ]; then
            # Calculate resources
            CPU_REQ=$(echo "$COMP_PODS" | jq -r '[.items[].spec.containers[].resources.requests.cpu // "0" | gsub("m$"; "") | tonumber] | add' 2>/dev/null || echo "0")
            CPU_LIM=$(echo "$COMP_PODS" | jq -r '[.items[].spec.containers[].resources.limits.cpu // "0" | gsub("m$"; "") | tonumber] | add' 2>/dev/null || echo "0")

            MEM_REQ=$(echo "$COMP_PODS" | jq -r '[.items[].spec.containers[].resources.requests.memory // "0" | if test("Gi$") then (gsub("Gi$"; "") | tonumber * 1024) elif test("Mi$") then (gsub("Mi$"; "") | tonumber) else 0 end] | add' 2>/dev/null || echo "0")
            MEM_LIM=$(echo "$COMP_PODS" | jq -r '[.items[].spec.containers[].resources.limits.memory // "0" | if test("Gi$") then (gsub("Gi$"; "") | tonumber * 1024) elif test("Mi$") then (gsub("Mi$"; "") | tonumber) else 0 end] | add' 2>/dev/null || echo "0")

            # Handle null/empty values
            CPU_REQ=${CPU_REQ:-0}
            CPU_LIM=${CPU_LIM:-0}
            MEM_REQ=${MEM_REQ:-0}
            MEM_LIM=${MEM_LIM:-0}

            TOTAL_CPU_REQ=$((TOTAL_CPU_REQ + ${CPU_REQ%.*}))
            TOTAL_CPU_LIM=$((TOTAL_CPU_LIM + ${CPU_LIM%.*}))
            TOTAL_MEM_REQ=$((TOTAL_MEM_REQ + ${MEM_REQ%.*}))
            TOTAL_MEM_LIM=$((TOTAL_MEM_LIM + ${MEM_LIM%.*}))

            printf "%-20s %6s %10sm %10sm %10sMi %10sMi\n" "$comp" "$POD_COUNT" "${CPU_REQ%.*}" "${CPU_LIM%.*}" "${MEM_REQ%.*}" "${MEM_LIM%.*}"
        fi
    done

    echo ""
    printf "${BLUE}%-20s %6s %10sm %10sm %10sMi %10sMi${NC}\n" "TOTAL" "-" "$TOTAL_CPU_REQ" "$TOTAL_CPU_LIM" "$TOTAL_MEM_REQ" "$TOTAL_MEM_LIM"
fi

echo ""

# 5. Storage Usage (only show when no component filter, as PVCs are not component-specific)
if [ -z "$COMPONENT" ]; then
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}5. Storage Usage${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    PVC_COUNT=$(kubectl get pvc -n "${NAMESPACE}" --no-headers 2>/dev/null | wc -l | tr -d ' ')
    echo -e "Persistent Volume Claims: ${GREEN}${PVC_COUNT}${NC}"

    if [ "$PVC_COUNT" -gt 0 ]; then
        echo ""
        kubectl get pvc -n "${NAMESPACE}" -o custom-columns=\
NAME:.metadata.name,\
STATUS:.status.phase,\
CAPACITY:.status.capacity.storage,\
STORAGECLASS:.spec.storageClassName 2>/dev/null
    fi

    echo ""
fi

# 6. Summary & Warnings
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ -n "$COMPONENT" ]; then
    echo -e "${CYAN}5. Summary & Warnings (${COMPONENT})${NC}"
else
    echo -e "${CYAN}6. Summary & Warnings${NC}"
fi
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Show cluster capacity only when no component filter
if [ -z "$COMPONENT" ]; then
    # Get cluster capacity
    TOTAL_CPU=$(kubectl get nodes -o json | jq '[.items[].status.capacity.cpu | tonumber] | add')
    TOTAL_MEM_KB=$(kubectl get nodes -o json | jq '[.items[].status.capacity.memory | gsub("Ki"; "") | tonumber] | add')
    TOTAL_MEM_MI=$((TOTAL_MEM_KB / 1024))

    echo -e "${BLUE}Cluster Capacity:${NC}"
    echo -e "  Total CPU: ${GREEN}${TOTAL_CPU}${NC} cores (${TOTAL_CPU}000m)"
    echo -e "  Total Memory: ${GREEN}$((TOTAL_MEM_MI / 1024))${NC} GB (${TOTAL_MEM_MI}Mi)"
    echo ""

    # Calculate usage percentages
    if [ -n "$TOTAL_CPU_REQ" ] && [ "$TOTAL_CPU" -gt 0 ]; then
        CPU_USAGE_PCT=$(awk "BEGIN {printf \"%.1f\", ($TOTAL_CPU_REQ/($TOTAL_CPU*1000))*100}")
        MEM_USAGE_PCT=$(awk "BEGIN {printf \"%.1f\", ($TOTAL_MEM_REQ/$TOTAL_MEM_MI)*100}")

        echo -e "${BLUE}Namespace Resource Usage:${NC}"

        # CPU usage with color
        if (( $(echo "$CPU_USAGE_PCT > $HIGH_CPU_THRESHOLD" | bc -l) )); then
            echo -e "  CPU Requested: ${RED}${TOTAL_CPU_REQ}m / $((TOTAL_CPU*1000))m (${CPU_USAGE_PCT}%)${NC} ${RED}⚠ HIGH${NC}"
            WARNINGS+=("CPU requests at ${CPU_USAGE_PCT}% of cluster capacity")
        elif (( $(echo "$CPU_USAGE_PCT > 60" | bc -l) )); then
            echo -e "  CPU Requested: ${YELLOW}${TOTAL_CPU_REQ}m / $((TOTAL_CPU*1000))m (${CPU_USAGE_PCT}%)${NC}"
        else
            echo -e "  CPU Requested: ${GREEN}${TOTAL_CPU_REQ}m / $((TOTAL_CPU*1000))m (${CPU_USAGE_PCT}%)${NC}"
        fi

        # Memory usage with color
        if (( $(echo "$MEM_USAGE_PCT > $HIGH_MEM_THRESHOLD" | bc -l) )); then
            echo -e "  Memory Requested: ${RED}${TOTAL_MEM_REQ}Mi / ${TOTAL_MEM_MI}Mi (${MEM_USAGE_PCT}%)${NC} ${RED}⚠ HIGH${NC}"
            WARNINGS+=("Memory requests at ${MEM_USAGE_PCT}% of cluster capacity")
        elif (( $(echo "$MEM_USAGE_PCT > 60" | bc -l) )); then
            echo -e "  Memory Requested: ${YELLOW}${TOTAL_MEM_REQ}Mi / ${TOTAL_MEM_MI}Mi (${MEM_USAGE_PCT}%)${NC}"
        else
            echo -e "  Memory Requested: ${GREEN}${TOTAL_MEM_REQ}Mi / ${TOTAL_MEM_MI}Mi (${MEM_USAGE_PCT}%)${NC}"
        fi
    fi
else
    # Component-specific summary
    echo -e "${BLUE}Component: ${COMPONENT}${NC}"
    echo -e "  CPU Requested: ${GREEN}${TOTAL_CPU_REQ}m${NC}"
    echo -e "  CPU Limit: ${GREEN}${TOTAL_CPU_LIM}m${NC}"
    echo -e "  Memory Requested: ${GREEN}${TOTAL_MEM_REQ}Mi${NC}"
    echo -e "  Memory Limit: ${GREEN}${TOTAL_MEM_LIM}Mi${NC}"
fi

echo ""

# Print all warnings
if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}⚠ WARNINGS (${#WARNINGS[@]})${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    for warning in "${WARNINGS[@]}"; do
        echo -e "  ${YELLOW}• ${warning}${NC}"
    done
    echo ""
    echo -e "${RED}✗ Resource pressure detected - review above${NC}"
    exit 1
else
    echo -e "${GREEN}✓ No resource pressure warnings${NC}"
    exit 0
fi
