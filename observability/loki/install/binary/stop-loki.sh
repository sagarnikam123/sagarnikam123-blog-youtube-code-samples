#!/bin/bash
echo "Stopping Loki..."
ps aux | grep loki | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
echo "Loki stopped"
