#!/bin/bash

# Automated Metrics Collection Script for Loki Monolithic Stack
# Collects metrics from Loki, Fluent Bit, and Prometheus
# Updated for new directory structure

# Configuration
METRICS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Collecting metrics from Loki monolithic stack..."
echo "📁 Metrics directory: $METRICS_DIR"
echo "⏰ Timestamp: $TIMESTAMP"
echo ""

# Function to check if service is running
check_service() {
    local url=$1
    local name=$2

    if curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $name is not accessible at $url${NC}"
        return 1
    fi
}

# Function to collect metrics
collect_metrics() {
    local url=$1
    local filename=$2
    local service_name=$3

    echo "📊 Collecting $service_name metrics..."

    if curl -s --connect-timeout 10 "$url" > "$METRICS_DIR/$filename"; then
        local lines=$(wc -l < "$METRICS_DIR/$filename")
        local size=$(du -h "$METRICS_DIR/$filename" | cut -f1)
        echo -e "${GREEN}✅ $service_name metrics collected: $lines lines, $size${NC}"
    else
        echo -e "${RED}❌ Failed to collect $service_name metrics${NC}"
        rm -f "$METRICS_DIR/$filename" 2>/dev/null
    fi
}

# Check service availability
echo "🔍 Checking service availability..."
check_service "http://localhost:3100/metrics" "Loki"
loki_available=$?
check_service "http://localhost:2020/api/v2/metrics/prometheus" "Fluent Bit"
fluent_bit_available=$?
check_service "http://localhost:9090/metrics" "Prometheus"
prometheus_available=$?
echo ""

# Collect metrics from available services
if [ "$loki_available" -eq 0 ]; then
    collect_metrics "http://localhost:3100/metrics" "loki-metrics-$TIMESTAMP" "Loki"
fi

if [ "$fluent_bit_available" -eq 0 ]; then
    collect_metrics "http://localhost:2020/api/v2/metrics/prometheus" "fluent-bit-v2-metrics-$TIMESTAMP" "Fluent Bit v2"
    collect_metrics "http://localhost:2020/api/v1/metrics/prometheus" "fluent-bit-v1-metrics-$TIMESTAMP" "Fluent Bit v1"
fi

if [ "$prometheus_available" -eq 0 ]; then
    collect_metrics "http://localhost:9090/metrics" "prometheus-metrics-$TIMESTAMP" "Prometheus"
fi

echo ""
echo "📋 Collection Summary:"
echo "===================="

# List collected files
for file in "$METRICS_DIR"/*-metrics-$TIMESTAMP; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        size=$(du -h "$file" | cut -f1)
        lines=$(wc -l < "$file")
        echo "📄 $filename: $lines lines, $size"
    fi
done

# Create symlinks to latest metrics (for easy access)
echo ""
echo "🔗 Creating symlinks to latest metrics..."

if [ -f "$METRICS_DIR/loki-metrics-$TIMESTAMP" ]; then
    ln -sf "loki-metrics-$TIMESTAMP" "$METRICS_DIR/loki-latest-metrics"
    echo "   loki-latest-metrics -> loki-metrics-$TIMESTAMP"
fi

if [ -f "$METRICS_DIR/fluent-bit-v2-metrics-$TIMESTAMP" ]; then
    ln -sf "fluent-bit-v2-metrics-$TIMESTAMP" "$METRICS_DIR/fluent-bit-latest-metrics"
    echo "   fluent-bit-latest-metrics -> fluent-bit-v2-metrics-$TIMESTAMP"
fi

if [ -f "$METRICS_DIR/prometheus-metrics-$TIMESTAMP" ]; then
    ln -sf "prometheus-metrics-$TIMESTAMP" "$METRICS_DIR/prometheus-latest-metrics"
    echo "   prometheus-latest-metrics -> prometheus-metrics-$TIMESTAMP"
fi

echo ""
echo -e "${GREEN}✅ Metrics collection completed!${NC}"
echo ""
echo "💡 Usage tips:"
echo "   - Use *-latest-metrics files for current analysis"
echo "   - Compare timestamped files for trend analysis"
echo "   - Import metrics into Grafana for visualization"
