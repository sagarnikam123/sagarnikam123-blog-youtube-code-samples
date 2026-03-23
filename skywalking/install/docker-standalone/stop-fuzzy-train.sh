#!/bin/bash
# =============================================================================
# Stop SkyWalking with Fuzzy-Train Log Generators
# =============================================================================

set -e

COMPOSE_FILE="docker-compose.fuzzy-train.yml"

echo "🛑 Stopping SkyWalking with Fuzzy-Train log generators..."
echo ""

# Ask if user wants to remove volumes
read -p "Do you want to remove all data volumes? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Stopping services and removing volumes..."
    docker compose -f "$COMPOSE_FILE" down -v
    echo "✅ Services stopped and all data removed"
else
    echo "📦 Stopping services (keeping data)..."
    docker compose -f "$COMPOSE_FILE" down
    echo "✅ Services stopped (data preserved)"
fi

echo ""
echo "💡 To start again, run: ./start-fuzzy-train.sh"
echo ""
