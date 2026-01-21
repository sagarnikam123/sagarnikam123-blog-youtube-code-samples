#!/bin/bash

#############################################
# Prometheus Sizing Report
# Analyzes current metrics to recommend resource sizing
#############################################

# Configuration
NAMESPACE="${NAMESPACE:-prometheus}"
PROM_POD=""

# Colors - use $'...' syntax for proper escape interpretation
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
echo "${GREEN}║   Prometheus Sizing Report            ║${NC}"
echo "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo "Namespace: ${YELLOW}$NAMESPACE${NC}"
echo ""

# Find Prometheus pod
PROM_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [[ -z "$PROM_POD" ]]; then
    echo "${RED}Error: No Prometheus pod found in namespace '$NAMESPACE'${NC}"
    exit 1
fi
echo "Pod: ${CYAN}$PROM_POD${NC}"
echo ""

# Helper function to query Prometheus
prom_query() {
    local query="$1"
    kubectl exec -n "$NAMESPACE" "$PROM_POD" -c prometheus -- \
        wget -qO- "http://localhost:9090/api/v1/query?query=$query" 2>/dev/null
}

#############################################
# 1. Current Metrics
#############################################
echo "${BLUE}═══ Current Metrics ═══${NC}"

# Active series
ACTIVE_SERIES=$(prom_query 'sum(prometheus_tsdb_head_series)' | jq -r '.data.result[0].value[1] // "0"')
ACTIVE_SERIES_NUM=${ACTIVE_SERIES%.*}
printf "  Active Series:     %'d\n" "$ACTIVE_SERIES_NUM"

# Head chunks
HEAD_CHUNKS=$(prom_query 'prometheus_tsdb_head_chunks' | jq -r '.data.result[0].value[1] // "0"')
HEAD_CHUNKS_NUM=${HEAD_CHUNKS%.*}
printf "  Head Chunks:       %'d\n" "$HEAD_CHUNKS_NUM"

# Scrape targets
TARGETS=$(prom_query 'count(up)' | jq -r '.data.result[0].value[1] // "0"')
printf "  Scrape Targets:    %s\n" "$TARGETS"

# Samples ingested rate (per second) - use 15m range for 5m scrape intervals
INGEST_RATE=$(prom_query 'sum(rate(prometheus_tsdb_head_samples_appended_total[15m]))' | jq -r '.data.result[0].value[1] // "0"')
INGEST_RATE_INT=$(printf "%.0f" "$INGEST_RATE" 2>/dev/null || echo "0")
printf "  Ingestion Rate:    %'d samples/sec\n" "$INGEST_RATE_INT"

echo ""

#############################################
# 2. Current Resource Usage
#############################################
echo "${BLUE}═══ Current Resource Usage ═══${NC}"

