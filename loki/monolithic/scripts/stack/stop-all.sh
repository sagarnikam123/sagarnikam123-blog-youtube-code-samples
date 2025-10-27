#!/bin/bash

# Stop All Loki Stack Services
# Stops all components in the correct order

echo "🛑 Stopping all Loki Stack services..."
echo ""

# Stop log scrapers first
echo "📊 Stopping log scrapers..."
echo "  Stopping Fluent Bit..."
ps aux | grep fluent-bit | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping Grafana Alloy..."
ps aux | grep alloy | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping Vector..."
ps aux | grep vector | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# Stop core services
echo "🏗️  Stopping core services..."
echo "  Stopping Loki..."
ps aux | grep loki | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping Grafana..."
ps aux | grep grafana | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo "  Stopping Prometheus..."
ps aux | grep prometheus | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# Stop storage last
echo "💾 Stopping storage..."
echo "  Stopping MinIO..."
ps aux | grep minio | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# Stop log generators
echo "📝 Stopping log generators..."
ps aux | grep fake-log-generator | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
ps aux | grep fuzzy-train | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo ""
echo "✅ All Loki Stack services stopped!"
echo ""
echo "💡 To clean up data directories, run:"
echo "   ./scripts/utils/cleanup.sh"
