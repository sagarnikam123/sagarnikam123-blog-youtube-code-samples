#!/bin/bash

# Loki Podman Start Script
# Runs monolithic Loki using Podman with same config files

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration options
CONFIG_FILE="loki-3.5.x-ui-filesystem-inmemory.yaml"
INCLUDE_MINIO=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -c, --config CONFIG      Config file name (default: $CONFIG_FILE)"
    echo "  -m, --with-minio         Include MinIO for S3 storage"
    echo "  -h, --help               Show this help"
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

echo "🐳 Starting Loki Podman Deployment"
echo "Configuration: $CONFIG_FILE"
echo "Include MinIO: $INCLUDE_MINIO"
echo ""

# Create pod for networking
echo "🔗 Creating pod network..."
podman pod create --name loki-pod -p 3100:3100 -p 9095:9095

# Create volumes
echo "💾 Creating volumes..."
podman volume create loki-data 2>/dev/null || true

# Start Loki container
echo "🚀 Starting Loki..."
podman run -d \
  --name loki-monolithic \
  --pod loki-pod \
  -v "$(pwd)/../configs:/etc/loki/configs:ro,Z" \
  -v loki-data:/tmp/loki:Z \
  -e HOSTNAME=loki-podman \
  --health-cmd="wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  --health-start-period=40s \
  grafana/loki:3.5.0 \
  -config.file=/etc/loki/configs/v3.x/v3.5.x/$CONFIG_FILE \
  -config.expand-env=true

# Start MinIO if requested
if [[ "$INCLUDE_MINIO" == "true" ]]; then
    echo "🗄️ Starting MinIO..."
    podman volume create minio-data 2>/dev/null || true
    podman run -d \
      --name loki-minio \
      --pod loki-pod \
      -v minio-data:/data:Z \
      -e MINIO_ROOT_USER=minioadmin \
      -e MINIO_ROOT_PASSWORD=minioadmin \
      minio/minio:latest \
      server /data --console-address ":9001"
fi

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
    echo "  • View logs: podman logs -f loki-monolithic"
    echo "  • Stop services: ./stop-podman.sh"
    echo "  • Restart: podman restart loki-monolithic"
else
    echo "❌ Loki failed to start properly"
    echo "📋 Troubleshooting:"
    echo "  • Check logs: podman logs loki-monolithic"
    echo "  • Check pod: podman pod ps"
    exit 1
fi