# Memory from process
MEMORY_BYTES=$(prom_query 'process_resident_memory_bytes' | jq -r '.data.result[0].value[1] // "0"')
MEMORY_GB=$(echo "scale=2; $MEMORY_BYTES / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "0")
MEMORY_MI=$(echo "scale=0; $MEMORY_BYTES / 1024 / 1024" | bc 2>/dev/null || echo "0")

# Get actual usage from metrics-server (with timeout)
ACTUAL_USAGE=$(timeout 5 kubectl top pod -n "$NAMESPACE" "$PROM_POD" --no-headers 2>/dev/null)
if [[ -n "$ACTUAL_USAGE" ]]; then
    ACTUAL_CPU=$(echo "$ACTUAL_USAGE" | awk '{print $2}')
    ACTUAL_MEM=$(echo "$ACTUAL_USAGE" | awk '{print $3}')
    echo "  CPU Usage:         $ACTUAL_CPU"
    echo "  Memory Usage:      $ACTUAL_MEM"
else
    echo "  Memory (process):  ${MEMORY_MI}Mi (~${MEMORY_GB}GB)"
fi

# Get configured limits (with timeout)
LIMITS=$(timeout 5 kubectl get pod -n "$NAMESPACE" "$PROM_POD" -o json 2>/dev/null | jq -r '
    .spec.containers[] | select(.name == "prometheus") |
    "  CPU Request:       \(.resources.requests.cpu // "not set")\n  CPU Limit:         \(.resources.limits.cpu // "not set")\n  Memory Request:    \(.resources.requests.memory // "not set")\n  Memory Limit:      \(.resources.limits.memory // "not set")"
' 2>/dev/null)
if [[ -n "$LIMITS" ]]; then
    echo "$LIMITS"
fi

echo ""

#############################################
# 3. Storage Usage
#############################################
echo "${BLUE}═══ Storage Usage ═══${NC}"

# TSDB size - format with leading zero
TSDB_BYTES=$(prom_query 'prometheus_tsdb_storage_blocks_bytes' | jq -r '.data.result[0].value[1] // "0"')
TSDB_MB=$(echo "scale=0; $TSDB_BYTES / 1024 / 1024" | bc 2>/dev/null || echo "0")
if [[ "$TSDB_MB" -ge 1024 ]]; then
    TSDB_GB=$(echo "scale=2; $TSDB_BYTES / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "0")
    # Add leading zero if needed
    [[ "$TSDB_GB" == .* ]] && TSDB_GB="0$TSDB_GB"
    echo "  TSDB Blocks:       ${TSDB_GB} GB"
else
    echo "  TSDB Blocks:       ${TSDB_MB} MB"
fi

# WAL size - format with leading zero
WAL_BYTES=$(prom_query 'prometheus_tsdb_wal_storage_size_bytes' | jq -r '.data.result[0].value[1] // "0"')
WAL_MB=$(echo "scale=0; $WAL_BYTES / 1024 / 1024" | bc 2>/dev/null || echo "0")
if [[ "$WAL_MB" -ge 1024 ]]; then
    WAL_GB=$(echo "scale=2; $WAL_BYTES / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "0")
    [[ "$WAL_GB" == .* ]] && WAL_GB="0$WAL_GB"
    echo "  WAL Size:          ${WAL_GB} GB"
else
    echo "  WAL Size:          ${WAL_MB} MB"
fi

# Retention - show hours if < 1 day
RETENTION=$(prom_query 'prometheus_tsdb_retention_limit_seconds' | jq -r '.data.result[0].value[1] // "0"')
RETENTION_INT=${RETENTION%.*}
if [[ "$RETENTION_INT" -eq 0 ]]; then
    # Fallback: get from flags API
    RETENTION_STR=$(kubectl exec -n "$NAMESPACE" "$PROM_POD" -c prometheus -- \
        wget -qO- 'http://localhost:9090/api/v1/status/flags' 2>/dev/null | \
        jq -r '.data["storage.tsdb.retention.time"] // "unknown"')
    echo "  Retention:         $RETENTION_STR"
elif [[ "$RETENTION_INT" -lt 86400 ]]; then
    RETENTION_HOURS=$(echo "scale=0; $RETENTION_INT / 3600" | bc 2>/dev/null || echo "0")
    echo "  Retention:         ${RETENTION_HOURS}h"
else
    RETENTION_DAYS=$(echo "scale=1; $RETENTION_INT / 86400" | bc 2>/dev/null || echo "0")
    [[ "$RETENTION_DAYS" == .* ]] && RETENTION_DAYS="0$RETENTION_DAYS"
    echo "  Retention:         ${RETENTION_DAYS} days"
fi

# PVC size
PVC_SIZE=$(kubectl get pvc -n "$NAMESPACE" -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].spec.resources.requests.storage}' 2>/dev/null)
if [[ -n "$PVC_SIZE" ]]; then
    echo "  PVC Size:          $PVC_SIZE"
fi

echo ""

#############################################
# 4. Remote Write Status (if configured)
#############################################
RW_ENABLED=$(prom_query 'prometheus_remote_storage_samples_total' | jq -r '.data.result | length')
if [[ "$RW_ENABLED" -gt 0 ]]; then
    echo "${BLUE}═══ Remote Write Status ═══${NC}"

    RW_RATE=$(prom_query 'sum(rate(prometheus_remote_storage_samples_total[15m]))' | jq -r '.data.result[0].value[1] // "0"')
    RW_RATE_INT=$(printf "%.0f" "$RW_RATE" 2>/dev/null || echo "0")
    printf "  Write Rate:        %'d samples/sec\n" "$RW_RATE_INT"

    RW_PENDING=$(prom_query 'sum(prometheus_remote_storage_samples_pending)' | jq -r '.data.result[0].value[1] // "0"')
    RW_PENDING_INT=${RW_PENDING%.*}
    printf "  Pending Samples:   %'d\n" "$RW_PENDING_INT"

    RW_FAILED=$(prom_query 'sum(prometheus_remote_storage_samples_failed_total)' | jq -r '.data.result[0].value[1] // "0"')
    RW_FAILED_INT=${RW_FAILED%.*}
    if [[ "$RW_FAILED_INT" -gt 0 ]]; then
        printf "  Failed Samples:    ${RED}%'d${NC}\n" "$RW_FAILED_INT"
    else
        printf "  Failed Samples:    ${GREEN}0${NC}\n"
    fi

    SHARDS=$(prom_query 'sum(prometheus_remote_storage_shards)' | jq -r '.data.result[0].value[1] // "0"')
    echo "  Active Shards:     ${SHARDS%.*}"

    echo ""
fi

#############################################
# 5. Sizing Recommendations
#############################################
echo "${BLUE}═══ Sizing Recommendations ═══${NC}"
echo ""

# Determine sizing tier based on active series
if [[ "$ACTIVE_SERIES_NUM" -lt 100000 ]]; then
    TIER="Small"
    REC_CPU_REQ="500m"
    REC_CPU_LIM="1"
    REC_MEM_REQ="1Gi"
    REC_MEM_LIM="2Gi"
    REC_STORAGE="10Gi"
elif [[ "$ACTIVE_SERIES_NUM" -lt 500000 ]]; then
    TIER="Medium"
    REC_CPU_REQ="1"
    REC_CPU_LIM="2"
    REC_MEM_REQ="2Gi"
    REC_MEM_LIM="4Gi"
    REC_STORAGE="25Gi"
elif [[ "$ACTIVE_SERIES_NUM" -lt 1000000 ]]; then
    TIER="Large"
    REC_CPU_REQ="1"
    REC_CPU_LIM="2"
    REC_MEM_REQ="4Gi"
    REC_MEM_LIM="8Gi"
    REC_STORAGE="50Gi"
elif [[ "$ACTIVE_SERIES_NUM" -lt 5000000 ]]; then
    TIER="XLarge"
    REC_CPU_REQ="2"
    REC_CPU_LIM="4"
    REC_MEM_REQ="8Gi"
    REC_MEM_LIM="16Gi"
    REC_STORAGE="100Gi"
elif [[ "$ACTIVE_SERIES_NUM" -lt 10000000 ]]; then
    TIER="XXLarge"
    REC_CPU_REQ="4"
    REC_CPU_LIM="8"
    REC_MEM_REQ="16Gi"
    REC_MEM_LIM="32Gi"
    REC_STORAGE="200Gi"
else
    TIER="Massive"
    REC_CPU_REQ="8"
    REC_CPU_LIM="16"
    REC_MEM_REQ="32Gi"
    REC_MEM_LIM="64Gi"
    REC_STORAGE="500Gi"
fi

echo "  Based on ${CYAN}${ACTIVE_SERIES_NUM}${NC} active series:"
echo ""
echo "  Sizing Tier:       ${YELLOW}$TIER${NC}"
echo ""
echo "  ${CYAN}Recommended Resources:${NC}"
echo "  ┌─────────────────┬─────────────┬─────────────┐"
echo "  │ Resource        │ Request     │ Limit       │"
echo "  ├─────────────────┼─────────────┼─────────────┤"
printf "  │ CPU             │ %-11s │ %-11s │\n" "$REC_CPU_REQ" "$REC_CPU_LIM"
printf "  │ Memory          │ %-11s │ %-11s │\n" "$REC_MEM_REQ" "$REC_MEM_LIM"
printf "  │ Storage         │ %-11s │ -           │\n" "$REC_STORAGE"
echo "  └─────────────────┴─────────────┴─────────────┘"

echo ""

#############################################
# 6. Helm Values Snippet
#############################################
echo "${BLUE}═══ Helm Values Snippet ═══${NC}"
echo ""
echo "  ${CYAN}# Add to your values.yaml:${NC}"
echo "  prometheus:"
echo "    prometheusSpec:"
echo "      resources:"
echo "        requests:"
echo "          cpu: $REC_CPU_REQ"
echo "          memory: $REC_MEM_REQ"
echo "        limits:"
echo "          cpu: $REC_CPU_LIM"
echo "          memory: $REC_MEM_LIM"
echo "      storageSpec:"
echo "        volumeClaimTemplate:"
echo "          spec:"
echo "            resources:"
echo "              requests:"
echo "                storage: $REC_STORAGE"

echo ""

#############################################
# 7. Sizing Reference Table
#############################################
echo "${BLUE}═══ Sizing Reference ═══${NC}"
echo ""
echo "  │ Active Series │ CPU Req │ CPU Lim │ Mem Req │ Mem Lim │ Storage │"
echo "  │───────────────│─────────│─────────│─────────│─────────│─────────│"
echo "  │ < 100K        │ 500m    │ 1       │ 1Gi     │ 2Gi     │ 10Gi    │"
echo "  │ 100K - 500K   │ 1       │ 2       │ 2Gi     │ 4Gi     │ 25Gi    │"
echo "  │ 500K - 1M     │ 1       │ 2       │ 4Gi     │ 8Gi     │ 50Gi    │"
echo "  │ 1M - 5M       │ 2       │ 4       │ 8Gi     │ 16Gi    │ 100Gi   │"
echo "  │ 5M - 10M      │ 4       │ 8       │ 16Gi    │ 32Gi    │ 200Gi   │"
echo "  │ > 10M         │ 8       │ 16      │ 32Gi    │ 64Gi    │ 500Gi   │"
echo ""
echo "  ${YELLOW}Note: Memory formula ≈ Active Series × 2-4 KB${NC}"
echo "  ${YELLOW}      Add 25% overhead if using remote write${NC}"

echo ""
echo "${GREEN}✓ Sizing report complete${NC}"
