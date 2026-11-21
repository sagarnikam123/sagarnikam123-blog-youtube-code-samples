#!/bin/bash
echo "Stopping Grafana..."
ps aux | grep grafana | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
echo "Grafana stopped"
