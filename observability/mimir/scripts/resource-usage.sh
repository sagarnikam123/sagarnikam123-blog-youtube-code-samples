#!/bin/bash

# Resource Usage vs Allocated Script
# Shows actual resource usage compared to requests/limits for pods in a namespace
# Flow: Cluster-Level → Namespace-Level → Pod-Level

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Cleanup temp files on exit
trap 'rm -f /tmp/pod_res_*.tmp 2>/dev/null' EXIT

# Check prerequisites
if ! command -v kubectl &>/dev/null; then
    echo -e "${RED}Error: kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

if ! command -v jq &>/dev/null; then
    echo -e "${RED}Error: jq not found. Install with: brew install jq (macOS) or apt-get install jq (Linux)${NC}"
    exit 1
fi

# Check cluster connectivity
if ! kubectl cluster-info &>/dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster. Check your kubeconfig.${NC}"
    exit 1
fi

# Default namespace
NAMESPACE="${1:-mimir-test}"

echo -e "${CYAN}=== RESOURCE USAGE ANALYSIS ===${NC}"
echo -e "Namespace: ${YELLOW}${NAMESPACE}${NC}"
echo ""

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo -e "${RED}Error: Namespace '$NAMESPACE' not found${NC}"
    echo -e "${YELLOW}Available namespaces:${NC}"
    kubectl get namespaces --no-headers 2>/dev/null | awk '{print "  - " $1}'
    exit 1
fi

