#!/bin/bash

# Loki Logs Analysis Script
# Checks Loki pods for errors, warnings, and displays full logs

set -euo pipefail

# Default configuration
NAMESPACE="loki"
TAIL_LINES="200"
SINCE_TIME=""
SHOW_ERRORS=true
SHOW_WARNINGS=true
SHOW_FULL_LOGS=false
SHOW_SAMPLE_LINES=5
COMPONENT=""
POD_NAME=""
ANY_POD=false
LIST_PODS=false

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to get available components from cluster
get_available_components() {
    # Get components from app.kubernetes.io/component label
    local k8s_components=$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.labels.app\.kubernetes\.io/component}' 2>/dev/null | tr ' ' '\n' | sort -u | grep -v '^$' || echo "")

    # Get components from app label (for subcharts like minio)
    local app_components=$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.labels.app}' 2>/dev/null | tr ' ' '\n' | sort -u | grep -v '^$' | grep -v '^loki$' || echo "")

    # Combine and deduplicate
    echo -e "${k8s_components}\n${app_components}" | sort -u | grep -v '^$'
}

# Usage function
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Analyze Loki pod logs for errors, warnings, or view full logs.

OPTIONS:
    -n, --namespace NAME     Kubernetes namespace (default: loki)
    -l, --lines NUMBER       Number of log lines to check (default: 200)
    -t, --time DURATION      Only show logs newer than duration (e.g., 5m, 1h, 30s)
    -s, --sample NUMBER      Number of sample error/warning lines to show (default: 5)
    -c, --component NAME     Filter by component (e.g., ingester, distributor, querier)
    -p, --pod NAME           Show logs for specific pod name
    -a, --any                Show logs from any single pod of the component (use with -c)
    -f, --full               Show full logs (no error/warning filtering)
    -e, --errors-only        Show only errors, skip warnings
    -w, --warnings-only      Show only warnings, skip errors
    --list-components        List available Loki components
    --list-pods              List pods for a component (use with -c)
    -h, --help               Display this help message

COMPONENTS:
    ingester, distributor, querier, query-frontend, query-scheduler,
    compactor, index-gateway, gateway, ruler, canary, minio,
    chunks-cache, results-cache

EXAMPLES:
    $(basename "$0")                                    # Analyze all pods (errors/warnings)
    $(basename "$0") -f                                 # Full logs from all pods
    $(basename "$0") -c ingester                        # All ingester pods
    $(basename "$0") -c ingester -a                     # Any single ingester pod
    $(basename "$0") -c ingester --list-pods            # List all ingester pods
    $(basename "$0") -c distributor -f                  # Full logs from all distributors
    $(basename "$0") -c querier -t 5m -e                # Querier errors from last 5 min
    $(basename "$0") -p loki-ingester-0                 # Specific pod
    $(basename "$0") -p loki-ingester-0 -f              # Full logs from specific pod
    $(basename "$0") -t 10m                             # All pods, last 10 minutes
    $(basename "$0") -t 1h -e                           # Errors from last hour
    $(basename "$0") --list-components                  # Show available components

EOF
    exit 0
}

# List components function
list_components() {
    echo -e "${BLUE}Available Loki Components in namespace '${NAMESPACE}':${NC}"
    echo ""

    local components=$(get_available_components)

    if [ -z "$components" ]; then
        echo -e "${YELLOW}No components found. Is Loki deployed in namespace '${NAMESPACE}'?${NC}"
        exit 1
    fi

    for comp in $components; do
        # Try app.kubernetes.io/component label first
        local pod_count=$(kubectl get pods -n "${NAMESPACE}" -l "app.kubernetes.io/component=${comp}" -o name 2>/dev/null | wc -l | tr -d ' ')

        # If no pods found, try app label
        if [ "$pod_count" -eq 0 ]; then
            pod_count=$(kubectl get pods -n "${NAMESPACE}" -l "app=${comp}" -o name 2>/dev/null | wc -l | tr -d ' ')
        fi

        echo -e "  ${GREEN}${comp}${NC} (${pod_count} pod(s))"
    done
    echo ""
    echo -e "Use with: ${CYAN}$(basename "$0") -c <component>${NC}"
    exit 0
}

