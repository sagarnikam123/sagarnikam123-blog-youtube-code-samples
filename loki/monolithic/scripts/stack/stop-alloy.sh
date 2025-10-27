#!/bin/bash
echo "🛑 Stopping Grafana Alloy..."
ps aux | grep alloy | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo "✅ Grafana Alloy stopped"
