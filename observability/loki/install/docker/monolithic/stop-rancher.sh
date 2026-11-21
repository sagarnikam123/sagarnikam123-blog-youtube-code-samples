#!/bin/bash

# Loki Rancher Desktop Stop Script
# Stops monolithic Loki Rancher Desktop deployment

REMOVE_VOLUMES=false
USE_NERDCTL=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -v, --remove-volumes     Remove data volumes (WARNING: deletes all data)"
    echo "  -n, --nerdctl            Use nerdctl instead of docker"
    echo "  -h, --help               Show this help"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--remove-volumes)
            REMOVE_VOLUMES=true
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
    COMPOSE_CMD="nerdctl compose"
else
    COMPOSE_CMD="docker compose"
fi

echo "🐳 Stopping Loki Rancher Desktop Deployment"
echo "Container Runtime: $(echo $COMPOSE_CMD | cut -d' ' -f1)"
echo ""

# Stop services
echo "🛑 Stopping services..."
$COMPOSE_CMD --profile s3-storage down

if [[ "$REMOVE_VOLUMES" == "true" ]]; then
    echo "⚠️  Removing data volumes..."
    $COMPOSE_CMD --profile s3-storage down -v
    echo "✅ Volumes removed"
else
    echo "💾 Data volumes preserved"
    echo "   Use -v/--remove-volumes to delete all data"
fi

echo ""
echo "✅ Loki Rancher Desktop deployment stopped"
echo ""
echo "📋 Management Commands:"
echo "  • Start again: ./start-rancher.sh"
echo "  • View containers: $(echo $COMPOSE_CMD | cut -d' ' -f1) ps -a"