# List pods for a component
list_pods_for_component() {
    local component=$1

    if [ -z "$component" ]; then
        echo -e "${RED}Error: --list-pods requires -c <component>${NC}"
        echo -e "Example: $(basename "$0") -c ingester --list-pods"
        exit 1
    fi

    echo -e "${BLUE}Pods for component '${component}' in namespace '${NAMESPACE}':${NC}"
    echo ""

    # Try app.kubernetes.io/component label first
    local pods=$(kubectl get pods -n "${NAMESPACE}" -l "app.kubernetes.io/component=${component}" \
        -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp,NODE:.spec.nodeName' \
        2>/dev/null)

    # If no pods found, try app label
    if [ $(echo "$pods" | wc -l) -le 1 ]; then
        pods=$(kubectl get pods -n "${NAMESPACE}" -l "app=${component}" \
            -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp,NODE:.spec.nodeName' \
            2>/dev/null)
    fi

    if [ -z "$pods" ] || [ $(echo "$pods" | wc -l) -le 1 ]; then
        echo -e "${YELLOW}No pods found for component '${component}'${NC}"
        echo ""
        echo -e "Available components:"
        local available=$(get_available_components)
        for comp in $available; do
            echo -e "  ${comp}"
        done
        exit 1
    fi

    echo "$pods"
    echo ""
    echo -e "Use with: ${CYAN}$(basename "$0") -p <pod-name>${NC}"
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -l|--lines)
            TAIL_LINES="$2"
            shift 2
            ;;
        -t|--time)
            SINCE_TIME="$2"
            shift 2
            ;;
        -s|--sample)
            SHOW_SAMPLE_LINES="$2"
            shift 2
            ;;
        -c|--component)
            COMPONENT="$2"
            shift 2
            ;;
        -p|--pod)
            POD_NAME="$2"
            shift 2
            ;;
        -a|--any)
            ANY_POD=true
            shift
            ;;
        -f|--full)
            SHOW_FULL_LOGS=true
            SHOW_ERRORS=false
            SHOW_WARNINGS=false
            shift
            ;;
        -e|--errors-only)
            SHOW_WARNINGS=false
            shift
            ;;
        -w|--warnings-only)
            SHOW_ERRORS=false
            shift
            ;;
        --list-components)
            list_components
            ;;
        --list-pods)
            LIST_PODS=true
            shift
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

# Build kubectl logs options
KUBECTL_LOG_OPTS=""
if [ -n "$SINCE_TIME" ]; then
    KUBECTL_LOG_OPTS="--since=${SINCE_TIME}"
else
    KUBECTL_LOG_OPTS="--tail=${TAIL_LINES}"
fi

# Error patterns to search for
ERROR_PATTERNS=(
    "error"
    "Error"
    "ERROR"
    "fatal"
    "Fatal"
    "FATAL"
    "panic"
    "Panic"
    "PANIC"
    "failed"
    "Failed"
    "FAILED"
)

# Warning patterns
WARNING_PATTERNS=(
    "warn"
    "Warn"
    "WARN"
    "warning"
    "Warning"
    "WARNING"
)

# Print header
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Loki Logs Analysis${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Namespace: ${GREEN}${NAMESPACE}${NC}"
    if [ -n "$SINCE_TIME" ]; then
        echo -e "Time Range: ${GREEN}last ${SINCE_TIME}${NC}"
    else
        echo -e "Tail Lines: ${GREEN}${TAIL_LINES}${NC}"
    fi
    if [ -n "$COMPONENT" ]; then
        echo -e "Component: ${GREEN}${COMPONENT}${NC}"
    fi
    if [ -n "$POD_NAME" ]; then
        echo -e "Pod: ${GREEN}${POD_NAME}${NC}"
    fi
    if [ "$SHOW_FULL_LOGS" = true ]; then
        echo -e "Mode: ${CYAN}Full Logs${NC}"
    elif [ "$SHOW_ERRORS" = true ] && [ "$SHOW_WARNINGS" = false ]; then
        echo -e "Mode: ${RED}Errors Only${NC}"
    elif [ "$SHOW_ERRORS" = false ] && [ "$SHOW_WARNINGS" = true ]; then
        echo -e "Mode: ${YELLOW}Warnings Only${NC}"
    else
        echo -e "Mode: ${CYAN}Errors & Warnings${NC}"
    fi
    echo ""
}

