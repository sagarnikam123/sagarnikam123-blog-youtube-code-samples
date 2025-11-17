#!/bin/bash

# MinIO OSS Start Script for Loki Monolithic Stack
# Uses MinIO OSS binary for local development

# Create data directory
mkdir -p "$HOME/data/minio"

echo "🚀 Starting MinIO OSS Server..."
echo ""

# Stop any existing MinIO processes
echo "🛑 Stopping existing MinIO processes..."
pkill -f 'minio server' 2>/dev/null || true
sleep 2

# Check if ports are still in use
if lsof -ti:9000 >/dev/null 2>&1; then
    echo "⚠️  Port 9000 still in use, force killing..."
    lsof -ti:9000 | xargs kill -9 2>/dev/null || true
fi
if lsof -ti:9001 >/dev/null 2>&1; then
    echo "⚠️  Port 9001 still in use, force killing..."
    lsof -ti:9001 | xargs kill -9 2>/dev/null || true
fi

# Check if MinIO binary exists
if ! command -v minio >/dev/null 2>&1; then
    echo "📥 MinIO not found. Installing MinIO OSS..."
    if command -v brew >/dev/null 2>&1; then
        # Install MinIO OSS via Homebrew
        brew install minio/stable/minio
    else
        echo "⚠️  Homebrew not found. Installing MinIO OSS manually..."
        curl -fsSL https://dl.min.io/server/minio/release/darwin-amd64/minio -o /usr/local/bin/minio
        chmod +x /usr/local/bin/minio
    fi
fi

# Start MinIO OSS server
echo "🔄 Starting MinIO OSS locally..."
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin \
minio server --console-address :9001 "$HOME/data/minio" >/dev/null 2>&1 &
MINIO_PID=$!

# Wait and check if it started
sleep 3
if kill -0 $MINIO_PID 2>/dev/null; then
    echo "✅ MinIO OSS started successfully"
    echo "🌐 MinIO API: http://127.0.0.1:9000"
    echo "🖥️  MinIO Console: http://127.0.0.1:9001"
    echo "🔑 Credentials: minioadmin/minioadmin"
else
    echo "❌ MinIO OSS failed to start"
    echo "📝 Try using Docker version: ./start-minio-oss.sh"
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
echo "✅ MinIO setup completed"
echo "🛑 Press Ctrl+C to stop MinIO server"
echo ""
echo "📋 Management Commands:"
echo "  • Stop MinIO: pkill -f 'minio server'"

# Wait for MinIO process
if kill -0 $MINIO_PID 2>/dev/null; then
    wait $MINIO_PID
else
    echo "❌ MinIO process not running"
fi
