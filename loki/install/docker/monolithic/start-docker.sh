#!/bin/bash

# Loki Docker Start Script
# Runs monolithic Loki using Docker Compose with same config files

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# =============================================================================
# Configuration Variables
# =============================================================================
LOKI_VERSION="3.5.0"
LOKI_IMAGE="grafana/loki:${LOKI_VERSION}"
CONFIG_FILE="loki-3.5.x-ui-filesystem-inmemory.yaml"
CONFIG_PATH="v3.x/v3.5.x"
CONTAINER_NAME="loki-monolithic"
NETWORK_NAME="loki-network"

# Port Configuration
LOKI_HTTP_PORT="3100"
LOKI_GRPC_PORT="9095"
MINIO_API_PORT="9000"
MINIO_CONSOLE_PORT="9001"

# MinIO Configuration
MINIO_VERSION="latest"
MINIO_IMAGE="minio/minio:${MINIO_VERSION}"
MINIO_USER="minioadmin"
MINIO_PASSWORD="minioadmin"

# Runtime Options
INCLUDE_MINIO=false
WAIT_TIME=10

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -c, --config CONFIG      Config file name (default: $CONFIG_FILE)"
    echo "  -m, --with-minio         Include MinIO for S3 storage"
    echo "  -h, --help               Show this help"
    echo ""
    echo "Available configs:"
    echo "  • loki-3.5.x-ui-filesystem-inmemory.yaml (default)"
    echo "  • loki-3.5.x-dev-local-storage.yaml"
    echo "  • loki-3.5.x-minimal-working.yaml"
    echo "  • loki-3.5.x-simple-working.yaml"
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

# Update docker-compose.yml with selected config and version
sed -i.bak "s|grafana/loki:[0-9]\+\.[0-9]\+\.[0-9]\+|$LOKI_IMAGE|" docker-compose.yml
sed -i.bak "s|/etc/loki/configs/v3.x/v3.5.x/.*\.yaml|/etc/loki/configs/$CONFIG_PATH/$CONFIG_FILE|" docker-compose.yml
sed -i.bak "s|minio/minio:.*|$MINIO_IMAGE|" docker-compose.yml
sed -i.bak "s|container_name: loki-.*|container_name: $CONTAINER_NAME|" docker-compose.yml

echo "🐳 Starting Loki Docker Deployment"
echo "Loki Version: $LOKI_VERSION"
echo "Configuration: $CONFIG_FILE"
echo "Config Path: $CONFIG_PATH"
echo "HTTP Port: $LOKI_HTTP_PORT"
echo "GRPC Port: $LOKI_GRPC_PORT"
echo "Include MinIO: $INCLUDE_MINIO"
echo ""

# Build compose command
COMPOSE_CMD="docker-compose up -d"
if [[ "$INCLUDE_MINIO" == "true" ]]; then
    COMPOSE_CMD="docker-compose --profile s3-storage up -d"
fi

# Start services
echo "🚀 Starting services..."
eval $COMPOSE_CMD

# Wait for services to be ready
echo "⏳ Waiting for Loki to be ready..."
sleep $WAIT_TIME

# Check health
echo "🔍 Checking service health..."
if curl -s --max-time 5 "http://localhost:$LOKI_HTTP_PORT/ready" >/dev/null 2>&1; then
    echo "✅ Loki is ready!"
    echo ""
    echo "🔗 Access URLs:"
    echo "  • Loki Web UI: http://localhost:$LOKI_HTTP_PORT/ui/"
    echo "  • Loki Ring Status: http://localhost:$LOKI_HTTP_PORT/ring"
    echo "  • Loki Configuration: http://localhost:$LOKI_HTTP_PORT/config"
    echo "  • Loki Metrics: http://localhost:$LOKI_HTTP_PORT/metrics"

    if [[ "$INCLUDE_MINIO" == "true" ]]; then
        echo "  • MinIO Console: http://localhost:$MINIO_CONSOLE_PORT ($MINIO_USER/$MINIO_PASSWORD)"
        echo "  • MinIO API: http://localhost:$MINIO_API_PORT"
    fi

    echo ""
    echo "📋 Management Commands:"
    echo "  • View logs: docker-compose logs -f loki"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart: docker-compose restart loki"
else
    echo "❌ Loki failed to start properly"
    echo "📋 Troubleshooting:"
    echo "  • Check logs: docker-compose logs loki"
    echo "  • Check config: docker-compose exec loki cat /etc/loki/configs/$CONFIG_PATH/$CONFIG_FILE"
    exit 1
fi
