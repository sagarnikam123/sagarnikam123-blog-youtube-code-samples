#!/bin/bash
echo "🛑 Stopping Fluent Bit..."
ps aux | grep fluent-bit | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo "✅ Fluent Bit stopped"
