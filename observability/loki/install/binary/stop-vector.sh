#!/bin/bash
echo "🛑 Stopping Vector..."
ps aux | grep vector | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo "✅ Vector stopped"
