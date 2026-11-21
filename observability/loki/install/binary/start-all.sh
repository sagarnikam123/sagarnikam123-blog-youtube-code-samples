#!/bin/bash

# Start All Loki Stack Services
# Starts all components in the correct order with health checks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🚀 Starting Loki Monolithic Stack...${NC}"
echo ""

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}⏳ Waiting for $name to be ready...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 2 "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "${RED}❌ $name failed to start within $((max_attempts * 2)) seconds${NC}"
    return 1
}

# Function to start service in background
start_service() {
    local script=$1
    local name=$2
    local url=$3

    echo -e "${BLUE}🔄 Starting $name...${NC}"

    # Start service in background
    nohup "$SCRIPT_DIR/$script" > "/tmp/${name,,}-startup.log" 2>&1 &
    local pid=$!

    # Wait a moment for startup
    sleep 3

    # Check if process is still running
    if ! kill -0 $pid 2>/dev/null; then
        echo -e "${RED}❌ $name failed to start${NC}"
        echo "Check log: /tmp/${name,,}-startup.log"
        return 1
    fi

    # Wait for service to be ready if URL provided
    if [ -n "$url" ]; then
        wait_for_service "$url" "$name"
    else
        echo -e "${GREEN}✅ $name started (PID: $pid)${NC}"
    fi
}

echo -e "${BLUE}📦 Starting storage services...${NC}"
start_service "start-minio.sh" "MinIO" "http://127.0.0.1:9001"

echo ""
echo -e "${BLUE}🏗️  Starting core services...${NC}"
start_service "start-loki.sh" "Loki" "http://127.0.0.1:3100/ready"
start_service "start-prometheus.sh" "Prometheus" "http://127.0.0.1:9090/-/ready"
start_service "start-grafana.sh" "Grafana" "http://127.0.0.1:3000/api/health"

echo ""
echo -e "${BLUE}📊 Starting log scrapers (optional)...${NC}"
echo -e "${YELLOW}💡 Log scrapers are optional. Start them manually if needed:${NC}"
echo "   • Fluent Bit: ./scripts/stack/start-fluent-bit.sh"
echo "   • Grafana Alloy: ./scripts/stack/start-alloy.sh"
echo "   • Vector: ./scripts/stack/start-vector.sh"

echo ""
echo -e "${GREEN}🎉 Loki Stack startup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Access URLs:${NC}"
echo "   • Loki: http://127.0.0.1:3100"
echo "   • Prometheus: http://127.0.0.1:9090"
echo "   • Grafana: http://127.0.0.1:3000 (admin/admin)"
echo "   • MinIO Console: http://127.0.0.1:9001 (minioadmin/minioadmin)"
echo ""
echo -e "${BLUE}🔧 Next steps:${NC}"
echo "   • Generate logs: ./scripts/logs/generate-logs.sh"
echo "   • Start log scraper: ./scripts/stack/start-fluent-bit.sh"
echo "   • Collect metrics: ./observability/metrics/collect-all-metrics.sh"
echo "   • Stop all: ./scripts/stack/stop-all.sh"
