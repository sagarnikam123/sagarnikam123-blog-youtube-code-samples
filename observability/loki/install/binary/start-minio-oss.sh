#!/bin/bash

# MinIO OSS Start Script for Loki Monolithic Stack
# Uses Docker to run open-source MinIO

# Create data directory
mkdir -p "$HOME/data/minio"

echo "🚀 Starting MinIO OSS Server (Docker)..."
echo ""

# Stop any existing MinIO container
docker stop minio-oss 2>/dev/null || true
docker rm minio-oss 2>/dev/null || true

# Start MinIO OSS with Docker
echo "🔄 Starting MinIO OSS container..."
docker run -d \
  --name minio-oss \
  -p 9000:9000 \
  -p 9001:9001 \
  -v "$HOME/data/minio:/data" \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio:latest \
  server /data --console-address ":9001"

if [ $? -eq 0 ]; then
    echo "✅ MinIO OSS started successfully"
    echo "🌐 MinIO API: http://127.0.0.1:9000"
    echo "🖥️  MinIO Console: http://127.0.0.1:9001"
    echo "🔑 Credentials: minioadmin/minioadmin"
else
    echo "❌ Failed to start MinIO OSS"
    echo "   Please ensure Docker is running"
    exit 1
fi

# Wait for MinIO to start
echo "⏳ Waiting for MinIO to start..."
sleep 5

# Setup MinIO client
if ! command -v mc >/dev/null 2>&1; then
    echo "📥 Installing MinIO client..."
    if command -v brew >/dev/null 2>&1; then
        brew install minio/stable/mc
    else
        echo "⚠️  Homebrew not found. Installing mc manually..."
        curl -fsSL https://dl.min.io/client/mc/release/darwin-amd64/mc -o /usr/local/bin/mc
        chmod +x /usr/local/bin/mc
    fi
fi

if command -v mc >/dev/null 2>&1; then
    echo "🔧 Setting up MinIO Client..."
    mc alias set myminio http://127.0.0.1:9000 minioadmin minioadmin

    echo "📦 Creating MinIO bucket 'loki-chunks'..."
    mc mb myminio/loki-chunks 2>/dev/null || echo "Bucket 'loki-chunks' already exists"

    echo "📦 Creating MinIO bucket 'loki-ruler'..."
    mc mb myminio/loki-ruler 2>/dev/null || echo "Bucket 'loki-ruler' already exists"
else
    echo "❌ Failed to install MinIO client"
    echo "   Buckets need to be created manually via web console"
fi

echo ""
echo "✅ MinIO OSS setup completed"
echo ""
echo "📋 Management Commands:"
echo "  • View logs: docker logs -f minio-oss"
echo "  • Stop MinIO: docker stop minio-oss"
echo "  • Remove container: docker rm minio-oss"
echo "  • Access console: http://127.0.0.1:9001"
echo "  • Access API: http://127.0.0.1:9000"
echo ""
echo "🛑 Press Ctrl+C to stop monitoring (container will keep running)"

# Monitor container logs
docker logs -f minio-oss
