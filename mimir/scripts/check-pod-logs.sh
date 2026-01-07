#!/bin/bash

#############################################
# Pod Logs Checker
# Retrieves logs from all pods in namespace
#############################################

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
NAMESPACE="${NAMESPACE:-mimir-test}"
LINES="${LINES:-50}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Checking Pod Logs (${LINES} lines each)${NC}"
echo -e "${BLUE}Namespace: ${NAMESPACE}${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Get all pods
PODS=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')

if [[ -z "$PODS" ]]; then
    echo -e "${YELLOW}No pods found in namespace ${NAMESPACE}${NC}"
    exit 1
fi

# Loop through each pod
for POD in $PODS; do
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Pod: ${POD}${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    kubectl logs -n "$NAMESPACE" "$POD" --tail="$LINES" 2>&1

    echo -e "\n${BLUE}--- End of ${POD} logs ---${NC}\n"
done

echo -e "\n${GREEN}✓ Log collection complete${NC}"
