#!/bin/bash
cd "$HOME/loki-stack/minio"
echo "Starting MinIO Server..."
echo "MinIO will be available at http://127.0.0.1:9000"
echo "MinIO Console will be available at http://127.0.0.1:9091"
./minio server --console-address :9091 "$HOME/.loki-data/minio" &

# Wait for MinIO to start
sleep 3

echo "Setting up MinIO Client..."
./mc alias set myminio http://127.0.0.1:9000 minioadmin minioadmin

echo "Creating MinIO bucket 'loki-data'..."
./mc mb myminio/loki-data 2>/dev/null || echo "Bucket 'loki-data' already exists"

echo "MinIO setup completed"
echo "Press Ctrl+C to stop MinIO server"
wait
