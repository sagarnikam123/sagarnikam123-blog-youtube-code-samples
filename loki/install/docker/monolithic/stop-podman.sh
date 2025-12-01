#!/bin/bash

# Loki Podman Stop Script
# Stops monolithic Loki Podman deployment

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

echo "🐳 Stopping Loki Podman Deployment"
echo ""

# Stop and remove containers
echo "🛑 Stopping containers..."
podman stop loki-monolithic loki-minio 2>/dev/null || true
podman rm loki-monolithic loki-minio 2>/dev/null || true

# Remove pod
echo "🔗 Removing pod..."
podman pod stop loki-pod 2>/dev/null || true
podman pod rm loki-pod 2>/dev/null || true

if [[ "$REMOVE_VOLUMES" == "true" ]]; then
    echo "⚠️  Removing data volumes..."
    podman volume rm loki-data minio-data 2>/dev/null || true
    echo "✅ Volumes removed"
else
    echo "💾 Data volumes preserved"
    echo "   Use -v/--remove-volumes to delete all data"
fi

echo ""
echo "✅ Loki Podman deployment stopped"
echo ""
echo "📋 Management Commands:"
echo "  • Start again: ./start-podman.sh"
echo "  • View remaining containers: podman ps -a"
echo "  • View volumes: podman volume ls"
