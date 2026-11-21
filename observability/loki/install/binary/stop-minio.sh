#!/bin/bash
echo "Stopping MinIO..."
ps aux | grep minio | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
echo "MinIO stopped"
