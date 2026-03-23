#!/bin/bash
# =============================================================================
# Start SkyWalking with Fuzzy-Train Log Generators
# =============================================================================

set -e

COMPOSE_FILE="docker-compose.fuzzy-train.yml"

echo "🚀 Starting SkyWalking with Fuzzy-Train log generators..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
echo "📦 Starting services..."
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Wait for OAP to be healthy
echo "   Waiting for OAP server..."
timeout=180
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -sf http://localhost:12800/healthcheck > /dev/null 2>&1; then
        echo "   ✅ OAP server is healthy"
        break
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "   ⏳ Still waiting... ($elapsed/$timeout seconds)"
done

if [ $elapsed -ge $timeout ]; then
    echo "   ⚠️  OAP server did not become healthy in time, but continuing..."
fi

echo ""
echo "✅ SkyWalking is running!"
echo ""
echo "📊 Access Points:"
echo "   • SkyWalking UI:    http://localhost:8080"
echo "   • OAP HTTP API:     http://localhost:12800"
echo "   • OAP Metrics:      http://localhost:1234/metrics"
echo "   • BanyanDB Health:  http://localhost:17913/api/healthz"
echo ""
echo "📝 Log Generators:"
echo "   • fuzzy-train-python (1 log/sec)"
echo "   • fuzzy-train-java (1 log/sec)"
echo ""
echo "🔔 Alerts will be sent to Microsoft Teams webhook"
echo ""
echo "💡 Tips:"
echo "   • Wait 1-2 minutes for services to register in UI"
echo "   • Select 'General Service' layer to see fuzzy-train services"
echo "   • Go to 'Log' tab to view generated logs"
echo ""
echo "📋 Useful commands:"
echo "   • View logs:    docker compose -f $COMPOSE_FILE logs -f"
echo "   • Check status: docker compose -f $COMPOSE_FILE ps"
echo "   • Stop:         docker compose -f $COMPOSE_FILE down"
echo "   • Stop + clean: docker compose -f $COMPOSE_FILE down -v"
echo ""