# Check if namespace has any pods
POD_COUNT=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [ "$POD_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: Namespace '$NAMESPACE' has no pods${NC}"
    echo -e "${YELLOW}Nothing to analyze. Exiting.${NC}"
    exit 0
fi

# Check if metrics-server is available
echo -e "${CYAN}Checking metrics-server availability...${NC}"
METRICS_AVAILABLE=true
if ! kubectl top nodes &>/dev/null; then
    METRICS_AVAILABLE=false
    echo -e "${RED}❌ metrics-server is NOT available or disabled${NC}"
    echo -e "${YELLOW}⚠️  Will show allocation info only (no actual usage data)${NC}"
    echo -e "${YELLOW}To enable full metrics, install with:${NC}"
    echo -e "  kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
    echo -e "${YELLOW}For Minikube:${NC}"
    echo -e "  minikube addons enable metrics-server"
    echo -e "${YELLOW}⏱️  Note: After enabling, wait 30-60 seconds for metrics collection to start${NC}"
else
    echo -e "${GREEN}✅ metrics-server is available${NC}"
fi
echo ""

#############################################
# CLUSTER-LEVEL OVERVIEW
#############################################

# Node CPU & Memory Resources
if [ "$METRICS_AVAILABLE" = true ]; then
  echo -e "${BLUE}=== CLUSTER: NODE RESOURCES (CPU & Memory) ===${NC}"
  printf "%-15s %12s %15s %15s %15s %15s %15s\n" "Node" "CPU Usage" "CPU Requested" "CPU Util" "Mem Usage" "Mem Requested" "Mem Util"
  printf "%-15s %12s %15s %15s %15s %15s %15s\n" "----" "---------" "-------------" "--------" "---------" "-------------" "--------"

  kubectl top nodes --no-headers 2>/dev/null | while read node cpu cpu_pct mem mem_pct; do
    alloc=$(kubectl describe node "$node" 2>/dev/null | awk '
      /cpu.*[0-9]+m.*\([0-9]+%\)/ {cpu_line=$0}
      /memory.*[0-9]+Mi.*\([0-9]+%\)/ {mem_line=$0}
      END {
        split(cpu_line, cpu_parts, " ");
        split(mem_line, mem_parts, " ");
        printf "%s %s", cpu_parts[2], mem_parts[2]
      }')
    cpu_req=$(echo $alloc | awk '{print $1}')
    mem_req=$(echo $alloc | awk '{print $2}')

    cpu_usage_num=$(echo $cpu | sed 's/m//')
    cpu_req_num=$(echo $cpu_req | sed 's/[^0-9]//g')
    mem_usage_num=$(echo $mem | sed 's/Mi//')
    mem_req_num=$(echo $mem_req | sed 's/[^0-9]//g')

    # Set defaults if empty
    cpu_req_num=${cpu_req_num:-0}
    mem_req_num=${mem_req_num:-0}

    if [ "$cpu_req_num" -gt 0 ]; then
      cpu_util=$(awk "BEGIN {printf \"%.1f\", ($cpu_usage_num / $cpu_req_num) * 100}")
    else
      cpu_util="0.0"
    fi

    if [ "$mem_req_num" -gt 0 ]; then
      mem_util=$(awk "BEGIN {printf \"%.1f\", ($mem_usage_num / $mem_req_num) * 100}")
    else
      mem_util="0.0"
    fi

    printf "%-15s %12s %15s %14s%% %15s %15s %14s%%\n" "$node" "$cpu" "$cpu_req" "$cpu_util" "$mem" "$mem_req" "$mem_util"
  done
else
  echo -e "${BLUE}=== CLUSTER: NODE ALLOCATION (metrics-server disabled) ===${NC}"
  kubectl get nodes -o json | jq -r '.items[] | "\(.metadata.name) \(.status.allocatable.cpu) \(.status.allocatable.memory)"' | while read node cpu mem; do
    echo -e "${YELLOW}Node: $node${NC}"
    echo "  Allocatable CPU: $cpu"
    echo "  Allocatable Memory: $mem"
  done
fi
echo ""

# Cluster Storage Overview
echo -e "${BLUE}=== CLUSTER: STORAGE OVERVIEW ===${NC}"
TOTAL_PV=$(kubectl get pv --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [ "$TOTAL_PV" -eq 0 ]; then
    echo -e "${YELLOW}No PVs found in cluster${NC}"
else
    echo -e "Total PVs: ${TOTAL_PV}"
    echo ""

    # PV summary by status
    echo "PV Status Summary:"
    kubectl get pv --no-headers 2>/dev/null | awk '{print $5}' | sort | uniq -c | while read count status; do
        if [ "$status" = "Bound" ]; then
            echo -e "  ${GREEN}$status: $count${NC}"
        elif [ "$status" = "Available" ]; then
            echo -e "  ${YELLOW}$status: $count${NC}"
        else
            echo -e "  ${RED}$status: $count${NC}"
        fi
    done
    echo ""

    # Total storage capacity
    TOTAL_CAPACITY=$(kubectl get pv -o json 2>/dev/null | jq -r '[.items[].spec.capacity.storage // "0Gi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber) elif endswith("Mi") then (rtrimstr("Mi") | tonumber / 1024) elif endswith("Ti") then (rtrimstr("Ti") | tonumber * 1024) else tonumber end) | add')
    echo -e "Total Cluster Storage Capacity: ${YELLOW}${TOTAL_CAPACITY}Gi${NC}"
fi
echo ""

# Node Storage Capacity
echo -e "${BLUE}=== CLUSTER: NODE STORAGE CAPACITY ===${NC}"
printf "%-15s %15s %15s %15s\n" "Node" "Capacity" "Allocatable" "Ephemeral"
printf "%-15s %15s %15s %15s\n" "----" "--------" "-----------" "---------"
kubectl get nodes -o json 2>/dev/null | jq -r '.items[] | "\(.metadata.name) \(.status.capacity."ephemeral-storage" // "0") \(.status.allocatable."ephemeral-storage" // "0")"' | while read node capacity allocatable; do
    # Convert to Gi for readability
    cap_gi=$(echo $capacity | sed 's/Ki$//' | awk '{printf "%.1f", $1/1024/1024}')
    alloc_gi=$(echo $allocatable | sed 's/Ki$//' | awk '{printf "%.1f", $1/1024/1024}')
    ephemeral_gi=$(awk "BEGIN {printf \"%.1f\", $cap_gi - $alloc_gi}")
    printf "%-15s %14sGi %14sGi %14sGi\n" "$node" "$cap_gi" "$alloc_gi" "$ephemeral_gi"
done
echo ""

#############################################
# NAMESPACE-LEVEL DETAILS
#############################################

# Calculate total requests and limits
echo -e "${BLUE}=== NAMESPACE: RESOURCE ALLOCATION (${NAMESPACE}) ===${NC}"
REQUESTS=$(kubectl get pods -n "$NAMESPACE" -o json | jq -r '
  [.items[].spec.containers[] | select(.name != "wait-for-dns") | .resources.requests // {}] |
  {
    cpu: ([.[].cpu // "0m"] | map(rtrimstr("m") | tonumber) | add),
    memory: ([.[].memory // "0Mi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber * 1024) elif endswith("Mi") then (rtrimstr("Mi") | tonumber) else tonumber end) | add)
  }
')

LIMITS=$(kubectl get pods -n "$NAMESPACE" -o json | jq -r '
  [.items[].spec.containers[] | select(.name != "wait-for-dns") | .resources.limits // {}] |
  {
    cpu: ([.[].cpu // "0m"] | map(rtrimstr("m") | tonumber) | add),
    memory: ([.[].memory // "0Mi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber * 1024) elif endswith("Mi") then (rtrimstr("Mi") | tonumber) else tonumber end) | add)
  }
')

CPU_REQ=$(echo "$REQUESTS" | jq -r '.cpu')
MEM_REQ=$(echo "$REQUESTS" | jq -r '.memory')
CPU_LIM=$(echo "$LIMITS" | jq -r '.cpu')
MEM_LIM=$(echo "$LIMITS" | jq -r '.memory')

if [ "$METRICS_AVAILABLE" = true ]; then
  # Get actual usage
  ACTUAL_CPU=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{sum+=$2} END {print sum}' | sed 's/m//')
  ACTUAL_MEM=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{sum+=$3} END {gsub(/Mi/,"",$0); print sum}')

  # Handle empty values
  ACTUAL_CPU=${ACTUAL_CPU:-0}
  ACTUAL_MEM=${ACTUAL_MEM:-0}

  # Calculate percentages (avoid division by zero)
  CPU_REQ_PCT=$(awk "BEGIN {printf \"%.1f\", ($CPU_REQ > 0) ? ($ACTUAL_CPU / $CPU_REQ) * 100 : 0}")
  MEM_REQ_PCT=$(awk "BEGIN {printf \"%.1f\", ($MEM_REQ > 0) ? ($ACTUAL_MEM / $MEM_REQ) * 100 : 0}")
  CPU_LIM_PCT=$(awk "BEGIN {printf \"%.1f\", ($CPU_LIM > 0) ? ($ACTUAL_CPU / $CPU_LIM) * 100 : 0}")
  MEM_LIM_PCT=$(awk "BEGIN {printf \"%.1f\", ($MEM_LIM > 0) ? ($ACTUAL_MEM / $MEM_LIM) * 100 : 0}")

  printf "%-15s %10s %10s %15s %12s\n" "Resource" "Requests" "Limits" "Actual Usage" "Utilization"
  printf "%-15s %10s %10s %15s %12s\n" "--------" "--------" "------" "------------" "-----------"
  printf "%-15s %9sm %9sm %14sm %9s%%\n" "CPU" "$CPU_REQ" "$CPU_LIM" "$ACTUAL_CPU" "$CPU_REQ_PCT"
  printf "%-15s %8sMi %8sMi %13sMi %9s%%\n" "Memory" "$MEM_REQ" "$MEM_LIM" "$ACTUAL_MEM" "$MEM_REQ_PCT"
  echo ""

  # Resource efficiency indicators
  echo -e "${BLUE}=== NAMESPACE: RESOURCE EFFICIENCY (${NAMESPACE}) ===${NC}"
  if [ "$CPU_REQ" -eq 0 ] || [ "$ACTUAL_CPU" -eq 0 ]; then
      echo -e "${YELLOW}⚠️  CPU: No resource requests or usage data${NC}"
  elif (( $(echo "$CPU_REQ_PCT < 30" | bc -l) )); then
      echo -e "${YELLOW}⚠️  CPU: Under-utilized (${CPU_REQ_PCT}% of requests)${NC}"
  elif (( $(echo "$CPU_REQ_PCT > 80" | bc -l) )); then
      echo -e "${RED}🔴 CPU: High utilization (${CPU_REQ_PCT}% of requests)${NC}"
  else
      echo -e "${GREEN}✅ CPU: Good utilization (${CPU_REQ_PCT}% of requests)${NC}"
  fi

  if [ "$MEM_REQ" -eq 0 ] || [ "$ACTUAL_MEM" -eq 0 ]; then
      echo -e "${YELLOW}⚠️  Memory: No resource requests or usage data${NC}"
  elif (( $(echo "$MEM_REQ_PCT < 40" | bc -l) )); then
      echo -e "${YELLOW}⚠️  Memory: Under-utilized (${MEM_REQ_PCT}% of requests)${NC}"
  elif (( $(echo "$MEM_REQ_PCT > 80" | bc -l) )); then
      echo -e "${RED}🔴 Memory: High utilization (${MEM_REQ_PCT}% of requests)${NC}"
  else
      echo -e "${GREEN}✅ Memory: Good utilization (${MEM_REQ_PCT}% of requests)${NC}"
  fi
else
  printf "%-15s %10s %10s\n" "Resource" "Requests" "Limits"
  printf "%-15s %10s %10s\n" "--------" "--------" "------"
  printf "%-15s %9sm %9sm\n" "CPU" "$CPU_REQ" "$CPU_LIM"
  printf "%-15s %8sMi %8sMi\n" "Memory" "$MEM_REQ" "$MEM_LIM"
  echo ""
  echo -e "${BLUE}=== NAMESPACE: RESOURCE EFFICIENCY ===${NC}"
  echo -e "${YELLOW}⚠️  Enable metrics-server to see actual usage and efficiency metrics${NC}"
  echo -e "${YELLOW}   Minikube: minikube addons enable metrics-server${NC}"
  echo -e "${YELLOW}   Kubernetes: kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml${NC}"
fi
echo ""

# Namespace Storage Information
echo -e "${BLUE}=== NAMESPACE: STORAGE (${NAMESPACE}) ===${NC}"
PVC_COUNT=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')

if [ "$PVC_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}No PVCs found in namespace${NC}"
    echo -e "${GREEN}✅ Using emptyDir or no persistent storage${NC}"
else
    echo -e "Total PVCs: ${PVC_COUNT}"
    echo ""
    printf "%-40s %-10s %-15s %-10s\n" "PVC Name" "Status" "Capacity" "StorageClass"
    printf "%-40s %-10s %-15s %-10s\n" "--------" "------" "--------" "------------"
    kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | while read pvc status volume capacity access mode storageclass age; do
        printf "%-40s %-10s %-15s %-10s\n" "$pvc" "$status" "$capacity" "$storageclass"
    done
    printf "%-40s %-10s %-15s %-10s\n" "----------------------------------------" "----------" "---------------" "------------"

    # Calculate total storage
    TOTAL_STORAGE=$(kubectl get pvc -n "$NAMESPACE" -o json 2>/dev/null | jq -r '[.items[].spec.resources.requests.storage // "0Gi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber) elif endswith("Mi") then (rtrimstr("Mi") | tonumber / 1024) else tonumber end) | add')
    printf "%-40s %-10s %-15s\n" "TOTAL" "" "${TOTAL_STORAGE}Gi"
fi
echo ""

#############################################
# POD-LEVEL BREAKDOWN
#############################################

# All pod resources with component grouping
if [ "$METRICS_AVAILABLE" = true ]; then
  echo -e "${BLUE}=== PODS: RESOURCE USAGE BY COMPONENT (${NAMESPACE}) ===${NC}"
else
  echo -e "${BLUE}=== PODS: RESOURCE ALLOCATION BY COMPONENT (${NAMESPACE}) ===${NC}"
  echo -e "${YELLOW}(metrics-server disabled - showing requests only)${NC}"
fi
echo ""

# Component summary
echo "Component Summary:"
printf "%-20s %10s %12s %8s\n" "Component" "CPU Req" "Memory Req" "Pods"
printf "%-20s %10s %12s %8s\n" "---------" "-------" "----------" "----"

# Create temp file for pod resources
POD_RES_FILE=$(mktemp)
kubectl get pods -n "$NAMESPACE" -o json | jq -r '.items[] |
  {name: .metadata.name,
   cpu_req: ([.spec.containers[] | select(.name != "wait-for-dns") | .resources.requests.cpu // "0m"] | map(rtrimstr("m") | tonumber) | add),
   mem_req: ([.spec.containers[] | select(.name != "wait-for-dns") | .resources.requests.memory // "0Mi"] | map(if endswith("Gi") then (rtrimstr("Gi") | tonumber * 1024) elif endswith("Mi") then (rtrimstr("Mi") | tonumber) else tonumber end) | add)
  } | "\(.name) \(.cpu_req) \(.mem_req)"' > "$POD_RES_FILE"

if [ "$METRICS_AVAILABLE" = true ]; then
  kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk -v pod_res_file="$POD_RES_FILE" '
BEGIN {
  while ((getline line < pod_res_file) > 0) {
    split(line, parts, " ");
    pod_cpu_req[parts[1]] = parts[2];
    pod_mem_req[parts[1]] = parts[3];
  }
  close(pod_res_file);
}
{
  pod=$1;
  cpu=$2; gsub(/m/, "", cpu);
  mem=$3; gsub(/Mi/, "", mem);

  # Extract component
  split(pod, parts, "-");
  if (parts[1] == "mimir") {
    comp = parts[2];
    if (parts[3] != "" && parts[3] !~ /^[0-9]/) {
      comp = parts[2] "-" parts[3];
    }
  } else {
    comp = parts[1];
  }

  comp_cpu[comp] += cpu;
  comp_mem[comp] += mem;
  comp_count[comp]++;
  total_cpu += cpu;
  total_mem += mem;
  total_pods++;

  # Calculate utilization
  cpu_req = pod_cpu_req[pod];
  mem_req = pod_mem_req[pod];
  cpu_util = (cpu_req > 0) ? sprintf("%.1f", (cpu / cpu_req) * 100) : "0.0";
  mem_util = (mem_req > 0) ? sprintf("%.1f", (mem / mem_req) * 100) : "0.0";

  total_cpu_req += cpu_req;
  total_mem_req += mem_req;

  pods[pod] = sprintf("  %-40s %10s %10s %10s %10s %10s %10s", pod, $2, cpu_req "m", cpu_util "%", $3, mem_req "Mi", mem_util "%");
  pod_comp[pod] = comp;
}
END {
  for (comp in comp_cpu) {
    printf "%-20s %9sm %11sMi %8d\n", comp, comp_cpu[comp], comp_mem[comp], comp_count[comp];
  }
  printf "%-20s %9s %11s %8s\n", "--------------------", "---------", "-----------", "--------";
  printf "%-20s %9sm %11sMi %8d\n", "TOTAL", total_cpu, total_mem, total_pods;

  print "";
  print "All Pods:";
  printf "  %-40s %10s %10s %10s %10s %10s %10s\n", "Pod", "CPU Usage", "CPU Req", "CPU Util", "Mem Usage", "Mem Req", "Mem Util";
  printf "  %-40s %10s %10s %10s %10s %10s %10s\n", "---", "---------", "-------", "--------", "---------", "-------", "--------";
  for (pod in pods) {
    print pods[pod];
  }
  printf "  %-40s %10s %10s %10s %10s %10s %10s\n", "---------------------------------------------", "----------", "----------", "----------", "----------", "----------", "----------";

  total_cpu_util = (total_cpu_req > 0) ? sprintf("%.1f", (total_cpu / total_cpu_req) * 100) : "0.0";
  total_mem_util = (total_mem_req > 0) ? sprintf("%.1f", (total_mem / total_mem_req) * 100) : "0.0";
  printf "  %-40s %9sm %9sm %9s%% %9sMi %9sMi %9s%%\n", "TOTAL", total_cpu, total_cpu_req, total_cpu_util, total_mem, total_mem_req, total_mem_util;
}'
else
  # Show allocation only when metrics unavailable
  awk -v pod_res_file="$POD_RES_FILE" '
  BEGIN {
    while ((getline line < pod_res_file) > 0) {
      split(line, parts, " ");
      pod = parts[1];
      cpu_req = parts[2];
      mem_req = parts[3];

      # Extract component
      split(pod, p, "-");
      if (p[1] == "mimir") {
        comp = p[2];
        if (p[3] != "" && p[3] !~ /^[0-9]/) {
          comp = p[2] "-" p[3];
        }
      } else {
        comp = p[1];
      }

      comp_cpu[comp] += cpu_req;
      comp_mem[comp] += mem_req;
      comp_count[comp]++;
      total_cpu += cpu_req;
      total_mem += mem_req;
      total_pods++;

      pods[pod] = sprintf("  %-40s %10s %10s", pod, cpu_req "m", mem_req "Mi");
    }
    close(pod_res_file);

    for (comp in comp_cpu) {
      printf "%-20s %9sm %11sMi %8d\n", comp, comp_cpu[comp], comp_mem[comp], comp_count[comp];
    }
    printf "%-20s %9s %11s %8s\n", "--------------------", "---------", "-----------", "--------";
    printf "%-20s %9sm %11sMi %8d\n", "TOTAL", total_cpu, total_mem, total_pods;

    print "";
    print "All Pods:";
    printf "  %-40s %10s %10s\n", "Pod", "CPU Req", "Mem Req";
    printf "  %-40s %10s %10s\n", "---", "-------", "-------";
    for (pod in pods) {
      print pods[pod];
    }
    printf "  %-40s %10s %10s\n", "---------------------------------------------", "----------", "----------";
    printf "  %-40s %9sm %9sMi\n", "TOTAL", total_cpu, total_mem;
  }'
fi
rm -f "$POD_RES_FILE"
echo ""

# Pod status summary
echo -e "${BLUE}=== PODS: STATUS (${NAMESPACE}) ===${NC}"
TOTAL_PODS=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')
RUNNING_PODS=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')
echo -e "Total Pods: ${TOTAL_PODS}"
echo -e "Running: ${GREEN}${RUNNING_PODS}${NC}"

if [ "$RUNNING_PODS" != "$TOTAL_PODS" ]; then
    echo -e "${RED}Not Running: $((TOTAL_PODS - RUNNING_PODS))${NC}"
    kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running --no-headers 2>/dev/null | awk '{printf "  %s: %s\n", $1, $3}'
fi
echo ""
