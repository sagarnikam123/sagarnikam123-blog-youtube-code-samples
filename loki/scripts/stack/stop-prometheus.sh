#!/bin/bash
echo "Stopping Prometheus..."
ps aux | grep prometheus | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
echo "Prometheus stopped"
