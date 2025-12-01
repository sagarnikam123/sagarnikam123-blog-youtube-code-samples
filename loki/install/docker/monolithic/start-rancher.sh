#!/bin/bash

# Loki Rancher Desktop Start Script
# Runs monolithic Loki using Rancher Desktop with same config files

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration options
CONFIG_FILE="loki-3.5.x-ui-filesystem-inmemory.yaml"
INCLUDE_MINIO=false
USE_NERDCTL=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -c, --config CONFIG      Config file name (default: $CONFIG_FILE)"
    echo "  -m, --with-minio         Include MinIO for S3 storage"
    echo "  -n, --nerdctl            Use nerdctl instead of docker"
    echo "  -h, --help               Show this help"
    echo ""
    echo "Rancher Desktop Options:"
    echo "  • Docker (default): Uses docker command"
    echo "  • containerd: Use -n/--nerdctl flag"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -m|--with-minio)
            INCLUDE_MINIO=true
            shift
            ;;
        -n|--nerdctl)
            USE_NERDCTL=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Set container runtime
if [[ "$USE_NERDCTL" == "true" ]]; then
    CONTAINER_CMD="nerdctl"
    COMPOSE_CMD="nerdctl compose"
else
    CONTAINER_CMD="docker"
    COMPOSE_CMD="docker compose"
fi

echo "🐳 Starting Loki Rancher Desktop Deployment"
echo "Container Runtime: $CONTAINER_CMD"
echo "Configuration: $CONFIG_FILE"
echo "Include MinIO: $INCLUDE_MINIO"
echo ""

# Check if Rancher Desktop is running
if ! $CONTAINER_CMD version >/dev/null 2>&1; then
    echo "❌ Rancher Desktop not running or $CONTAINER_CMD not available"
    echo "📋 Please ensure:"
    echo "  • Rancher Desktop is started"
    echo "  • Container runtime is enabled"
    echo "  • PATH includes container tools"
    exit 1
fi

# Update docker-compose.yml with selected config
sed -i.bak "s|/etc/loki/configs/v3.x/v3.5.x/.*\.yaml|/etc/loki/configs/v3.x/v3.5.x/$CONFIG_FILE|" docker-compose.yml

# Build compose command
COMPOSE_ARGS="up -d"
if [[ "$INCLUDE_MINIO" == "true" ]]; then
    COMPOSE_ARGS="--profile s3-storage up -d"
fi

# Start services
echo "🚀 Starting services..."
$COMPOSE_CMD $COMPOSE_ARGS

# Wait for services to be ready
echo "⏳ Waiting for Loki to be ready..."
sleep 10

# Check health
echo "🔍 Checking service health..."
if curl -s --max-time 5 "http://localhost:3100/ready" >/dev/null 2>&1; then
    echo "✅ Loki is ready!"
    echo ""
    echo "🔗 Access URLs:"
    echo "  • Loki Web UI: http://localhost:3100/ui/"
    echo "  • Loki Ring Status: http://localhost:3100/ring"
    echo "  • Loki Configuration: http://localhost:3100/config"
    echo "  • Loki Metrics: http://localhost:3100/metrics"

    if [[ "$INCLUDE_MINIO" == "true" ]]; then
        echo "  • MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
        echo "  • MinIO API: http://localhost:9000"
    fi

    echo ""
    echo "📋 Management Commands:"
    echo "  • View logs: $COMPOSE_CMD logs -f loki"
    echo "  • Stop services: ./stop-rancher.sh"
    echo "  • Container status: $CONTAINER_CMD ps"
else
    echo "❌ Loki failed to start properly"
    echo "📋 Troubleshooting:"
    echo "  • Check logs: $COMPOSE_CMD logs loki"
    echo "  • Check containers: $CONTAINER_CMD ps -a"
    echo "  • Check Rancher Desktop status"
    exit 1
fi