# Get pods based on filters
get_pods() {
    local pods=""

    if [ -n "$POD_NAME" ]; then
        # Specific pod
        pods="$POD_NAME"
    elif [ -n "$COMPONENT" ]; then
        # Try app.kubernetes.io/component label first
        pods=$(kubectl get pods -n "${NAMESPACE}" \
            -l "app.kubernetes.io/component=${COMPONENT}" \
            -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")

        # If no pods found, try app label (for subcharts like minio)
        if [ -z "$pods" ]; then
            pods=$(kubectl get pods -n "${NAMESPACE}" \
                -l "app=${COMPONENT}" \
                -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
        fi

        # If still no pods, try name pattern as fallback
        if [ -z "$pods" ]; then
            pods=$(kubectl get pods -n "${NAMESPACE}" \
                -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | tr ' ' '\n' | grep -E "loki-${COMPONENT}" || echo "")
        fi
    else
        # All pods
        pods=$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    fi

    echo "$pods"
}

# Function to check logs for patterns
check_pod_logs() {
    local pod=$1
    local pattern_type=$2
    shift 2
    local patterns=("$@")

    local found=0

    for pattern in "${patterns[@]}"; do
        local matches=$(kubectl logs "$pod" -n "${NAMESPACE}" ${KUBECTL_LOG_OPTS} 2>/dev/null | grep -i "$pattern" | wc -l | tr -d ' ')
        if [ "$matches" -gt 0 ]; then
            found=$((found + matches))
        fi
    done

    echo "$found"
}

# Show full logs for a pod
show_full_logs() {
    local pod=$1

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Pod: ${GREEN}${pod}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Check pod status
    POD_STATUS=$(kubectl get pod "$pod" -n "${NAMESPACE}" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    RESTART_COUNT=$(kubectl get pod "$pod" -n "${NAMESPACE}" -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null || echo "0")

    echo -e "Status: ${GREEN}${POD_STATUS}${NC} | Restarts: ${YELLOW}${RESTART_COUNT}${NC}"
    echo ""

    kubectl logs "$pod" -n "${NAMESPACE}" ${KUBECTL_LOG_OPTS} 2>/dev/null || echo -e "${RED}Failed to get logs${NC}"
    echo ""
}

# Analyze logs for a pod (errors/warnings) - categorized by actual log level
analyze_pod_logs() {
    local pod=$1

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Pod: ${GREEN}${pod}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Check pod status
    POD_STATUS=$(kubectl get pod "$pod" -n "${NAMESPACE}" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    RESTART_COUNT=$(kubectl get pod "$pod" -n "${NAMESPACE}" -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null || echo "0")

    echo -e "Status: ${GREEN}${POD_STATUS}${NC} | Restarts: ${YELLOW}${RESTART_COUNT}${NC}"

    # Get logs once and categorize by actual log level
    local logs=$(kubectl logs "$pod" -n "${NAMESPACE}" ${KUBECTL_LOG_OPTS} 2>/dev/null)

    # Count by actual log level (level=error, level=fatal, level=panic)
    local error_count=0
    local warning_count=0

    if [ "$SHOW_ERRORS" = true ]; then
        # Match actual error level in structured logs
        error_count=$(echo "$logs" | grep -cE 'level=(error|fatal|panic|ERROR|FATAL|PANIC)' 2>/dev/null || true)
        error_count=$((error_count + 0))  # Ensure integer
    fi

    if [ "$SHOW_WARNINGS" = true ]; then
        # Match actual warning level in structured logs
        warning_count=$(echo "$logs" | grep -cE 'level=(warn|warning|WARN|WARNING)' 2>/dev/null || true)
        warning_count=$((warning_count + 0))  # Ensure integer
    fi

    if [ "$error_count" -gt 0 ] && [ "$SHOW_ERRORS" = true ]; then
        echo -e "${RED}✗ Errors found: ${error_count}${NC}"
        TOTAL_ERRORS=$((TOTAL_ERRORS + error_count))
        PODS_WITH_ERRORS=$((PODS_WITH_ERRORS + 1))

        echo -e "${RED}Recent error lines (level=error/fatal/panic):${NC}"
        echo "$logs" | grep -E 'level=(error|fatal|panic|ERROR|FATAL|PANIC)' | tail -"${SHOW_SAMPLE_LINES}" | sed 's/^/  /'
    elif [ "$SHOW_ERRORS" = true ]; then
        echo -e "${GREEN}✓ No errors found${NC}"
    fi

    if [ "$warning_count" -gt 0 ] && [ "$SHOW_WARNINGS" = true ]; then
        echo -e "${YELLOW}⚠ Warnings found: ${warning_count}${NC}"
        TOTAL_WARNINGS=$((TOTAL_WARNINGS + warning_count))
        PODS_WITH_WARNINGS=$((PODS_WITH_WARNINGS + 1))

        echo -e "${YELLOW}Recent warning lines (level=warn):${NC}"
        echo "$logs" | grep -E 'level=(warn|warning|WARN|WARNING)' | tail -"${SHOW_SAMPLE_LINES}" | sed 's/^/  /'
    elif [ "$SHOW_WARNINGS" = true ]; then
        echo -e "${GREEN}✓ No warnings found${NC}"
    fi

    echo ""
}

# Main execution

# Handle --list-pods early (needs COMPONENT to be set)
if [ "$LIST_PODS" = true ]; then
    list_pods_for_component "$COMPONENT"
fi

print_header

echo -e "${BLUE}Fetching Loki pods...${NC}"
PODS=$(get_pods)

if [ -z "$PODS" ]; then
    if [ -n "$COMPONENT" ]; then
        echo -e "${RED}✗ No pods found for component '${COMPONENT}' in namespace '${NAMESPACE}'${NC}"
        echo -e "${YELLOW}Available components:${NC}"
        local available=$(get_available_components)
        if [ -n "$available" ]; then
            for comp in $available; do
                echo -e "  ${comp}"
            done
        else
            echo -e "  (none found)"
        fi
    elif [ -n "$POD_NAME" ]; then
        echo -e "${RED}✗ Pod '${POD_NAME}' not found in namespace '${NAMESPACE}'${NC}"
    else
        echo -e "${RED}✗ No pods found in namespace '${NAMESPACE}'${NC}"
    fi
    exit 1
fi

# Convert to array
POD_ARRAY=($PODS)
POD_COUNT=${#POD_ARRAY[@]}

# If --any flag is set, pick first pod only
if [ "$ANY_POD" = true ] && [ "$POD_COUNT" -gt 1 ]; then
    PODS="${POD_ARRAY[0]}"
    POD_COUNT=1
    echo -e "${GREEN}✓ Selected 1 pod (--any mode)${NC}"
else
    echo -e "${GREEN}✓ Found ${POD_COUNT} pod(s)${NC}"
fi
echo ""

# Initialize counters
TOTAL_ERRORS=0
TOTAL_WARNINGS=0
PODS_WITH_ERRORS=0
PODS_WITH_WARNINGS=0

# Process pods
for pod in $PODS; do
    if [ "$SHOW_FULL_LOGS" = true ]; then
        show_full_logs "$pod"
    else
        analyze_pod_logs "$pod"
    fi
done

# Summary (only for analysis mode)
if [ "$SHOW_FULL_LOGS" = false ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Timestamp (UTC): ${GREEN}$(date -u '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "Total Pods: ${GREEN}${POD_COUNT}${NC}"
    if [ "$SHOW_ERRORS" = true ]; then
        echo -e "Pods with Errors: ${RED}${PODS_WITH_ERRORS}${NC}"
        echo -e "Total Errors: ${RED}${TOTAL_ERRORS}${NC}"
    fi
    if [ "$SHOW_WARNINGS" = true ]; then
        echo -e "Pods with Warnings: ${YELLOW}${PODS_WITH_WARNINGS}${NC}"
        echo -e "Total Warnings: ${YELLOW}${TOTAL_WARNINGS}${NC}"
    fi
    echo ""

    # Exit code based on findings
    if [ "$TOTAL_ERRORS" -gt 0 ]; then
        echo -e "${RED}✗ Issues detected - review logs above${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ All pods healthy${NC}"
        exit 0
    fi
fi
