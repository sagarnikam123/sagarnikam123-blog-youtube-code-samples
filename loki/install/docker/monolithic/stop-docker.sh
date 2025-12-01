#!/bin/bash

# Loki Docker Stop Script
# Stops monolithic Loki Docker deployment

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REMOVE_VOLUMES=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -v, --remove-volumes     Remove data volumes (WARNING: deletes all data)"
    echo "  -h, --help               Show this help"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--remove-volumes)
            REMOVE_VOLUMES=true
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

echo "🐳 Stopping Loki Docker Deployment"
echo ""

# Stop services
echo "🛑 Stopping services..."
docker-compose --profile s3-storage down

if [[ "$REMOVE_VOLUMES" == "true" ]]; then
    echo "⚠️  Removing data volumes..."
    docker-compose --profile s3-storage down -v
    docker volume rm loki-monolithic_loki-data loki-monolithic_minio-data 2>/dev/null || true
    echo "✅ Volumes removed"
else
    echo "💾 Data volumes preserved"
    echo "   Use -v/--remove-volumes to delete all data"
fi

echo ""
echo "✅ Loki Docker deployment stopped"
echo ""
echo "📋 Management Commands:"
echo "  • Start again: ./start-docker.sh"
echo "  • View remaining containers: docker ps -a"
echo "  • Remove all: docker-compose down -v --remove-orphans"
